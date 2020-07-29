### Flask server acting as the backend for the React website, calling MainV10 for the 
### digitisation process

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
from sqlalchemy import create_engine
import pymysql
import ast
from PyPDF2 import PdfFileReader, PdfFileReader, PdfFileWriter
import hashlib
import binascii
import filecmp
import math
import shutil
# install the following 2 libs first
# from flask_sqlalchemy import SQLAlchemy
# from flask_marshmallow import Marshmallow
# from models.question import Question

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
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

### Home Tab 

## Uploadfile: User clicked Choose PDF File or dropped files into the dotted box area. The user’s files will be saved under
# /ReactPDF folder. If a custom page is defined, PyPDF2 is used to truncate the pdf file. After this, the file 
# is saved under the same folder. The MainV10 script is started using a new thread, while returning success to 
# React. React will then call Stream(method below). 
@app.route('/uploadfile', methods=['GET', 'POST'])
def uploadfile():
    response = None
    if request.method == 'POST':
        currentIP = request.remote_addr

        fileDownloaded = request.files["myFile"]
        filename = fileDownloaded.filename
        fileDownloaded.save(os.path.join("./ReactPDF", filename))

        infile = PdfFileReader("ReactPDF/" + filename, 'rb')
        output = PdfFileWriter()
        currentStartPage = request.args.get("currentStartPage")
        currentEndPage = request.args.get("currentEndPage")

        ignoreCustomPageRange = request.args.get("ignoreCustomPageRange")

        if ignoreCustomPageRange == "true":
            for i in range(infile.numPages):
                p = infile.getPage(i)
                output.addPage(p)
        else:
            # 0-index
            for i in range(int(currentStartPage) - 1, int(currentEndPage)):
                p = infile.getPage(i)
                output.addPage(p)

        with open("ReactPDF/" + filename, 'wb') as f:
            output.write(f)

        currentTime = str(datetime.now())
        pdf_file = open("ReactPDF/" + filename, "rb")
        pdf_data_binary = pdf_file.read()
        pdf_bas64 = "data:application/pdf;base64," + (base64.b64encode(pdf_data_binary)).decode("ascii")

        # Unique entry for each request using timestamp!
        requestIDRaw = currentIP + "_" + currentTime
        uniqueID = randomString()
        requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
        sessionID = requestIDProcessed + "_" + uniqueID

        process = Process()
        thread = threading.Thread(target=process.main, args=(filename, sessionID))
        thread.start()
        return jsonify(
            {"Succeeded": "yes", "YourSessionID": sessionID, "YourIP": str(currentIP), "YourTime": currentTime,
             'filename': filename, 'pdf_base64': pdf_bas64})

## Pushfile: User clicked Process PDF in one or more files in the pdf table. The appropriate directory 
# where the pdfs are stored will be indicated, which is under /datassd in Azure, and under /pdfs in the
# developer’s local drive. What happens after is similar to Uploadfile. Custom page range selection is
# taken into account, and MainV10 script will be called. React will then call Stream(method below in Section 2.6).
@app.route('/pushfile', methods=['GET', 'POST'])
def pushfile():
    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    # Unique entry for each request using timestamp!
    requestIDRaw = currentIP + "_" + currentTime
    uniqueID = randomString()
    requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
    sessionID = requestIDProcessed + "_" + uniqueID
    filename = request.args.get("name") + ".pdf"
    azureDir = "/datassd/pdf_downloader-master/pdfs/"
    localDir = "pdfs/"
    myDir = ""

    if os.path.exists(azureDir):
        myDir = azureDir
    elif os.path.exists(localDir):
        myDir = localDir
    else:
        return jsonify(
            {"Succeeded": "no", "YourSessionID": sessionID, "YourIP": str(currentIP), "YourTime": currentTime,
             'filename': ""})

    if os.path.exists(myDir + filename):
        response = None
        infile = PdfFileReader(myDir + filename, 'rb')
        output = PdfFileWriter()
        currentStartPage = request.args.get("currentStartPage")
        currentEndPage = request.args.get("currentEndPage")
        ignoreCustomPageRange = request.args.get("ignoreCustomPageRange")
        newFilename = request.args.get("name") + "_" + sessionID + ".pdf"

        if ignoreCustomPageRange == "false":
            # 0-index
            for i in range(int(currentStartPage) - 1, int(currentEndPage)):
                p = infile.getPage(i)
                output.addPage(p)

            with open("ReactPDF/" + newFilename, 'wb') as f:
                output.write(f)
        else:
            shutil.copyfile(myDir + filename, "ReactPDF/" + newFilename)

        pdf_file = open("ReactPDF/" + newFilename, "rb")
        pdf_data_binary = pdf_file.read()
        pdf_bas64 = "data:application/pdf;base64," + (base64.b64encode(pdf_data_binary)).decode("ascii")

        process = Process()
        thread = threading.Thread(target=process.main, args=(newFilename, sessionID))
        thread.start()
        return jsonify(
            {"Succeeded": "yes", "YourSessionID": sessionID, "YourIP": str(currentIP), "YourTime": currentTime,
             'filename': newFilename, 'pdf_base64': pdf_bas64})
    else:
        return jsonify(
            {"Succeeded": "no", "YourSessionID": sessionID, "YourIP": str(currentIP), "YourTime": currentTime,
             'filename': "", 'pdf_base64': ""})

## Getpdfpages: User either uploaded or pushed a file, and selected to use custom pdf page range.
# This method is used to feedback to React the number of pages this pdf has, allowing the user to 
# select a range from this pdf page range given.
@app.route('/getpdfpages', methods=['GET', 'POST'])
def getpdfpages():
    name = request.args.get("name")
    isExisting = request.args.get("isExisting")
    filePath = ""
    if isExisting == "no":
        fileDownloaded = request.files["myFile"]
        fileDownloaded.save(os.path.join("./ReactPDF", name + ".pdf"))
        filePath = "./ReactPDF/" + name + ".pdf"
    else:
        azureDir = "/datassd/pdf_downloader-master/pdfs/"
        localDir = "pdfs/"

        if os.path.exists(azureDir):
            filePath = azureDir + name + ".pdf"
        elif os.path.exists(localDir):
            filePath = localDir + name + ".pdf"

    pdf = PdfFileReader(open(filePath, 'rb'))
    noOfPages = int(pdf.getNumPages())
    return jsonify({"Succeeded": "yes", "noOfPages": noOfPages})

## Killsession: Every Session call of the MainV10 script listens to the event whereby the Session is killed. 
# The Killsession method is called when the user uploads or pushes a new file, thereby killing the previous 
# session to save resources. The Session call identifies that it is killed based on its sessionID.
@app.route('/killsession', methods=['GET', 'POST'])
def killsession():
    sessionID = request.args.get("sessionID")
    if sessionID == "":
        return jsonify({"Succeeded": "yes"})
    else:
        entry = {'delete': "yes"}

        with open('Sessions/' + sessionID + "_kill" + ".json", 'w') as outfile:
            json.dump(entry, outfile)
        return jsonify({"Succeeded": "yes"})

## Get_message: Every Session call of the MainV10 script is given an unique sessionID based on the IP address,
#  timestamp and a random string. The MainV10 script will save the progress of this session in a .json file 
# with the sessionID. This shows the current question, page and stage. Get_message simply reads this .json 
# file with the progress information and returns to Stream.
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

    return jsonify({"Succeeded": "yes"})

## Stream: As mentioned above, Stream is called by React after the user uploads or pushes 
# a file. Stream calls Get_message to monitor the progress of the digitisation process of
#  MainV10 script. This progress information is returned to React, which updates its progress
#  bar. When React detects that the progress is full, it will call Getresult.
@app.route('/stream')
def stream():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")
    sessionID = request.args.get("sessionID")
    curRequestNo = request.args.get("curRequestNo")

    if request.headers.get('accept') == 'text/event-stream':
        def events():
            time.sleep(.1)  # an artificial delay
            yield 'data: {}\n\n'.format(get_message(currentIP, currentTime, sessionID, curRequestNo))

        return flask.Response(events(), content_type='text/event-stream')

## Getresult: Reads the output CSV of the Session call of the MainV10 script. The correct output 
# CSV file is identified based on the unique sessionID string. A triple nested list containing 
# the pdf information is generated and returned to React. The first layer is each page, the 
# second layer is each question in the page, and the third layer is the attributes of each question.
@app.route('/getresult', methods=['GET', 'POST'])
def getresult():
    sessionID = request.args.get("sessionID")
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")

    df = pd.read_csv("Output/" + sessionID + "_output.csv")
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
                page = rows["Question"].replace('"', "'") if rows["Question"] != "" else "-"
                ans_a = rows["A"] if rows["A"] != "" else "-"
                ans_b = rows["B"] if rows["B"] != "" else "-"
                ans_c = rows["C"] if rows["C"] != "" else "-"
                ans_d = rows["D"] if rows["D"] != "" else "-"
                qnNum = rows["Number"]
                base64imgs = rows["Image File"]
                answer = rows["Answer"]
                question_type = rows["question_type"]
                image = rows["Image"]
                qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type, image]
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
                    image = rows["Image"]
                    qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type,
                               image]
                    # append question list to page list
                    thisPageList.append(qn_list)

    dirpath = os.getcwd()
    items = os.listdir(dirpath + "/Sessions")
    for item in items:
        if sessionID in item:
            os.remove(os.path.join(dirpath + "/Sessions", item))

    row_json.append(thisPageList)
    return jsonify(row_json)

## Listpdf: This populates the pdf table with information. The appropriate directory where the 
# pdfs are stored will be indicated, which is under /datassd in Azure, and under /pdfs in the 
# developer’s local drive. Note that since there are ~10,000 pdf files in the system, it will 
# be slow to retrieve all of them in one batch. Hence, total_batches is specified as 10, where
#  React will send 10 requests to Flask with each request returning ~1000 pdf files only. 
# The pdf information will populate the pdf table as it arrives, reducing the latency time for the user.

# Each pdf entry in the table has a Status attribute. This can be of four types: Not Processed, In 
# Library Only, In Database Only or In Library and Database. Each pdf file is hashed using SHA512 
# from its Base64 string. This is stored as an entry in the pdfbank MySQL table, with attributes 
# inDatabase and inLibrary. Listpdf will perform a Select query, and update the Status attribute 
#  the pdf entry based on its inDatabase and inLibrary attributes.
@app.route('/listpdf', methods=['GET', 'POST'])
def listpdf():
    pdfs = []
    azureDir = "/datassd/pdf_downloader-master/pdfs/"
    localDir = "pdfs/"
    myDir = ""
    currentBatch = int(request.args.get("batch"))

    if os.path.exists(azureDir):
        myDir = azureDir
    elif os.path.exists(localDir):
        myDir = localDir
    else:
        return jsonify({"Succeeded": "no", "Pdfs": pdfs})

    ### PDFBANK
    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()

        
    items = os.listdir(myDir)
    total_batches = 10

    total_size = len(items)
    batch_size = math.ceil(total_size / total_batches)

    lower_bound = currentBatch * batch_size
    upper_bound = (currentBatch * batch_size) + batch_size
    if upper_bound > total_size:
        upper_bound = total_size
    batched_items = items[lower_bound: upper_bound]
    
    select_query = "SELECT * FROM pdfbank"
    cursor.execute(select_query)
    select_results = cursor.fetchall()
    
    for item in batched_items:
        if item == "hash":
            continue
        name = item.replace(".pdf", "")

        lastModified = datetime.fromtimestamp(os.path.getmtime(myDir + item))
        status = "Not Processed"

        try:
            pdfhash = ""
            if not os.path.exists(myDir + "hash/"):
                os.makedirs(myDir + "hash/")

            if not os.path.exists(myDir + "hash/" + name + ".txt"):
                # Cache for the hash, so it will be faster
                pdf_file = open(myDir + item, "rb")
                pdf_data_binary = pdf_file.read()
                pdf_bas64 = "data:application/pdf;base64," + (base64.b64encode(pdf_data_binary)).decode("ascii")
                encoded_string = pdf_bas64[28:].encode('ascii')
                pdfhash = hashlib.sha512(encoded_string).hexdigest()
                
                file1 = open(myDir + "hash/" + name + ".txt", "w")
                file1.write(pdfhash)
            else:
                with open(myDir + "hash/" + name + ".txt", "r") as hashfile:
                    pdfhash = hashfile.read()



            filtered_select_results = [k for k in select_results if pdfhash in k]
            if len(filtered_select_results) > 0:
                ## [0] for the first value with the pdfhash, since it should be unique
                ## [2] for the third value in the row, which contains the inLibrary column
                ## [3] for the fourth value in the row, which contains the inDatabase column
                inLibrary = filtered_select_results[0][2]
                inDatabase = filtered_select_results[0][3]

                if inLibrary == 0:
                    if inDatabase == 0:
                        status = "Not Processed"
                    elif inDatabase == 1:
                        status = "In Database Only"
                elif inLibrary == 1:
                    if inDatabase == 0:
                        status = "In Library Only"
                    elif inDatabase == 1:
                        status = "In Library and Database"

        except Exception as e:
            con.rollback()
            print(e)

        newFile = {
            'name': name,
            'lastModified': lastModified,
            'status': status,
        }
        pdfs.append(newFile)

    return jsonify({"Succeeded": "yes", "Pdfs": pdfs})

## Openpdf: The user clicks Download PDF on one or more pdf files in the pdf table. 
# The appropriate directory where the pdfs are stored will be indicated, which is 
# under /datassd in Azure, and under /pdfs in the developer’s local drive. The pdf
#  file will be read and encoded in Base64 format, which is returned back to the
#  user. React converts this Base64 string into a downloadable pdf file for the user.
@app.route('/openpdf', methods=['GET', 'POST'])
def openpdf():
    name = request.args.get("name") + ".pdf"
    azureDir = "/datassd/pdf_downloader-master/pdfs/"
    localDir = "pdfs/"
    myDir = ""

    if os.path.exists(azureDir):
        myDir = azureDir
    elif os.path.exists(localDir):
        myDir = localDir
    else:
        return jsonify({"Succeeded": "no", "fileData": ""})

    if os.path.exists(myDir + name):
        encoded_string = ""
        with open(myDir + name, "rb") as pdf_file:
            encoded_string = "data:application/pdf;base64," + base64.b64encode(pdf_file.read()).decode("utf-8")
        return jsonify({"Succeeded": "yes", "fileData": encoded_string})
    else:
        return jsonify({"Succeeded": "no", "fileData": ""})


### Edit Tab functions
##  Findworkspace: First function called when the user clicks Save Workspace. If a workspace with the 
# same name under Workspaces/csv/ already exists, the user will be prompted if the user wants to 
#  the existing workspace. Each Workspace is stored in three separate files, under Workspaces/csv/, 
# Workspaces/pdf/, and Workspaces/attributes/. The csv file stores the questions data of the pdf file. 
# The pdf file stores the Base64 string of the pdf file. The attribute file stores the exam paper data 
# such as school name and type of exam.
@app.route('/findworkspace', methods=['GET', 'POST'])
def findworkspace():
    name = request.args.get("name") + ".txt"
    data = ""
    fileData = ""
    if os.path.exists('Workspaces/csv/' + name):
        return jsonify({"Exists": "yes"})
    else:
        return jsonify({"Exists": "no"})

## renameworkspace: Second function called when the user clicks Save Workspace. The Workspace
# files under Workspaces/csv/, Workspaces/pdf/, and Workspaces/attributes/ will each be renamed accordingly.
@app.route('/renameworkspace', methods=['GET', 'POST'])
def renameworkspace():
    oldname = request.args.get("oldName") + ".txt"
    newname = request.args.get("newName") + ".txt"

    if os.path.exists('Workspaces/csv/' + oldname):
        os.replace('Workspaces/csv/' + oldname, 'Workspaces/csv/' + newname)
        if os.path.exists('Workspaces/pdf/' + oldname):
            os.replace('Workspaces/pdf/' + oldname, 'Workspaces/pdf/' + newname)
            if os.path.exists('Workspaces/attribute/' + oldname):
                os.replace('Workspaces/attribute/' + oldname, 'Workspaces/attribute/' + newname)
                return jsonify({"Succeeded": "yes"})
            else:
                return jsonify({"Succeeded": "no"})
        else:
            return jsonify({"Succeeded": "no"})
    else:
        return jsonify({"Succeeded": "no"})

## Savecsv: Third function called when the user clicks Save Workspace. The csv file is 
# stored under Workspaces/csv/. The csv file stores the questions data of the pdf file.
@app.route('/savecsv', methods=['GET', 'POST'])
def savecsv():
    name = request.args.get("name")
    if not os.path.exists("Workspaces/csv"):
        os.makedirs("Workspaces/csv")
    file1 = open("Workspaces/csv/" + name + ".txt", "wb")
    file1.write(request.data)

    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    return jsonify({"Succeeded": "yes", "YourIP": str(currentIP), "YourTime": currentTime})

## Savepdf: Fourth function called when the user clicks Save Workspace. The pdf file is stored 
# under Workspaces/pdf/. The pdf file stores the Base64 string of the pdf file. Updates the 
# inWorkspace attribute of the pdf file in pdfbank to 1.
@app.route('/savepdf', methods=['GET', 'POST'])
def savepdf():
    name = request.args.get("name")
    pdfdata = request.data[28:]
    pdfhash = hashlib.sha512(pdfdata).hexdigest()
    
    if not os.path.exists("Workspaces/pdf"):
        os.makedirs("Workspaces/pdf")
    file1 = open("Workspaces/pdf/" + name + ".txt", "wb")
    file1.write(request.data)

    if not os.path.exists("Workspaces/hash"):
        os.makedirs("Workspaces/hash")
    file2 = open("Workspaces/hash/" + name + ".txt", "w")
    file2.write(pdfhash)

    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    ### PDFBANK
    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()

    create_table_query = """create table if not exists pdfbank(
    id int auto_increment primary key,
    hashcode VARCHAR(128) UNIQUE,
    inLibrary int,
    inDatabase int
    )"""

    update_query = """INSERT INTO pdfbank (hashcode, inLibrary, inDatabase)
                    VALUES (%s,%s, %s)
                    ON DUPLICATE KEY UPDATE inLibrary = 1;
                    """ 
                    
    try:
        cursor.execute(create_table_query)
        cursor.execute(update_query, (pdfhash, 1, 0)) 

        con.commit()

    except Exception as e:
        con.rollback()
        print("2: " + str(e))
        
        

    return jsonify({"Succeeded": "yes", "YourIP": str(currentIP), "YourTime": currentTime})

## Saveattribute: Fifth function called when the user clicks Save Workspace. The attribute file 
# is stored under Workspaces/attributes/. The attribute file stores the exam paper data such as
# school name and type of exam.
@app.route('/saveattribute', methods=['GET', 'POST'])
def saveattribute():
    filename = request.args.get("filename")
    school = request.args.get("school")
    subject = request.args.get("subject")
    level = request.args.get("level")
    year = request.args.get("year")
    exam = request.args.get("exam")

    if not os.path.exists("Workspaces/attribute"):
        os.makedirs("Workspaces/attribute")
    file1 = open("Workspaces/attribute/" + filename + ".txt", "wb")
    attrStr = filename + ";" + school + ";" + subject + ";" + level + ";" + year + ";" + exam
    file1.write(attrStr.encode('utf-8'))

    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    return jsonify({"Succeeded": "yes", "YourIP": str(currentIP), "YourTime": currentTime})

## Checkdatabase: First function called when the user clicks Upload all questions to database or 
# Upload selected questions to database. The SHA512 hash of the pdf file that the user is trying 
# to upload will be received from React. Flask will check the number of entries that exist in 
# qbank with the specified SHA512 hash. This number is returned to React.
@app.route('/checkdatabase', methods=['GET', 'POST'])
def checkdatabase():
    pdfdata = request.data[28:]
    pdfhash = hashlib.sha512(pdfdata).hexdigest()
    
    number = 0
    exists = "no"

    # find number of rows with the hashcode
    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()
    count_query = "select * from qbank where hashcode = %s"

    try:
        cursor.execute(count_query, pdfhash)
        number = cursor.rowcount
    except Exception as e:
        con.rollback()
        return jsonify({"Succeeded": "no", "Exists" : exists, "Number" : number})


    if number > 0:
        exists = "yes"
    return jsonify({"Succeeded": "yes", "Exists" : exists, "Number" : number})

## Updatedatabase: Second function called when the user clicks Upload all questions to database
#  or Upload selected questions to database. Qbank stores all the questions that the user uploads. 
# Each entry contains the question json information and the corresponding pdf SHA512 hash. 
# All previous entries in qbank with the same pdf SHA512 hash will be deleted, as the user 
# is already prompted under Checkdatabase. Updatedatabase creates the question json and pdf 
# hash value based on the data received from React, and inserts these values into the qbank 
# database. Furthermore, the entry with the corresponding pdf SHA512 hash in pdfbank will have 
# its inDatabase attribute updated as 1.
@app.route('/updatedatabase', methods=['GET', 'POST'])
def updatedatabase():
    school = request.args.get("school")
    subject = request.args.get("subject")
    level = request.args.get("level")
    year = request.args.get("year")
    exam = request.args.get("exam")

    decoded_data = request.data.decode("utf-8")
    eval_dict = ast.literal_eval(decoded_data)

    pdfdata = eval_dict["pdfData"][28:]
    listdata = eval_dict["validData"]
    pdfhash = hashlib.sha512(pdfdata.encode("utf-8")).hexdigest()
    

    output_list = []
    for page in listdata:
        for row in page:
            choice_dict = {
                "1": {"text": row[2], "image" : ""},
                "2": {"text": row[3], "image" : ""},
                "3": {"text": row[4], "image" : ""},
                "4": {"text": row[5], "image" : ""},
            }

            row_dict = {
                "level": level,
                "page": row[0],
                "question": row[1],
                "question_type": row[9],
                "choices": choice_dict,
                "answer": row[8],
                "subject": subject,
                "year": year,
                "school": school,
                "exam": exam,
                "number": row[6],
                "image": row[7],
            }
            output_list.append(row_dict)

    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()

    ### PDFBANK

    create_table_query = """create table if not exists pdfbank(
    id int auto_increment primary key,
    hashcode VARCHAR(128) UNIQUE,
    inLibrary int,
    inDatabase int
    )"""

    update_query = """INSERT INTO pdfbank (hashcode, inLibrary, inDatabase)
                    VALUES (%s,%s, %s)
                    ON DUPLICATE KEY UPDATE inDatabase = 1;
                    """ 
                    
    try:
        cursor.execute(create_table_query)
        cursor.execute(update_query, (pdfhash, 0, 1)) 

        con.commit()

    except Exception as e:
        con.rollback()
        print("4: " + str(e))        

    ## QBANK
    create_table_query = """create table if not exists qbank(
    id int auto_increment primary key,
    question json,
    hashcode VARCHAR(10000)
    )"""

    insert_query = """INSERT INTO qbank(question,hashcode) VALUES (%s,%s)"""
    
    overwrite_query = """DELETE FROM qbank WHERE hashcode = %s  """

    request_list = []
    for x in output_list:
        request_list.append((json.dumps(x),pdfhash))

    try:
        cursor.execute(create_table_query)

        cursor.execute(overwrite_query, pdfhash) 
        
        cursor.executemany(insert_query, request_list)
        con.commit()

    except Exception as e:
        con.rollback()

    con.close()
    return jsonify({"Succeeded": "yes"})

### Workspace Tab functions
## Openworkspace: The user clicks open workspace button of a workspace entry in the workspace table. 
# How a workspace is saved is explained under Findworkspace. Each of the three files corresponding 
# to a single workspace is loaded into Flask, from Workspaces/csv/, Workspaces/pdf/ and 
# Workspaces/attributes/. These data are passed back to React. React then opens the Edit tab 
# based on these data. The csv data is used to produce the questions on the right, the pdf 
# data is used to produce the pdf preview on the left, while the attribute data is used to 
# produce the file information on the top.
@app.route('/openworkspace', methods=['GET', 'POST'])
def openworkspace():
    name = request.args.get("name") + ".txt"
    data = ""
    fileData = ""
    attributeData = ""

    if not os.path.exists('Workspaces/csv/' + name):
        return jsonify({"Succeeded": "nocsv", "data": "", "fileData": ""})

    if not os.path.exists('Workspaces/pdf/' + name):
        return jsonify({"Succeeded": "nopdf", "data": "", "fileData": ""})

    if not os.path.exists('Workspaces/attribute/' + name):
        return jsonify({"Succeeded": "noattribute", "data": "", "fileData": ""})

    with open('Workspaces/csv/' + name, 'r', encoding="utf8") as file1:
        data = file1.read()

    with open('Workspaces/pdf/' + name, 'r', encoding="utf8") as file2:
        fileData = file2.read()

    with open('Workspaces/attribute/' + name, 'r', encoding="utf8") as file3:
        attributeData = file3.read()

    attributeDataSplit = attributeData.split(";")
    attributeDataDict = {
        'filename': attributeDataSplit[0],
        'school': attributeDataSplit[1],
        'subject': attributeDataSplit[2],
        'level': attributeDataSplit[3],
        'year': attributeDataSplit[4],
        'exam': attributeDataSplit[5],
    }

    return jsonify({"Succeeded": "yes", "data": data, "fileData": fileData, "attributeData": attributeDataDict})

## Deleteworkspace: The user clicks delete workspace button of a workspace entry in the workspace table.
#  All three files corresponding to the single workspace are deleted from Flask.The entry in pdfbank 
# corresponding to the pdf SHA512 hash of this pdf file will have its inWorkspace attribute updated 
# to 0. Note that this happens only if this Workspace is the only Workspace left with the pdf hash value.
@app.route('/deleteworkspace', methods=['GET', 'POST'])
def deleteworkspace():
    name = request.args.get("name") + ".txt"
    if os.path.exists('Workspaces/pdf/' + name):
        numOfSame = 0
        for item in os.listdir('Workspaces/pdf/'):
            if filecmp.cmp('Workspaces/pdf/' + name, 'Workspaces/pdf/' + item):
                numOfSame = numOfSame + 1

        ##Only update pdfbank if no other workspaces contains the same exact pdf file
        if numOfSame == 1:
            ### PDFBANK
            con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
            cursor = con.cursor()

            create_table_query = """create table if not exists pdfbank(
            id int auto_increment primary key,
            hashcode VARCHAR(128) UNIQUE,
            inLibrary int,
            inDatabase int
            )"""

            update_query = """INSERT INTO pdfbank (hashcode, inLibrary, inDatabase)
                            VALUES (%s,%s, %s)
                            ON DUPLICATE KEY UPDATE inLibrary = 0;
                            """ 
                            
            try:
                pdfhash = ""
                with open('Workspaces/pdf/' + name, "rb") as pdf_file:
                    filedata = pdf_file.read()[28:]
                    pdfhash = hashlib.sha512(filedata).hexdigest()

                cursor.execute(create_table_query)
                cursor.execute(update_query, (pdfhash, 0, 0)) 

                con.commit()

            except Exception as e:
                con.rollback()
                print("3: " + str(e))

        os.remove('Workspaces/pdf/' + name)
        if os.path.exists('Workspaces/csv/' + name):
            os.remove('Workspaces/csv/' + name)
            if os.path.exists('Workspaces/attribute/' + name):
                os.remove('Workspaces/attribute/' + name)
                return jsonify({"Succeeded": "yes"})
            else:
                return jsonify({"Succeeded": "no"})
        else:
            return jsonify({"Succeeded": "no"})
    else:
        return jsonify({"Succeeded": "no"})

## Listworkspace: The user clicks on Refresh data in the workspace table, or is simply 
# called when the user clicks the Library Tab. The Status attribute of the workspace is the 
# same as explained under Listpdf. The attributes of the Workspaces(Name, Last Modified and 
# Status) are received from the pdfbank table with a SELECT query. This Workspaces data is 
# returned to React to populate the Workspaces table.
@app.route('/listworkspace', methods=['GET', 'POST'])
def listworkspace():
    workspaces = []
    
    ### PDFBANK
    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()
    
    if os.path.exists("Workspaces/csv"):
        select_query = "SELECT * FROM pdfbank"
        cursor.execute(select_query)
        select_results = cursor.fetchall()

        items = os.listdir("Workspaces/csv")
        for item in items:
            name = item.replace(".txt", "")
            lastModified = datetime.fromtimestamp(os.path.getmtime("Workspaces/csv/" + item))

            status = "Not Processed"
            count_query = "SELECT * FROM pdfbank WHERE hashcode = %s"

            try:
                pdfhash = ""
                
                if not os.path.exists("Workspaces/hash"):
                    os.makedirs("Workspaces/hash")

                if not os.path.exists("Workspaces/hash/" + name + ".txt"):
                    # Cache for the hash, so it will be faster
                    with open("Workspaces/pdf/" + name + ".txt", "r") as pdf_file:
                        filedata = pdf_file.read()[28:]
                        pdfhash = hashlib.sha512(filedata.encode("utf-8")).hexdigest()
                    
                    file1 = open("Workspaces/hash/" + name + ".txt", "w")
                    file1.write(pdfhash)
                else:
                    with open("Workspaces/hash/" + name + ".txt", "r") as hashfile:
                        pdfhash = hashfile.read()
                        
    

                filtered_select_results = [k for k in select_results if pdfhash in k]
                if len(filtered_select_results) > 0:
                    ## [0] for the first value with the pdfhash, since it should be unique
                    ## [2] for the third value in the row, which contains the inLibrary column
                    ## [3] for the fourth value in the row, which contains the inDatabase column
                    inLibrary = filtered_select_results[0][2]
                    inDatabase = filtered_select_results[0][3]

                    if inLibrary == 0:
                        if inDatabase == 0:
                            status = "Not Processed"
                        elif inDatabase == 1:
                            status = "In Database Only"
                    elif inLibrary == 1:
                        if inDatabase == 0:
                            status = "In Library Only"
                        elif inDatabase == 1:
                            status = "In Library and Database"

            except Exception as e:
                con.rollback()
                

            newFile = {
                'name': name,
                'lastModified': lastModified,
                'status': status,
            }
            workspaces.append(newFile)

    return jsonify({"Succeeded": "yes", "Workspaces": workspaces})

### Database Tab functions
## Getdatabase: The user clicks on Refresh data in the database table, or is simply called when
#  the user clicks the Database Tab. The various attributes of each question are received from 
# the qbank table with a SELECT query. This database data is returned to React to populate the 
# database table.
@app.route('/getdatabase', methods=['GET', 'POST'])
def getdatabase():
    con = pymysql.connect(host='localhost', user='root', passwd='Aa04369484911', db='youzu')
    cursor = con.cursor()

    query = """SELECT * FROM qbank"""
    output_table = []
    try:
        cursor.execute(query)
        for x in cursor:
            question = json.loads(x[1])
            question["1"] = question["choices"]["1"]["text"]
            question["2"] = question["choices"]["2"]["text"]
            question["3"] = question["choices"]["3"]["text"]
            question["4"] = question["choices"]["4"]["text"]
            del question["choices"]
            output_table.append(question)

    except Exception as e:
        con.rollback()

    con.close()
    return jsonify({"Succeeded": "yes", "Table" : output_table})


def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.sample(string.ascii_letters + string.digits, k=stringLength))


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=3003)
