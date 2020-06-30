import random
import string

def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.sample(string.ascii_letters + string.digits, k=stringLength))

print("Random String is ", randomString())
print("Random String is ", randomString(20))
print("Random String is ", randomString(20))