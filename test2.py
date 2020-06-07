
import time
import threading

def main(db, x):
    for i in range(100):
        val = db.get('192.168.1.1')["page"] + 1
        db.update('192.168.1.1', {'page': val})
        tid = threading.get_ident() 
        print(str(tid) + ": " + str(db.get('192.168.1.1')))