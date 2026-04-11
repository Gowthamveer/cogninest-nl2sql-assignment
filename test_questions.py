"""
test_questions.py
Automated test runner — sends all 20 assignment questions to the running API
and prints a formatted report.

Usage (server must be running):
    python test_questions.py
"""

import json
import time

import requests

BASE_URL = "http://localhost:8001"

QUESTIONS = [
    (1,  "How many patients do we have?",                     "Returns count"),
    (2,  "List all doctors and their specializations",        "Returns doctor list"),
    (3,  "Show me appointments for last month",               "Filters by date"),
    (4,  "Which doctor has the most appointments?",           "Aggregation + ordering"),
    (5,  "What is the total revenue?",                        "SUM of invoice amounts"),
    (6,  "Show revenue by doctor",                            "JOIN + GROUP BY"),
    (7,  "How many cancelled appointments last quarter?",     "Status filter + date"),
    (8,  "Top 5 patients by spending",                        "JOIN + ORDER + LIMIT"),
    (9,  "Average treatment cost by specialization",          "Multi-table JOIN + AVG"),
    (10, "Show monthly appointment count for the past 6 months", "Date grouping"),
    (11, "Which city has the most patients?",                 "GROUP BY + COUNT"),
    (12, "List patients who visited more than 3 times",       "HAVING clause"),
    (13, "Show unpaid invoices",                              "Status filter"),
    (14, "What percentage of appointments are no-shows?",     "Percentage calculation"),
    (15, "Show the busiest day of the week for appointments", "Date function"),
    (16, "Revenue trend by month",                            "Time series"),
    (17, "Average appointment duration by doctor",            "AVG + GROUP BY"),
    (18, "List patients with overdue invoices",               "JOIN + filter"),
    (19, "Compare revenue between departments",               "JOIN + GROUP BY"),
    (20, "Show patient registration trend by month",          "Date grouping"),
]

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"


def run_tests():
    print("\n" + "═" * 70)
    print("  NL2SQL TEST RUNNER — 20 Questions")
    print("═" * 70)

    # Check server
    try:
        h = requests.get(f"{BASE_URL}/health", timeout=5)
        info = h.json()
        print(f"  Server : {BASE_URL}")
        print(f"  DB     : {info.get('database', '?')}")
        print(f"  Memory : {info.get('agent_memory_items', '?')} items")
    except Exception as e:
        print(f"{RED}  ❌ Server not reachable: {e}{RESET}")
        print("  Start with: uvicorn main:app --port 8000")
        return

    print("═" * 70 + "\n")

    passed = failed = partial = 0
    results = []

    for num, question, expected in QUESTIONS:
        print(f"Q{num:02d}  {question}")
        t0 = time.time()
        try:
            resp = requests.post(
                f"{BASE_URL}/chat",
                json={"question": question},
                timeout=60,
            )
            elapsed = time.time() - t0
            data = resp.json()

            sql       = data.get("sql_query") or ""
            row_count = data.get("row_count") or 0
            error     = data.get("error")
            cached    = data.get("cached", False)

            if error and not sql:
                status = "FAIL"
                icon   = f"{RED}❌{RESET}"
                failed += 1
            elif not sql:
                status = "PARTIAL"
                icon   = f"{YELLOW}⚠️ {RESET}"
                partial += 1
            else:
                status = "PASS"
                icon   = f"{GREEN}✅{RESET}"
                passed += 1

            tag = "(cached)" if cached else ""
            print(f"     {icon} {status}  |  rows={row_count}  |  {elapsed:.1f}s {tag}")
            if sql:
                short_sql = sql.replace("\n", " ").strip()[:80]
                print(f"     SQL: {short_sql}{'…' if len(sql) > 80 else ''}")
            if error:
                print(f"     ERR: {error}")

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"     {RED}❌ EXCEPTION{RESET}: {exc}  ({elapsed:.1f}s)")
            failed += 1
            status = "FAIL"
            sql    = ""

        results.append({"num": num, "question": question, "status": status, "sql": sql})
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    total = len(QUESTIONS)
    print("═" * 70)
    print(f"  RESULTS:  {GREEN}✅ Passed: {passed}{RESET}  |  "
          f"{YELLOW}⚠️  Partial: {partial}{RESET}  |  "
          f"{RED}❌ Failed: {failed}{RESET}  |  Total: {total}")
    print(f"  PASS RATE: {passed}/{total} = {100*passed//total}%")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    run_tests()
