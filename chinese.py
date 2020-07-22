import sys
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

IMAGE_PATH = r"C:\Users\graez\Downloads\chinese_single.PNG"

# open image
im = Image.open(IMAGE_PATH)

# preprocessing
im = im.convert('L')                             # grayscale
im = im.filter(ImageFilter.MedianFilter())       # a little blur
im = im.point(lambda x: 0 if x < 140 else 255)   # threshold (binarize)

text = pytesseract.image_to_string(im,lang='chi_sim',config='--psm 6')           # pass preprocessed image to tesseract
print(text)                                      # print