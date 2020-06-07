from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
import ast
from MainV9 import main
import os
import pandas as pd
import threading, time
import flask
import itertools
from dbj import dbj

from datetime import datetime


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db = dbj('mydb.json')
currentObj = {}

def setObj(newObj):
    currentObj = newObj

@app.route("/")
def home():
    return "<h1>Welcome man, enjoy your stay<h1>"
    
def get_message(currentIP, currentTime):
    out_dict = {}
    # Unique entry for each request using timestamp!
    requestIDRaw = currentIP + "_" + currentTime
    requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")
    print(requestIDProcessed)
    print(db.getall())
    if not db.exists(requestIDProcessed):
        out_dict["ipExists"] = "no"
        out_dict["timeStampExists"] = "no"
        out_dict["currentIP"] = currentIP
        out_dict["curentTimeStamp"] = currentTime
        return json.dumps(out_dict)
    else:
        val = db.get(requestIDProcessed)

        out_dict["ipExists"] = "yes"
        out_dict["timeStampExists"] = "yes"
        out_dict["currentIP"] = currentIP
        out_dict["curentTimeStamp"] = currentTime

        out_dict["stage"] = val['stage']
        out_dict["page"] = val['page']
        out_dict["total"] = val['total']
        return json.dumps(out_dict)
    

@app.route('/stream')
def index():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")
    if request.headers.get('accept') == 'text/event-stream':
        def events():
            time.sleep(.1)  # an artificial delay
            yield 'data: {}\n\n'.format(get_message(currentIP, currentTime))
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

        if not db.exists(requestIDProcessed):
            entry = {'stage': 0, 'page' : 0, 'total' : 0}
            db.insert(entry, requestIDProcessed)

        print("Forking....")
        thread = threading.Thread(target=main, args=(filename, db, requestIDProcessed, setObj))
        thread.start()
        return jsonify({"Succeeded": "yes", "YourIP" : str(currentIP), "YourTime" : currentTime})


@app.route('/getresult', methods = ['GET', 'POST'])
def getresult():
    currentIP = request.args.get("currentIP")
    currentTime = request.args.get("currentTime")

    requestIDRaw = currentIP + "_" + currentTime
    requestIDProcessed = currentTime.replace(":", "-").replace(".", "_")

    df = pd.read_csv(requestIDProcessed + "/output.csv")

    # Create an empty list 
    row_json = []
    
    # Iterate over each row 
    for index, rows in df.iterrows(): 
        # Create list for the current row 
        my_list =[rows["Level"], rows["Question"], rows["isMCQ"], rows["A"], rows["B"], rows["C"], rows["D"], rows["Subject"], rows["Year"], rows["School"], rows["Exam"], rows["Number"], rows["Image"], rows["Image File"]] 
        # append the list to the final list 
        row_json.append(my_list)
    
    return jsonify(row_json)

if __name__ == '__main__':
    app.run(threaded=True, port=5000)