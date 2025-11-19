from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import sqlite3


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = "dental.db"
def get_db():
    conn = sqlite3.connect(db)
    # make this to return list of dict instead of list of tupple
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html", name=session.get("user_name"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT * FROM user
            WHERE email = ? AND password = ?
            """,
            (email, password),
        )
        user = cur.fetchone()

        if not user:
            conn.close()
            return render_template("login.html", error="Invalid email or password.")

        cur.execute(
            """
            SELECT name FROM person
            WHERE user_id = ?
            """,
            (user["user_id"],)
        )
        name_row = cur.fetchone()
        conn.close()

        session["user_email"] = email
        session["user_name"] = name_row["name"]
        return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name    = request.form.get("name")
        dob     = request.form.get("dob")
        gender  = request.form.get("gender")
        email   = request.form.get("email")
        phone   = request.form.get("phone")
        pw      = request.form.get("password")
        ssn     = request.form.get("ssn")
        address = request.form.get("address")

        if not name or not dob or not gender or not email or not phone or not pw:
            return render_template(
                "register.html",
                error="Please tester, dont try to break system."
            )

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT email FROM user WHERE email = ?", (email,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return render_template("register.html", error="Email is already registered.")
        
        cur.execute("SELECT phone FROM person WHERE phone = ?", (phone,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return render_template("register.html", error="Phone is already registered.")

        cur.execute(
            "INSERT INTO user (email, password) VALUES (?, ?)",
            (email, pw)
        )
        

        cur.execute("""
            SELECT user_id
            FROM user
            WHERE email = ?
            """, 
            (email,)
        )
        row = cur.fetchone()
        user_id = row["user_id"]

        cur.execute(
            """
            INSERT INTO person (user_id, name, dob, gender, phone, ssn, address, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, dob, gender, phone, ssn, address, "patient")
        )

        conn.commit()
        conn.close()

        return redirect("/login")


    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/book", methods=["GET", "POST"])
def book():
    if not session.get("user_email"):
        return redirect("/login")
    
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        clinic_id = request.form.get("clinic_id")
        treatment_id = request.form.get("treatment_id")
        doctor_id = request.form.get("doctor_id")
        date = request.form.get("date")
        time = request.form.get("time")
        note = request.form.get("note")

        if not clinic_id or not treatment_id or not doctor_id or not date or not time:
            conn.close()
            return render_template("book.html", error="missing")
        
        cur.execute(
            """
            SELECT person_id FROM person
            WHERE user_id = (SELECT user_id FROM user WHERE email = ?)
            """,
            (session["user_email"],)
        )
        row = cur.fetchone()
        patient_id = row["person_id"]


        # check for duplicate book
        cur.execute(
            """
            SELECT appointment_id FROM appointment
            WHERE doctor_id = ? AND date = ? AND time = ?
            """,
            (doctor_id, date, time)
        )
        exist = cur.fetchone()

        if exist:
            conn.close()
            return render_template("book.html", error="duplicated book")
        
        cur.execute(
            """
            INSERT INTO appointment (patient_id, doctor_id, treatment_id, clinic_id, date, time, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (patient_id, doctor_id, treatment_id, clinic_id, date, time, note)
        )
        
        conn.commit()
        conn.close()
        return render_template("/")


    # show the booking form
    clinics = cur.execute("SELECT * FROM clinic").fetchall()
    treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
    doctors = cur.execute("""SELECT person_id, name FROM person WHERE role = 'doctor'""")


    return render_template(
        "book.html",
        clinics=clinics,
        treatments=treatments,
        doctors=doctors,
        name=session.get("user_name")
        )