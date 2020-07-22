### (IGNORE) Used to test the workspace bug

# with open('P5-Chinese-SA2-2009-CHIJ.txt', 'r', encoding='utf8') as myfile:
#   data = myfile.read()

# print(data[880750:880850])

# with open('P1-Maths-2010-SA2-Henry-Park.txt', 'r', encoding='utf8') as myfile:
#   data = myfile.read()
#
# #1480176
# print('"' + data[1480160:1480180] + '"')
# print("-----------")
# print('"' + data[1480140:1480199] + '"')

#### UPDATE PDFBANK ACCORDING TO WORKSPACES/HASH ####
from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
import json
import ast
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
import hashlib
import binascii
import filecmp
import shutil

con = pymysql.connect(host='localhost', user='root', passwd='Youzu2020!', db='youzu')
cursor = con.cursor()

workdir = '/datassd/DevelopmentBuild/youzu-flask/Workspaces/hash/'
items = os.listdir(workdir)

insert_query = """INSERT INTO pdfbank (hashcode, inLibrary, inDatabase)
                            VALUES (%s,%s, %s) ON DUPLICATE KEY update hashcode=hashcode"""
for item in items:
  with open(workdir+item,'rb') as hash_file:
    hash_data = hash_file.read()
    try:
      cursor.execute(insert_query,(hash_data,1,0))
      con.commit()
    except Exception as e:
      con.rollback()

con.close()
