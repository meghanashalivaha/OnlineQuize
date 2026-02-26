from flask import Flask, render_template, request, redirect, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "quiz_secret_key"


# ---------- DATABASE ---------- #

def init_db():

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_questions():

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")

    if c.fetchone()[0] == 0:

        questions = [

            ("Capital of India?", "Delhi", "Mumbai", "Chennai", "Kolkata", "Delhi"),

            ("Python is?", "Language", "Animal", "Car", "Game", "Language"),

            ("2 + 5 = ?", "6", "7", "8", "5", "7"),

            ("HTML used for?", "Structure", "Logic", "Game", "Server", "Structure"),

            ("CSS used for?", "Styling", "Logic", "Database", "Server", "Styling"),

            ("Largest planet?", "Earth", "Mars", "Jupiter", "Venus", "Jupiter"),

            ("Flask is?", "Framework", "Browser", "OS", "Database", "Framework"),

            ("Which is number?", "Hello", "World", "10", "Python", "10"),

            ("Python comment symbol?", "#", "//", "--", "**", "#"),

            ("Output function?", "print()", "show()", "echo()", "display()", "print()")

        ]

        c.executemany(
            "INSERT INTO questions(question,option1,option2,option3,option4,answer) VALUES(?,?,?,?,?,?)",
            questions
        )

    conn.commit()
    conn.close()


init_db()
insert_questions()


# ---------- REGISTER ---------- #

@app.route("/", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("quiz.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            message = "Username already exists!"
        else:
            c.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )
            conn.commit()
            conn.close()

            return redirect("/login")

        conn.close()

    return render_template("register.html", message=message)


# ---------- LOGIN ---------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("quiz.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/welcome")
        else:
            message = "Invalid Login!"

    return render_template("login.html", message=message)


# ---------- WELCOME ---------- #

@app.route("/welcome")
def welcome():

    if "user" not in session:
        return redirect("/login")

    return render_template("welcome.html", username=session["user"])


# ---------- START QUIZ ---------- #

@app.route("/start_quiz")
def start_quiz():

    session["score"] = 0
    session["qno"] = 0

    return redirect("/quiz")


# ---------- QUIZ ---------- #

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("quiz.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    questions = c.execute("SELECT * FROM questions").fetchall()

    conn.close()

    qno = session.get("qno", 0)

    # save answer
    if request.method == "POST":

        selected = request.form.get("option")

        if selected == session.get("correct_answer"):
            session["score"] += 1

        session["qno"] += 1
        qno = session["qno"]

    if qno >= len(questions):
        return redirect("/result")

    question = questions[qno]

    # shuffle options
    options = [
        question["option1"],
        question["option2"],
        question["option3"],
        question["option4"]
    ]

    random.shuffle(options)

    # store correct answer in session
    session["correct_answer"] = question["answer"]

    return render_template(
        "quiz.html",
        question=question["question"],
        options=options,
        qno=qno+1,
        total=len(questions)
    )


# ---------- RESULT ---------- #

@app.route("/result")
def result():

    score = session.get("score", 0)

    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    total = c.fetchone()[0]

    conn.close()

    percentage = (score/total)*100

    if percentage >= 80:
        message = "Excellent Work!"
    elif percentage >= 50:
        message = "Good Job!"
    else:
        message = "Keep Practicing!"

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=round(percentage,2),
        message=message
    )


# ---------- RESTART QUIZ (NO LOGIN REQUIRED) ---------- #

@app.route("/restart")
def restart():

    session["score"] = 0
    session["qno"] = 0

    return redirect("/quiz")


# ---------- LOGOUT ---------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------- RUN ---------- #

if __name__ == "__main__":
    app.run(debug=True)