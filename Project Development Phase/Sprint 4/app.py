from flask import Flask, render_template, request, redirect
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment
from apscheduler.schedulers.background import BackgroundScheduler
import ibm_db
import bcrypt
import os
import smtplib
import requests
import json


load_dotenv()

db = os.getenv("bludb")
host = os.getenv("19af6446-6171-4641-8aba-9dcff8e1b6ff.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud")
port = os.getenv("30699")
sslcert = os.getenv("DigiCertGlobalRootCA.crt")
userId = os.getenv("vdw12720")
password = os.getenv("2C3yBJCDvrFURLPQ")
sendgrid = os.getenv('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')
email = os.getenv('jfadamd@gmail.com')
mail_pwd = os.getenv('Fazlina@133')
rapid_api_key = os.getenv('3409a567c4msh2e0d0415517da34p1f45f9jsnbaa995a10995')

conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=19af6446-6171-4641-8aba-9dcff8e1b6ff.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30699;Security=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=vdw12720;PWD=2C3yBJCDvrFURLPQ;","","")


def message(subject="Python Notification",text="", img=None, attachment=None):

    # build message contents
    msg = MIMEMultipart()

    f = open("./templates/mail.html", "r")
    html_content = f.read()

    html_contentt = Environment().from_string(
        html_content).render(msg=text)

    # Add Subject
    msg['Subject'] = subject

    # Add text contents
    msg.attach(MIMEText(html_contentt, 'html'))
    return msg


def mail():

    # initialize connection to our email server,
    # we will use gmail here
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()

    # Login with your email and password
    smtp.login(email, mail_pwd)

    url = "https://newscatcher.p.rapidapi.com/v1/search_enterprise"

    querystring = {"q": "Elon Musk", "lang": "en",
                   "sort_by": "relevancy", "page": "1", "media": "True"}

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "newscatcher.p.rapidapi.com"
    }

    response = requests.request(
        "GET", url, headers=headers, params=querystring)
    json_object = json.loads(response.text)

    data = json_object["articles"][0]["title"]
    print(data)

    # Call the message function
    msg = message("Exciting news today!", data)

    sql = "SELECT email FROM users"
    stmt = ibm_db.prepare(conn, sql)
    # ibm_db.bind_param(stmt, 1, "ahamedjuhaif132@gmail.com")
    ibm_db.execute(stmt)
    users = []
    # auth_token = ibm_db.fetch_row(stmt)
    while ibm_db.fetch_row(stmt) != False:
        users.append(ibm_db.result(stmt, 0))

    # Make a list of emails, where you wanna send mailto = ["jfadamd@gmail.com"]

    # Provide some data to the sendmail function!
    smtp.sendmail(from_addr="ahamedjuhaif132@outlook.com",
                            to_addrs=users, msg=msg.as_string())

    # Finally, don't forget to close the connection
    smtp.quit()


sched = BackgroundScheduler(daemon=True)
sched.add_job(mail, 'interval', minutes=60)
sched.start()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('signin.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':

        email = request.form['username']
        pwd = request.form['password']
        password = ""

        sql = "SELECT password FROM users WHERE email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        auth_token = ibm_db.fetch_assoc(stmt)

        if auth_token:
            result = pwd

            if result:
                return redirect("/dashboard", code=302)
            else:
                return render_template('signin.html', msg="Invalid Credentials")
        else:
            return render_template('signin.html', msg="User doesn't exist")


@app.route('/signup')
def signup_form():
    return render_template('signup.html')


@app.route('/create_user', methods=['POST', 'GET'])
def create_user():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']
        firstName = request.form['first_name']
        lastName = request.form['last_name']
      #  intersts = request.form['interests']
        # converting password to array of bytes
        hashed_password=password

        insert_sql = "INSERT INTO users VALUES (?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, firstName)
        ibm_db.bind_param(prep_stmt, 2, lastName)
        ibm_db.bind_param(prep_stmt, 3, email)
        ibm_db.bind_param(prep_stmt, 4, hashed_password)
       # ibm_db.bind_param(prep_stmt, 5, intersts)
        ibm_db.execute(prep_stmt)

        message = Mail(
            from_email='ahamedjuhaif132@outlook.com',
            to_emails=email,
            subject='Sending with Twilio SendGrid is Fun',
            html_content='<strong>and easy to do anywhere, even with Python</strong>')
        try:
            sg = SendGridAPIClient(sendgrid)
            response = sg.send(message)
        except Exception as e:
            print("ERROR: PC LOAD LETTER")

        return redirect("/dashboard", code=302)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/notifications')
def notifications():
    return render_template('notifications.html')


@app.route('/profile', methods=['POST', 'GET'])
def profile():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
      # interests = request.form['interests']
        # converting password to array of bytes
        bytes = password.encode('utf-8')

        # generating the salt
        salt = bcrypt.gensalt()

        # Hashing the password
        hashed_password = bcrypt.hashpw(bytes, salt)

        sql = "SELECT first_name, last_name, email FROM users WHERE email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        print(ibm_db.execute(stmt))

        insert_sql = "INSERT INTO users VALUES (?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, hashed_password)
        #ibm_db.bind_param(prep_stmt, 2, interests)
        ibm_db.execute(prep_stmt)

        message = Mail(
            from_email='ahamedjuhaif132@outlook.com',
            to_emails=email,
            subject='Sending with Twilio SendGrid is Fun',
            html_content='<strong>and easy to do anywhere, even with Python</strong>')
        try:
            sg = SendGridAPIClient(
                sendgrid)
            response = sg.send(message)
        except Exception as e:
            print("ERROR: PC LOAD LETTER")

        return render_template('dashboard.html', msg="Details uploaded successfuly..")
    elif request.method == 'GET':
        email = 'ahamedjuhaif132@outlook.com'
        sql = "SELECT first_name, email FROM users WHERE email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        data = ibm_db.fetch_assoc(stmt)
        print(type(data))
    return render_template('profile.html', msg=data)


# mail()
# schedule.every(5).seconds.do(mail)
if __name__ == "__main__":
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    app.run(debug=True)
