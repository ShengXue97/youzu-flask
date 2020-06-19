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

# install the following 2 libs first
# from flask_sqlalchemy import SQLAlchemy
# from flask_marshmallow import Marshmallow
# from models.question import Question

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
    
def get_message(currentIP, currentTime, requestIDProcessed):
    out_dict = {}
    time.sleep(1)
    # Unique entry for each request using timestamp!
    entry = None
    foundSession = False
    if os.path.exists('Sessions/' + requestIDProcessed + ".json"):
        with open('Sessions/' + requestIDProcessed + ".json") as json_file:
            entry = json.load(json_file)
            foundSession = True

    if not foundSession:
        out_dict["ipExists"] = "no"
        out_dict["timeStampExists"] = "no"
        out_dict["currentIP"] = currentIP
        out_dict["curentTimeStamp"] = currentTime
        return json.dumps(out_dict)
    else:
        out_dict["ipExists"] = "yes"
        out_dict["timeStampExists"] = "yes"
        out_dict["currentIP"] = currentIP
        out_dict["curentTimeStamp"] = currentTime

        out_dict["stage"] = entry['stage']
        out_dict["page"] = entry['page']
        out_dict["total"] = entry['total']
        return json.dumps(out_dict)
    

@app.route('/stream')
def index():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")
    requestIDRaw = currentIP + "_" + currentTime
    requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")

    if request.headers.get('accept') == 'text/event-stream':
        def events():
            time.sleep(.1)  # an artificial delay
            yield 'data: {}\n\n'.format(get_message(currentIP, currentTime, requestIDProcessed))
        return flask.Response(events(), content_type='text/event-stream')


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
        requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")

        if not requestIDProcessed in session:
            entry = {'stage': 0, 'page' : 0, 'total' : 0, 'output' : []}
            session[requestIDProcessed] = entry

        print("Forking....")
        process = Process()
        thread = threading.Thread(target=process.main, args=(filename, requestIDProcessed))
        thread.start()
        return jsonify({"Succeeded": "yes", "YourIP" : str(currentIP), "YourTime" : currentTime})


@app.route('/getresult', methods = ['GET', 'POST'])
def getresult():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")

    requestIDRaw = currentIP + "_" + currentTime
    requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
    
    df = pd.read_csv(requestIDProcessed + "_output.csv")
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
                page = rows["Question"] if rows["Question"] != "" else "-"
                ans_a = rows["A"] if rows["A"] != "" else "-"
                ans_b = rows["B"] if rows["B"] != "" else "-"
                ans_c = rows["C"] if rows["C"] != "" else "-"
                ans_d = rows["D"] if rows["D"] != "" else "-"
                qnNum = rows["Number"]
                qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum]
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
                    page = rows["Question"] if rows["Question"] != "" else "-"
                    ans_a = rows["A"] if rows["A"] != "" else "-"
                    ans_b = rows["B"] if rows["B"] != "" else "-"
                    ans_c = rows["C"] if rows["C"] != "" else "-"
                    ans_d = rows["D"] if rows["D"] != "" else "-"
                    qnNum = rows["Number"]
                    qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum]
                    # append question list to page list
                    thisPageList.append(qn_list)

    row_json.append(thisPageList)
    os.remove(requestIDProcessed + "_output.csv")
    return jsonify(row_json)


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=3001)
