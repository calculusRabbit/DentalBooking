from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from werkzeug.utils import secure_filename
import sqlite3


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
            INSERT INTO person (user_id, name, dob, gender, phone, ssn, address, role, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, dob, gender, phone, ssn, address, "patient", "default-avatar.jpg")
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
            clinics = cur.execute("SELECT * FROM clinic").fetchall()
            treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
            doctors = cur.execute("SELECT person_id, name FROM person WHERE role = 'doctor'").fetchall()
            conn.close()
            return render_template(
                "book.html", 
                error="Please fill in all fields.",
                clinics=clinics,
                treatments=treatments,
                doctors=doctors,
                name=session.get("user_name")
            )
        
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
            clinics = cur.execute("SELECT * FROM clinic").fetchall()
            treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
            doctors = cur.execute("SELECT person_id, name FROM person WHERE role = 'doctor'").fetchall()
            conn.close()
            return render_template(
                "book.html", 
                error="This time slot is already booked. Please choose another time.",
                clinics=clinics,
                treatments=treatments,
                doctors=doctors,
                name=session.get("user_name")
            )
        
        cur.execute(
            """
            INSERT INTO appointment (patient_id, doctor_id, treatment_id, clinic_id, date, time, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (patient_id, doctor_id, treatment_id, clinic_id, date, time, note)
        )
        apt_id = cur.lastrowid

        conn.commit()
        conn.close()
        return redirect(f"/book_confirm?id={apt_id}")
    


    # show the booking form
    clinics = cur.execute("SELECT * FROM clinic").fetchall()
    treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
    doctors = cur.execute("""SELECT person_id, name FROM person WHERE role = 'doctor'""").fetchall()
    conn.close()

    return render_template(
        "book.html",
        clinics=clinics,
        treatments=treatments,
        doctors=doctors,
        name=session.get("user_name")
        )


@app.route("/book_confirm")
def book_confirm():
    if not session.get("user_email"):
        return redirect("/login")
    
    
    appointment_id = request.args.get("id")
    
    conn = get_db()
    cur = conn.cursor()
    
    
    cur.execute(
        """
        SELECT person_id FROM person
        WHERE user_id = (SELECT user_id FROM user WHERE email = ?)
        """,
        (session["user_email"],)
    )
    row = cur.fetchone()
    patient_id = row["person_id"]

    # select everything that like belong to user
    info = cur.execute(
        """
        SELECT 
            T1.appointment_id,
            T1.date,
            T1.time,
            T1.note,
            T2.name AS clinic_name,
            T2.location AS clinic_location,
            T2.phone AS clinic_phone,
            T3.name AS treatment_name,
            T3.cost AS treatment_cost,
            T4.name AS doctor_name
        FROM appointment T1
        INNER JOIN clinic T2 ON T1.clinic_id = T2.clinic_id
        INNER JOIN treatment_name T3 ON T1.treatment_id = T3.treatment_id
        INNER JOIN person T4 ON T1.doctor_id = T4.person_id
        WHERE T1.appointment_id = ? AND T1.patient_id = ?
        """,
        (appointment_id, patient_id)
    ).fetchone()

    if not info:
        return redirect("/")
    
    conn.close()
    return render_template("book_confirm.html", info=info, name=session.get("user_name"))


@app.route("/appointments")
def viewAppointment():
    if not session.get("user_email"):
        return redirect("/login")
    conn = get_db()
    cur = conn.cursor()
    
    
    row = cur.execute(
        """
        SELECT person_id FROM person
        WHERE user_id = (SELECT user_id FROM user WHERE email = ?)
        """,
        (session["user_email"],)
    ).fetchone()


    patient_id = row["person_id"]
    
    # get all infos
    appointments = cur.execute(
        """
        SELECT 
            T1.appointment_id,
            T1.date,
            T1.time,
            T1.note,
            T2.name AS clinic_name,
            T2.location AS clinic_location,
            T3.name AS treatment_name,
            T3.cost AS treatment_cost,
            T4.name AS doctor_name
        FROM appointment T1
        INNER JOIN clinic T2 ON T1.clinic_id = T2.clinic_id
        INNER JOIN treatment_name T3 ON T1.treatment_id = T3.treatment_id
        INNER JOIN person T4 ON T1.doctor_id = T4.person_id
        WHERE T1.patient_id = ?
        """,
        (patient_id,)
    ).fetchall()
    
    conn.close()

    return render_template("appointments.html", name=session.get("user_name"), appointments=appointments)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if not session.get("user_email"):
        return redirect("/login")
    
    appointment_id = request.args.get("id")
    
    if not appointment_id:
        return redirect("/appointments")
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT person_id FROM person
        WHERE user_id = (SELECT user_id FROM user WHERE email = ?)
        """,
        (session["user_email"],)
    )
    row = cur.fetchone()
    patient_id = row["person_id"]
    
    if request.method == "POST":
        clinic_id = request.form.get("clinic_id")
        treatment_id = request.form.get("treatment_id")

        doctor_id = request.form.get("doctor_id")
        date = request.form.get("date")
        time = request.form.get("time")
        note = request.form.get("note")

        clinics = cur.execute("SELECT * FROM clinic").fetchall()
        treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
        doctors = cur.execute("SELECT person_id, name FROM person WHERE role = 'doctor'").fetchall()

        appointment = cur.execute(
            """
            SELECT * FROM appointment
            WHERE appointment_id = ?
            """,
            (appointment_id)
        ).fetchone()
        
        
        if not clinic_id or not treatment_id or not doctor_id or not date or not time:
            
            conn.close()
            return render_template(
                "edit.html",
                error="Please fill in all fields.",
                clinics=clinics,
                treatments=treatments,
                doctors=doctors,
                appointment=appointment,
                name=session.get("user_name")
            )
        
        # duplicated
        cur.execute(
            """
            SELECT appointment_id FROM appointment
            WHERE doctor_id = ? AND date = ? AND time = ? AND appointment_id != ?
            """,
            (doctor_id, date, time, appointment_id)
        )
        exist = cur.fetchone()
        
        if exist:    
            conn.close()
            return render_template(
                "edit.html",
                error="This time slot is already booked. Please choose another time.",
                clinics=clinics,
                treatments=treatments,
                doctors=doctors,
                appointment=appointment,
                name=session.get("user_name")
            )
        
        # Update the appointment
        cur.execute(
            """
            UPDATE appointment
            SET clinic_id = ?, treatment_id = ?, doctor_id = ?, date = ?, time = ?, note = ?
            WHERE appointment_id = ? AND patient_id = ?
            """,
            (clinic_id, treatment_id, doctor_id, date, time, note, appointment_id, patient_id)
        )
        
        conn.commit()
        conn.close()
        
        return redirect("/appointments")
    

    appointment = cur.execute(
        """
        SELECT * FROM appointment
        WHERE appointment_id = ?
        """,
        (appointment_id)
    ).fetchone()
    
    clinics = cur.execute("SELECT * FROM clinic").fetchall()
    treatments = cur.execute("SELECT * FROM treatment_name").fetchall()
    doctors = cur.execute("SELECT person_id, name FROM person WHERE role = 'doctor'").fetchall()
    
    conn.close()
    
    return render_template(
        "edit.html",
        appointment=appointment,
        clinics=clinics,
        treatments=treatments,
        doctors=doctors,
        name=session.get("user_name")
    )


@app.route("/cancel")
def cancel():
    if not session.get("user_email"):
        return redirect("/login")
    
    appointment_id = request.args.get("id")
    
    if not appointment_id:
        return redirect("/appointments")
    
    conn = get_db()
    cur = conn.cursor()
    
    
    cur.execute(
        """
        SELECT person_id FROM person
        WHERE user_id = (SELECT user_id FROM user WHERE email = ?)
        """,
        (session["user_email"],)
    )
    row = cur.fetchone()
    patient_id = row["person_id"]
    
    # Delete the appointment)
    cur.execute(
        """
        DELETE FROM appointment
        WHERE appointment_id = ? AND patient_id = ?
        """,
        (appointment_id, patient_id)
    )
    
    conn.commit()
    conn.close()
    
    return redirect("/appointments?cancelled=1")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_email"):
        return redirect("/login")
    
    conn = get_db()
    cur = conn.cursor()


    row = cur.execute(
        "SELECT user_id FROM user WHERE email = ?",
        (session["user_email"],)
    ).fetchone()
    user_id = row["user_id"]

    pw = cur.execute("SELECT password FROM user WHERE user_id = ?", (user_id,)).fetchone()
    pw = pw["password"]


    if request.method == "POST":
        action = request.form.get("action")

        if action == "upload_avatar":
            img = request.files['avatar']
            if img.filename == '':
                person = cur.execute("SELECT * FROM person WHERE user_id = ?", (user_id,)).fetchone()
                return render_template("profile.html", person=person, error="No file selected", name=session.get("user_name"), password=pw)

            filename = f"avatar_{user_id}.jpg"
            filepath = f"static/images/{filename}"
            with open(filepath, 'wb') as f:
                f.write(img.read())

            cur.execute("UPDATE person SET avatar = ? WHERE user_id = ?", (filename, user_id))
            conn.commit()
            conn.close()

            
        elif action == "update_property":
            property = request.form.get("property")
            value = request.form.get("value")

            if not value:
                person = cur.execute("SELECT * FROM person WHERE user_id = ?", (user_id,)).fetchone()
                conn.close()
                return render_template("profile.html", person=person, error="enter input", name=session.get("user_name"), password=pw)

            cur.execute(f"UPDATE person SET {property} = ? WHERE user_id = ?", (value, user_id))
            
            
            conn.commit()
            conn.close()

            if property == 'name':
                session["user_name"] = value
            
            return redirect("/profile?info_updated=1")
        
        elif action == "update_password":
            property = request.form.get("property")
            value = request.form.get("value")

            if not value:
                person = cur.execute("SELECT * FROM person WHERE user_id = ?", (user_id,)).fetchone()
                conn.close()
                return render_template("profile.html", person=person, error="enter input", name=session.get("user_name"))

        

    
    person = cur.execute("SELECT * FROM person WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template("profile.html", person=person, name=session.get("user_name"), password=pw)

            