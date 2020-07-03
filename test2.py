import re

text = "dbedb\fwwf"
text = re.sub(r'\\[^bfnrt"\]', '', text)
print(text)