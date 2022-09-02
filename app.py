from flask import Flask, render_template, request, redirect
import pymysql
import boto3
from werkzeug.utils import secure_filename

ACCESS_KEY = "AKIATK7IBVZB7HEMNTEU"
SECRET_KEY = "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"
AWS_REGION = "us-east-2"

ENDPOINT="cloud-db-2.cvs0m08whlok.us-east-2.rds.amazonaws.com"
PORT="3306"
USR="admin"
PASSWORD="Pivkan-gajde5"
DBNAME="appdb"

app = Flask(__name__)

@app.route('/')
def main():
    return render_template("login.html")

@app.route('/notfound')
def notfound():
    return render_template("usernotfound.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/mainpage',methods=["GET"])
def mainpage():
    email= request.args.get('email')
    password= request.args.get('password')
    print(email,password)
    try:
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM billing_log;")
        query_results = cur.fetchall()
        cur.execute("SELECT * FROM billing_log Where email ='"+email+"' AND password = '"+password+"';")
        query_results = cur.fetchall()
        if len(query_results)>=1:
            return redirect("sendfile")
        else:
            return redirect("/notfound")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")

@app.route('/sendfile', methods=["GET", "POST"])
def sendFile():     
    if request.method == "POST":
        #creating s3 and sns clients
        s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        sns_client = boto3.client('sns', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,region_name=AWS_REGION)

        #gets file and uploads to s3
        f = request.files['fileupload']
        filename=f.filename.split("\\")[-1]
        f.save(secure_filename(filename))
        s3_client.upload_file(filename, "cloud--bucket", "images/"+filename)

        #creating sns topic and publishing message
        topic_arn = "arn:aws:sns:us-east-2:229730528835:cloud-topic"
        message = "https://s3.console.aws.amazon.com/s3/object/cloud--bucket?region=us-east-2&prefix=images/" + str(filename)
        sns_client.publish(TopicArn=topic_arn,Message=message,Subject='Link to Photo')

        #storing user uploads in database
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        message_insertion = "INSERT INTO billing_log(email,password,imagelink) VALUES('test1@gmail.com','password'," + "'" +message+"'"+ ");"
        cur.execute(message_insertion)
        conn.commit()
        cur.execute("SELECT * FROM billing_log;")

    return render_template('sendfile.html')

#this function initializes the database. its endpoint must be run prior to user login. 
@app.route('/initialize')
def initialize():
    try:
        print("INITIALIZING DATABASE")
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        try:
            cur.execute("DROP TABLE billing_log;")
            print("table deleted")
        except Exception as e:
            print("cannot delete table")
        cur.execute("CREATE TABLE billing_log(email VARCHAR(20), password VARCHAR(20), img VARCHAR(250));")
        print("table created")
        cur.execute("INSERT INTO billing_log(email,password,imagelink) VALUES('test1@gmail.com','password','init data');")
        conn.commit()
        cur.execute("SELECT * FROM billing_log;")
        query_results = cur.fetchall()
        print(query_results)
        return redirect("/")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
