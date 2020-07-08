# with open('P5-Chinese-SA2-2009-CHIJ.txt', 'r', encoding='utf8') as myfile:
#   data = myfile.read()

# print(data[880750:880850])

with open('P1-Maths-2010-SA2-Henry-Park.txt', 'r', encoding='utf8') as myfile:
  data = myfile.read()

#1480176
print('"' + data[1480160:1480180] + '"')
print("-----------")
print('"' + data[1480140:1480199] + '"')