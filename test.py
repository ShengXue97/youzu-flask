from dbj import dbj
from test2 import main
import threading, time
import time

class Status:
    def __init__(self):
        self.page = 1

db = dbj('mydb.json')
user = {'page': 0}
db.insert(user, '192.168.1.1')

value = db.get('192.168.1.1')
print(value)

status = Status()
x = 0

for i in range(10):
    thread = threading.Thread(target=main, args=(db, x))
    thread.start()

while True:
    time.sleep(0.1)
    print("1: " + str(db.get('192.168.1.1')))