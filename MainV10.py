# V10E: Current implementation - Working on English Papers (MCQ)
### For English MCQs Questions only ###

### For English MCQs Questions only ###

### For English MCQs Questions only ###


### For English MCQs Questions only ###
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps
from GibberishDetector import classify
import os
import sys
from pdf2image import convert_from_path
import io
import re
import pandas as pd
import platform
import math as m
import ast
import shutil
import base64
import os.path
from os import path
import json


class Process:
    def __init__(self):
        self.pg_number = 1
        self.pg_cnt_ls = []
        self.pg_num_1 = 2
        self.requestID = ""
        
        self.qn_num = 1
        self.total_qns = 0
        self.pg_num = 1
        self.diagram_count = 1
        self.filename = ""
        self.total_pages = -1
        self.image_count = 0
        self.current_section = ""
        self.file_attribute_list = []
        self.filenames_list = []
        self.qn_images_list = []
        self.global_df = pd.DataFrame(
            columns=['Level', 'Page', 'Question', 'Comment', 'A', 'B', 'C', 'D', 'Subject', 'Year', 'School', 'Exam',
                     'Number', 'Image',
                     'Image File'])

    def get_image(self, image_path):
        """Get a numpy array of an image so that one can access values[x][y]."""
        image = Image.open(image_path, 'r')
        image = image.convert('L')  # makes it greyscale
        width, height = image.size
        pixel_values = list(image.getdata())
        if image.mode == 'RGB':
            channels = 3
        elif image.mode == 'L':
            channels = 1
        else:
            print("Unknown mode: %s" % image.mode)
            return None
        pixel_values = np.array(pixel_values).reshape((width, height, channels))
        return pixel_values

    def is_white_image(self, image_name):
        numpy_array = self.get_image(image_name + ".jpg")
        total_pixels = numpy_array.size
        num_of_black = 0
        num_of_white = 0

        for i in numpy_array:
            for j in i:
                if j[0] > 200:
                    num_of_white = num_of_white + 1
                else:
                    num_of_black = num_of_black + 1

        white_percentage = num_of_white / total_pixels
        # Save as inverted image if it is a negative image
        if white_percentage < 0.75:
            # load image# Load image
            im = Image.open(image_name + ".jpg")

            # Invert
            result = ImageOps.invert(im)

            # Save
            result.save(image_name + "_inverted.jpg")
            return False
        else:
            return True

    def get_thresh_and_contours(self, img, filename):
        # Blurring
        imgBlur = cv2.GaussianBlur(img, (7, 7), 1)
        # cv2.imshow("blur",imgBlur)

        # convert to gray
        gray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("gray",gray)

        # threshold the grayscale image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        # Draw contours
        result = img.copy()

        # use morphology erode to blur horizontally
        # kernel = np.ones((500,3), np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 3))  # 250,3
        morph = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)

        # if re.search(r'english', self.filename, re.I):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 30))  # previously 20,30 for eng papers
        # else:
        #     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 17))  # previously 20,30 for eng papers
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)

        resized = cv2.resize(morph, (700, 850))
        # cv2.imshow("morph",resized)

        # find contours
        cntrs = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]
        return thresh, cntrs, result, morph

    def merge_contours(self, thresh, cntrs, x_tolerance, y_tolerance):
        # Erase small contours, and contours which small aspect ratio (close to a square)
        for c in cntrs:
            area = cv2.contourArea(c)

            # Fill very small contours with zero (erase small contours).
            if area < 100:
                cv2.fillPoly(thresh, pts=[c], color=0)
                continue

            # https://stackoverflow.com/questions/52247821/find-width-and-height-of-rotatedrect
            rect = cv2.minAreaRect(c)
            (x, y), (w, h), angle = rect
            # aspect_ratio = max(w, h) / min(w, h)

            # Assume zebra line must be long and narrow (long part must be at lease 1.5 times the narrow part).
            '''
            if (aspect_ratio < 1.5):
                cv2.fillPoly(thresh, pts=[c], color=0)
                continue
                '''

        # Use "close" morphological operation to close the gaps between contours
        # https://stackoverflow.com/questions/18339988/implementing-imcloseim-se-in-opencv
        try:
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
                                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (x_tolerance, y_tolerance)))
        except:
            # Likely nothing to merge, so there is an error
            pass
        finally:
            # Find contours in thresh_gray after closing the gaps
            cntrs, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            return thresh, cntrs
        # thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
        #                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (x_tolerance, y_tolerance)));
        #
        # # Find contours in thresh_gray after closing the gaps
        # cntrs, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # return thresh, cntrs

    def draw_contours(self, result, img, cntrs, image_name):

        ### document_data_list = self.draw_contours(result, img, cntrs, image_name)### draw_cntr called

        # Contains list of tuples of (data, type, y_coord)
        # data contains actual string if it is a text, and the image path in TempImages if it contains an image.
        # type is "text" or "image"
        # y_coord contains y coordinates of the text or image
        document_data_list = []
        height, width, channels = img.shape

        # if re.search(r'english', self.filename, re.I):
        result_1 = img.copy()
        # image preprocessing and find contours for blank line detection
        gray_1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh_1 = cv2.threshold(gray_1, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        detected_lines = cv2.morphologyEx(thresh_1, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

        cnts_line = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts_line = cnts_line[0] if len(cnts_line) == 2 else cnts_line[1]
        # draw contours for blank line
        for c in cnts_line:
            # cv2.drawContours(image, [c], -1, (0,0,255), 3)
            x1, y1, w1, h1 = cv2.boundingRect(c)
            if 0.05 < w1 / width < 0.2:
                cv2.rectangle(result, (x1, y1), (x1 + w1, y1 + h1), (255, 0, 0), 2)
                texted = cv2.putText(result_1, '(EMPTY)____', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (0, 0, 0), 2, cv2.LINE_AA) #1.2-->0.8
                texted = cv2.dilate(texted, np.ones((2, 2), np.uint8), iterations=1)
        for c in cntrs:
            area = cv2.contourArea(c) / 10000
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
            if "texted" in locals():
                grayish = cv2.cvtColor(texted, cv2.COLOR_BGR2GRAY)
                # image = cv2.imread(img, 0)

            else:
                grayish = cv2.cvtColor(result_1, cv2.COLOR_BGR2GRAY)
                # image = cv2.imread(img, 0)
            thresh = 255 - cv2.threshold(grayish, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            ###cropping out image and convert to text
            if y-10 > 0 and y+h+10 < height and x-20 > 0 and x+w+20 < width :
                ROI = thresh[y-10 : y+h+10, x-20 : x+w+20]
            else:
                ROI = thresh[y :y + h , x :x + w ]
            text = pytesseract.image_to_string(ROI, lang='eng', config='--psm 6')
            text = re.sub(r"\(EMPTY[\)]*|\(FMPTY[\)]*|\(eEmpTy[\)]*|\(Fupty[\)]*|\(Fuprty[\)]", "_________", text, flags=re.I)
            pseudo_text = text

            if w / width > 0.05 and y / height < 0.95:  # and (x/width < 0.4 or x/width > 0.5)
                # hough line detector included too for eng
                new_image = img[y:y + h, x:x + w]
                dst = cv2.Canny(new_image, 50, 200, None, 3)
                linesp = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 2)
                # if self.is_gibberish(text) and w/h < 5:
                if self.is_gibberish(text) or 0.35 < (w * h) / (width * height) < 0.97 or linesp is not None:
                    if h / height > 0.1 and w / h < 5:
                        # Likely to be an image
                        new_image = img[y:y + h, x:x + w]
                        cv2.imwrite("TempImages/" + self.requestID + "_" + str(self.diagram_count) + ".jpg", new_image)
                        # store in base64 as well into document_data_list
                        with open("TempImages/" + self.requestID + "_" + str(self.diagram_count) + ".jpg", "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        document_data_list.append(
                            ("TempImages/" + self.requestID + "_" + str(self.diagram_count) + ".jpg", "image", y,
                             pseudo_text, encoded_string))
                        self.diagram_count = self.diagram_count + 1
                    else:
                        # Likely to be text, just small regions like "Go on to the next page"
                        document_data_list.append((text, "text", y, pseudo_text, ""))
                else:
                    # Likely to be a text
                    document_data_list.append((text, "text", y, pseudo_text, ""))
        # for non english papers, no blank line detection required
        # else:
        #     for c in cntrs:
        #         area = cv2.contourArea(c) / 10000
        #         x, y, w, h = cv2.boundingRect(c)
        #         cv2.rectangle(result, (x - 10, y - 10), (x + w + 5, y + h + 5), (0, 0, 255), 2)
        #         if platform.system() == "Windows":
        #             pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
        #
        #         # Read as binary image
        #         image = cv2.imread(image_name + ".jpg", 0)
        #
        #         thresh = 255 - cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        #
        #         ROI = thresh[y:y + h, x:x + w]
        #         text = pytesseract.image_to_string(ROI, lang='eng', config='--psm 6')
        #         pseudo_text = text
        #
        #         # Only add the image if it is large enough,
        #         # and the entire image has illegal text symbols(which is likely to be a diagram)
        #         # if w/width > 0.0302 and h/height > 0.0213 and y/height < 0.95:
        #         if w / width > 0.1 and h / height > 0.001 and y / height < 0.95 and w / h < 25:  # and (x/width < 0.4 or x/width > 0.5)
        #             # if is_gibberish(text) and w/h < 5:
        #             ############## trying out hough transform as a filter!!! ###############
        #             new_image = img[y:y + h, x:x + w]
        #             dst = cv2.Canny(new_image, 50, 200, None, 3)
        #             linesp = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 2)
        #             if linesp is not None or self.is_gibberish(text):
        #                 cv2.imwrite("TempImages/" + str(self.diagram_count) + ".jpg", new_image)
        #                 document_data_list.append(
        #                     ("TempImages/" + str(self.diagram_count) + ".jpg", "image", y, pseudo_text))
        #                 self.diagram_count = self.diagram_count + 1
        #             else:
        #                 # large chunk that resembles diagram, but really is text
        #                 document_data_list.append((text, "text", y, pseudo_text))
        return document_data_list

    def is_gibberish(self, text):
        # global self.filename
        is_definitely_not_gibberish = False
        split = text.split("\n")

        total_value = 0
        if len(split) == 0:
            return False

        # Every line in the contour box
        for s in split:
            # if re.search(r'english', self.filename, re.I):
            if "(1)" in s or "(2)" in s or "(3)" in s or "(4)" in s or "(a)" in s or "(b)" in s or "(c)" in s or "(d)" in s:
                # if there is a answer number, it is definitely not gibberish. i.e we want it as a text, not image
                is_definitely_not_gibberish = True
            # elif re.search(r'math', self.filename, re.I):
            #     # some qn headers for non-english papers are auto recognized as gibberish, so we want to correct that
            #     search_sentence = re.search(r'[?0-9]+[.,]+', s, re.I)
            #     numberans_search = re.search(r'[\[\(\{][1-4a-b]+[]\)\}]|Ans]', s, re.I)
            #     if search_sentence or numberans_search:
            #         is_definitely_not_gibberish = True
            # else:
            #     # definitely a science paper, where options (1)-(4) should not always be treated as not gibberish
            #     search_sentence = re.search(r'[?0-9]+[.,]+', s, re.I)
            #     if search_sentence or "(a)" in s or "(b)" in s or "(c)" in s or "(d)" in s:
            #         is_definitely_not_gibberish = True

        gibberish_likelihood_percentage = classify(s)
        total_value = total_value + gibberish_likelihood_percentage

        if is_definitely_not_gibberish:
            return False

        average_percentage = total_value / len(split)
        if average_percentage > 45:
            # likely to be gibberish
            return True
        else:
            return False


    def write_data_to_document(self, document_data_list, qn_coord):
        # qn_coord is a tuple consisting of nested (pg_number, y) tuples of each contour

        # Sort data of text and images according to their y values, and add them to a word document
        document_data_list.sort(key=lambda tup: tup[2])
        current_ans_list = []
        found_ans_options = False
        first_ans_pos = -1

        # file_attribute_list -> [paper_level, paper_subject, paper_year, paper_school, paper_exam_type]
        paper_level = self.file_attribute_list[0].upper()
        paper_subject = self.file_attribute_list[1].upper()
        paper_year = self.file_attribute_list[2]
        paper_school = self.file_attribute_list[3]
        paper_exam_type = self.file_attribute_list[4].upper()

        final_text = ""
        final_image = ""
        ans_a = "-"
        ans_b = "-"
        ans_c = "-"
        ans_d = "-"

        for i in range(len(document_data_list)):
            data = document_data_list[i]
            item = data[0]  # TempImages/5.jpg
            typeof = data[1]
            y_coord = data[2]
            pseudo_text = data[3]
            base64img = data[4]

            # STEP 2: Find ans sections
            #regex = re.compile('[\[\(\|\{][0-9]?[0-9][\]\)\}\|]')
            #(any type of character within brackets, len < 3)
            regex = re.compile('[\[\(\|\{].{1,3}[\]\)\}\|]')#|.{1,3}[\]\)\}\|]

            matches = regex.finditer(pseudo_text)
            match_list = []
            for match in matches:
                match_list.append(match)
            for i in range(len(match_list)):
                match = match_list[i]
                lineno = pseudo_text.count('\n', 0, match.start())

                if len(current_ans_list) <= 3:
                    startpos = match.regs[0][0]
                    endpos = match.regs[0][1]
                    if len(current_ans_list) == 0:
                        first_ans_pos = startpos

                    if i == len(match_list) - 1:
                        # Last match
                        substr = pseudo_text[startpos:]
                        current_ans_list.append(substr)
                    else:
                        # Still have matches after
                        nextstartpos = match_list[i + 1].regs[0][0]
                        substr = pseudo_text[startpos:nextstartpos]
                        current_ans_list.append(substr)
                else:
                    break
            ans_a = "-" if len(current_ans_list) <= 0 else current_ans_list[0]
            ans_a = re.sub('[\[\(\|\{]1[\]\)\}\|]', '', ans_a)
            ans_b = "-" if len(current_ans_list) <= 1 else current_ans_list[1]
            ans_b = re.sub('[\[\(\|\{]2[\]\)\}\|]', '', ans_b)
            ans_c = "-" if len(current_ans_list) <= 2 else current_ans_list[2]
            ans_c = re.sub('[\[\(\|\{]3[\]\)\}\|]', '', ans_c)
            ans_d = "-" if len(current_ans_list) <= 3 else current_ans_list[3]
            ans_d = re.sub('[\[\(\|\{]4[\]\)\}\|]', '', ans_d)

            # STEP 3: Add question to dataframe
            if typeof == "text" and item != "":
                if first_ans_pos == -1:
                    # Ans options not found yet
                    final_text = final_text + item
                    final_text = re.sub(r'[0-9][0-9]|[0-9]', '',final_text,1)
                else:
                    # Ans options found
                    final_text = final_text + item[:first_ans_pos]
                    final_text = re.sub(r'[0-9][0-9]|[0-9]', '',final_text,1)

            elif typeof == "image":
                final_image = final_image + base64img + " "

        contains_image = "No"
        if final_image != "":
            contains_image = "Yes"
        if final_text == "":
            final_text = "-"
        if final_image == "":
            final_image = "-"

        self.global_df.loc[self.qn_num] = [paper_level, qn_coord[self.qn_num][0], final_text, "-", ans_a, ans_b, ans_c, ans_d,
                                           paper_subject,
                                           paper_year, paper_school, paper_exam_type, self.qn_num, contains_image,
                                           final_image]

        ## insert question type under comments column
        for index, row in self.global_df.iterrows():
            if len(self.pg_cnt_ls) == 0:
                self.global_df.at[index, 'Comment'] = 'MCQ'
            else:
                if row['Page'] < min(self.pg_cnt_ls):
                    self.global_df.at[index, 'Comment'] = 'MCQ'
                elif row['Page'] > max(self.pg_cnt_ls):
                    self.global_df.at[index, 'Comment'] = 'Structured Qn'
                for x in self.pg_cnt_ls:
                    if row['Page'] == x:
                        self.global_df.at[index, 'Comment'] = 'Unsupported Question Type'

    def generate_document(self, filename, qn_coord):
        print("STAGE 2 (Output Generation): PG " + str(self.qn_num) + "/" + str(self.total_qns))
        entry = {'stage': 2, 'page' : self.qn_num, 'total' : self.total_qns, 'output' : [], 'filename' : self.filename}
        with open('Sessions/' + self.requestID + ".json", 'w') as outfile:
            json.dump(entry, outfile)

        image_name = filename.replace(".jpg", "")
        ###### Step 1: Get the initial thresh and contours
        img = cv2.imread(image_name + ".jpg")
        height, width, channels = img.shape
        # if math paper, remove the vertical lines on the right side of the page
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        remove_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        if re.search(r'math', filename, re.I):
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if x / width > 0.7 or x / width < 0.1:
                    cv2.drawContours(img, [c], -1, (255, 255, 255), 20)
        else:
            # eliminate unwanted horizontal lines at paper margins due to scanning
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if x / width > 0.9 or x / width < 0.1:
                    cv2.drawContours(img, [c], -1, (255, 255, 255), 20)
        thresh, cntrs, result, morph = self.get_thresh_and_contours(img, self.filename)

        ###### Step 2: Merge contours that are close together
        # Modify the x and y tolerance to change how far it must be before it will merge!
        # Merge all contours on the same page for unsupported sections
        # if self.pg_num in self.pg_cnt_ls:
        #     x_tolerance = m.floor(0.3 * width)  # previously 300px 0.3
        #     y_tolerance = m.floor(0.1 * height)  # previously 35px 0.02
        # else:
        x_tolerance = m.floor(0.18138 * width)  # previously 300px 0.3
        y_tolerance = m.floor(0.014964 * height)  # previously 35px 0.02
        # else:
        #     x_tolerance = m.floor(0.18 * width)  # previously 300px
        #     y_tolerance = m.floor(0.009 * height)  # previously 0.014964 #SX: 0.015

        thresh, cntrs = self.merge_contours(thresh, cntrs, x_tolerance, y_tolerance)

        ###### Step 3: Draw the contours on the image
        # ordered_value_tuples contains ordered tuples of (text, y_coord)
        # document_data_list contains list of tuples of (data, type, y_coord)
        # data contains actual string if it is a text, and the image path in TempImages if it contains an image.
        # type is "text" or "image"
        # y_coord contains y coordinates of the text or image
        document_data_list = self.draw_contours(result, img, cntrs, image_name)
        # cv2.imwrite("contour_img/" + str(file_count) + ".jpg", result)

        ###### Step 4: Write and Save to a new Microsoft Word Document
        self.write_data_to_document(document_data_list, qn_coord)
        # Remove /images from image_name. example image_name is images/P6_English_2019_CA1_CHIJ/pg_1_P6_English_2019_CA1_CHIJ.jpg
        image_name = image_name.split('/', 1)[1]
        # Test paper name found in /images, example parentdir is P6_English_2019_CA1_CHIJ
        parentdir = image_name.split('/', 1)[0]

        # cv2.imshow("THRESH", thresh)
        # cv2.imshow("MORPH", morph)

        ####### Step 5: Display results
        ims = cv2.resize(result, (700, 850))
        cv2.imwrite("TempContours/" + self.requestID + "_" + str(self.pg_num) + ".jpg", ims)
        self.pg_num = self.pg_num + 1
        # cv2.imshow("RESULT", ims)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    # Copies all files from src directory to dest directory
    def copytree(self, src, dst, symlinks=False, ignore=None):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                self.copytree(s, d, symlinks, ignore)
            else:
                if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                    shutil.copy2(s, d)

    def section_chk(self, image, j, k):
        # global pg_cnt_ls
        # global pg_number
        ### file is a single page(img)
        # img = cv2.imread(image_name + ".jpg")
        height, width, channels = image.shape
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        target_word = []
        count = 1
        coord_ls = []
        for x in range(j, k):
            target_word.append('(' + str(x) + ')')
            target_word.append(str(x) + '.')
        for ele in target_word:
            word_occurences = [i for i, word in enumerate(data["text"]) if word.lower() == ele]
            for occ in word_occurences:
                # extract the width, height, top and left position for that detected word
                # w = data["width"][occ]
                # h = data["height"][occ]
                x = data["left"][occ]
                y = data["top"][occ]
                count += 1
                coord_ls.append([count, y, x])

        coord_ls.sort(key=lambda x: x[1])
        if len(coord_ls) == 0:
            pass
        else:
            avg_loc = sum(x[2] for x in coord_ls) / (len(coord_ls) * width)
            if 0.25 < avg_loc < 0.55 and 8 < self.pg_number < 20:
                self.pg_cnt_ls.append(self.pg_number)

        return self.pg_cnt_ls

    def crop_image(self, image_path, new_image_path, top, bottom, ignoreBottom, ignoreTop):
        # Opens a image in RGB mode
        image_name = image_path.replace(".jpg", "")
        im = Image.open(image_path)

        # Size of the image in pixels (size of orginal image)
        # (This is not mandatory)
        width, height = im.size

        # Setting the points for cropped image
        left = 0
        right = width

        # Cropped image of above dimension
        # (It will not change orginal image)
        im1 = None
        if ignoreBottom and ignoreTop:
            im1 = im.crop((left, 0, right, height))
        elif ignoreBottom and (not ignoreTop):
            # Giving room for the cropped images
            if top - 10 >= 0:
                top = top - 10
            else:
                top = 0
            im1 = im.crop((left, top, right, height))
        else:
            # Giving room for the cropped images
            if top - 10 >= 0:
                top = top - 10
            else:
                top = 0

            if bottom + 10 <= height:
                bottom = bottom + 1
            else:
                bottom = height
            im1 = im.crop((left, top, right, bottom))

        if new_image_path != "":
            im1.save(new_image_path,dpi=(500,500))
            if not new_image_path in self.qn_images_list:
                self.qn_images_list.append(new_image_path)
        else:
            im1.save(self.requestID + "_" + "temp.jpg",dpi=(500,500))

    def save_qn_images(self, qn_coord):
        self.total_qns = len(qn_coord) - 2
        for qn_num in range(1, len(qn_coord)):
            qn = qn_coord[qn_num]
            # For last qn
            if qn_num == len(qn_coord) - 1:
                image_path = self.filenames_list[qn[0] - 1]
                new_image_path = "TempImages/" + self.requestID + "_" + "qn_" + str(qn_num) + ".jpg"
                self.crop_image(image_path, new_image_path, qn[1], 0, True, False)
            else:
                next_qn = qn_coord[qn_num + 1]
                if qn[0] == next_qn[0]:
                    # Current qn on same page as next qn
                    image_path = self.filenames_list[qn[0] - 1]
                    new_image_path = "TempImages/" + self.requestID + "_" + "qn_" + str(qn_num) + ".jpg"
                    self.crop_image(image_path, new_image_path, qn[1], next_qn[1], False, False)
                else:
                    # Current qn on different page from next qn, means qn spans across
                    # multiple pages
                    image_path = self.filenames_list[qn[0] - 1]
                    new_image_path = "TempImages/" + self.requestID + "_" + "qn_" + str(qn_num) + ".jpg"
                    self.crop_image(image_path, new_image_path, qn[1], 0, True, False)
                    for pg_num in range(qn[0] + 1, next_qn[0] + 1):
                        if pg_num == next_qn[0]:
                            im1 = cv2.imread(new_image_path)
                            self.crop_image(self.filenames_list[pg_num - 1], "", 0, next_qn[1], False, False)
                            im2 = cv2.imread(self.requestID + "_" + "temp.jpg")
                            h1, w1, channels = im1.shape
                            h2, w2, channels1 = im2.shape
                            ### resize 2nd image if imgs are of different sizes
                            im2 = cv2.resize(im2, (w1, h2))
                            im_v = cv2.vconcat([im1, im2])
                            cv2.imwrite(new_image_path, im_v)
                        else:
                            im1 = cv2.imread(new_image_path)
                            self.crop_image(self.filenames_list[pg_num - 1], "", 0, 0, True, True)
                            im2 = cv2.imread(self.requestID + "_" + "temp.jpg")
                            h1, w1, channels = im1.shape
                            h2, w2, channels1 = im2.shape
                            ### resize 2nd image if imgs are of different sizes
                            im2 = cv2.resize(im2, (w1, h2))
                            im_v = cv2.vconcat([im1, im2])
                            cv2.imwrite(new_image_path, im_v)

    # Map the page number and y coordinates of each question
    def find_qn_coords(self, filenames_list):
        qn_coord = []
        qn_coord.append((0, 0))
        self.qn_num = 1
        self.diagram_count = 1

        for filename in filenames_list:
            print("STAGE 1 (Digitisation): PG " + str(self.pg_number - 1) + "/" + str(self.total_pages))
            entry = {'stage': 1, 'page' : str(self.pg_number - 1), 'total' : self.total_pages, 'output' : [], 'filename' : self.filename}
            with open('Sessions/' + self.requestID + ".json", 'w') as outfile:
                json.dump(entry, outfile)
            
            image_name = filename.replace(".jpg", "")
            ###### Step 1A: Read the image and check for special sections
            img = cv2.imread(image_name + ".jpg")
            height, width, channels = img.shape

            section_targ = []
            coord_ls = []
            count = 1

            target_word = []
            sorted_cntr_tuples = []
            #for section detection under 'Comments' column
            for j in range(21, 70):
                section_targ.append('(' + str(j) + ')')
                section_targ.append(str(j) + '.')

            # usually only need to catch questions past Q20, due to weird question number e.g. (29)
            for a in range(21, 101):
                target_word.append('(' + str(a) + ')')
            # same case for strangely placed qns, but they have a "." in front instead of parenthesis
            for b in range(0, 101):

                target_word.append(str(b) + '.')

            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # section check for every page
            for ele in section_targ:
                word_occurences1 = [i for i, word in enumerate(data["text"]) if word.lower() == ele]
                for occ in word_occurences1:
                    x1 = data["left"][occ]
                    y1 = data["top"][occ]
                    count += 1
                    coord_ls.append([count, y1, x1])
            coord_ls.sort(key=lambda x: x[1])
            if len(coord_ls) == 0:
                pass
            else:
                avg_loc = sum(x[2] for x in coord_ls) / (len(coord_ls) * width)
                if 0.25 < avg_loc < 0.55 and 8 < self.pg_number < 20:
                    self.pg_cnt_ls.append(self.pg_number)

            for ele in target_word:
                word_occurences = [i for i, word in enumerate(data["text"]) if word.lower() == ele]
                for occ in word_occurences:
                    if self.pg_number > 10 and y/height > 0.18: #self.pg_number > 10
                        w = data["width"][occ]
                        h = data["height"][occ]
                        x = data["left"][occ]
                        y = data["top"][occ]
                        sorted_cntr_tuples.append(("", self.pg_number, y, w, h, x))

            ###### Step 1B: Get the initial thresh and contours
            # img = cv2.imread(image_name + ".jpg")

            thresh, cntrs, result, morph = self.get_thresh_and_contours(img, filename)

            ###### Step 2: Merge contours that are close together
            # Modify the x and y tolerance to change how far it must be before it will merge!
            x_tolerance = m.floor(0.01 * width)  # previously 0.02138
            y_tolerance = m.floor(0.01 * height)  # previously 0.024964
            thresh, cntrs = self.merge_contours(thresh, cntrs, x_tolerance, y_tolerance)

            for c in cntrs:
                area = cv2.contourArea(c) / 10000
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)

                if (0.01 < area < 0.1) and y / height < 0.855 and (0 < x / width < 0.25) and (0.2 < w / h < 2):
                    if y - 5 > 0 and y + h + 5 < height and x - 5 > 0 and x + w + 5 < width:
                        new_image = img[y - 5: y + h + 5, x - 5: x + w + 5]
                    else:
                        new_image = img[y:y + h, x:x + w]

                    text = pytesseract.image_to_string(new_image, lang='eng', config='--psm 6')
                    if text != "":
                        # Check if pseudo_text contains numbers contained in any brackets
                        matches = re.search(r'[a-zA-Z]', text, re.I)
                        illegal_qn_strings = ["(", ")", "[", "]", "{", "}", "|", "NO"]
                        # Do not accept text as question if it contains any of these strings
                        contains_illegal_qn_string = any(ele in text.lower() for ele in illegal_qn_strings)
                        # Do not repeat tuples in second round of qn finding
                        probably_same_contour = False
                        for onetuple in sorted_cntr_tuples:
                            if abs(y - onetuple[2]) < 15 and self.pg_number == onetuple[1]:
                                probably_same_contour = True
                        if not contains_illegal_qn_string and not probably_same_contour and not matches:
                            sorted_cntr_tuples.append((c, self.pg_number, y, w, h, int(x / width)))

            sorted_cntr_tuples.sort(key=lambda tup: tup[2])

            # Comment this out to visualise the processing of small contours under TempImages/small_[NAME].jpg
            small_cntrs = []
            for c, self.pg_number, y, w, h, xw in sorted_cntr_tuples:
                if c is not "":
                    x, y, w, h = cv2.boundingRect(c)
                    new_image = img[y:y + h, x:x + w]
                else:
                    new_image = img[y:y + h, xw:xw + w]
                cv2.imwrite("TempImages/" + self.requestID + "_" + "small_" + str(self.diagram_count) + ".jpg", new_image)
                # Read as binary image - only if we want to test what small image was read as (DEBUGGING)
                small_image = cv2.imread("TempImages/" + self.requestID + "_" + "small_" + str(self.diagram_count) + ".jpg", 0)
                small_cntrs.append((self.pg_number, y))
                self.diagram_count = self.diagram_count + 1

            for c, self.pg_number, y, w, h, xw in sorted_cntr_tuples:
                qn_coord.append((self.pg_number, y))
            # page number will increment with every /small_ image appended to TempContours/
            cv2.imwrite("TempContours/" + self.requestID + "_" + str(self.pg_num) + ".jpg", result)


            self.pg_number = self.pg_number + 1

        return qn_coord

    def find_paper_attributes(self, paper_name):
        # global filename
        paper_name = paper_name.lower()
        paper_subject = ""
        paper_level = ""
        paper_exam_type = ""
        paper_year = ""
        paper_school = ""

        if re.search(r'english', paper_name, re.I):
            paper_subject = "english"
        elif re.search(r'math', paper_name, re.I):
            paper_subject = "math"
        elif re.search(r'science', paper_name, re.I):
            paper_subject = "science"

        if re.search(r'p[0-9]', paper_name, re.I):
            match = re.search(r'p[0-9]', paper_name, re.I)
            startpos = match.regs[0][0]
            endpos = match.regs[0][1]
            paper_level = paper_name[startpos:endpos]

        if re.search(r'ca1', paper_name, re.I):
            paper_exam_type = "ca1"
        elif re.search(r'ca2', paper_name, re.I):
            paper_exam_type = "ca2"
        elif re.search(r'sa1', paper_name, re.I):
            paper_exam_type = "sa1"
        elif re.search(r'sa2', paper_name, re.I):
            paper_exam_type = "sa2"

        if re.search(r'[0-9][0-9][0-9][0-9]', paper_name, re.I):
            match = re.search(r'[0-9][0-9][0-9][0-9]', paper_name, re.I)
            startpos = match.regs[0][0]
            endpos = match.regs[0][1]
            paper_year = paper_name[startpos:endpos]

        paper_name_split = paper_name.split("_")
        if len(paper_name_split) <= 1:
            paper_name_split = paper_name.split("-")

        illegal_paper_name_strings = [paper_subject, paper_level, paper_exam_type, paper_year]
        for i in illegal_paper_name_strings:
            if i == "":
                illegal_paper_name_strings.remove(i)

        for part in paper_name_split:
            contains_illegal_paper_name_string = any(ele in part.lower() for ele in illegal_paper_name_strings)
            if not contains_illegal_paper_name_string:
                paper_school = paper_school + part + "_"

        paper_school = paper_school[:-1]
        return paper_level, paper_subject, paper_year, paper_school, paper_exam_type

    '''def acc_matrix(self.image_count, verifier, pdfname):
        if any(verifier["Paper Name"].values == pdfname):
            num_qns = int(verifier.loc[pdfname, "Questions"])
            num_images = int(verifier.loc[pdfname, "Images"])
            qn_acc = (self.qn_num / num_qns) * 100
            img_acc = (self.image_count / num_images) * 100
            return qn_acc, img_acc
        else:
            pass'''

    def main(self, pdfname, requestID):
        global total_pages
        global global_df
        global file_attribute_list
        print(pdfname)
        
        self.requestID = requestID
        self.global_df = pd.DataFrame(
            columns=['Level', 'Page', 'Question', 'Comment', 'A', 'B', 'C', 'D', 'Subject', 'Year', 'School',
                     'Exam',
                     'Number',
                     'Image', 'Image File'])

        if not os.path.exists("TempImages"):
            os.makedirs("TempImages")

        if not os.path.exists("TempContours"):
            os.makedirs("TempContours")

        paper_name = pdfname.replace(".pdf", "")
        self.filename = paper_name
        pdf_path = "ReactPDF/" + paper_name + ".pdf"
        pages = convert_from_path(pdf_path)
        pg_cntr = 1
        self.filenames_list = []
        self.file_attribute_list = self.find_paper_attributes(paper_name)

        sub_dir = str("images/" + self.requestID + "_" + pdf_path.split('/')[-1].replace('.pdf', '') + "/")
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        if len(pages) == 1:
            paige=pages
        else:
            paige=pages
        for index, page in enumerate(paige):
            filename = "pg_" + str(pg_cntr) + '_' + pdf_path.split('/')[-1].replace('.pdf', '.jpg')
            page.save(sub_dir + filename)
            pg_cntr = pg_cntr + 1
            image_name = (sub_dir + filename).replace('.jpg', '')
            if not self.is_white_image(image_name):
                image_name = image_name + "_inverted"
            self.filenames_list.append(image_name + ".jpg")


        self.total_pages = len(self.filenames_list)
        qn_coord = self.find_qn_coords(self.filenames_list)
        # qn_coord = ast.literal_eval("[(0, 0, 0, 0), (2, 1365, 1, ''), (2, 1703, 2, ''), (3, 1131, 3, ''), (3, 1819, 4, ''), (4, 966, 5, ''), (4, 1779, 6, ''), (5, 2056, 7, ''), (6, 744, 8, ''), (6, 1934, 9, ''), (7, 757, 10, ''), (7, 1924, 11, ''), (8, 905, 12, ''), (8, 1710, 13, ''), (9, 1077, 14, ''), (9, 1914, 15, ''), (10, 1256, 16, ''), (11, 1630, 17, ''), (12, 1385, 18, ''), (13, 1432, 19, ''), (14, 1401, 20, ''), (15, 1292, 21, ''), (16, 1047, 22, ''), (17, 1295, 23, ''), (18, 1169, 24, ''), (19, 1005, 25, ''), (19, 1527, 26, ''), (20, 1535, 27, ''), (21, 1186, 28, ''), (21, 1968, 29, ''), (24, 1630, 30, 2), (26, 1591, 31, 2), (27, 1584, 32, 2), (29, 268, 33, 3), (30, 1935, 34, 2), (31, 1858, 35, 3), (32, 1035, 36, 3), (33, 1711, 37, 1), (34, 1553, 38, 1), (35, 1395, 39, 1), (36, 1739, 40, 3)]")
        self.save_qn_images(qn_coord)

        self.qn_num = 1
        for filename in self.qn_images_list:
            self.generate_document(filename, qn_coord)
            self.qn_num = self.qn_num + 1

        '''df = pd.read_csv("ReactPDF/pdfverifier.csv")
        verifier = df.set_index("Paper Name", drop=False)
        qn_acc, img_acc = acc_matrix(self.image_count, verifier, pdfname)
        print("\n" + "Accuracy of Question Numbers: " + str(qn_acc) + "%")
        if img_acc > 100:
            print("Accuracy of Images : " + str(img_acc) + "%")
            print("There could be too much noise being recognized as images, consider improving the filter" + "\n")
        else:
            print("Accuracy of Images : " + str(img_acc) + "%" + "\n")'''
        self.global_df.to_csv(self.requestID + "_output.csv")
        entry = {'stage': 3, 'page': 0, 'total': 0, 'output': [], 'filename': self.filename,
                 'level': self.file_attribute_list[0], 'subject': self.file_attribute_list[1],
                 'year': self.file_attribute_list[2], 'school': self.file_attribute_list[3],
                 'exam': self.file_attribute_list[4]}
        with open('Sessions/' + self.requestID + ".json", 'w') as outfile:
            json.dump(entry, outfile)

        # Copies all the output to a new folder under Output/PDF NAME
        dirpath = os.getcwd()
        # self.copytree(dirpath + "/TempContours", dirpath + "/Output/" + paper_name + "/TempContours")
        # self.copytree(dirpath + "/TempImages", dirpath + "/Output/" + paper_name + "/TempImages")
        # self.copytree(dirpath + "/images/" + paper_name, dirpath + "/Output/" + paper_name + "/images")
        # shutil.copyfile(dirpath + "/output.csv", dirpath + "/Output/" + paper_name + "/output.csv")

        # shutil.rmtree(dirpath + "/TempContours")
        # shutil.rmtree(dirpath + "/TempImages")
        # shutil.rmtree(dirpath + "/images/")
        items = os.listdir(dirpath + "/TempImages")
        for item in items:
            if requestID in item:
                os.remove(os.path.join(dirpath + "/TempImages", item))

        items = os.listdir(dirpath + "/TempContours")
        for item in items:
            if requestID in item:
                os.remove(os.path.join(dirpath + "/TempContours", item))
        

        if path.exists(dirpath + "/images/" + requestID + "_" + pdfname):
            shutil.rmtree(dirpath + "/images/" + requestID + "_" + pdfname)


'''for curFilename in os.listdir("ReactPDF"):
    if curFilename.endswith("P6_English_2019_CA1_CHIJ.pdf"):
        filename = curFilename
        main(curFilename)
        self.qn_num = 1
        pg_num = 1
        diagram_count = 1
        total_pages = -1
        self.image_count = 0
        self.current_section = ""
        current_ans_list = []
        found_ans_options = False'''

# process = Process()

# filename = "P6_English_2019_CA1_CHIJ_2Pages"
# process.main(filename, "2")




