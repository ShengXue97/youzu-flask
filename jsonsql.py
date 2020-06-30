import pandas as pd
from sqlalchemy import create_engine
import pymysql, os, json

# convert csv to df
df = pd.read_csv("/home/edu/DevelopmentBuild/youzu-flask/2020-06-25 11-52-30_066700_kiPa3qsA_output.csv") #insert file path

#clean df
df1=df.drop(df.columns[0], axis=1)
df1 = df1.fillna('-')

#create json object output_list
output_list=[]
colname = list(df1)
# print(colname)
for index, row in df1.iterrows():
    row_dict = {}
    choice_dict = {}
    for col in colname:
        if col == 'A' or col == 'B' or col == 'C' or col == 'D':
            choice_dict[col] = row[col]
        else:
            row_dict[col] = row[col]
    row_dict['Choices'] = choice_dict
    output_list.append(row_dict)



# connection to mysql database
con = pymysql.connect(host = 'localhost',user = 'root',passwd = 'Youzu2020!',db = 'youzu');
cursor = con.cursor();



create_table_query = """create table if not exists qbank(
id int auto_increment primary key,
question json
)""";
cursor.execute(create_table_query)
def show_tables():
    cursor.execute("""show tables""")


def insert_data(json_obj):
    insert_query = """insert into qbank(question) values (%s)"""
    for x in json_obj:
        cursor.execute(insert_query, json.dumps(x))

def reset_table():
    cursor.execute("""truncate table qbank""")

# def update():

def reset_counter():
    cursor.execute("""ALTER TABLE qbank AUTO_INCREMENT = 1""")

try:
    reset_table()
    
    con.commit();
    print('update successful')

except Exception as e:
    con.rollback();
    print("exception occured:", e)

con.close();
