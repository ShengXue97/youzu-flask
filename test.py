# with open('P5-Chinese-SA2-2009-CHIJ.txt', 'r', encoding='utf8') as myfile:
#   data = myfile.read()

# print(data[880750:880850])

with open('P4-Science-CA2-2005-Nanyang.txt', 'r', encoding='utf8') as myfile:
  data = myfile.read()

#186121
print('"' + data[186121:186200] + '"')
print("-----------")
print('"' + data[185900:186400] + '"')