from datetime import datetime
currentTime = str(datetime.now())
print((currentTime.replace(":", "-").replacee(".", "_")))