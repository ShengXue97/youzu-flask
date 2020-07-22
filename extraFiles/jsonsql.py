import pandas as pd
from sqlalchemy import create_engine
import pymysql, os, json

# convert csv to df
# df = pd.read_csv("/home/edu/DevelopmentBuild/youzu-flask/2020-06-25 11-52-30_066700_kiPa3qsA_output.csv") #insert file path

# #clean df
# df1=df.drop(df.columns[0], axis=1)
# df1 = df1.fillna('-')

# #create json object output_list
# output_list=[]
# colname = list(df1)
# # print(colname)
# for index, row in df1.iterrows():
#     row_dict = {}
#     choice_dict = {}
#     for col in colname:
#         if col == 'A' or col == 'B' or col == 'C' or col == 'D':
#             choice_dict[col] = row[col]
#         else:
#             row_dict[col] = row[col]
#     row_dict['Choices'] = choice_dict
#     output_list.append(row_dict)



# connection to mysql database
con = pymysql.connect(host = 'localhost',user = 'root',passwd = 'Youzu2020!',db = 'youzu');
cursor = con.cursor();



create_table_query = """create table if not exists qbank(
    id int auto_increment primary key,
    question json,
    hashcode VARCHAR(100)
    )""";
cursor.execute(create_table_query)
def show_tables():
    cursor.execute("""show tables""")

def delete_table():
    cursor.execute("""DROP TABLE IF EXISTS qbank""")
    
def insert_data(json_obj):
    insert_query = """insert into qbank(question) values (%s)"""
    for x in json_obj:
        cursor.execute(insert_query, json.dumps(x))

def reset_table():
    cursor.execute("""truncate table qbank""")

def insert_column():
    cursor.execute("""Alter table qbank add column hashcode VARCHAR(100) not null after question""")

def reset_counter():
    cursor.execute("""ALTER TABLE qbank AUTO_INCREMENT = 1""")
    
def overwrite_query():
    cursor.execute("""delete from qbank where hashcode = %s """)

def update_hash_query():
    cursor.execute("""update qbank set hashcode = 'db7ad91061d48783cf37762e11f347955f0acbc0b14270dd06aa7e690e6abcb72901de74edef520b25a33c122529e0b9683564b42965f412abb2501368baf5f7' where hashcode = '27b6664da634a0b745d0'""")
try:
    update_hash_query()

    con.commit();
    print('update successful')
    print(cursor.rowcount,'record(s) modified')

except Exception as e:
    con.rollback();
    print("exception occured:", e)

con.close();