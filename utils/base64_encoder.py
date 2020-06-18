import base64, cv2
from PIL import Image
from io import BytesIO, StringIO
import numpy as np

def encode(filepath):
# read the image from the path and transfer to base64
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

# if you need a numpy to base64:

    # img = your numpy image
    # _, im_arr = cv2.imencode('.jpg', img)
    # im_bytes = im_arr.tobytes()
    # encoded_string = base64.b64encode(im_bytes)

    return encoded_string

def decode(base64_string):
# read the image in base64 string and transfer to numpy format(same as cv2.imread())
    byte_img = base64.b64decode(base64_string)
    pimg = Image.open(BytesIO(byte_img))
    return cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)