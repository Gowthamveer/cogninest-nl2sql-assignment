"""
seed_memory.py
Pre-seeds DemoAgentMemory with 15 known-good question → SQL pairs so the
Vanna 2.0 agent has a strong head-start before any user asks a question.

Run once AFTER setup_database.py:
    python seed_memory.py
"""

import asyncio
import uuid

from vanna import ToolContext
from vanna.core.user import User

# Import shared singletons (builds the Agent + memory on import)
from vanna_setup import agent_memory, DEFAULT_USER

# ─── 15 seed pairs ─────────────────────────────────────────────────────────────

SEED_QA: list[dict] = [

    # ── Patient queries ──────────────────────────────────────────────────────
    {
        "question": "How many patients do we have?",
        "sql": "SELECT COUNT(*) AS total_patients FROM patients;",
    },
    {
        "question": "List all patients and their cities",
        "sql": (
            "SELECT first_name, last_name, city "
            "FROM patients "
            "ORDER BY last_name, first_name;"
        ),
    },
    {
        "question": "How many male and female patients do we have?",
        "sql": (
            "SELECT gender, COUNT(*) AS count "
            "FROM patients "
            "GROUP BY gender;"
        ),
    },
    {
        "question": "Which city has the most patients?",
        "sql": (
            "SELECT city, COUNT(*) AS patient_count "
            "FROM patients "
            "GROUP BY city "
            "ORDER BY patient_count DESC "
            "LIMIT 1;"
        ),
    },
    {
        "question": "List patients who visited more than 3 times",
        "sql": (
            "SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count "
            "FROM patients p "
            "JOIN appointments a ON a.patient_id = p.id "
            "GROUP BY p.id, p.first_name, p.last_name "
            "HAVING COUNT(a.id) > 3 "
            "ORDER BY visit_count DESC;"
        ),
    },

    # ── Doctor queries ───────────────────────────────────────────────────────
    {
        "question": "List all doctors and their specializations",
        "sql": (
            "SELECT name, specialization, department "
            "FROM doctors "
            "ORDER BY specialization, name;"
        ),
    },
    {
        "question": "Which doctor has the most appointments?",
        "sql": (
            "SELECT d.name, d.specialization, COUNT(a.id) AS appointment_count "
            "FROM doctors d "
            "JOIN appointments a ON a.doctor_id = d.id "
            "GROUP BY d.id, d.name, d.specialization "
            "ORDER BY appointment_count DESC "
            "LIMIT 1;"
        ),
    },

    # ── Appointment queries ───────────────────────────────────────────────────
    {
        "question": "Show me appointments for last month",
        "sql": (
            "SELECT a.id, p.first_name || ' ' || p.last_name AS patient, "
            "       d.name AS doctor, a.appointment_date, a.status "
            "FROM appointments a "
            "JOIN patients p ON p.id = a.patient_id "
            "JOIN doctors  d ON d.id = a.doctor_id "
            "WHERE strftime('%Y-%m', a.appointment_date) = "
            "      strftime('%Y-%m', date('now', '-1 month')) "
            "ORDER BY a.appointment_date;"
        ),
    },
    {
        "question": "How many cancelled appointments last quarter?",
        "sql": (
            "SELECT COUNT(*) AS cancelled_count "
            "FROM appointments "
            "WHERE status = 'Cancelled' "
            "  AND appointment_date >= date('now', '-3 months');"
        ),
    },
    {
        "question": "What percentage of appointments are no-shows?",
        "sql": (
            "SELECT "
            "  ROUND(100.0 * SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) "
            "        / COUNT(*), 2) AS no_show_percentage "
            "FROM appointments;"
        ),
    },
    {
        "question": "Show monthly appointment count for the past 6 months",
        "sql": (
            "SELECT strftime('%Y-%m', appointment_date) AS month, "
            "       COUNT(*) AS appointment_count "
            "FROM appointments "
            "WHERE appointment_date >= date('now', '-6 months') "
            "GROUP BY month "
            "ORDER BY month;"
        ),
    },

    # ── Financial queries ─────────────────────────────────────────────────────
    {
        "question": "What is the total revenue?",
        "sql": (
            "SELECT ROUND(SUM(total_amount), 2) AS total_revenue "
            "FROM invoices "
            "WHERE status = 'Paid';"
        ),
    },
    {
        "question": "Show revenue by doctor",
        "sql": (
            "SELECT d.name AS doctor, d.specialization, "
            "       ROUND(SUM(t.cost), 2) AS total_revenue "
            "FROM treatments t "
            "JOIN appointments a ON a.id = t.appointment_id "
            "JOIN doctors      d ON d.id = a.doctor_id "
            "GROUP BY d.id, d.name, d.specialization "
            "ORDER BY total_revenue DESC;"
        ),
    },
    {
        "question": "Show unpaid invoices",
        "sql": (
            "SELECT p.first_name || ' ' || p.last_name AS patient, "
            "       i.invoice_date, i.total_amount, i.paid_amount, "
            "       ROUND(i.total_amount - i.paid_amount, 2) AS balance, i.status "
            "FROM invoices i "
            "JOIN patients p ON p.id = i.patient_id "
            "WHERE i.status IN ('Pending', 'Overdue') "
            "ORDER BY i.status, balance DESC;"
        ),
    },

    # ── Time-based queries ────────────────────────────────────────────────────
    {
        "question": "Top 5 patients by total spending",
        "sql": (
            "SELECT p.first_name || ' ' || p.last_name AS patient, "
            "       ROUND(SUM(i.total_amount), 2) AS total_spending "
            "FROM invoices i "
            "JOIN patients p ON p.id = i.patient_id "
            "GROUP BY p.id, p.first_name, p.last_name "
            "ORDER BY total_spending DESC "
            "LIMIT 5;"
        ),
    },
]

# ─── Seeding logic ─────────────────────────────────────────────────────────────

async def seed_memory() -> None:
    """Write all 15 Q→SQL pairs into DemoAgentMemory."""

    ctx = ToolContext(
        user=DEFAULT_USER,
        conversation_id="seed-session",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory,
    )

    for i, pair in enumerate(SEED_QA, start=1):
        await agent_memory.save_tool_usage(
            question=pair["question"],
            tool_name="run_sql",
            args={"sql": pair["sql"]},
            context=ctx,
            success=True,
            metadata={"source": "manual_seed", "index": i},
        )
        print(f"  [{i:02d}/15] Seeded: {pair['question'][:60]}")

    print(f"\n✅ Agent memory seeded with {len(SEED_QA)} Q&A pairs.")
    print(   "   The agent will now use these as examples for new questions.")


if __name__ == "__main__":
    print("🌱 Seeding Vanna 2.0 agent memory …\n")
    asyncio.run(seed_memory())
