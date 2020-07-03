# with open('P5-Chinese-SA2-2009-CHIJ.txt', 'r', encoding='utf8') as myfile:
#   data = myfile.read()

# print(data[880750:880850])

with open('P4-Science-SA2-2010-NanYang.txt', 'r', encoding='utf8') as myfile:
  data = myfile.read()

#809308
print('"' + data[809300:809320] + '"')
print('"' + data[809000:809600] + '"')