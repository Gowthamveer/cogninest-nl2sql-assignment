"""
vanna_setup.py
Initialises the Vanna 2.0 Agent with:
  - OpenAILlmService    (Ollama local — OpenAI-compatible, FREE, no API key)
  - ToolRegistry        (RunSqlTool + VisualizeDataTool + memory tools)
  - DemoAgentMemory     (in-memory learning store)
  - SqliteRunner        (built-in SQLite execution)
  - SimpleUserResolver  (single default user)
  - Agent               (wired together)

LLM Provider
────────────
This project uses Ollama (Option C) — a completely free, local LLM.
No API key is required. Just install Ollama and run: ollama pull mistral

To switch providers, set LLM_PROVIDER in your .env file:
  LLM_PROVIDER=ollama   (default — no key needed)
  LLM_PROVIDER=gemini   (needs GOOGLE_API_KEY)
  LLM_PROVIDER=groq     (needs GROQ_API_KEY)
"""

import os
from dotenv import load_dotenv

from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
)
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory

# LLM imports — use the one matching your chosen provider
from vanna.integrations.openai import OpenAILlmService   # For Ollama & Groq
# from vanna.integrations.google import GeminiLlmService  # Uncomment for Gemini

load_dotenv()

DB_PATH = "clinic.db"

# ─── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_USER = User(
    id="default_user",
    username="clinic_user",
    email="user@clinic.ai",
    roles=["user"],
)

# ─── Simple User Resolver ──────────────────────────────────────────────────────

class SimpleUserResolver(UserResolver):
    """Treats every request as the same default user (suitable for a demo)."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return DEFAULT_USER


# ─── LLM Service Factory ──────────────────────────────────────────────────────

def _create_llm_service():
    """
    Creates the LLM service based on LLM_PROVIDER env var.

    Supported values:
      - 'ollama' (default) — local, no API key needed
      - 'groq'             — free cloud, needs GROQ_API_KEY
      - 'gemini'           — free cloud, needs GOOGLE_API_KEY
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

    if provider == "ollama":
        # Option C — Ollama (local, no API key)
        # Uses OpenAI-compatible endpoint exposed by Ollama
        return OpenAILlmService(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            api_key="ollama",                              # placeholder, Ollama ignores it
            base_url="http://localhost:11434/v1",           # Ollama's OpenAI-compatible API
        )

    elif provider == "groq":
        # Option B — Groq (free cloud tier)
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not set in .env — get a free key at https://console.groq.com")
        return OpenAILlmService(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
        )

    elif provider == "gemini":
        # Option A — Google Gemini (free via AI Studio)
        from vanna.integrations.google import GeminiLlmService
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_key:
            raise ValueError("GOOGLE_API_KEY not set in .env — get a free key at https://aistudio.google.com/apikey")
        return GeminiLlmService(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=gemini_key,
            temperature=0.2,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER='{provider}'. "
            f"Supported: ollama, groq, gemini"
        )


# ─── Agent Factory ─────────────────────────────────────────────────────────────

def build_agent() -> tuple[Agent, DemoAgentMemory]:
    """
    Creates and returns the Vanna 2.0 Agent and its shared memory instance.

    Returns
    -------
    agent  : the fully wired Agent
    memory : the DemoAgentMemory so callers can inspect / seed it directly
    """

    # 1. LLM Service (auto-detected from LLM_PROVIDER env var)
    llm_service = _create_llm_service()

    # 2. Database runner
    sql_runner = SqliteRunner(database_path=DB_PATH)

    # 3. Tool Registry
    registry = ToolRegistry()
    registry.register_local_tool(RunSqlTool(sql_runner=sql_runner), access_groups=["*"])
    registry.register_local_tool(VisualizeDataTool(), access_groups=["*"])
    registry.register_local_tool(SaveQuestionToolArgsTool(), access_groups=["*"])
    registry.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=["*"])
    # 4. Agent Memory
    memory = DemoAgentMemory(max_items=5_000)

    # 5. User Resolver
    user_resolver = SimpleUserResolver()

    # 6. Agent Config
    config = AgentConfig(
        max_tool_iterations=12,
        stream_responses=False,   # we collect all chunks in main.py
        temperature=0.0,
    )

    # 7. Agent
    agent = Agent(
        llm_service=llm_service,
        tool_registry=registry,
        user_resolver=user_resolver,
        agent_memory=memory,
        config=config,
    )

    return agent, memory


# ─── Module-level singletons (imported by main.py and seed_memory.py) ─────────

agent, agent_memory = build_agent()

