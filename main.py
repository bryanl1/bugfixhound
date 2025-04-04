#main.py BugFixHound
from io import BytesIO
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
import typing
from xml.etree.ElementTree import Element, SubElement, ElementTree
import sqlite3
import uvicorn

app = FastAPI()
app.secret_key = 'super-secret'


_report_types = ['Coding Error', 'Design Issue', 'Hardware Error', 'Suggestion', 'Documentation', 'Query']
_severities = ['Fatal', 'Serious', 'Minor']
_priority=[1,2,3,4,5,6]
_status=['Open', 'Closed', 'Resolved']
_resolution=['Pending', 'Fixed', 'Cannot be reproduced', 'Deferred', 'As designed', 'Withdrawn by reporter', 'Need more info', 
             'Disagree with suggestion', 'Duplicate']
_resolution_version=[0,1,2,3,4,5]
_priority_labels = ['Fix immediately', 'Fix as soon as possible', 'Fix before next milestone', 'Fix before release', 'Fix if possible', 'Optional']

def connect():
    return sqlite3.connect('bugfix.db')

#Message Flashing functionality
def flash(request: Request, message: typing.Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})
def get_flashed_messages(request: Request):
    #print(request.session)
    return request.session.pop("_messages") if "_messages" in request.session else []

middleware = [
    Middleware(SessionMiddleware, secret_key='super-secret')
]
# Add the middleware to the FastAPI app
app = FastAPI(middleware=middleware)
#app.add_middleware(HTTPSRedirectMiddleware)
app.secret_key = 'super-secret'
import os
angular_build_path = os.path.join(os.path.dirname(__file__), "dist/angular-frontend")


# Add the static files and templates
app.mount("/angular", StaticFiles(directory="dist/angular-frontend", html=True), name="angular")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals['get_flashed_messages'] = get_flashed_messages


# Mount Angular frontend

#testing
#@app.get("/")
#@app.get("/angular/")
#async def index(request: Request):
#    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/existing-jinja-page")
async def existing_page():
    return "This is a Jinja-rendered page"

# Define the routes
#@app.get("/")
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    if 'logged_in' in request.session:
        return templates.TemplateResponse("home.html", { "request":request, "username": request.session.get('username'), "password": request.session.get('password'), "userlevel": request.session.get('userlevel') })
    
    return templates.TemplateResponse("login.html", {"request": request, "username": request.session.get('username'), "password": request.session.get('password') })

@app.post("/")
@app.post("/login",response_class=HTMLResponse)
async def login(request: Request, username: str = Form(), password: str = Form(...)):

    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM employees WHERE username = ?", (username,))
        employee = res.fetchone()
        if employee and employee['password'] == password:
            print("DB RESULT: found employee named ", employee['name'], " username: ", employee['username'])
    except sqlite3.Error as e:
     print("A login database error occurred:", e.args[0])

    if employee and employee['password'] == password:
        request.session['logged_in'] = True
        request.session['username'] = username
        request.session['password'] = password
        userlevel = employee["userlevel"]
        request.session['userlevel'] = userlevel
        return templates.TemplateResponse("home.html", {"request": request,"username": username, "password": password, "userlevel": userlevel})
    else:
        flash(request, "Couldn't find your username or password", "Error")
        return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('logged_in', None)
    request.session.pop('username', None)
    request.session.pop('password', None)
    request.session.pop('userlevel', None)
    flash(request, "You have been logged out", "Success")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
@app.post("/home") #userlevel 1 routes post(home) after add_bug
async def home(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to access the homepage", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("home.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

@app.get("/maintain_database")
@app.post("/maintain_database")
async def maintain_database(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login as Admin level to access database maintenance", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    #more robust, add userlevel check/redirect also
    return templates.TemplateResponse("maintain_database.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

@app.get("/manage_employee")
@app.post("/manage_employee")
async def manage_employee(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to access database maintenance", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    if request.session.get('userlevel') != 3:
        return templates.TemplateResponse("home.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

    #Getting employees from database
    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM employees")
        employees = res.fetchall()
        print("db RESULT: found employees ", len(employees))
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
    #May clean this up, values not sent in context are ignored, or treated null in template
    if employees:
        return templates.TemplateResponse("manage_employee.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "employees": employees})
    
    return templates.TemplateResponse("manage_employee.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

@app.post("/add_employee")
async def add_employee(request: Request, name: str = Form(), username: str = Form(), password: str = Form(), userlevel: int = Form()):
    print("FORM: ",name, username, password, userlevel)
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("INSERT INTO employees (name, username, password, userlevel) VALUES (?, ?, ?, ?)", (name, username, password, userlevel))
        con.commit()
        print("db RESULT: added employee named ", name, " username: ", username)
        flash(request, f"Employee {name} added", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't add employee", "Error")
    return RedirectResponse(url='/manage_employee')
    #Redirect response sometimes repeates input to db on async, may consider template response in some cases
    #return templates.TemplateResponse("manage_employee.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

@app.post("/update_employee")
async def update_employee(request: Request, name: str = Form(), username: str = Form(), password: str = Form(), userlevel: int = Form(),id: int = Form() ):
    print("FORM: ",name, username, password, userlevel, id)
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE employees SET name = ?, username = ?, password = ?, userlevel = ? WHERE id = ?", (name, username, password, userlevel, id))
        con.commit()
        print("DB RESULT: updated employee named ", name, " username: ", username)
        flash(request, f"Employee {name} updated", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't update employee", "Error")
    return RedirectResponse(url='/manage_employee')

@app.get("/delete_employee/{id}")
async def delete_employee(request: Request, id: int):
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("DELETE FROM employees WHERE id = ?", (id,))
        con.commit()
        flash(request, f"Employee {id} deleted", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't delete employee", "Error")
    return RedirectResponse(url='/manage_employee')

@app.get("/manage_areas")
@app.post("/manage_areas")
async def manage_areas(request: Request, program_id: int = Form(None)):
    if 'logged_in' not in request.session:
        flash(request, "Please login as Admin level to access database maintenance", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    
    if program_id: #for filtering
        print("Filtering program id: ",program_id)

    programs = None
    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM programs")
        programs = res.fetchall()

        if program_id:
            res = cur.execute("SELECT  * FROM areas WHERE program_id = ?", (program_id,))
        else:
            res = cur.execute("SELECT  * FROM areas")
        areas = res.fetchall()
        print(f"DB RESULT: Found {len(programs)} programs ")
        print(f"DB RESULT: Found {len(areas)} areas ")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])

    amount = 0 #amount of programs found    
    if programs:
        amount = len(programs)
        return templates.TemplateResponse("manage_areas.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "programs": programs, "areas": areas})

    return templates.TemplateResponse("manage_areas.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "amount": amount})

@app.post("/add_area")
async def add_area(request: Request, program_id: int = Form(), area: str = Form()):
    print("FORM: ",program_id, area)

    try:
        con = connect()
        cur = con.cursor()
        cur.execute("INSERT INTO areas (program_id, area) VALUES (?, ?)", (program_id, area))
        con.commit()
        print("db RESULT: added area named ", area, " to program id: ", program_id)
        flash(request, f"Area {area} added to program:{program_id}", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't add area", "Error")
    return RedirectResponse(url='/manage_areas')

@app.post("/update_area")
async def update_area(request: Request, program_id: int = Form(), area: str = Form(), id: int = Form()):
    print("FORM: ",program_id, area, id)
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE areas SET program_id = ?, area = ? WHERE id = ?", (program_id, area, id))
        con.commit()
        print("db RESULT: updated area named ", area, " to program id: ", program_id)
        flash(request, f"Area {area} updated to program:{program_id}", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't update area", "Error")
    return RedirectResponse(url='/manage_areas')

@app.get("/delete_area/{id}")
async def delete_area(request: Request, id: int):
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("DELETE FROM areas WHERE id = ?", (id,))
        con.commit()
        flash(request, f"Area {id} deleted", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't delete area", "Error")
    return RedirectResponse(url='/manage_areas')

@app.get("/manage_program")
@app.post("/manage_program")
async def manage_program(request: Request):
    if 'logged_in' not in request.session or request.session.get('userlevel') != 3:
        page = "login.html"
        if 'logged_in' not in request.session:
            page = "login.html"
        elif request.session.get('userlevel') != 3:
            page = "home.html"
        flash(request, "Please login as Admin level to access database maintenance", "Error")
        return templates.TemplateResponse(page, {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})
    
    #Getting programs from database
    programs = None
    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM programs")
        programs = res.fetchall()
        print(f"DB RESULT: Found {len(programs)} programs ")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])

    if programs:
        return templates.TemplateResponse("manage_program.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "programs": programs})
    
    return templates.TemplateResponse("manage_program.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel')})

@app.post("/add_program")
async def add_program(request: Request, program: str = Form(), release: str = Form(), version: str = Form()):
    print("FORM: ",program, release, version)
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("INSERT INTO programs (program, release, version) VALUES (?, ?, ?)", (program, release, version))
        con.commit()
        print("db RESULT: added program named ", program, ": ", release, ",", version)
        flash(request, f"Program {program} added", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't add program", "Error")
    return RedirectResponse(url='/manage_program')

@app.post("/update_program")
async def update_program(request: Request, program: str = Form(), release: str = Form(), version: str = Form(),id: int = Form() ):
    print("Updating: ",program, release, version, id)
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE programs SET program = ?, release = ?, version = ? WHERE id = ?", (program, release, version, id))
        con.commit()
        print("db RESULT: updated program named ", program, ": ", release, ",", version)
        flash(request, f"Program {program} updated", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't update program", "Error")
    return RedirectResponse(url='/manage_program')

@app.get("/delete_program/{id}")
async def delete_program(request: Request, id: int):
    #return {"mock": f"Delete Program {id}"}
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("DELETE FROM programs WHERE id = ?", (id,))
        con.commit()
        flash(request, f"Program {id} deleted", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't delete program", "Error")
    return RedirectResponse(url='/manage_program')

@app.get("/manage_bug")
@app.post("/manage_bug")
async def manage_bug(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to view/update bug reports", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    if request.session.get('userlevel') != 3:
        flash(request, "Please login as Admin level to access database maintenance", "Error")
        #consider redirecting to logout..or someting with message flashing
        return templates.TemplateResponse("home.html", {"request": request})
    
    reports = None
    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM reports")
        reports = res.fetchall()
        res = cur.execute("SELECT  * FROM programs")
        programs = res.fetchall()
        res = cur.execute("SELECT  * FROM areas")
        areas = res.fetchall()
        employees = cur.execute("SELECT  * FROM employees")
        employees = employees.fetchall()
        print(f"DB RESULT: Found {len(reports)} reports ")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
    
    report_types = _report_types
    severities = _severities
    priority= _priority
    priority_labels=_priority_labels
    status=_status
    resolution=_resolution
    resolution_version=_resolution_version

    return templates.TemplateResponse("manage_bug.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "reports": reports, "programs":programs, "areas":areas, "employees":employees, "report_types": report_types, "severities": severities, "priority": priority, "priority_labels": priority_labels, "status": status, "resolution": resolution, "resolution_version": resolution_version, "reportsCount": len(reports) })
                                                          #, "formatted_attachment": formatted_attachment })

@app.get("/add_bug")
async def add_bug(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to add new bug reports", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    
    #Getting tables from database
    programs = None
    areas = None
    employees = None
    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM programs")
        programs = res.fetchall()
        res = cur.execute("SELECT  * FROM areas")
        areas = res.fetchall()
        res = cur.execute("SELECT  * FROM employees")
        employees = res.fetchall()
        print(f"DB RESULT: Found {len(programs)} programs ")
        print(f"DB RESULT: Found {len(areas)} areas ")
        print(f"DB RESULT: Found {len(employees)} employees ")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])

    report_types = _report_types
    severities = _severities
    priority= _priority
    priority_labels=_priority_labels
    status=_status
    resolution=_resolution
    resolution_version=_resolution_version

    return templates.TemplateResponse("add_bug.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'),"programs": programs, "areas": areas, "employees": employees, "report_types": report_types,"severities": severities,"priority": priority, "priority_labels": priority_labels, "status": status, "resolution": resolution, "resolution_version": resolution_version})
    
@app.post("/add_bug")
async def add_bug(request: Request, 
    #Required Entries
    program: str = Form(),
    report_type: str = Form(), 
    severity: str = Form(),
    problem_summary: str = Form(),
    reproducible: int = Form(), 
    problem: str = Form(),
    reported_by: str = Form(), 
    date_reported: str = Form(),
    #Optional Entries
    functional_area: str = Form(None), assigned_to: str = Form(None), comments: str = Form(None),  status: str = Form(None), 
    priority: int = Form(None), resolution: str = Form(None), resolution_version: int = Form(None), resolution_by: str = Form(None),
    date_resolved: str = Form(None), tested_by: str = Form(None),   suggested_fix: str = Form(None),
    ):

    form = await request.form()

    report_type = form.get('report_type')
    severity = form.get('severity')
    problem_summary = form.get('problem_summary')
    reproducible = form.get('reproducible')
    problem = form.get('problem')
    reported_by = form.get('reported_by')
    date_reported = form.get('date_reported')
    functional_area = form.get('functional_area')
    assigned_to = form.get('assigned_to')
    comments = form.get('comments')
    status = form.get('status')
    priority = form.get('priority')
    resolution = form.get('resolution')
    resolution_version = form.get('resolution_version')
    resolution_by = form.get('resolution_by')
    date_resolved = form.get('date_resolved')
    tested_by = form.get('tested_by')
    suggested_fix = form.get('suggested_fix')
    
    filename = form['attachment'].filename
    attachment = form['attachment'].file.read()

    program = program.split(":")
    form_pid = program[3]
    version = program[2]
    release = program[1]
    program = program[0]
    
    if functional_area:
        functional_area = functional_area.split(":")
        form_aid = functional_area[1]
        functional_area = functional_area[0]

    # Making sure program and area id selected are in database TODO both PID ..need more robust AID
    con = connect()
    cur = con.cursor()
    #cur.execute("SELECT id FROM programs WHERE program = ?", (program,))
    cur.execute("SELECT id FROM programs WHERE id = ?", (form_pid,)) 
    program_id = cur.fetchone()
    con.commit()
    if program_id != None:
        program_id = program_id[0]
    cur.execute("SELECT id FROM areas WHERE area = ?", (functional_area,))
    #cur.execute("SELECT id FROM areas WHERE id = ?", (form_aid,))
    area_id = cur.fetchone()
    if area_id != None:
        area_id = area_id[0]
    con.commit()
    print("PROGRAM ID: ",program_id)
    print("AREA ID: ",area_id)

    try:
        cur.execute("INSERT INTO reports (program, report_type, severity, problem_summary, reproducible, problem, reported_by, date_reported, functional_area, assigned_to, comments, status, priority, resolution, resolution_version, resolution_by,date_resolved, tested_by, program_id, area_id, attachment, filename, suggested_fix) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?, ?, ?)", 
                (program, report_type, severity, 
                                problem_summary, reproducible, problem, reported_by, 
                                date_reported, functional_area, assigned_to, comments, 
                                status, priority, resolution, resolution_version, resolution_by,
                                date_resolved, tested_by, program_id, area_id, attachment, filename, suggested_fix))
        con.commit()
        flash(request, f"Report {cur.lastrowid} for {program} added successfully", "Success")
        print(f"Bug {cur.lastrowid} entry Success!")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, f"Couldn't add bug: {e.args[0]}", "Error")

    if request.session['userlevel'] == 1:
        return RedirectResponse(url='/home')
   
    return RedirectResponse(url='/manage_bug')
                    

@app.post("/update_bug")
async def update_bug(request: Request):

    form = await request.form()
    id = form.get('id')
    program = form.get('program')
    report_type = form.get('report_type')
    severity = form.get('severity')
    problem_summary = form.get('problem_summary')
    reproducible = form.get('reproducible')
    problem = form.get('problem')
    reported_by = form.get('reported_by')
    date_reported = form.get('date_reported')
    functional_area = form.get('functional_area')
    assigned_to = form.get('assigned_to')
    comments = form.get('comments')
    status = form.get('status')
    priority = form.get('priority')
    resolution = form.get('resolution')
    resolution_version = form.get('resolution_version')
    resolution_by = form.get('resolution_by')
    date_resolved = form.get('date_resolved')
    tested_by = form.get('tested_by')
    suggested_fix = form.get('suggested_fix')

    filename = form['attachment'].filename
    attachment = form['attachment'].file.read()

    updateattachment = True
    if filename == '': #Case when no new attachment in Edit, so keep the old one
        if 'currfil' in form:
            updateattachment = False
    
    program = program.split(":")
    form_pid = int(program[1])
    program = program[0]

    con = connect()
    cur = con.cursor()

    #cur.execute("SELECT id FROM programs WHERE program = ?", (program,))
    cur.execute("SELECT id FROM programs WHERE id = ?", (form_pid,))
    program_id = cur.fetchone()

    if program_id != None:
        program_id = program_id[0]
    
    #TODO has bug for areas with some duplicate names,
    cur.execute("SELECT id FROM areas WHERE area = ?", (functional_area,))
    area_id = cur.fetchone()

    if area_id != None:
        area_id = area_id[0]

    try:

        cur.execute("UPDATE reports SET program = ?, report_type = ?, severity = ?, problem_summary = ?, reproducible = ?, problem = ?, reported_by = ?, date_reported = ?, functional_area = ?, assigned_to = ?, comments = ?, status = ?, priority = ?, resolution = ?, resolution_version = ?, resolution_by = ?, date_resolved = ?, tested_by = ?, program_id = ?, area_id = ?, suggested_fix = ? WHERE id = ?", 
                (program, report_type, severity, problem_summary, reproducible, problem, reported_by, date_reported, functional_area, assigned_to, comments, status, priority, resolution, resolution_version, resolution_by, date_resolved, tested_by, program_id, area_id, suggested_fix, id))
        if updateattachment:
            cur.execute("UPDATE reports SET attachment = ?, filename = ? WHERE id = ?", (attachment, filename, id))
        con.commit()
        flash(request, f"Report {id} for {program} updated", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't update report, DB error", "Error")
    return RedirectResponse(url='/manage_bug')

#@app.get("/delete_bug")#if sent without id, error
@app.get("/delete_bug/{id}")
async def delete_bug(request: Request, id: int):
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("DELETE FROM reports WHERE id = ?", (id,))
        con.commit()
        flash(request, f"Report {id} deleted", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't delete report", "Error")
    return RedirectResponse(url='/manage_bug')


@app.get("/search_bug")
async def search_bug(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to view/update bug reports", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    if request.session.get('userlevel') == 1:
        flash(request, "Please login as Employee(2) level or higher to access search", "Error")
        return RedirectResponse(url='/logout')
    
    #Getting tables from database
    con = connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute("SELECT  * FROM programs")
    programs = res.fetchall()
    res = cur.execute("SELECT  * FROM areas")
    areas = res.fetchall()
    employees = cur.execute("SELECT  * FROM employees")
    employees = employees.fetchall()
    print(f"DB RESULT: Found {len(programs)} programs ")
    print(f"DB RESULT: Found {len(areas)} areas ")
    print(f"DB RESULT: Found {len(employees)} employees ")

    report_types = _report_types
    severities = _severities
    priority= _priority
    priority_labels=_priority_labels
    status=_status
    resolution=_resolution
    resolution_version=_resolution_version

    return templates.TemplateResponse("search_bug.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "report_types": report_types, "severities": severities, "priority": priority, "priority_labels": priority_labels, "status": status, "resolution": resolution, "resolution_version": resolution_version, "programs": programs, "areas": areas, "employees": employees})

@app.post("/search_bug")
async def search_bug(request: Request):
    form = await request.form()

    field_values = {
        "program": form.get('program'),
        "report_type": form.get('report_type'),
        "severity": form.get('severity'),
        "functional_area": form.get('functional_area'),
        "assigned_to": form.get('assigned_to'),
        "reported_by": form.get('reported_by'),
        "status": form.get('status'),
        "priority": form.get('priority'),
        "resolution": form.get('resolution'),
        "resolution_by": form.get('resolution_by'),
        "date_reported": form.get('date_reported')
    }
    if field_values['date_reported']=='':
        field_values['date_reported']=None

    sql = "SELECT * FROM reports"
    conditions = []
    for field, value in field_values.items():
        if field == 'status' and value == 'ALL': #special case for status
            value = None
        if value!=None:
            conditions.append(f"{field} = '{value}'")
        
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    con = connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(sql)
    searched_reports = res.fetchall()
    print(sql)

    print(f"DB RESULT: Found {len(searched_reports)} reports ")

    try:
        con = connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT  * FROM programs")
        programs = res.fetchall()
        res = cur.execute("SELECT  * FROM areas")
        areas = res.fetchall()
        employees = cur.execute("SELECT  * FROM employees")
        employees = employees.fetchall()
        print(f"DB RESULT: Found {len(searched_reports)} reports ")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])

    report_types = _report_types
    severities = _severities
    priority= _priority
    priority_labels=_priority_labels
    status=_status
    resolution=_resolution
    resolution_version=_resolution_version
    search = True

    return templates.TemplateResponse("manage_bug.html", {"request": request, "username": request.session.get('username'), "userlevel": request.session.get('userlevel'), "reports": searched_reports, "programs":programs, "areas":areas, "employees":employees, "report_types": report_types, "severities": severities, "priority": priority, "priority_labels": priority_labels, "status": status, "resolution": resolution, "resolution_version": resolution_version, "reportsCount": len(searched_reports), "search": search})


@app.get("/download_attachment/{filename}")
async def download_attachment( filename: str = ""):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT attachment FROM reports WHERE filename = ?", (filename,))
    data = cur.fetchone()
    print("DOWNLOADING FILENAME: ",filename)
    print("BYTE LENGTH FOUND: ",len(data[0]))
    return Response( content=data[0], media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.get("/delete_attachment/{id}")
async def delete_attachment(request: Request, id: int):
    #print("Hello DELETING ATTACHMENT: ",id)
    #return {"mock": f"Delete Attachment {id}"}
    try:
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE reports SET attachment = NULL, filename = NULL WHERE id = ?", (id,))
        con.commit()
        flash(request, f"Attachment for bug report {id} deleted", "Success")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
        flash(request, "Couldn't delete attachment", "Error")
    return RedirectResponse(url='/manage_bug')

@app.post("/export_data")
async def export_data(request: Request):
    if 'logged_in' not in request.session:
        flash(request, "Please login to export data", "Error")
        return templates.TemplateResponse("login.html", {"request": request})
    if request.session.get('userlevel') != 3:
        flash(request, "Please login as Admin level to access database maintenance", "Error")
        return RedirectResponse(url='/logout')
    
    form = await request.form()
    table_name = form.get('table_name')
    file_type = form.get('file_type')
    print("EXPORTING: ",table_name, file_type)

    con = connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(f"SELECT  * FROM {table_name}")
    rowdata = res.fetchall()
    root = Element(table_name)

    for row in rowdata:
        record = SubElement(root, "tuple")
        for key in row.keys():
            field = SubElement(record, key)
            field.text = str(row[key])

    tree = ElementTree(root)
    if file_type == 'xml':
        tree.write(f'{table_name.upper()}.xml')
    elif file_type == 'ascii':
        with open(f'{table_name.upper()}.txt', 'w') as f:
            for row in rowdata:
                for key in row.keys():
                    f.write(f"{key}: {row[key]}\n")
                f.write(f"{row}\n")
    
    cur.close()
    con.close()
    print(f"SUCCESS Exported {table_name} to {file_type}")
    return RedirectResponse(url='/maintain_database')


#FIXME Ideally,function is to inline the image or text file..maybe compromise with just text...not satisfying
# FastAPI does not provide a file response function that provides a html formatted view of the file, has to be done manually
@app.get("/view_attachment/{filename}}")
async def view_attachment( filename: str = ""):
    #TODO make this render the attachment in the browser,
    #TODO make this download the attachment? already does this but it's awkward
    #TODO make this open the attachment in the browser, or view it in the browser
    #add id input parameter, get the attachment from the db..
    from fastapi.responses import StreamingResponse
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT attachment FROM reports WHERE filename = ?", (filename,))
    data = cur.fetchone()
    print("FILENAME: ",filename)
    print("DATA LENGTH FOUND: ",len(data[0]))
    print("SOME DATA", data[0][:10])
    #request = None
    #return templates.TemplateResponse("item.html", { "request":request, "filename": filename, "data": data})
    #return StreamingResponse(BytesIO(data), download_name=filename,  as_attachment=False)
    #return StreamingResponse(BytesIO(data['attachment']), download_name=filename,  as_attachment=False)
    #return {"mock": "View Attachment", "filename":filename, "data": data}
    #    headers = {'Content-Disposition': 'inline; filename="test.jpeg"'}
    #return Response(im_bytes, headers=headers, media_type='image/jpeg')
    return Response( content=data[0], media_type="image/png", headers={"Content-Disposition": f"inline; filename={filename}"})
    #return StreamingResponse(data, media_type="application/octet-stream", headers={"Content-Disposition": f"inline; filename={filename}"})

### Database Initialization scripting ###
# The provided .db files should be ready to use, with just naming to bugfix.db
# One should be imitating what this script does, to create the database from scratch
# Do not run this endpoint unless you want to reset the database completely
@app.get("/initdb")
async def initdb(request: Request):
    try:
        con = sqlite3.connect('bugfix.db')
        cur = con.cursor()
        #cur.execute("DROP TABLE IF EXISTS employees")
        #cur.execute("DROP TABLE IF EXISTS programs")
        #cur.execute("DROP TABLE IF EXISTS areas")
        #cur.execute("DROP TABLE IF EXISTS reports")
        
        #cur.execute("CREATE TABLE  IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, username TEXT, password TEXT, userlevel INTEGER)")
        #cur.execute("INSERT INTO employees (name, username, password, userlevel) VALUES ('Admin', 'admin', '123', 3)")
        #cur.execute("INSERT INTO employees (name, username, password, userlevel) VALUES ('User', 'user', '123', 1)")
        
        #cur.execute("CREATE TABLE IF NOT EXISTS programs (id INTEGER PRIMARY KEY, program TEXT, release TEXT, version TEXT)")
        #cur.execute("CREATE TABLE IF NOT EXISTS areas (id INTEGER PRIMARY KEY, program_id INTEGER, area TEXT, FOREIGN KEY(program_id) REFERENCES programs(id) ON DELETE CASCADE)")
        #cur.execute("CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, program TEXT, report_type TEXT, severity TEXT, problem_summary TEXT, reproducible TINYINT(1), problem TEXT, suggested_fix TEXT, reported_by TEXT, date_reported DATE, functional_area TEXT, assigned_to TEXT, comments TEXT, status TEXT, priority INTEGER, resolution TEXT, resolution_version INTEGER, resolution_by TEXT, date_resolved DATE, tested_by TEXT, program_id INTEGER, area_id INTEGER, filename TEXT, attachment BLOB, FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE, FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE)")
        con.commit()
        print("Database re initialized, be careful")
    except sqlite3.Error as e:
        print("A database error occurred:", e.args[0])
    employees = cur.execute("SELECT * FROM employees")
    print(employees.fetchall())
    con.close()
    return {"message": "Database initialized"}
