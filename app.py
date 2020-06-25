from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
import json
import ast
from MainV10 import Process
import os
import pandas as pd
import threading, time
import flask
import itertools
from datetime import datetime
import os.path
import base64
import string
import random

# install the following 2 libs first
# from flask_sqlalchemy import SQLAlchemy
# from flask_marshmallow import Marshmallow
# from models.question import Question
class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
        
app = Flask(__name__)
cors = CORS(app)

# db = SQLAlchemy(app)
# ma = Marshmallow(app)
# # change to your mysql settings here,create an empty schema before you run the code.
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://your_account_name:your_password@your_mysql_address/your_database_name'

app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = "EFWM@!R@!@MF!!@$#^@#%#@^"
@app.route("/")
def home():
    return "<h1>Welcome man, enjoy your stay<h1>"

# @app.route("/")
# def home():
#     # this step is to create a table defined in models,can put it somewhere else and add on better try except.
#     try:
#         db.create_all()
#     except:
#         print("create wrong")
#     return "<h1>Welcome man, enjoy your stay<h1>"
    
def get_message(currentIP, currentTime, sessionID, curRequestNo):
    out_dict = {}
    time.sleep(1)
    # Unique entry for each request using timestamp!
    entry = None
    foundSession = False
    if os.path.exists('Sessions/' + sessionID + ".json"):
        with open('Sessions/' + sessionID + ".json") as json_file:
            entry = json.load(json_file)
            foundSession = True

    if not foundSession:
        out_dict["curRequestNo"] = curRequestNo
        out_dict["ipExists"] = "no"
        out_dict["timeStampExists"] = "no"
        out_dict["currentIP"] = currentIP
        out_dict["currentTimeStamp"] = currentTime
        out_dict["filename"] = ""
        out_dict["level"] = ""
        out_dict["subject"] = ""
        out_dict["year"] = ""
        out_dict["school"] = ""
        out_dict["exam"] = ""
        return json.dumps(out_dict)
    else:
        out_dict["curRequestNo"] = curRequestNo
        out_dict["ipExists"] = "yes"
        out_dict["timeStampExists"] = "yes"
        out_dict["currentIP"] = currentIP
        out_dict["currentTimeStamp"] = currentTime

        out_dict["stage"] = entry['stage']
        out_dict["page"] = entry['page']
        out_dict["total"] = entry['total']
        out_dict["filename"] = entry['filename']
        out_dict["level"] = entry['level']
        out_dict["subject"] = entry['subject']
        out_dict["year"] = entry['year']
        out_dict["school"] = entry['school']
        out_dict["exam"] = entry['exam']
        return json.dumps(out_dict)
    

@app.route('/stream')
def index():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")
    sessionID = request.args.get("sessionID")
    curRequestNo = request.args.get("curRequestNo")

    if request.headers.get('accept') == 'text/event-stream':
        def events():
            time.sleep(.1)  # an artificial delay
            yield 'data: {}\n\n'.format(get_message(currentIP, currentTime, sessionID, curRequestNo))
        return flask.Response(events(), content_type='text/event-stream')

@app.route('/listpdf', methods = ['GET', 'POST'])
def listpdf():
    pdfs = []
    if os.path.exists("pdfs"):
        items = os.listdir("pdfs")
        for item in items:
            name = item.replace(".pdf", "")
            lastModified = datetime.fromtimestamp(os.path.getmtime("pdfs/" + item))
            newFile = {
                'name' : name,
                'lastModified' : lastModified,
            }
            pdfs.append(newFile)

    return jsonify({"Succeeded": "yes", "Pdfs" : pdfs})

@app.route('/findworkspace', methods = ['GET', 'POST'])
def findworkspace():
    name = request.args.get("name") + ".txt"
    data = ""
    fileData = ""
    if os.path.exists('Workspaces/csv/' + name):
        return jsonify({"Exists": "yes"})
    else:
        return jsonify({"Exists": "no"})
        
@app.route('/savecsv', methods = ['GET', 'POST'])
def savecsv():
    name = request.args.get("name")
    if not os.path.exists("Workspaces/csv"):
        os.makedirs("Workspaces/csv")
    file1 = open("Workspaces/csv/" + name + ".txt","wb") 
    file1.write(request.data) 

    
    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    return jsonify({"Succeeded": "yes", "YourIP" : str(currentIP), "YourTime" : currentTime})

@app.route('/savepdf', methods = ['GET', 'POST'])
def savepdf():
    name = request.args.get("name")
    if not os.path.exists("Workspaces/pdf"):
        os.makedirs("Workspaces/pdf")
    file1 = open("Workspaces/pdf/" + name + ".txt","wb") 
    file1.write(request.data) 
    
    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    return jsonify({"Succeeded": "yes", "YourIP" : str(currentIP), "YourTime" : currentTime})

@app.route('/openpdf', methods = ['GET', 'POST'])
def openpdf():
    name = request.args.get("name") + ".pdf"
    if os.path.exists('pdfs/' + name):
        encoded_string = ""
        with open('pdfs/' + name, "rb") as pdf_file:
            encoded_string = "data:application/pdf;base64," + base64.b64encode(pdf_file.read()).decode("utf-8") 
        return jsonify({"Succeeded": "yes", "fileData" : encoded_string})
    else:
        return jsonify({"Succeeded": "no", "fileData" : ""})

@app.route('/openworkspace', methods = ['GET', 'POST'])
def openworkspace():
    name = request.args.get("name") + ".txt"
    data = ""
    fileData = ""
    if os.path.exists('Workspaces/csv/' + name):
        with open('Workspaces/csv/' + name, 'r', encoding="utf8") as file1:
            data = file1.read()
        if os.path.exists('Workspaces/pdf/' + name):
            with open('Workspaces/pdf/' + name, 'r', encoding="utf8") as file2:
                fileData = file2.read()
            return jsonify({"Succeeded": "yes", "data" : data, "fileData" : fileData})
        else:
            return jsonify({"Succeeded": "yes", "data" : "", "fileData" : ""})
    else:
        return jsonify({"Succeeded": "yes", "data" : "", "fileData" : ""})

@app.route('/deleteworkspace', methods = ['GET', 'POST'])
def deleteworkspace():
    name = request.args.get("name") + ".txt"
    if os.path.exists('Workspaces/pdf/' + name):
        os.remove('Workspaces/pdf/' + name)
        if os.path.exists('Workspaces/csv/' + name):
            os.remove('Workspaces/csv/' + name)
            return jsonify({"Succeeded": "yes"})
        else:
            return jsonify({"Succeeded": "no"})
    else:
        return jsonify({"Succeeded": "no"})


@app.route('/renameworkspace', methods = ['GET', 'POST'])
def renameworkspace():
    oldname = request.args.get("oldName") + ".txt"
    newname = request.args.get("newName") + ".txt"
    print(oldname + ";" + newname)
    if os.path.exists('Workspaces/csv/' + oldname):
        os.rename('Workspaces/csv/' + oldname, 'Workspaces/csv/' + newname)
        if os.path.exists('Workspaces/pdf/' + oldname):
            os.rename('Workspaces/pdf/' + oldname, 'Workspaces/pdf/' + newname)
            return jsonify({"Succeeded": "yes"})
        else:
            return jsonify({"Succeeded": "no"})
    else:
        return jsonify({"Succeeded": "no"})

@app.route('/listworkspace', methods = ['GET', 'POST'])
def listworkspace():
    workspaces = []
    if os.path.exists("Workspaces/csv"):
        items = os.listdir("Workspaces/csv")
        for item in items:
            name = item.replace(".txt", "")
            lastModified = datetime.fromtimestamp(os.path.getmtime("Workspaces/csv/" + item))
            newFile = {
                'name' : name,
                'lastModified' : lastModified,
            }
            workspaces.append(newFile)

    return jsonify({"Succeeded": "yes", "Workspaces" : workspaces})

@app.route('/pushfile', methods = ['GET', 'POST'])
def pushfile():
    print("called1")
    filename = request.args.get("name") + ".pdf"
    if os.path.exists('pdfs/' + filename):
        response = None
        if request.method == 'POST':
            currentIP = request.remote_addr
            print(currentIP)
            currentTime = str(datetime.now())

            # Unique entry for each request using timestamp!
            requestIDRaw = currentIP + "_" + currentTime
            uniqueID = randomString()
            requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
            sessionID = requestIDProcessed + "_" + uniqueID

            print("Forking....")
            process = Process()
            thread = threading.Thread(target=process.main, args=(filename, sessionID))
            thread.start()
            return jsonify({"Succeeded": "yes", "YourSessionID" : sessionID, "YourIP" : str(currentIP), "YourTime" : currentTime, 'filename': filename})

@app.route('/killsession', methods = ['GET', 'POST'])
def killsession():
    sessionID = request.args.get("sessionID")
    if sessionID == "":
        return jsonify({"Succeeded": "yes"})
    else:
        entry = {'delete' : "yes"}
                    
        with open('Sessions/' + sessionID +"_kill" + ".json", 'w') as outfile:
            json.dump(entry, outfile)
        return jsonify({"Succeeded": "yes"})
    
@app.route('/uploadfile', methods = ['GET', 'POST'])
def uploadfile():
    print("called1")
    response = None
    if request.method == 'POST':
        currentIP = request.remote_addr
        print(currentIP)

        fileDownloaded=request.files["myFile"]
        filename = fileDownloaded.filename
        fileDownloaded.save(os.path.join("./ReactPDF", filename))
        currentTime = str(datetime.now())

        # Unique entry for each request using timestamp!
        requestIDRaw = currentIP + "_" + currentTime
        uniqueID = randomString()
        requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
        sessionID = requestIDProcessed + "_" + uniqueID

        print("Forking....")
        process = Process()
        thread = threading.Thread(target=process.main, args=(filename, sessionID))
        thread.start()
        return jsonify({"Succeeded": "yes", "YourSessionID" : sessionID, "YourIP" : str(currentIP), "YourTime" : currentTime, 'filename': filename})


@app.route('/getresult', methods = ['GET', 'POST'])
def getresult():
    sessionID = request.args.get("sessionID")
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")

    df = pd.read_csv(sessionID + "_output.csv")
    df = df.fillna("-")


    # Create required qn or pg lists
    thisPageList = []
    row_json = []  # [[[]]]
    # Iterate over each row 
    currentPageNum = 1
    for index, rows in df.iterrows():
        check = False
        # Create list for the current row
        while check is False:
            pageNum = rows["Page"]
            if pageNum == currentPageNum:
                check = True
                page = rows["Question"].replace('"', "'" ) if rows["Question"] != "" else "-"
                ans_a = rows["A"] if rows["A"] != "" else "-"
                ans_b = rows["B"] if rows["B"] != "" else "-"
                ans_c = rows["C"] if rows["C"] != "" else "-"
                ans_d = rows["D"] if rows["D"] != "" else "-"
                qnNum = rows["Number"]
                base64imgs = rows["Image File"]
                answer = rows["Answer"]
                question_type = rows["question_type"]
                # print("base64: " + base64imgs)
                qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type]
                # append question list to page list
                thisPageList.append(qn_list)
            # once page changes, append previous page list to the final list
            elif pageNum > currentPageNum:
                row_json.append(thisPageList)
                currentPageNum += 1
                thisPageList = []
                pageNum = rows["Page"]
                # append that particular first qn on the new page to the now empty PageList
                if pageNum == currentPageNum:
                    check = True
                    page = rows["Question"] if rows["Question"].replace('"', "'") != "" else "-"
                    ans_a = rows["A"] if rows["A"] != "" else "-"
                    ans_b = rows["B"] if rows["B"] != "" else "-"
                    ans_c = rows["C"] if rows["C"] != "" else "-"
                    ans_d = rows["D"] if rows["D"] != "" else "-"
                    qnNum = rows["Number"]
                    base64imgs = rows["Image File"]
                    answer = rows["Answer"]
                    question_type = rows["question_type"]
                    # print("base64: " + base64imgs)
                    qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type]
                    # append question list to page list
                    thisPageList.append(qn_list)


    dirpath = os.getcwd()
    items = os.listdir(dirpath + "/Sessions")
    for item in items:
        if sessionID in item:
            os.remove(os.path.join(dirpath + "/Sessions", item))

    row_json.append(thisPageList)
    # print(row_json)
    # for page in row_json:
    #     print("Page " + str(row_json.index(page) + 1) + ": " + str(len(page)) + " questions")
    os.remove(sessionID + "_output.csv")
    return jsonify(row_json)

def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choices(string.ascii_letters + string.digits, k=stringLength))

if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=3001)
