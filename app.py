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


@app.route('/listpdf', methods=['GET', 'POST'])
def listpdf():
    pdfs = []
    azureDir = "/datassd/pdf_downloader-master/pdfs/"
    localDir = "pdfs/"
    myDir = ""

    if os.path.exists(azureDir):
        myDir = azureDir
    elif os.path.exists(localDir):
        myDir = localDir
    else:
        return jsonify({"Succeeded": "no", "Pdfs": pdfs})

    items = os.listdir(myDir)
    for item in items:
        name = item.replace(".pdf", "")
        lastModified = datetime.fromtimestamp(os.path.getmtime(myDir + item))
        newFile = {
            'name': name,
            'lastModified': lastModified,
        }
        pdfs.append(newFile)

    return jsonify({"Succeeded": "yes", "Pdfs": pdfs})


@app.route('/findworkspace', methods=['GET', 'POST'])
def findworkspace():
    name = request.args.get("name") + ".txt"
    data = ""
    fileData = ""
    if os.path.exists('Workspaces/csv/' + name):
        return jsonify({"Exists": "yes"})
    else:
        return jsonify({"Exists": "no"})


# 'filename': defaultFilename,
# 'school': defaultSchoolname,
# 'subject': defaultFilesubject,
# 'level': defaultPaperlevel,
# 'year': defaultPaperyear,
# 'exam': defaultExam,

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


@app.route('/getpdfpages', methods=['GET', 'POST'])
def getpdfpages():
    name = request.args.get("name")
    isExisting = request.args.get("isExisting")
    filePath = ""
    print("um" + name)
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


@app.route('/savepdf', methods=['GET', 'POST'])
def savepdf():
    name = request.args.get("name")
    if not os.path.exists("Workspaces/pdf"):
        os.makedirs("Workspaces/pdf")
    file1 = open("Workspaces/pdf/" + name + ".txt", "wb")
    file1.write(request.data)

    currentIP = request.remote_addr
    currentTime = str(datetime.now())

    return jsonify({"Succeeded": "yes", "YourIP": str(currentIP), "YourTime": currentTime})


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


@app.route('/deleteworkspace', methods=['GET', 'POST'])
def deleteworkspace():
    name = request.args.get("name") + ".txt"
    if os.path.exists('Workspaces/pdf/' + name):
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


@app.route('/listworkspace', methods=['GET', 'POST'])
def listworkspace():
    workspaces = []
    if os.path.exists("Workspaces/csv"):
        items = os.listdir("Workspaces/csv")
        for item in items:
            name = item.replace(".txt", "")
            lastModified = datetime.fromtimestamp(os.path.getmtime("Workspaces/csv/" + item))
            newFile = {
                'name': name,
                'lastModified': lastModified,
            }
            workspaces.append(newFile)

    return jsonify({"Succeeded": "yes", "Workspaces": workspaces})


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

        if ignoreCustomPageRange == "true":
            for i in range(infile.numPages):
                p = infile.getPage(i)
                output.addPage(p)
        else:
            # 0-index
            for i in range(int(currentStartPage) - 1, int(currentEndPage)):
                p = infile.getPage(i)
                output.addPage(p)

        newFilename = request.args.get("name") + "_" + sessionID + ".pdf"
        with open("ReactPDF/" + newFilename, 'wb') as f:
            output.write(f)

        pdf_file = open("ReactPDF/" + newFilename, "rb")
        pdf_data_binary = pdf_file.read()
        pdf_bas64 = "data:application/pdf;base64," + (base64.b64encode(pdf_data_binary)).decode("ascii")

        print("Forking....")
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

        print("Forking....")
        process = Process()
        thread = threading.Thread(target=process.main, args=(filename, sessionID))
        thread.start()
        return jsonify(
            {"Succeeded": "yes", "YourSessionID": sessionID, "YourIP": str(currentIP), "YourTime": currentTime,
             'filename': filename, 'pdf_base64': pdf_bas64})


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


@app.route('/updatedatabase', methods=['GET', 'POST'])
def updatedatabase():
    school = request.args.get("school")
    subject = request.args.get("subject")
    level = request.args.get("level")
    year = request.args.get("year")
    exam = request.args.get("exam")

    decoded_data = request.data.decode("utf-8")
    list_data = ast.literal_eval(decoded_data)

    output_list = []
    for page in list_data:
        for row in page:
            choice_dict = {
                "A": row[2],
                "B": row[3],
                "C": row[4],
                "D": row[5]
            }

            row_dict = {
                "Level": level,
                "Page": row[0],
                "Question": row[1],
                "Question_type": row[9],
                "Choices": choice_dict,
                "Answer": row[8],
                "Subject": subject,
                "Year": year,
                "School": school,
                "Exam": exam,
                "Number": row[6],
                "Image File": row[7],
            }
            output_list.append(row_dict)

    con = pymysql.connect(host='localhost', user='root', passwd='Youzu2020!', db='youzu')
    cursor = con.cursor()

    create_table_query = """create table if not exists qbank(
    id int auto_increment primary key,
    question json
    )"""
    insert_query = """insert into qbank(question) values (%s)"""

    try:
        cursor.execute(create_table_query)
        for x in output_list:
            cursor.execute(insert_query, json.dumps(x))
        con.commit()
        print('successfully inserted values')

    except Exception as e:
        con.rollback()
        print("exception occured:", e)

    con.close()
    return jsonify({"Succeeded": "yes"})

@app.route('/getdatabase', methods=['GET', 'POST'])
def getdatabase():
    con = pymysql.connect(host='localhost', user='root', passwd='Youzu2020!', db='youzu')
    cursor = con.cursor()

    query = """SELECT * FROM qbank"""
    output_table = []
    try:
        cursor.execute(query)
        for x in cursor:
            question = json.loads(x[1])
            question["A"] = question["Choices"]["A"]
            question["B"] = question["Choices"]["B"]
            question["C"] = question["Choices"]["C"]
            question["D"] = question["Choices"]["D"]
            del question["Choices"]
            output_table.append(question)

    except Exception as e:
        con.rollback()
        print("exception occured:", e)

    con.close()
    return jsonify({"Succeeded": "yes", "Table" : output_table})

# @app.before_request
# def log_request_info():
#     app.logger.debug('Headers: %s', request.headers)
#     app.logger.debug('Body: %s', request.get_data())

#     with open("request_header_log.txt", "a") as myfile:
#         myfile.write('Headers: "' + str(request.headers) + '"\n')
#         myfile.write('-----------------------------------------\n')

#     with open("request_body_log.txt", "a") as myfile:
#         myfile.write('Body: "' + str(request.get_data()) + '"\n')
#         myfile.write('-----------------------------------------\n')

## Below are helper methods not part of API

def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.sample(string.ascii_letters + string.digits, k=stringLength))


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)