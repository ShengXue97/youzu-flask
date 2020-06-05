from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
import ast
from MainV9 import main
from MainV9 import Status
import os
import pandas as pd
import threading, time
import flask
import itertools

from datetime import datetime


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# dictionary of tuple: status(whether there is an ongoing request from this ip), and the Status object of that request.
ip_status_dict = {}

@app.route("/")
def home():
    return "<h1>Welcome man, enjoy your stay<h1>"
    
def get_message(currentIP):
    '''this could be any function that blocks until data is ready'''
    time.sleep(0.5)
    out_dict = {}
    if currentIP in ip_status_dict:
        value = ip_status_dict[currentIP]
        # Only returns the value relevant to the currentIP address
        out_dict["ipExists"] = "yes"
        out_dict["running"] = value[0]
        out_dict["done"] = value[1].done
        out_dict["stage"] = value[1].stage
        out_dict["page"] = value[1].page
        out_dict["total"] = value[1].total

        #Set done to 0, this prevents the opening of multiple edit tabs
        ip_status_dict[currentIP][1].running = 0
        ip_status_dict[currentIP][1].value[1].done = 0
        return json.dumps(out_dict)
    else:
        out_dict["ipExists"] = "no"
        return json.dumps(out_dict)
    

@app.route('/stream')
def index():
    currentIP = request.args.get("currentIP")
    if request.headers.get('accept') == 'text/event-stream':
        def events():
            time.sleep(.1)  # an artificial delay
            yield 'data: {}\n\n'.format(get_message(currentIP))
        return flask.Response(events(), content_type='text/event-stream')

@app.route("/redeploy")
def redeploy():
    ip_status_dict.clear()
    return jsonify({"Reset success": "yes"})

@app.route('/uploadfile', methods = ['GET', 'POST'])
def uploadfile():
    print("called1")
    ip_status_dict.clear()
    response = None
    if request.method == 'POST':
        currentIP = request.remote_addr
        print(currentIP)
        # if currentIP in ip_status_dict:
        #     if ip_status_dict[currentIP][0] == True:
        #         return jsonify({"Succeeded": "yes"})

        fileDownloaded=request.files["myFile"]
        filename = fileDownloaded.filename
        fileDownloaded.save(os.path.join("./ReactPDF", filename))
        status = Status()
        ip_status_dict[currentIP] = (True, status)
        # main(filename, status)

        print("Forking....")
        thread = threading.Thread(target=main, args=(filename, status))
        thread.start()
        return jsonify({"Succeeded": "yes", "YourIP" : str(currentIP)})


@app.route('/getresult', methods = ['GET', 'POST'])
def getresult():
    df = pd.read_csv("output.csv")

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