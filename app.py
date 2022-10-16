# Include all necessary libraries

from flask import Flask, render_template, request, session, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import itertools
import re

from helpers import login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    
# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/tsc'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

'''Create all tables for the database'''
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200), nullable = False)
    username = db.Column(db.String(25), nullable = False)
    school = db.Column(db.String(50), nullable = False)
    major = db.Column(db.String(100), nullable = False)
    studentID = db.Column(db.String(30), nullable = True)
    cgpa = db.Column(db.Float, nullable = True)
    password = db.Column(db.String(200), nullable = False)
    theme = db.Column(db.String(20), nullable = False)

    # Create relationships so other tables can use the User's primary key id
    courses = db.relationship('Courses', backref='user')
    exams = db.relationship('Exams', backref='user')
    todo =  db.relationship('Todo', backref='user')
    timetable = db.relationship('Timetable', backref='user')
    outlines = db.relationship('Outlines', backref='user')
    deactivated = db.relationship('Deactivated', backref='user')
    bugs = db.relationship('Bugs', backref='user')
    feedback = db.relationship('Feedback', backref='user')
    
    def __init__(self, fullname, username, school, major, studentID, cgpa, password, theme):
        self.fullname = fullname
        self.username = username
        self.school = school
        self.major = major
        self.studentID = studentID
        self.cgpa = cgpa
        self.password = password
        self.theme = theme

class Courses(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    courseCode = db.Column(db.String(15), nullable = False)
    courseName = db.Column(db.String(200), nullable = False)
    courseUnits = db.Column(db.Integer, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, courseCode, courseName, courseUnits, user_id):
        self.courseCode = courseCode
        self.courseName = courseName
        self.courseUnits = courseUnits
        self.user_id = user_id

class Exams(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    examDateTime = db.Column(db.String(50), nullable = False)
    courseCode = db.Column(db.String(15), nullable = False) 
    examVenue = db.Column(db.String(50), nullable = False)
    examStatus = db.Column(db.String(10), nullable = False)
    examType = db.Column(db.String(5), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, examDateTime, courseCode, examVenue, examStatus, examType, user_id): 
        self.examDateTime = examDateTime
        self.courseCode = courseCode
        self.examVenue = examVenue
        self.examStatus = examStatus
        self.user_id = user_id
        self.examType = examType

class Todo(db.Model):
    __tablename__ = 'todo'
    id = db.Column(db.Integer, primary_key=True)
    taskType = db.Column(db.String(15), nullable = False)
    taskCourse = db.Column(db.String(15), nullable = False)
    task = db.Column(db.String(300), nullable = False)
    taskDeadline = db.Column(db.String(100), nullable = False)
    taskStatus = db.Column(db.String(10), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, taskType, taskCourse, task, taskDeadline, taskStatus, user_id):
        self.taskType = taskType
        self.taskCourse = taskCourse
        self.task = task
        self.taskDeadline = taskDeadline
        self.taskStatus = taskStatus
        self.user_id = user_id

class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    classDay = db.Column(db.String(15), nullable = False)
    courseCode = db.Column(db.String(15), nullable = False)
    classTime = db.Column(db.String(20), nullable = False)
    classVenue = db.Column(db.String(30), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, classDay, courseCode, classTime, classVenue, user_id):
        self.classDay = classDay
        self.courseCode = courseCode
        self.classTime = classTime
        self.classVenue = classVenue 
        self.user_id = user_id

class Outlines(db.Model):
    __tablename__ = 'outlines'
    id = db.Column(db.Integer, primary_key=True)
    courseCode = db.Column(db.String(15), nullable = False)
    topicWeek = db.Column(db.Integer, nullable = False)
    topic = db.Column(db.String(200), nullable = False)
    topicDetails = db.Column(db.String(400), nullable = False)
    topicStatus = db.Column(db.String(15), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, courseCode, topicWeek, topic, topicDetails, topicStatus, user_id):
        self.courseCode = courseCode
        self.topicWeek = topicWeek
        self.topic = topic
        self.topicDetails = topicDetails
        self.topicStatus = topicStatus
        self.user_id = user_id

class Bugs(db.Model):
    __tablename__ = 'bugs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable = False)
    bugPage = db.Column(db.String(30), nullable = False)
    bugDetails = db.Column(db.String(500), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, username, bugPage, bugDetails, user_id):
        self.username = username
        self.bugPage = bugPage
        self.bugDetails = bugDetails
        self.user_id = user_id
    
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable = False)
    feedbackType = db.Column(db.String(15), nullable = False)
    feedbackDetails = db.Column(db.String(500), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, username, feedbackType, feedbackDetails, user_id):
        self.username = username
        self.feedbackType = feedbackType
        self.feedbackDetails = feedbackDetails
        self.user_id = user_id

class Deactivated(db.Model):
    __tablename__ = 'deactivated'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id

# Register a new user into TSC
@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        all_users = list(itertools.chain(Users.query.with_entities(Users.username).all()))
        
        json = request.get_json()

        # Check if username exists
        username_check = Users.query.filter_by(username=json['username']).first()
        if username_check:   
            return jsonify(status="error1")

        # Username compliance (letters, digits _ - and . only), Special characters cannot start the username 
        # Special characters cannot be successive in the username
        elif re.match(r'^(?![-._])(?!.*[_.-]{2})[\w.-]{1,25}$', json['username']) is None:
            return jsonify(status="error2")

        for i in range(len(all_users)):
            if json['username'].casefold() == all_users[i][0].casefold():
                return jsonify(status="error1")
        
        # Ensure password and confirmation match
        if json['password'] != json['confirm_password']:
            return jsonify(status="error3") 
            
        # Ensure password is 8 or more characters
        elif len(json['password']) < 8:
            return jsonify(status="error4")
        
        # Ensure password at least one number:
        elif any(char.isdigit() for char in json['password']) == False:
            return jsonify(status="error4")    

        # Enter new user into table
        fullname = json['fullname']
        school = json['school']
        major = json['major']
        studentID = json['studentID']
        cgpa = json['cgpa']
        username = json['username']
        password = generate_password_hash(json['password'])
        theme = "style.css"
        
        user = Users(fullname=fullname.strip(), username=username.strip(), school=school.strip(), major=major.strip(), studentID=studentID.strip(), cgpa=cgpa.strip(), password=password, theme=theme)
        db.session.add(user)
        db.session.commit()

        # Remember which user has logged in
        session["user_id"] = Users.query.order_by(Users.id.desc()).first()
            
        return jsonify(status="registered")

    return render_template("register.html", theme="style.css")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        if request.get_json():
            json = request.get_json()
            username = json['username']
            password = json['password']
            status = json['status']
            
            # Handle admin access
            if username == "TheAdmin@TSC.com" and password == "jack":
                admin = Users(fullname="admin",username="admin",school="admin",major="admin",studentID="admin",cgpa="admin",
                        password="admin",theme="admin")
                session["user_id"] = admin
                return jsonify(status="admin")

            # Allow username case insensitivity for login
            all_users = list(itertools.chain(Users.query.with_entities(Users.username).all()))
            for i in range(len(all_users)):
                if username.casefold().strip() == all_users[i][0].casefold():
                    username_login = all_users[i][0]

            # Query database for username
            username_check = Users.query.filter_by(username=username_login).first()
            if username_check.username.casefold().strip() is None or not check_password_hash(username_check.password, password):
                return None

            # Remember which user has logged in
            session["user_id"] = username_check

            isDeactivated = Deactivated.query.filter_by(user_id=session["user_id"].id).first()
            if isDeactivated:
                return jsonify(status="deactivated")
            else:
                return jsonify(status="logged")

    return render_template("login.html", theme="style.css")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/deactivation", methods=["GET","POST"])
@login_required
def deactivation():
    userId = session.get("user_id").id

    if request.method == "POST":
        if request.get_json():
            json = request.get_json()
            status = json['status']

            if status == "deactivate":
                user = Users.query.filter_by(id=userId).first()
                deactivatedUser = Deactivated(username=user.username,user_id=user.id)
                db.session.add(deactivatedUser)
                db.session.commit()
                return jsonify(status="Account indefinitely but not permanently deactivated.")
            if status == "reactivate":
                isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
                if not isDeactivated:
                    return jsonify(status="Account is already activated!")
                user = Users.query.filter_by(id=userId).first()
                username = user.username
                Deactivated.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="Welcome Back {}".format(username))
            if status == "deleteAccount":
                isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
                if not isDeactivated:
                    return jsonify(status="Account must be deactivated before permanent deletion!")
                Courses.query.filter_by(user_id=userId).delete()
                Outlines.query.filter_by(user_id=userId).delete()
                Timetable.query.filter_by(user_id=userId).delete()
                Todo.query.filter_by(user_id=userId).delete()
                Exams.query.filter_by(user_id=userId).delete()
                Deactivated.query.filter_by(user_id=userId).delete()
                Users.query.filter_by(id=userId).delete()
                db.session.commit()
                return jsonify(status="Deleted")
    else:
        return render_template("deactivation.html", theme="style.css")

@app.route("/deleted")
def deleted():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/")
def index():
    if session.get("user_id") == None:
        user = 0
        theme="style.css"
    else:
        if session.get("user_id").theme == "admin":
            user = 1
            theme="style.css"
            return render_template("index.html", user=user, theme=theme)
        user = 1
        userId = session.get("user_id").id
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
        if isDeactivated:
            deactivated = 1
            return render_template("index.html",deactivated=deactivated,user=user ,theme=theme)
    return render_template("index.html", user=user, theme=theme)

@app.route("/home", methods=["GET","POST"])
@login_required
def home():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    user = Users.query.filter_by(id=userId).first()
    todo = Todo.query.filter_by(user_id=userId,taskStatus="Urgent").all()

    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    date_time = datetime.now()
    day = date_time.weekday()
    classDay = days[day]
    classes = Timetable.query.filter_by(user_id=userId,classDay=classDay).all()

    # exams = Exams.query.where(and_(or_(Exams.examStatus == 'Urgent', Exams.examStatus == 'Undone'),Exams.user_id == userId)).limit(5).all()
    exams = Exams.query.filter_by(user_id=userId,examStatus="Undone").order_by(Exams.examDateTime).limit(3).all()

    theUser = Users.query.filter_by(id=userId).first()
    theme = theUser.theme
    if not theme:
        theme = "style.css"
    return render_template("home.html", user=user,todo=todo,classes=classes,exams=exams, theme=theme)

@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    if request.method == "POST":
        if request.get_json():
            json = request.get_json()
            status = json['status']

            if status == "edit":
                user = Users.query.filter_by(id=userId).first()
                fullname = user.fullname
                username = user.username
                school = user.school
                studentID = user.studentID
                major = user.major
                cgpa = user.cgpa
                userId = user.id
                return jsonify(fullname=fullname,username=username,school=school,studentID=studentID,major=major,cgpa=cgpa,userId=userId,status="DONE")
            if status == "saveUpdate":
                current = Users.query.filter_by(id=userId).first()
                currentUsername = current.username
                fullname = json['fullname']
                username = json['username']
                school = json['school']
                studentID = json['studentID']
                major = json['major']
                cgpa = json['cgpa']

                all_users = list(itertools.chain(Users.query.with_entities(Users.username).all()))
                # Check if username exists
                username_check = Users.query.filter_by(username=json['username'].strip()).first()
                if username_check and username_check.username != currentUsername:   
                    return jsonify(status="error1")
                # Username compliance (letters, digits _ - and . only)
                elif re.match(r'^(?![-._])(?!.*[_.-]{2})[\w.-]{1,25}$', json['username']) is None:
                    return jsonify(status="error2")
                for i in range(len(all_users)):
                    if json['username'].casefold().strip() == all_users[i][0].casefold() and json['username'].casefold().strip() != currentUsername.casefold():
                        return jsonify(status="error1")
                if username.casefold().strip() == currentUsername.casefold() and username.strip() != currentUsername:
                    Users.query.filter_by(id=userId).update(dict(fullname=fullname.strip(),username=username.strip(),studentID=studentID.strip(),school=school.strip(),major=major.strip(),cgpa=cgpa.strip()))
                    db.session.commit()
                    return jsonify(fullname=fullname,username=username,studentID=studentID,school=school,major=major,cgpa=cgpa,status="success")
                Users.query.filter_by(id=userId).update(dict(fullname=fullname.strip(),username=username.strip(),studentID=studentID.strip(),school=school.strip(),major=major.strip(),cgpa=cgpa.strip()))
                db.session.commit()

                return jsonify(fullname=fullname,username=username,studentID=studentID,school=school,major=major,cgpa=cgpa,status="success")
            
            if status == "changePassword":
                user = Users.query.filter_by(id=userId).first()
                currentPassword = user.password
                oldPassword = json['oldPassword']
                newPassword = generate_password_hash(json['newPassword'])

                # https://werkzeug.palletsprojects.com/en/2.0.x/utils/#werkzeug.security.check_password_hash
                # currentPassword is a hashed value, oldPassword is a string
                # Check old password confirmation
                # Ensure password and confirmation match
                if check_password_hash(currentPassword, oldPassword) == True:
                    if json['newPassword'] != json['confirmPassword']:
                        return jsonify(status="error2") 
                    
                    # Ensure password is 8 or more characters
                    elif len(json['newPassword']) < 8:
                        return jsonify(status="error3")
                    
                    # Ensure password at least one number:
                    elif any(char.isdigit() for char in json['newPassword']) == False:
                        return jsonify(status="error3")
                    
                    Users.query.filter_by(id=userId).update(dict(password=newPassword))
                    db.session.commit()
                    return jsonify(status="success")

                else:
                    return jsonify(status="error1")
            
            if status == "changeTheme":
                styleID = json['styleID']
                theme = "style" + styleID +".css"
                Users.query.filter_by(id=userId).update(dict(theme=theme))
                db.session.commit()
                return jsonify(theme=theme,status="success")

    else:
        user = Users.query.filter_by(id=userId).first()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("profile.html", user=user, theme=theme)

@app.route("/deletion", methods=["GET", "POST"])
@login_required
def deletion():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    if request.method == "POST":
        if request.get_json():
            json = request.get_json()
            status = json['status']

            if status == "deleteCourses":
                Courses.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="All courses successfully deleted!")
            if status == "deleteOutlines":
                Outlines.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="All outlines successfully deleted!")
            if status == "deleteClasses":
                Timetable.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="All classes successfully deleted!")
            if status == "deleteAcademicTasks":
                Todo.query.filter_by(user_id=userId,taskType="AT").delete()
                db.session.commit()
                return jsonify(status="All academic tasks successfully deleted!")
            if status == "deleteNonAcademicTasks":
                Todo.query.filter_by(user_id=userId,taskType="NAT").delete()
                db.session.commit()
                return jsonify(status="All non-academic tasks successfully deleted!")
            if status == "deleteTasks":
                Todo.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="All tasks successfully deleted!")
            if status == "deleteMidSemesters":
                Exams.query.filter_by(user_id=userId,examType="MS").delete()
                db.session.commit()
                return jsonify(status="All mid-semesters successfully deleted!")
            if status == "deleteExams":
                Exams.query.filter_by(user_id=userId,examType="E").delete()
                db.session.commit()
                return jsonify(status="All examinations successfully deleted!")
            if status == "deleteAssessments":
                Exams.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="All assessments successfully deleted!")
            if status == "deleteEverything":
                Courses.query.filter_by(user_id=userId).delete()
                Outlines.query.filter_by(user_id=userId).delete()
                Timetable.query.filter_by(user_id=userId).delete()
                Todo.query.filter_by(user_id=userId).delete()
                Exams.query.filter_by(user_id=userId).delete()
                db.session.commit()
                return jsonify(status="It is Done.")


        return None
    else:
        count = {'courseCount': Courses.query.filter_by(user_id=userId).count(),
                'outlineCount': Outlines.query.filter_by(user_id=userId).count(),
                'classCount': Timetable.query.filter_by(user_id=userId).count(),
                'academicCount': Todo.query.filter_by(user_id=userId, taskType="AT").count(),
                'nonAcademicCount': Todo.query.filter_by(user_id=userId, taskType="NAT").count(),
                'taskCount': Todo.query.filter_by(user_id=userId).count(),
                'midSemesterCount': Exams.query.filter_by(user_id=userId, examType="MS").count(),
                'examCount': Exams.query.filter_by(user_id=userId, examType="E").count(),
                'assessmentCount': Exams.query.filter_by(user_id=userId).count()}
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("deletion.html", count=count,theme=theme)

@app.route("/help", methods=["GET","POST"])
def help():
    if request.method == "POST":
        userId = session.get("user_id").id
    
        if request.get_json():
            json = request.get_json()
            status = json['status']
            
            if status == "bug":
                bugPage = json['bugPage']
                bugDetails = json['bugDetails']
                username = session.get("user_id").username

                bug = Bugs(user_id=userId,username=username,bugPage=bugPage,bugDetails=bugDetails)
                db.session.add(bug)
                db.session.commit()
                return jsonify(status="success")
                
            if status == "feedback":
                feedbackType = json['feedbackType']
                feedbackDetails = json['feedbackDetails']
                username = session.get("user_id").username

                feedback = Feedback(user_id=userId,username=username,feedbackType=feedbackType,feedbackDetails=feedbackDetails)
                db.session.add(feedback)
                db.session.commit()
                return jsonify(status="success")
    else:
        if session.get("user_id") == None:
            theme="style.css"
        else:
            userId = session.get("user_id").id
            theUser = Users.query.filter_by(id=userId).first()
            theme = theUser.theme
            # Make sure a deactivated user can't access the rest of the webapp
            isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
            if isDeactivated:
                deactivated = 1
                return render_template("help.html",deactivated=deactivated,theme=theme)
        return render_template("help.html", theme=theme)

@app.route("/courses", methods=["GET", "POST"])
@login_required
def courses():

    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")
    
    # Get number of courses user has so far
    ''' courseCount = Courses.query.filter_by(user_id=userId).count() '''
    
    # Get list of user's course codes
    takenCourseCodes = list(itertools.chain(Courses.query.with_entities(Courses.courseCode).filter_by(user_id=userId).all()))
    takenList = []
    for i in range(len(takenCourseCodes)):
        takenList.append(takenCourseCodes[i][0])

    # Create a new course
    if request.method == "POST":

        # The status from the ajax post request determines what actions need to be taken
        if request.get_json():
            json = request.get_json()
            status = json['status']
            
            # Return pre-filled form to edit
            if status == "edit":
                rowid = json['rowId']
                course = Courses.query.filter_by(id=rowid).first()
                courseCode = course.courseCode
                courseName = course.courseName
                courseUnits = course.courseUnits
                return jsonify(rowId=rowid,courseCode=courseCode,courseName=courseName,courseUnits=courseUnits,status="DONE")
            # Save the edited row, update the database and update the table
            if status == "saveEdit":
                rowid = json['courseId']
                oldCourse = Courses.query.filter_by(id=rowid).first()
                oldCourseCode = oldCourse.courseCode
                courseCode = json['courseCode']
                courseName = json['courseName']
                courseUnits = json['courseUnits']
                # Ensure course code is not taken
                if courseCode in takenList and courseCode != oldCourseCode:
                    courses = Courses.query.filter_by(user_id=userId).order_by(Courses.courseUnits.desc()).all()
                    return None

                Courses.query.filter_by(id=rowid).update(dict(courseCode=courseCode.upper().strip(), courseName=courseName.strip(), courseUnits=courseUnits))
                ''' TO DO: When other pages are sorted, make sure to prevent errors by only updating what has already been created
                Might be bulky but use conditionals to prevent updating empty records '''
                # Update other tables
                Exams.query.filter_by(courseCode = oldCourseCode).update(dict(courseCode=courseCode.upper()))
                Outlines.query.filter_by(courseCode = oldCourseCode).update(dict(courseCode=courseCode.upper()))
                Todo.query.filter_by(taskCourse = oldCourseCode).update(dict(taskCourse=courseCode.upper()))
                Timetable.query.filter_by(courseCode = oldCourseCode).update(dict(courseCode=courseCode.upper()))
                db.session.commit()
                return jsonify(courseCode=courseCode, courseName=courseName, courseUnits=courseUnits,courseId=rowid,status="SAVED")
            # Delete a course 
            if status == "delete":
                rowid = json['rowId']
                course = Courses.query.filter_by(id=rowid).first()
                courseCode = course.courseCode
                Courses.query.filter_by(id=rowid).delete()
                Outlines.query.filter_by(courseCode=courseCode).delete()
                Exams.query.filter_by(courseCode=courseCode).delete()
                Timetable.query.filter_by(courseCode=courseCode).delete()
                Todo.query.filter_by(taskCourse=courseCode).delete()
                db.session.commit()
                status = "DONE"
                return jsonify(status=status)
            # Add a new course
            if status == "add":
                courseCode = json['courseCode']
                courseName = json['courseName']
                courseUnits = json['courseUnits']
                courseId = json['courseId']
                # Ensure course code is not taken
                if courseCode.upper() in takenList:
                    return jsonify(status="CodeTaken")
                # Add course to courses database
                course = Courses(courseCode=courseCode.upper().strip(), courseName=courseName.strip(), courseUnits=courseUnits, user_id=userId)
                db.session.add(course)
                db.session.commit()
                # Return json data and update table with ajax
                course = Courses.query.filter_by(courseCode=courseCode.upper()).first()
                courseId = course.id
                return jsonify(courseCode=courseCode,courseName=courseName,courseUnits=courseUnits, courseId=courseId, status="success")
        

    else:
        courses = Courses.query.filter_by(user_id=userId).order_by(Courses.courseUnits.desc()).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("courses.html", courses=courses, theme=theme)

@app.route("/outlines", methods=["GET", "POST"])
@login_required
def outlines():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")
    # If url comes with extra argument, assign it to a variable 
    courseCodeArg = request.args.get('courseCode')
    # Edit also comes an argument so make sure this only works from the courses page
    if courseCodeArg and not request.form.get("select"):
        courseCode = courseCodeArg
        courseOutline = Outlines.query.filter_by(user_id=userId, courseCode=courseCode).order_by(Outlines.topicWeek).all()
        courses = Courses.query.filter_by(user_id=userId).order_by(Courses.courseCode).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("outlines.html", courses=courses, courseOutline=courseOutline, courseCode=courseCode, theme=theme)
    
    if request.method == "POST":
        # Show selected course's outline
        if request.form.get("select"):
            courseCode = request.form.get("outlineSelect")
            courseOutline = Outlines.query.filter_by(user_id=userId, courseCode=courseCode).order_by(Outlines.topicWeek).all()
            courses = Courses.query.filter_by(user_id=userId).order_by(Courses.courseCode).all()
            theUser = Users.query.filter_by(id=userId).first()
            theme = theUser.theme
            return render_template("outlines.html", courses=courses, courseOutline=courseOutline, courseCode=courseCode, theme=theme)
        
        # Change topic status using Ajax
        if request.get_json():
            json = request.get_json()
            status = json['status']
            
            if status == "add":
                courseCode = json['courseCode']
                topicWeek = json['topicWeek']
                topic = json['topic']
                topicDetails = json['topicDetails']
                topicStatus = json['topicStatus']

                outline = Outlines(courseCode=courseCode.upper().strip(), topicWeek=topicWeek.strip(), topic=topic.strip(), topicDetails=topicDetails.strip(), topicStatus=topicStatus, user_id=userId)
                db.session.add(outline)
                db.session.commit()

                outline = Outlines.query.filter_by(user_id=userId).order_by(Outlines.id.desc()).first()
                topicId = outline.id
                return jsonify(courseCode=courseCode, topicWeek=topicWeek, topic=topic, topicDetails=topicDetails, topicStatus=topicStatus, topicId=topicId)

            if status == "edit":
                rowid = json['rowId']
                outline = Outlines.query.filter_by(id=rowid).first()
                courseCode = outline.courseCode
                topicWeek = outline.topicWeek
                topic = outline.topic
                topicDetails = outline.topicDetails
                return jsonify(rowId=rowid,courseCode=courseCode,topicWeek=topicWeek,topic=topic,topicDetails=topicDetails)

            if status == "saveEdit":
                topicId = json['topicId']
                topicWeek = json['topicWeek']
                topic = json['topic']
                topicDetails = json['topicDetails']
                Outlines.query.filter_by(id=topicId).update(dict(topicWeek=topicWeek.strip(),topic=topic.strip(),topicDetails=topicDetails.strip()))
                db.session.commit()
                return jsonify(topicId=topicId,topicWeek=topicWeek,topic=topic,topicDetails=topicDetails)

            if status == 'Undone':
                topicId = json['topicId']
                status = 'Urgent'
                Outlines.query.filter_by(id=topicId).update(dict(topicStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == 'Urgent':
                topicId = json['topicId']
                status = 'Done'
                Outlines.query.filter_by(id=topicId).update(dict(topicStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == 'Done':
                status  = 'Undone'
                topicId = json['topicId']
                Outlines.query.filter_by(id=topicId).update(dict(topicStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == "Delete":
                topicId = json['topicId']
                Outlines.query.filter_by(id=topicId).delete()
                db.session.commit()
                status = "DONE"
                return jsonify(status=status)
            if status == "deleteCourseOutline":
                courseCode = json['courseCode']
                Outlines.query.filter_by(user_id=userId,courseCode=courseCode).delete()
                db.session.commit()
                return jsonify(status="DONE")
    
    else:
        courses = Courses.query.filter_by(user_id=userId).order_by(Courses.courseCode).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("outlines.html", courses=courses, theme=theme)

@app.route("/exams", methods=["GET", "POST"])
@login_required
def exams():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    # If url comes with extra argument, assign it to a variable 
    courseCodeArg = request.args.get('courseCode')
    # Edit also comes an argument so make sure this only works from the courses page
    if courseCodeArg:
        courseCode = courseCodeArg
        exams = Exams.query.filter_by(user_id=userId, courseCode=courseCode).order_by(Exams.examDateTime).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("exams.html", courseCode=courseCode, exams=exams, view=4, theme=theme)

    if request.method == "POST":
        if request.form.get("examsFilter"):
            courses = Courses.query.filter_by(user_id=userId).all()
            if int(request.form.get("examsFilter")) == 1:
                exams = Exams.query.filter_by(user_id=userId).order_by(Exams.examDateTime).all()
                view = int(request.form.get("examsFilter"))
                theUser = Users.query.filter_by(id=userId).first() 
                theme = theUser.theme
                return render_template("exams.html", courses=courses, exams=exams, view=view, theme=theme)
            elif int(request.form.get("examsFilter")) == 2:
                exams = Exams.query.filter_by(user_id=userId, examType="MS").order_by(Exams.examDateTime).all()
                view = int(request.form.get("examsFilter"))
                theUser = Users.query.filter_by(id=userId).first()
                theme = theUser.theme
                return render_template("exams.html", courses=courses, exams=exams, view=view, theme=theme)
            elif int(request.form.get("examsFilter")) == 3:
                exams = Exams.query.filter_by(user_id=userId, examType="E").order_by(Exams.examDateTime).all()
                view = int(request.form.get("examsFilter"))
                theUser = Users.query.filter_by(id=userId).first()
                theme = theUser.theme
                return render_template("exams.html", courses=courses, exams=exams, view=view, theme=theme)
        
        # Change status value and display using Ajax 
        if request.get_json():
            json = request.get_json()
            status = json['status']
            
            if status == "add":
                courseCode = json['courseCode']
                examDateTime = json['examDateTime']
                examVenue = json['examVenue']
                examStatus = json['examStatus']
                examType = json['examType']
                viewValue = json['viewValue']

                exam = Exams(courseCode=courseCode.upper().strip(), examDateTime= examDateTime, examVenue=examVenue.strip(), examStatus=examStatus, examType=examType, user_id=userId)
                db.session.add(exam)
                db.session.commit()

                # Return user to the same page with newly added outline
                exam = Exams.query.filter_by(user_id=userId).order_by(Exams.id.desc()).first()
                examId = exam.id
                return jsonify(examDateTime=examDateTime,courseCode=courseCode,examVenue=examVenue,examStatus=examStatus,examType=examType,examId=examId, viewValue=viewValue)
            
            if status == "edit":
                rowid = json['rowId']
                exam = Exams.query.filter_by(id=rowid).first()
                examDateTime = exam.examDateTime
                courseCode = exam.courseCode
                examVenue = exam.examVenue
                examStatus = exam.examStatus
                examType = exam.examType
                status = "DONE"
                return jsonify(rowId=rowid,examDateTime=examDateTime,courseCode=courseCode,examVenue=examVenue,examStatus=examStatus,examType=examType, status=status)
            
            if status == "saveEdit":
                examId = json['examId']
                oldExam = Exams.query.filter_by(id=examId).first()
                oldExamType = oldExam.examType

                examDateTime = json['examDateTime']
                examType = json['examType']
                examVenue = json['examVenue']
                Exams.query.filter_by(id=examId).update(dict(examDateTime=examDateTime, examVenue=examVenue.strip(), examType=examType))
                db.session.commit()

                if oldExamType != examType:
                    view = "remove"
                else:
                    view = "same"

                exam = Exams.query.filter_by(id=examId).first()
                courseCode = exam.courseCode
                return jsonify(examId=examId,examDateTime=examDateTime,examVenue=examVenue,examType=examType,courseCode=courseCode,view=view)

            if status == 'Undone':
                status = 'Done'
                examId = json['examId']
                Exams.query.filter_by(id=examId).update(dict(examStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == 'Done':
                status = 'Undone'
                examId = json['examId']
                Exams.query.filter_by(id=examId).update(dict(examStatus=status))
                db.session.commit()
                return jsonify(status=status)

            if status == "Delete":
                examId = json['examId']
                Exams.query.filter_by(id=examId).delete()
                db.session.commit()
                status = "DONE"
                return jsonify(status=status)
        
    else:
        courses = Courses.query.filter_by(user_id=userId).all()
        exams = Exams.query.filter_by(user_id=userId).order_by(Exams.examDateTime).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("exams.html", courses=courses, exams=exams, view=1, theme=theme)

@app.route("/timetable", methods=["GET", "POST"])
@login_required
def timetable():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    if request.method == "POST":
        
        if request.get_json():
            json = request.get_json()
            status = json['status']

            if status == "add":
                courseCode = json['courseCode']
                classDay = json['classDay']
                classTime = json['classTime']
                classVenue = json['classVenue']

                classDayNumber = Timetable.query.filter_by(user_id=userId,classDay=classDay).count()
                
                lecture = Timetable(classDay=classDay,courseCode=courseCode,classTime=classTime,classVenue=classVenue.strip(),user_id=userId)
                db.session.add(lecture)
                db.session.commit()

                lecture = Timetable.query.filter_by(user_id=userId).order_by(Timetable.id.desc()).first()
                classId = lecture.id

                return jsonify(courseCode=courseCode,classDay=classDay,classTime=classTime,classVenue=classVenue,classId=classId,classDayNumber=classDayNumber)

            if status == "edit":
                classId = json['classId']
                lecture = Timetable.query.filter_by(id=classId).first()
                classDay = lecture.classDay
                classTime = lecture.classTime
                courseCode = lecture.courseCode
                classVenue = lecture.classVenue
                currentClassDayNumber = Timetable.query.filter_by(user_id=userId,classDay=classDay).count()
                
                return jsonify(classId=classId,classDay=classDay,classTime=classTime,classVenue=classVenue,courseCode=courseCode,currentClassDayNumber=currentClassDayNumber,status="DONE")

            if status == "saveEdit":
                classId = json['classId']
                classDay = json['classDay']
                classTime = json['classTime']
                classVenue = json['classVenue']
                courseCode = json['courseCode']
                newClassDayNumber = Timetable.query.filter_by(user_id=userId,classDay=classDay).count()
                
                Timetable.query.filter_by(id=classId).update(dict(classDay=classDay,classTime=classTime,classVenue=classVenue.strip(),courseCode=courseCode))
                db.session.commit()

                return jsonify(classId=classId,classDay=classDay,classTime=classTime,classVenue=classVenue,courseCode=courseCode,newClassDayNumber=newClassDayNumber)

            if status == "Delete":
                classId = json['classId']
                classDay = json['classDay']
                Timetable.query.filter_by(id=classId).delete()
                db.session.commit()

                # Longest day of the week has 9 letters and shortest 6, if a button with Cont was pressed, 
                # it will be 10 characters, use this to ensure the right classDay is used in query below
                if len(classDay) > 9:
                    classDay = classDay[:-4]
                classDayNumber = Timetable.query.filter_by(user_id=userId, classDay=classDay).count()
                return jsonify(classDayNumber=classDayNumber,classDay=classDay, status="DONE")
    else:
        courses = Courses.query.filter_by(user_id=userId).all()
        monday = Timetable.query.filter_by(user_id=userId, classDay="monday").order_by(Timetable.classTime).offset(1).all()
        tuesday = Timetable.query.filter_by(user_id=userId, classDay = "tuesday").order_by(Timetable.classTime).offset(1).all()
        wednesday = Timetable.query.filter_by(user_id=userId, classDay = "wednesday").order_by(Timetable.classTime).offset(1).all()
        thursday = Timetable.query.filter_by(user_id=userId, classDay = "thursday").order_by(Timetable.classTime).offset(1).all()
        friday = Timetable.query.filter_by(user_id=userId, classDay = "friday").order_by(Timetable.classTime).offset(1).all()
        saturday = Timetable.query.filter_by(user_id=userId, classDay = "saturday").order_by(Timetable.classTime).offset(1).all()
        sunday = Timetable.query.filter_by(user_id=userId, classDay = "sunday").order_by(Timetable.classTime).offset(1).all()
        firstMonday = Timetable.query.filter_by(user_id=userId, classDay="monday").order_by(Timetable.classTime).first()
        firstTuesday = Timetable.query.filter_by(user_id=userId, classDay = "tuesday").order_by(Timetable.classTime).first()
        firstWednesday = Timetable.query.filter_by(user_id=userId, classDay = "wednesday").order_by(Timetable.classTime).first()
        firstThursday = Timetable.query.filter_by(user_id=userId, classDay = "thursday").order_by(Timetable.classTime).first()
        firstFriday = Timetable.query.filter_by(user_id=userId, classDay = "friday").order_by(Timetable.classTime).first()
        firstSaturday = Timetable.query.filter_by(user_id=userId, classDay = "saturday").order_by(Timetable.classTime).first()
        firstSunday = Timetable.query.filter_by(user_id=userId, classDay = "sunday").order_by(Timetable.classTime).first()
        mondaySpan = Timetable.query.filter_by(user_id=userId, classDay="monday").order_by(Timetable.classTime).count()
        if mondaySpan == 0:
            mondaySpan = 1
        tuesdaySpan = Timetable.query.filter_by(user_id=userId, classDay = "tuesday").order_by(Timetable.classTime).count()
        if tuesdaySpan == 0:
            tuesdaySpan = 1
        wednesdaySpan = Timetable.query.filter_by(user_id=userId, classDay = "wednesday").order_by(Timetable.classTime).count()
        if wednesdaySpan == 0:
            wednesdaySpan = 1
        thursdaySpan = Timetable.query.filter_by(user_id=userId, classDay = "thursday").order_by(Timetable.classTime).count()
        if thursdaySpan == 0:
            thursdaySpan = 1
        fridaySpan = Timetable.query.filter_by(user_id=userId, classDay = "friday").order_by(Timetable.classTime).count()
        if fridaySpan == 0:
            fridaySpan = 1
        saturdaySpan = Timetable.query.filter_by(user_id=userId, classDay = "saturday").order_by(Timetable.classTime).count()
        if saturdaySpan == 0:
            saturdaySpan = 1
        sundaySpan = Timetable.query.filter_by(user_id=userId, classDay = "sunday").order_by(Timetable.classTime).count()
        if sundaySpan == 0:
            sundaySpan = 1

        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("timetable.html", courses=courses, monday=monday, tuesday=tuesday, wednesday=wednesday, 
                                thursday=thursday, friday=friday, saturday=saturday, sunday=sunday, firstMonday=firstMonday, 
                                firstTuesday=firstTuesday, firstWednesday=firstWednesday, firstThursday=firstThursday, 
                                firstFriday=firstFriday, firstSaturday=firstSaturday, firstSunday=firstSunday, mondaySpan=mondaySpan,
                                tuesdaySpan=tuesdaySpan, wednesdaySpan=wednesdaySpan, thursdaySpan=thursdaySpan,
                                fridaySpan=fridaySpan, saturdaySpan=saturdaySpan, sundaySpan=sundaySpan, theme=theme)

@app.route("/todo", methods=["GET", "POST"])
@login_required
def todo():
    userId = session.get("user_id").id

    isDeactivated = Deactivated.query.filter_by(user_id=userId).first()
    if isDeactivated:
        return redirect("/deactivation")

    # If url comes with extra argument, assign it to a variable 
    courseCodeArg = request.args.get('courseCode')
    # Edit also comes an argument so make sure this only works from the courses page
    if courseCodeArg:
        courseCode = courseCodeArg 
        todo = Todo.query.filter_by(user_id=userId, taskCourse=courseCode).order_by(Todo.taskDeadline).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("todo.html", courseCode=courseCode, todo=todo, view=4, theme=theme)

    if request.method == "POST":
        if request.form.get("todoFilter"):
            courses = Courses.query.filter_by(user_id=userId).all()
            if int(request.form.get("todoFilter")) == 1:
                todo = Todo.query.filter_by(user_id=userId).order_by(Todo.taskDeadline).all()
                view = int(request.form.get("todoFilter"))
                theUser = Users.query.filter_by(id=userId).first()
                theme = theUser.theme
                return render_template("todo.html", courses=courses, todo=todo, view=view, theme=theme)
            elif int(request.form.get("todoFilter")) == 2:
                todo = Todo.query.filter_by(user_id=userId, taskType="AT").order_by(Todo.taskDeadline).all()
                view = int(request.form.get("todoFilter"))
                theUser = Users.query.filter_by(id=userId).first()
                theme = theUser.theme
                return render_template("todo.html", courses=courses, todo=todo, view=view, theme=theme)
            elif int(request.form.get("todoFilter")) == 3:
                todo = Todo.query.filter_by(user_id=userId, taskType="NAT").order_by(Todo.taskDeadline).all()
                view = int(request.form.get("todoFilter"))
                theUser = Users.query.filter_by(id=userId).first()
                theme = theUser.theme
                return render_template("todo.html", todo=todo, view=view, theme=theme)
        
        # Change status value and display using Ajax 
        if request.get_json():
            json = request.get_json()
            status = json['status']
            
            if status == "add":
                taskCourse = json['taskCourse']
                taskDeadline = json['taskDeadline']
                task = json['task']
                taskStatus = json['taskStatus']
                taskType = json['taskType']
                viewValue = json['viewValue']

                taskTodo = Todo(taskCourse=taskCourse.upper().strip(),  taskDeadline=taskDeadline, task=task.strip(), taskStatus=taskStatus, taskType=taskType, user_id=userId)
                db.session.add(taskTodo)
                db.session.commit()

                # Return user to the same page with newly added outline
                todo = Todo.query.filter_by(user_id=userId).order_by(Todo.id.desc()).first()
                taskId = todo.id
                return jsonify(taskCourse=taskCourse,taskDeadline=taskDeadline,task=task,taskStatus=taskStatus,taskType=taskType,taskId=taskId, viewValue=viewValue)
            
            if status == "edit":
                taskId = json['taskId']
                todo = Todo.query.filter_by(id=taskId).first()
                taskDeadline = todo.taskDeadline
                taskCourse = todo.taskCourse
                if taskCourse == "---":
                    taskCourse = "Non-Academic"
                task = todo.task
                taskStatus = todo.taskStatus
                taskType = todo.taskType
                status = "DONE"
                return jsonify(taskId=taskId, taskDeadline=taskDeadline, taskCourse=taskCourse, task=task, taskStatus=taskStatus, taskType=taskType, status=status)

            if status == "saveEdit":
                taskId = json['taskId']

                taskDeadline = json['taskDeadline']
                task = json['task']
                Todo.query.filter_by(id=taskId).update(dict(taskDeadline=taskDeadline, task=task.strip()))
                db.session.commit()

                return jsonify(taskId=taskId, taskDeadline=taskDeadline, task=task)

            if status == 'Undone':
                status = 'Urgent'
                taskId = json['taskId']
                Todo.query.filter_by(id=taskId).update(dict(taskStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == 'Urgent':
                status  = 'Done'
                taskId = json['taskId']
                Todo.query.filter_by(id=taskId).update(dict(taskStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == 'Done':
                status  = 'Undone'
                taskId = json['taskId']
                Todo.query.filter_by(id=taskId).update(dict(taskStatus=status))
                db.session.commit()
                return jsonify(status=status)
            if status == "Delete":
                taskId = json['taskId']
                Todo.query.filter_by(id=taskId).delete()
                db.session.commit()
                status = "DONE"
                return jsonify(status=status)
    else:
        courses = Courses.query.filter_by(user_id=userId).all()
        todo = Todo.query.filter_by(user_id=userId).order_by(Todo.taskDeadline).all()
        theUser = Users.query.filter_by(id=userId).first()
        theme = theUser.theme
        return render_template("todo.html", view=1, courses=courses, todo=todo, theme=theme)

@app.route("/admin", methods=["GET","POST"])
@login_required
def admin():
    # Make sure user only accesses admin by typing in the right credentials at login
    if session.get("user_id").theme != "admin":
        return redirect("/logout")

    if request.method == "POST":
        if request.get_json():
            json = request.get_json()
            status = json['status']

            if status == "deleteBug":
                bugId = json['id']
                Bugs.query.filter_by(id=bugId).delete()
                db.session.commit()
                number = Bugs.query.count()
                return jsonify(status="DONE", number=number)
            else:
                feedbackId = json['id']
                Feedback.query.filter_by(id=feedbackId).delete()
                db.session.commit()
                # Slice the status to get the type of feedback and count the new number after deleting a row
                number = Feedback.query.filter_by(feedbackType=status[6:].lower()).count()
                return jsonify(status="DONE", number=number)

    else:
        # Get user numbers and put them into the necessary dictionary
        deactivatedUsersCount = Deactivated.query.count()
        activeUsersCount = Users.query.count()
        try:
            totalUsersCount = Users.query.order_by(Users.id.desc()).first().id
        except:
            totalUsersCount = 0
        deletedUsersCount = totalUsersCount - (activeUsersCount + deactivatedUsersCount)
        usersCounts = {"deactivated": Deactivated.query.count(), 
                    "active": Users.query.count(), 
                    "total": Users.query.order_by(Users.id.desc()).first().id , 
                    "deleted": deletedUsersCount}

        # Get courses numbers and put them into dictionary
        coursesCounts = {"total": Courses.query.count(), 
                        "units": Courses.query.with_entities(func.sum(Courses.courseUnits))[0][0]}

        # Get average cgpa
        averageCGPA = Users.query.with_entities(func.avg(Users.cgpa))[0][0]

        # Get number of topics
        outlineCounts = {"total": Outlines.query.count(), 
                    "undone": Outlines.query.filter_by(topicStatus="Undone").count(), 
                    "urgent": Outlines.query.filter_by(topicStatus="Urgent").count(), 
                    "done": Outlines.query.filter_by(topicStatus="Done").count()}

        #Get number of classes and classes that day
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        timetableCounts = {"total": Timetable.query.count(), 
                    "today": Timetable.query.filter_by(classDay=days[datetime.now().weekday()]).count(), 
                    "monday": Timetable.query.filter_by(classDay="monday").count(), 
                    "tuesday": Timetable.query.filter_by(classDay="tuesday").count(),
                        "wednesday": Timetable.query.filter_by(classDay="wednesday").count(), 
                        "thursday": Timetable.query.filter_by(classDay="thursday").count(), 
                        "friday": Timetable.query.filter_by(classDay="friday").count(), 
                        "saturday": Timetable.query.filter_by(classDay="saturday").count(), 
                        "sunday": Timetable.query.filter_by(classDay="sunday").count()}

        # Get number of tasks and their filtrations
        todoCounts = {"total": Todo.query.count(), 
                    "totalAT": Todo.query.filter_by(taskType="AT").count(),
                    "totalNAT": Todo.query.filter_by(taskType="NAT").count(), 
                    "undoneAT": Todo.query.filter_by(taskType="AT",taskStatus="Undone").count(),
                    "urgentAT": Todo.query.filter_by(taskType="AT",taskStatus="Urgent").count(), 
                    "doneAT": Todo.query.filter_by(taskType="AT",taskStatus="Done").count(), 
                    "undoneNAT": Todo.query.filter_by(taskType="NAT",taskStatus="Undone").count(),
                    "urgentNAT": Todo.query.filter_by(taskType="NAT",taskStatus="Urgent").count(), 
                    "doneNAT": Todo.query.filter_by(taskType="NAT",taskStatus="Done").count()}
        
        # Get number of assessments and the assessments that day
        assessmentToday = 0
        for i in range(Exams.query.count()):
            if Exams.query.with_entities(Exams.examDateTime).all()[i][0][:-6] == datetime.now().isoformat()[0:10]:
                assessmentToday += 1
        assessmentCounts = {"total": Exams.query.count(), 
                            "exams": Exams.query.filter_by(examType="E").count(), 
                            "ms": Exams.query.filter_by(examType="MS").count(), 
                            "undoneE": Exams.query.filter_by(examType="E",examStatus="Undone").count(),
                            "doneE": Exams.query.filter_by(examType="E",examStatus="Done").count(), 
                            "undoneMS": Exams.query.filter_by(examType="MS",examStatus="Undone").count(), 
                            "doneMS": Exams.query.filter_by(examType="MS",examStatus="Done").count(), 
                            "today":assessmentToday}

        # Get number of theme used
        styleCounts = {"p1": Users.query.filter_by(theme="style.css").count(),
                    "p2": Users.query.filter_by(theme="style2.css").count(),
                    "p3": Users.query.filter_by(theme="style3.css").count(),
                    "p4": Users.query.filter_by(theme="style4.css").count(),
                    "p5": Users.query.filter_by(theme="style5.css").count(),
                    "p6": Users.query.filter_by(theme="style6.css").count(),
                    "p7": Users.query.filter_by(theme="style7.css").count(),
                    "p8": Users.query.filter_by(theme="style8.css").count(),
                    "p9": Users.query.filter_by(theme="style9.css").count(),
                    "p10": Users.query.filter_by(theme="style10.css").count()}
        
        # Get Bugs and Feedback
        bugs = Bugs.query.all()
        comments = Feedback.query.filter_by(feedbackType="comment").all()
        questions = Feedback.query.filter_by(feedbackType="question").all()
        suggestions = Feedback.query.filter_by(feedbackType="suggestion").all()
        bugs_feedbackCounts = {"bugs": Bugs.query.count(),
                            "comments": Feedback.query.filter_by(feedbackType="comment").count(),
                            "suggestions": Feedback.query.filter_by(feedbackType="suggestion").count(),
                            "questions": Feedback.query.filter_by(feedbackType="question").count()
                            }

                    

        return render_template("admin.html", usersCounts=usersCounts,averageCGPA=averageCGPA,coursesCounts=coursesCounts,
                            outlineCounts=outlineCounts,timetableCounts=timetableCounts,
                            todoCounts=todoCounts,assessmentCounts=assessmentCounts, styleCounts=styleCounts,
                            bugs=bugs,comments=comments,questions=questions,suggestions=suggestions,
                            bugs_feedbackCounts=bugs_feedbackCounts)

if __name__ == '__main__':
    app.run(debug=True)