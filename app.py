import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, Response
import models

app = Flask(__name__)
app.config["DATABASE"] = "payroll.db"
app.config["BASIC_AUTH_USERNAME"] = os.environ.get("BASIC_AUTH_USERNAME", "admin")
app.config["BASIC_AUTH_PASSWORD"] = os.environ.get("BASIC_AUTH_PASSWORD", "changeme")

@app.before_request
def before_request():
    models.init_db()

@app.teardown_appcontext
def teardown_db(exception):
    models.close_db()

def check_auth(username, password):
    return username == app.config["BASIC_AUTH_USERNAME"] and password == app.config["BASIC_AUTH_PASSWORD"]

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

def parse_salary(raw):
    raw = raw.strip().replace("£", "").replace(",", "")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", raw):
        raise ValueError("Invalid salary format")
    pounds, _, decimals = raw.partition(".")
    decimals = (decimals + "00")[:2]
    return int(pounds) * 100 + int(decimals)

def format_salary(pence):
    return f"£{pence / 100:,.2f}"

@app.route("/")
@auth_required
def list_employees():
    employees = models.get_all_employees()
    return render_template("list.html", employees=employees, format_salary=format_salary)

@app.route("/employees/add", methods=["GET", "POST"])
@auth_required
def add_employee():
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            salary = parse_salary(request.form["salary"])
            models.create_employee(name, salary)
            return redirect(url_for("list_employees"))
        except Exception as e:
            return render_template("form.html", error=str(e), form=request.form)
    return render_template("form.html", form={}, error=None)

@app.route("/employees/<int:emp_id>")
@auth_required
def view_employee(emp_id):
    employee = models.get_employee(emp_id)
    return render_template("detail.html", employee=employee, format_salary=format_salary)

@app.route("/employees/<int:emp_id>/edit", methods=["GET", "POST"])
@auth_required
def edit_employee(emp_id):
    employee = models.get_employee(emp_id)
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            salary = parse_salary(request.form["salary"])
            models.update_employee(emp_id, name, salary)
            return redirect(url_for("view_employee", emp_id=emp_id))
        except Exception as e:
            return render_template("form.html", error=str(e), form=request.form)
    form = {"name": employee["name"], "salary": str(employee["salary_gbp_pence"]/100)}
    return render_template("form.html", form=form, error=None)

@app.route("/employees/<int:emp_id>/delete", methods=["POST"])
@auth_required
def delete_employee(emp_id):
    models.delete_employee(emp_id)
    return redirect(url_for("list_employees"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
