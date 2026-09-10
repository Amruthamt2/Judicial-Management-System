from flask import Flask, render_template, request, redirect, session, flash
from db import get_db

app = Flask(__name__)
app.secret_key = "judicial_secret"


# ===================== LOGIN =====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            SELECT u.user_id, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.email=%s AND u.password=%s AND r.role_name=%s
        """, (email, password, role))

        user = cur.fetchone()

        if user:
            session["user_id"] = user["user_id"]
            session["role"] = user["role_name"]

            if role == "Admin":
                return redirect("/admin-dashboard")
            elif role == "Judge":
                return redirect("/judge-dashboard")
            elif role == "Clerk":
                return redirect("/clerk-dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ===================== LOGOUT =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===================== ADMIN DASHBOARD =====================
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect("/")
    return render_template("admin_dashboard.html")


# ===================== JUDGE DASHBOARD =====================
@app.route("/judge-dashboard")
def judge_dashboard():
    if session.get("role") != "Judge":
        return redirect("/")
    return render_template("judge_dashboard.html")


# ===================== CLERK DASHBOARD =====================
@app.route("/clerk-dashboard")
def clerk_dashboard():
    if session.get("role") != "Clerk":
        return redirect("/")
    return render_template("clerk_dashboard.html")


# ===================== CLERK: VIEW CASES =====================
@app.route("/clerk-view-cases")
def clerk_view_cases():
    if session.get("role") != "Clerk":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            c.case_id,
            c.case_type,
            c.filing_date,
            c.current_status,
            j.judge_name
        FROM cases c
        LEFT JOIN judges j ON c.judge_id = j.judge_id
        ORDER BY c.case_id DESC
    """)

    cases = cur.fetchall()
    return render_template("clerk_view_cases.html", cases=cases)


# ===================== ADD CASE (ADMIN) =====================
@app.route("/add-case", methods=["GET", "POST"])
def add_case():
    if session.get("role") != "Admin":
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("""
            INSERT INTO cases
            (case_type, filing_date, current_status, judge_id)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["type"],
            request.form["date"],
            request.form["status"],
            request.form["judge"]
        ))

        db.commit()
        flash("✅ Case added successfully and assigned to Judge", "success")
        return redirect("/add-case")

    return render_template("add_case.html")


# ===================== VIEW CASES (ADMIN) =====================
@app.route("/view-cases")
def view_cases():
    if session.get("role") != "Admin":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            c.case_id,
            c.case_type,
            c.filing_date,
            c.current_status,
            j.judge_name
        FROM cases c
        LEFT JOIN judges j ON c.judge_id = j.judge_id
        ORDER BY c.case_id DESC
    """)

    cases = cur.fetchall()
    return render_template("view_cases.html", cases=cases)


# ===================== ADMIN: UPDATE CASE STATUS =====================
@app.route("/update-case-status", methods=["POST"])
def update_case_status():
    if session.get("role") != "Admin":
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE cases
        SET current_status = %s
        WHERE case_id = %s
    """, (
        request.form["status"],
        request.form["case_id"]
    ))

    db.commit()
    flash("✅ Case status updated", "success")
    return redirect("/view-cases")


# ===================== JUDGE: VIEW OWN CASES =====================
@app.route("/judge-cases")
def judge_cases():
    if session.get("role") != "Judge":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            c.case_id,
            c.case_type,
            c.filing_date,
            c.current_status
        FROM cases c
        JOIN judges j ON c.judge_id = j.judge_id
        WHERE j.user_id = %s
        ORDER BY c.case_id DESC
    """, (session["user_id"],))

    cases = cur.fetchall()
    return render_template("judge_cases.html", cases=cases)


# ===================== ADD + VIEW HEARINGS (JUDGE) =====================
@app.route("/add-hearing", methods=["GET", "POST"])
def add_hearing():
    if session.get("role") != "Judge":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute("""
            INSERT INTO hearings
            (case_id, hearing_date, outcome, next_hearing_date)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["case"],
            request.form["date"],
            request.form["outcome"],
            request.form["next"]
        ))
        db.commit()
        flash("✅ Hearing added successfully", "success")

    cur.execute("""
        SELECT 
            h.hearing_id,
            h.case_id,
            h.hearing_date,
            h.outcome,
            h.next_hearing_date
        FROM hearings h
        JOIN cases c ON h.case_id = c.case_id
        JOIN judges j ON c.judge_id = j.judge_id
        WHERE j.user_id = %s
        ORDER BY h.hearing_date DESC
    """, (session["user_id"],))

    hearings = cur.fetchall()
    return render_template("add_hearing.html", hearings=hearings)


# ===================== JUDGE: UPDATE HEARING STATUS =====================
# ===================== UPDATE HEARING OUTCOME (JUDGE) =====================
@app.route("/update-hearing-outcome", methods=["POST"])
def update_hearing_outcome():
    if session.get("role") != "Judge":
        return redirect("/")

    hearing_id = request.form["hearing_id"]
    outcome = request.form["outcome"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE hearings
        SET outcome = %s
        WHERE hearing_id = %s
    """, (outcome, hearing_id))

    db.commit()
    flash("✅ Hearing outcome updated", "success")
    return redirect("/add-hearing")
# ===================== ADD + VIEW ADJOURNMENTS (JUDGE) =====================
@app.route("/add-adjournment", methods=["GET", "POST"])
def add_adjournment():
    if session.get("role") != "Judge":
        return redirect("/")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute("""
            INSERT INTO adjournments
            (hearing_id, reason_id, adjournment_date, remarks)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["hearing"],
            request.form["reason"],
            request.form["date"],
            request.form["remarks"]
        ))
        db.commit()
        flash("✅ Adjournment recorded successfully", "success")

    cur.execute("""
        SELECT 
            a.adjournment_id,
            h.case_id,
            a.adjournment_date,
            d.category AS reason,
            a.remarks
        FROM adjournments a
        JOIN delay_reasons d ON a.reason_id = d.reason_id
        JOIN hearings h ON a.hearing_id = h.hearing_id
        JOIN cases c ON h.case_id = c.case_id
        JOIN judges j ON c.judge_id = j.judge_id
        WHERE j.user_id = %s
        ORDER BY a.adjournment_id DESC
    """, (session["user_id"],))

    adjournments = cur.fetchall()
    return render_template("add_adjournment.html", adjournments=adjournments)


# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)