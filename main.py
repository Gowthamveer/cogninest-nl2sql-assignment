"""
main.py
FastAPI application for the NL2SQL clinic chatbot (Vanna 2.0).

Endpoints
─────────
POST /chat    — ask a question in English, get SQL + results + optional chart
GET  /health  — liveness + memory-item count

Run:
    uvicorn main:app --reload --port 8000
"""

import asyncio
from contextlib import asynccontextmanager
import json
import logging
import re
import sqlite3
import time
import uuid
from functools import lru_cache
from typing import Any, Optional

import plotly.io as pio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from vanna.core.user import RequestContext

# ── import shared agent (built once at startup) ────────────────────────────────
from vanna_setup import DB_PATH, agent, agent_memory
from seed_memory import seed_memory   # also available as a helper

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("nl2sql")

# ─── Rate Limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ─── FastAPI App ──────────────────────────────────────────────────────────────

# ─── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle for the FastAPI app."""
    logger.info("🚀 NL2SQL API starting up …")
    logger.info("   Database  : %s", DB_PATH)
    logger.info("   Tables    : %s", get_db_table_info())
    try:
        await seed_memory()
        logger.info("   Memory    : seeded with 15 Q&A pairs")
    except Exception as exc:
        logger.warning("   Memory seed skipped: %s", exc)
    yield   # ← app runs here
    logger.info("👋 NL2SQL API shutting down.")


app = FastAPI(
    title="NL2SQL Clinic Chatbot",
    description="Ask plain-English questions about the clinic database.",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Simple in-process cache (question → response dict) ───────────────────────

_CACHE: dict[str, dict] = {}
CACHE_TTL = 300        # seconds
MAX_CACHE_SIZE = 500   # max entries before oldest are evicted


def _cache_get(key: str) -> dict | None:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["_ts"]) < CACHE_TTL:
        logger.info("Cache HIT for: %s", key[:60])
        return entry["data"]
    return None


def _cache_set(key: str, data: dict) -> None:
    # Evict oldest entries if cache is full
    if len(_CACHE) >= MAX_CACHE_SIZE:
        oldest_key = min(_CACHE, key=lambda k: _CACHE[k]["_ts"])
        del _CACHE[oldest_key]
    _CACHE[key] = {"_ts": time.time(), "data": data}


# ─── SQL Validation ───────────────────────────────────────────────────────────

BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "EXEC", "EXECUTE", "XP_", "SP_", "GRANT", "REVOKE",
    "SHUTDOWN", "SQLITE_MASTER", "SQLITE_SEQUENCE", "ATTACH", "DETACH",
}


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    Only SELECT statements that contain no dangerous keywords are allowed.
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty."

    normalised = sql.upper().strip()

    # Must start with SELECT
    if not normalised.startswith("SELECT"):
        return False, "Only SELECT queries are permitted."

    # Check for blocked keywords
    for kw in BLOCKED_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, normalised):
            return False, f"Dangerous keyword detected: {kw}"

    return True, "ok"


# ─── Schema helper (for system prompt / health) ───────────────────────────────

def get_db_table_info() -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return ", ".join(tables)
    except Exception:
        return "unavailable"


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Plain-English question about the clinic data.",
        examples=["Show me the top 5 patients by total spending"],
    )


class ChatResponse(BaseModel):
    question: str
    message: str
    sql_query: Optional[str] = None
    columns: Optional[list[str]] = None
    rows: Optional[list[list[Any]]] = None
    row_count: Optional[int] = None
    chart: Optional[dict] = None
    chart_type: Optional[str] = None
    cached: bool = False
    error: Optional[str] = None


# ─── Component Parsers ────────────────────────────────────────────────────────

def _extract_sql(text: str) -> Optional[str]:
    """Pull first ```sql ... ``` block, or the first SELECT statement."""
    # markdown code block
    m = re.search(r"```(?:sql)?\s*(SELECT[\s\S]+?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # bare SELECT
    m = re.search(r"(SELECT\s[\s\S]+?;)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _parse_components(components: list) -> dict:
    """
    Walk the list of UiComponent objects yielded by Agent.send_message and
    pull out: final_text, sql, data_frame, chart_json.
    """
    result = {
        "text": [],
        "sql": None,
        "columns": None,
        "rows": None,
        "chart": None,
        "chart_type": None,
    }

    for comp in components:
        # Rich text / simple text
        if hasattr(comp, "rich_component") and comp.rich_component is not None:
            rc = comp.rich_component
            # RichTextComponent
            if hasattr(rc, "content"):
                text_val = rc.content
                result["text"].append(str(text_val))
                sql_found = _extract_sql(str(text_val))
                if sql_found and not result["sql"]:
                    result["sql"] = sql_found

            # DataFrameComponent
            if hasattr(rc, "dataframe") and rc.dataframe is not None:
                df = rc.dataframe
                result["columns"] = list(df.columns)
                result["rows"]    = df.values.tolist()

            # SimpleTextComponent / IconTextComponent
            if hasattr(rc, "text"):
                txt = str(rc.text)
                result["text"].append(txt)
                sql_found = _extract_sql(txt)
                if sql_found and not result["sql"]:
                    result["sql"] = sql_found

        # Simple component
        if hasattr(comp, "simple_component") and comp.simple_component is not None:
            sc = comp.simple_component
            if hasattr(sc, "text"):
                txt = str(sc.text)
                result["text"].append(txt)
                sql_found = _extract_sql(txt)
                if sql_found and not result["sql"]:
                    result["sql"] = sql_found

        # ArtifactComponent – might carry a plotly figure JSON
        if hasattr(comp, "rich_component"):
            rc = comp.rich_component
            if rc and hasattr(rc, "artifact"):
                try:
                    fig_json = json.loads(rc.artifact)
                    result["chart"]      = fig_json
                    result["chart_type"] = "bar"
                except Exception:
                    pass

    result["message"] = "\n".join(filter(None, result["text"])).strip()
    if not result["message"]:
        result["message"] = "Query executed successfully."

    return result


def _run_sql_direct(sql: str) -> tuple[list[str], list[list]]:
    """Fallback: run validated SQL directly against SQLite and return results."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(sql)
    columns = [d[0] for d in cur.description] if cur.description else []
    rows    = [list(row) for row in cur.fetchall()]
    conn.close()
    return columns, rows


# ─── Startup logic moved to lifespan() above ─────────────────────────────────


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """Liveness check + memory diagnostics."""
    db_ok = False
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    mem_items = len(agent_memory._memories)

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "db_path": DB_PATH,
        "tables": get_db_table_info(),
        "agent_memory_items": mem_items,
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("30/minute")
async def chat(request: Request, body: QuestionRequest):
    """
    Accepts a plain-English question, generates SQL with Vanna 2.0, executes it,
    and returns results + optional chart.
    """
    question = body.question.strip()
    logger.info("📨 Question: %s", question)

    # ── Cache check ──────────────────────────────────────────────────────────
    cached = _cache_get(question)
    if cached:
        return ChatResponse(**cached, cached=True)

    # ── Build request context ────────────────────────────────────────────────
    req_ctx = RequestContext(
        headers={},
        cookies={},
        metadata={"request_id": str(uuid.uuid4())},
    )

    # ── Call Vanna Agent ─────────────────────────────────────────────────────
    components: list = []
    try:
        async for component in agent.send_message(req_ctx, question):
            components.append(component)
    except Exception as exc:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

    parsed = _parse_components(components)

    # ── SQL Validation ───────────────────────────────────────────────────────
    sql = parsed["sql"]
    if sql:
        valid, reason = validate_sql(sql)
        if not valid:
            logger.warning("SQL validation failed: %s | SQL: %s", reason, sql)
            return ChatResponse(
                question=question,
                message="I generated a query that cannot be executed for security reasons.",
                error=f"SQL validation failed: {reason}",
            )

        # ── Fallback direct execution if agent didn't return data ────────────
        if parsed["columns"] is None:
            try:
                cols, rows = _run_sql_direct(sql)
                parsed["columns"] = cols
                parsed["rows"]    = rows
                if not rows:
                    parsed["message"] = "The query ran successfully but returned no data."
            except Exception as exc:
                logger.error("SQL execution error: %s", exc)
                return ChatResponse(
                    question=question,
                    message="The query ran into an error during execution.",
                    sql_query=sql,
                    error=str(exc),
                )

    elif not parsed["columns"]:
        # Agent couldn't generate any SQL
        logger.warning("No SQL generated for: %s", question)
        return ChatResponse(
            question=question,
            message=parsed["message"] or "I could not generate a SQL query for that question. "
                    "Please try rephrasing it.",
            error="No SQL generated",
        )

    # ── Build response ───────────────────────────────────────────────────────
    row_count = len(parsed["rows"]) if parsed["rows"] else 0
    if row_count == 0 and not parsed.get("error"):
        parsed["message"] = "No data found for your query."

    response_data = {
        "question":  question,
        "message":   parsed["message"],
        "sql_query": sql,
        "columns":   parsed["columns"],
        "rows":      parsed["rows"],
        "row_count": row_count,
        "chart":     parsed["chart"],
        "chart_type": parsed["chart_type"],
        "error":     None,
        "cached":    False,
    }

    _cache_set(question, response_data)
    logger.info("✅ Answered | rows=%d | sql=%s", row_count, (sql or "")[:80])
    return ChatResponse(**response_data)


# ─── Dev entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

