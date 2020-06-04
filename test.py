class test:
    def __init__(self):
        self.x = 1
        self.y = 10

newTest = test()




def add(testObj):
    testObj.x = testObj.x + testObj.y

add(newTest)
print(newTest.x)