"""
setup_database.py
Creates the clinic.db SQLite database with schema and realistic dummy data.
Run once: python setup_database.py
"""

import sqlite3
import random
from datetime import datetime, timedelta, date

DB_PATH = "clinic.db"

# ─── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS treatments;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS patients;

CREATE TABLE IF NOT EXISTS patients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT,
    phone           TEXT,
    date_of_birth   DATE,
    gender          TEXT,
    city            TEXT,
    registered_date DATE
);

CREATE TABLE IF NOT EXISTS doctors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    specialization  TEXT,
    department      TEXT,
    phone           TEXT
);

CREATE TABLE IF NOT EXISTS appointments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER,
    doctor_id        INTEGER,
    appointment_date DATETIME,
    status           TEXT,
    notes            TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS treatments (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id     INTEGER,
    treatment_name     TEXT,
    cost               REAL,
    duration_minutes   INTEGER,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER,
    invoice_date  DATE,
    total_amount  REAL,
    paid_amount   REAL,
    status        TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
"""

# ─── Seed data ─────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Bhavna", "Chirag", "Deepika",
    "Eshan", "Farah", "Gaurav", "Himani", "Ishan", "Jyoti", "Karan",
    "Lavanya", "Manish", "Neha", "Omkar", "Priya", "Rahul", "Sneha",
    "Tarun", "Usha", "Vikram", "Yogesh", "Zara", "Rohan", "Meera",
    "Siddharth", "Kavita", "Aditya", "Pooja", "Sameer", "Riya", "Neeraj",
    "Anjali", "Harsh", "Divya", "Mohit", "Shalini", "Abhishek", "Tanvi",
    "Rajesh", "Sunita", "Vivek", "Geeta", "Nikhil", "Rekha", "Suresh", "Lata"
]

LAST_NAMES = [
    "Sharma", "Gupta", "Patel", "Verma", "Singh", "Kumar", "Mehta",
    "Joshi", "Shah", "Rao", "Reddy", "Nair", "Pillai", "Das", "Bose",
    "Malhotra", "Khanna", "Agarwal", "Mishra", "Tiwari", "Srivastava",
    "Pandey", "Chauhan", "Dubey", "Yadav", "Saxena", "Banerjee", "Mukherjee"
]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Vijayawada", "Surat"
]

SPECIALIZATIONS = [
    "Dermatology", "Cardiology", "Orthopedics", "General", "Pediatrics"
]

DEPARTMENTS = {
    "Dermatology": "Skin & Aesthetics",
    "Cardiology":  "Heart & Vascular",
    "Orthopedics": "Bones & Joints",
    "General":     "General Medicine",
    "Pediatrics":  "Child Health"
}

DOCTOR_NAMES = [
    ("Dr. Ananya Sharma",  "Dermatology"),
    ("Dr. Rohan Mehta",    "Dermatology"),
    ("Dr. Priya Nair",     "Dermatology"),
    ("Dr. Vikram Singh",   "Cardiology"),
    ("Dr. Sunita Gupta",   "Cardiology"),
    ("Dr. Aditya Rao",     "Cardiology"),
    ("Dr. Karan Patel",    "Orthopedics"),
    ("Dr. Meera Joshi",    "Orthopedics"),
    ("Dr. Siddharth Das",  "Orthopedics"),
    ("Dr. Neha Verma",     "General"),
    ("Dr. Rahul Kumar",    "General"),
    ("Dr. Pooja Saxena",   "General"),
    ("Dr. Chirag Reddy",   "Pediatrics"),
    ("Dr. Divya Pillai",   "Pediatrics"),
    ("Dr. Arjun Banerjee", "Pediatrics"),
]

TREATMENTS = {
    "Dermatology": [
        ("Acne Treatment",        random.uniform, (200, 800)),
        ("Chemical Peel",         random.uniform, (500, 2000)),
        ("Laser Hair Removal",    random.uniform, (1000, 5000)),
        ("Skin Biopsy",           random.uniform, (300, 1200)),
        ("Eczema Consultation",   random.uniform, (150, 600)),
    ],
    "Cardiology": [
        ("ECG",                   random.uniform, (300, 800)),
        ("Echocardiography",      random.uniform, (1500, 4000)),
        ("Stress Test",           random.uniform, (800, 2500)),
        ("Blood Pressure Mgmt",   random.uniform, (150, 500)),
        ("Angioplasty",           random.uniform, (3000, 5000)),
    ],
    "Orthopedics": [
        ("X-Ray",                 random.uniform, (200, 600)),
        ("Physiotherapy",         random.uniform, (300, 1200)),
        ("Fracture Treatment",    random.uniform, (1000, 3500)),
        ("Joint Injection",       random.uniform, (500, 2000)),
        ("MRI Scan",              random.uniform, (2000, 4500)),
    ],
    "General": [
        ("General Consultation",  random.uniform, (100, 400)),
        ("Blood Test Panel",      random.uniform, (200, 800)),
        ("Vaccination",           random.uniform, (150, 600)),
        ("Diabetes Management",   random.uniform, (200, 700)),
        ("Health Screening",      random.uniform, (500, 1500)),
    ],
    "Pediatrics": [
        ("Child Wellness Visit",  random.uniform, (100, 350)),
        ("Immunization",          random.uniform, (100, 400)),
        ("Growth Assessment",     random.uniform, (150, 450)),
        ("Fever Treatment",       random.uniform, (100, 350)),
        ("Nutritional Counseling",random.uniform, (200, 600)),
    ],
}

STATUSES     = ["Scheduled", "Completed", "Cancelled", "No-Show"]
INV_STATUSES = ["Paid", "Pending", "Overdue"]

NOTES_POOL = [
    "Patient reported mild discomfort.",
    "Follow-up in 2 weeks.",
    "Prescribed medication as discussed.",
    "Lab results pending.",
    "Patient doing well post-procedure.",
    "Referred to specialist.",
    "No complications observed.",
    None, None, None   # ~30 % NULL
]


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def rand_datetime(start: date, end: date) -> datetime:
    d   = rand_date(start, end)
    hour = random.randint(8, 17)
    minute = random.choice([0, 15, 30, 45])
    return datetime(d.year, d.month, d.day, hour, minute)


def rand_phone() -> str | None:
    if random.random() < 0.15:   # 15 % NULL
        return None
    return f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def rand_email(first: str, last: str) -> str | None:
    if random.random() < 0.20:   # 20 % NULL
        return None
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    return f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{random.choice(domains)}"


def build_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Create tables
    cur.executescript(SCHEMA)
    conn.commit()

    today  = date.today()
    year_ago = today - timedelta(days=365)

    # ── Doctors (15) ────────────────────────────────────────────────────────
    doctors = []
    for name, spec in DOCTOR_NAMES:
        dept  = DEPARTMENTS[spec]
        phone = rand_phone() or f"+91-9{random.randint(100000000, 999999999)}"
        cur.execute(
            "INSERT INTO doctors (name, specialization, department, phone) VALUES (?, ?, ?, ?)",
            (name, spec, dept, phone)
        )
        doctors.append((cur.lastrowid, spec))
    conn.commit()

    # ── Patients (200) ──────────────────────────────────────────────────────
    # Create a weight distribution so some patients are repeaters
    patients = []
    for _ in range(200):
        fn   = random.choice(FIRST_NAMES)
        ln   = random.choice(LAST_NAMES)
        dob  = rand_date(date(1950, 1, 1), date(2010, 12, 31))
        reg  = rand_date(year_ago, today)
        city = random.choice(CITIES)
        gender = random.choice(["M", "F"])
        cur.execute(
            """INSERT INTO patients
               (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fn, ln, rand_email(fn, ln), rand_phone(), dob.isoformat(),
             gender, city, reg.isoformat())
        )
        patients.append(cur.lastrowid)
    conn.commit()

    # ── Appointments (500) ──────────────────────────────────────────────────
    # Skew: 30 % of patients get 60 % of appointments (repeat visitors)
    heavy_patients = random.sample(patients, k=60)
    light_patients = [p for p in patients if p not in heavy_patients]

    def pick_patient():
        if random.random() < 0.60:
            return random.choice(heavy_patients)
        return random.choice(light_patients)

    # Skew doctors too (some busier than others)
    doctor_weights = [random.uniform(0.5, 3.0) for _ in doctors]
    total_w = sum(doctor_weights)
    doctor_probs = [w / total_w for w in doctor_weights]

    appointments = []   # (appt_id, doctor_id, patient_id, status)
    for _ in range(500):
        pat_id  = pick_patient()
        doc_idx = random.choices(range(len(doctors)), weights=doctor_probs)[0]
        doc_id, _ = doctors[doc_idx]
        appt_dt = rand_datetime(year_ago, today)
        status  = random.choices(STATUSES, weights=[15, 55, 20, 10])[0]
        note    = random.choice(NOTES_POOL)
        cur.execute(
            """INSERT INTO appointments
               (patient_id, doctor_id, appointment_date, status, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (pat_id, doc_id, appt_dt.strftime("%Y-%m-%d %H:%M:%S"), status, note)
        )
        appointments.append((cur.lastrowid, doc_id, pat_id, status))
    conn.commit()

    # ── Treatments (350, only for Completed appointments) ───────────────────
    completed = [(aid, did, pid) for aid, did, pid, st in appointments if st == "Completed"]
    selected  = random.sample(completed, k=min(350, len(completed)))

    # Build doctor → specialization map
    doc_spec = {did: spec for did, spec in doctors}

    for appt_id, doc_id, _ in selected:
        spec  = doc_spec.get(doc_id, "General")
        pool  = TREATMENTS.get(spec, TREATMENTS["General"])
        tname, fn_rand, (lo, hi) = random.choice(pool)
        cost  = round(fn_rand(lo, hi), 2)
        dur   = random.randint(15, 120)
        cur.execute(
            """INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
               VALUES (?, ?, ?, ?)""",
            (appt_id, tname, cost, dur)
        )
    conn.commit()

    # ── Invoices (300) ──────────────────────────────────────────────────────
    invoice_patients = random.sample(patients, k=min(300, len(patients)))
    for pat_id in invoice_patients:
        inv_date   = rand_date(year_ago, today)
        total      = round(random.uniform(100, 5000), 2)
        inv_status = random.choices(INV_STATUSES, weights=[55, 25, 20])[0]
        paid       = (total if inv_status == "Paid"
                      else round(random.uniform(0, total * 0.5), 2) if inv_status == "Pending"
                      else 0.0)
        cur.execute(
            """INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
               VALUES (?, ?, ?, ?, ?)""",
            (pat_id, inv_date.isoformat(), total, paid, inv_status)
        )
    conn.commit()
    conn.close()

    print(f"✅ Database created: {DB_PATH}")
    print(f"   Patients      : 200")
    print(f"   Doctors       : 15  (across 5 specializations)")
    print(f"   Appointments  : 500 (varied statuses over last 12 months)")
    print(f"   Treatments    : {len(selected)} (linked to completed appointments)")
    print(f"   Invoices      : {len(invoice_patients)}")


if __name__ == "__main__":
    build_db()
