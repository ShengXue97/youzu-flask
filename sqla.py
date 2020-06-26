# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
#
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Youzu2020!@127.0.0.1:3306/youzu'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#
# db = SQLAlchemy(app)
#
#
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     location = db.Column(db.String(120), unique=True, nullable=False)
#
#     def __init__(self, name, location):
#       self.name  = name
#       self.location = location

import pandas as pd
from sqlalchemy import create_engine

# "/home/edu/DevelopmentBuild/youzu-flask/test-sqla.csv"

column_names = ['','Level', 'Page','Question','Comment','A','B','C','D']

df = pd.read_csv('/home/edu/DevelopmentBuild/youzu-flask/test-sqla.csv', header = 0)
#print(df)
engine = create_engine('mysql://root:Youzu2020!@127.0.0.1:3306/youzu')
with engine.connect() as conn, conn.begin():
    df.to_sql('TEST', conn, if_exists='append', index=False)