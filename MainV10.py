'''
V10: This is the main code that is used for processing the entire PDF and outputting a nested list question format
This implementation works as a class that is split into many functions, with process.main() as the call for all fns
app.py (flask end) will call MainV10 in its call for /pushfile.

Currently, the main focus here is on MCQs, with English MCQs performing the best, followed by Science, then Math.
'''
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps
from GibberishDetector import classify
import os
from pdf2image import convert_from_path
import re
import pandas as pd
import platform
import math as m
import shutil
import base64
import os.path
from os import path
import json
from autocorrect import Speller

# Tesseract-OCR pointer (only if running the back-end code on your local computer)
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"


class Process:
    def __init__(self):
        # these are the default attributes that every PDF begins with
        self.pg_number = 1
        self.pg_cnt_ls = []
        self.pg_num_1 = 2
        self.sessionID = ""
        self.diag_list = []
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
            columns=['Level', 'Page', 'Question', 'question_type', 'A', 'B', 'C', 'D', 'Answer', 'Subject', 'Year',
                     'School', 'Exam',
                     'Number', 'Image',
                     'Image File', 'Answer'])

    # if the user stops the PDF conversion halfway, we will remove all instantiated folders
    def is_session_killed(self):
        if os.path.exists('Sessions/' + self.sessionID + "_kill" + ".json"):
            # This session is killed!
            os.remove('Sessions/' + self.sessionID + "_kill" + ".json")
            if os.path.exists('Sessions/' + self.sessionID + ".json"):
                os.remove('Sessions/' + self.sessionID + ".json")

            print("Killed " + self.sessionID)
            return True
        else:
            return False

    # this fn maps each PDF page to an image in numpy array form to access its pixel values [x][y]
    def get_image(self, image_path):
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

    # this fn checks if the PDF page (image) is negative (scan issue), and converts it back to positive
    def is_white_image(self, image_name):
        # The higher the white_percentage_threshold, the more likely this fn is to detect the image as negative
        white_percentage_threshold = 0.75
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
        if white_percentage < white_percentage_threshold:
            # load image# Load image
            im = Image.open(image_name + ".jpg")

            # Invert
            result = ImageOps.invert(im)

            # Save
            result.save(image_name + "_inverted.jpg")
            return False
        else:
            return True

    # this fn pre-processes each image (now all positive), before returning their detected contours
    def get_thresh_and_contours(self, img, filename):
        # step 1: blurring
        imgBlur = cv2.GaussianBlur(img, (7, 7), 1)

        # step 2: converting blurred img to grayscale
        gray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)

        # step 3: threshold the grayscale image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        result = img.copy()

        # step 4: apply morph_dilate on the image to enhance and close gaps in broken contour lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)

        # step 5: apply the morph_open on the image to remove unnecessary noise in the image (random small lines, etc.)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 30))
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)

        # step 6: with the pre-processed image, find and return its relevant contours and threshold
        cntrs = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]
        return thresh, cntrs, result, morph

    # this fn takes the pre-processed image, and merges the close contours together (for text/diagram analysis)
    def merge_contours(self, thresh, cntrs, x_tolerance, y_tolerance):
        # area_threshold is the smallest area allowed for the contour before it is removed
        area_threshold = 100

        for c in cntrs:
            area = cv2.contourArea(c)
            # fill very small contours with zero (erase small contours).
            if area < area_threshold:
                cv2.fillPoly(thresh, pts=[c], color=0)
                continue

        # use "close" morphological operation to close the gaps between contours
        # https://stackoverflow.com/questions/18339988/implementing-imcloseim-se-in-opencv
        try:
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
                                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (x_tolerance, y_tolerance)))
        except:
            # likely nothing to merge, so there is an error
            pass
        finally:
            # find contours in thresh_gray after closing the gaps, and return these new contours
            cntrs, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            return thresh, cntrs

    # this fn takes in the new contours (merged and not merged), and draws these contours
    def draw_contours(self, result, img, cntrs, image_name):
        document_data_list = []  # will contain list of tuples of (data, type, y_coord)
        height, width, channels = img.shape
        result_1 = img.copy()

        # image pre-processing for blank line detection (e.g. fill in the blank in "John, ____ helps his mother")
        gray_1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 1: grayscale
        thresh_1 = cv2.threshold(gray_1, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]  # 2: threshold
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))  # 3: kernel
        detected_lines = cv2.morphologyEx(thresh_1, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)  # 4: morph_open
        cnts_line = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 5: find lines
        cnts_line = cnts_line[0] if len(cnts_line) == 2 else cnts_line[1]  # 6: rm duplicates
        # draw out contours over important blank lines, then add text over these lines on the image
        for c in cnts_line:
            x1, y1, w1, h1 = cv2.boundingRect(c)
            # if the horizontal line is in this given length, we will identify it as essential to the text
            if 0.05 < w1 / width < 0.2:
                cv2.rectangle(result, (x1, y1), (x1 + w1, y1 + h1), (255, 0, 0), 2)
                # word of choice over line is EMPTY, since even if conversion to line fails, user can guess its meaning
                texted = cv2.putText(result_1, '(EMPTY)____', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (0, 0, 0), 2, cv2.LINE_AA)  # places '(EMPTY)____' over lines on the image
                texted = cv2.dilate(texted, np.ones((2, 2), np.uint8), iterations=1)  # accentuates contours in image
        # additional pre-processing for essential filters
        for c in cntrs:
            area = cv2.contourArea(c) / 10000
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
            if "texted" in locals():
                grayish = cv2.cvtColor(texted, cv2.COLOR_BGR2GRAY)
            else:
                grayish = cv2.cvtColor(result_1, cv2.COLOR_BGR2GRAY)
            thresh = 255 - cv2.threshold(grayish, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            # cropping out image and convert to text
            if y - 10 > 0 and y + h + 10 < height and x - 20 > 0 and x + w + 20 < width:
                ROI = thresh[y - 10: y + h + 10, x - 20: x + w + 20]
            else:
                ROI = thresh[y:y + h, x:x + w]
            text = pytesseract.image_to_string(ROI, lang='eng', config='--psm 6')
            # for lines identified as essential horizontal lines, generate the blank line as text from the image
            text = re.sub(r"\(EMPTY[\)]*|\(FMPTY[\)]*|\(eEmpTy[\)]*|\(Fupty[\)]*|\(Fuprty[\)]", "_________", text,
                          flags=re.I)
            # removing watermark that gets appended into questions
            text = re.sub("www.testpapersfree.com|http://www. testpapersfree.com", "", text, flags=re.I)
            # removing section headers from papers
            text = re.sub(r"^(Questions).+(Show your).+((provided)|(stated))?\.?$", "", text, flags=re.I)
            pseudo_text = text

            # side-processing the cropped image to remove unnecessary lines
            if w / width > 0.05 and y / height < 0.95:
                new_image = img[y:y + h, x:x + w]
                dst = cv2.Canny(new_image, 50, 200, None, 3)
                # remove the horizontal separators in math papers (Mostly section B)
                if re.search('math', self.filename, re.I):
                    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
                    enhanced_dst = cv2.dilate(dst, horizontal_kernel, None, None, iterations=1)
                    remove_dst_horizontal = cv2.morphologyEx(enhanced_dst, cv2.MORPH_OPEN, horizontal_kernel,
                                                             iterations=1)
                    cnts_dst = cv2.findContours(remove_dst_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cnts_dst = cnts_dst[0] if len(cnts_dst) == 2 else cnts_dst[1]
                    for c in cnts_dst:
                        height, width, channels = img.shape
                        x, y, w, h = cv2.boundingRect(c)
                        if w / width > 0.4 and 0.2 < y / height < 0.8:
                            cv2.drawContours(dst, [c], -1, (0, 0, 0), 20)

                # detect probabilistic hough-lines
                linesp = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 2)
                # these filters (mainly is_gibberish and hough line detection) will seperate text from diagrams
                if self.is_gibberish(text) or 0.35 < (w * h) / (width * height) < 0.97 or linesp is not None:
                    if h / height > 0.1 and w / h < 5:
                        # Likely to be an image
                        new_image = img[y:y + h, x:x + w]
                        cv2.imwrite("TempImages/" + self.sessionID + "_" + str(self.diagram_count) + ".jpg", new_image)
                        # store in base64 as well into document_data_list
                        with open("TempImages/" + self.sessionID + "_" + str(self.diagram_count) + ".jpg",
                                  "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        document_data_list.append(
                            ("TempImages/" + self.sessionID + "_" + str(self.diagram_count) + ".jpg", "image", y,
                             pseudo_text, encoded_string, "", ""))
                        self.diagram_count = self.diagram_count + 1
                        self.diag_list.append([(y, y + h), (x, x + w)])
                    else:
                        # Likely to be text, just small regions like "Go on to the next page"
                        document_data_list.append((text, "text", y, pseudo_text, "", y + h / 2, x + w / 2))
                else:
                    # Likely to be a text
                    document_data_list.append((text, "text", y, pseudo_text, "", y + h / 2, x + w / 2))
        return document_data_list

    # this is a helper fn that checks if the given detected line is gibberish or not
    def is_gibberish(self, text):
        # the higher threshold_percentage is, the higher the tolerance for nonsense in the text
        threshold_percentage = 45  # if too high, some diagrams without hough lines may be detected as text
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
        if average_percentage > threshold_percentage:
            # likely to be gibberish
            return True
        else:
            return False

    # this fn captures the coords of where each qn starts
    def find_qn_coords(self, filenames_list):
        qn_coord = []  # each element in the list will be in the format (self.pg_number, y)
        qn_coord.append((0, 0))
        self.qn_num = 1
        self.diagram_count = 1
        # the tolerance values are how close 2 cntrs must be for merger into a single qn contour
        x_tolerance_threshold = 0.01  # 0.02138 in a previous version, but turned out to be too large
        y_tolerance_threshold = 0.01  # previously 0.024964

        for filename in filenames_list:
            if self.is_session_killed():
                return True
            print("STAGE 2 (Digitisation): PG " + str(self.pg_number) + "/" + str(self.total_pages) +
                  ", Filename: " + self.filename + ", SessionID: " + self.sessionID)

            entry = {'stage': 2, 'page': str(self.pg_number), 'total': self.total_pages, 'output': [],
                     'filename': self.filename, 'level': self.file_attribute_list[0],
                     'subject': self.file_attribute_list[1],
                     'year': self.file_attribute_list[2], 'school': self.file_attribute_list[3],
                     'exam': self.file_attribute_list[4]}

            with open('Sessions/' + self.sessionID + ".json", 'w') as outfile:
                json.dump(entry, outfile)

            image_name = filename.replace(".jpg", "")

            # step 1A: read the image and check for special sections
            img = cv2.imread(image_name + ".jpg")
            height, width, channels = img.shape

            section_targ = []
            coord_ls = []
            count = 1

            target_word = []
            sorted_cntr_tuples = []

            # for section detection under 'Comments' column
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

            # section check for every page; specific to eng papers(works by identifying pages of 'unsupported' qn type), comment out for other subjects
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
                    if self.pg_number > 10 and y / height > 0.18:  # self.pg_number > 10
                        w = data["width"][occ]
                        h = data["height"][occ]
                        x = data["left"][occ]
                        y = data["top"][occ]
                        sorted_cntr_tuples.append(("", self.pg_number, y, w, h, x))

            # step 1B: get the initial thresh and contours
            thresh, cntrs, result, morph = self.get_thresh_and_contours(img, filename)

            # step 2: merge contours that are close together
            # Modify the x and y tolerance to change how far it must be before it will merge!
            x_tolerance = m.floor(x_tolerance_threshold * width)
            y_tolerance = m.floor(y_tolerance_threshold * height)
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

            # Writes small contours found into TempImages in format "TempImages/small_[NAME].jpg"
            small_cntrs = []
            for c, self.pg_number, y, w, h, xw in sorted_cntr_tuples:
                if c is not "":
                    x, y, w, h = cv2.boundingRect(c)
                    new_image = img[y:y + h, x:x + w]
                else:
                    new_image = img[y:y + h, xw:xw + w]
                cv2.imwrite("TempImages/" + self.sessionID + "_" + "small_" + str(self.diagram_count) + ".jpg",
                            new_image)
                small_image = cv2.imread(
                    "TempImages/" + self.sessionID + "_" + "small_" + str(self.diagram_count) + ".jpg", 0)
                small_cntrs.append((self.pg_number, y))
                self.diagram_count = self.diagram_count + 1

            for c, self.pg_number, y, w, h, xw in sorted_cntr_tuples:
                qn_coord.append((self.pg_number, y))

            cv2.imwrite("TempContours/" + self.sessionID + "_" + str(self.pg_num) + ".jpg", result)
            # at the end of one page (file in filenames_list), increment the global pg_number count
            self.pg_number = self.pg_number + 1

        return qn_coord

    # this fn gathers the important file attributes from the other fns, sorting them into relevant information
    def write_data_to_document(self, document_data_list, qn_coord):
        # qn_coord is a tuple consisting of nested (pg_number, y) tuples of each contour
        # Sort document_data_list according to element y-coordinates
        document_data_list.sort(key=lambda tup: tup[2])
        current_ans_list = []
        found_ans_options = False
        first_ans_pos = -1
        spell = Speller()

        # file_attribute_list -> [paper_level, paper_subject, paper_year, paper_school, paper_exam_type]
        paper_level = self.file_attribute_list[0].upper()
        paper_subject = self.file_attribute_list[1].upper()
        paper_year = self.file_attribute_list[2]
        paper_school = self.file_attribute_list[3]
        paper_exam_type = self.file_attribute_list[4].upper()

        # additional output required from this fn
        final_text = ""
        final_image = ""
        ans_a = "-"
        ans_b = "-"
        ans_c = "-"
        ans_d = "-"
        answer = "-"  # answer will stay as "-" for user to alter

        for i in range(len(document_data_list)):
            data = document_data_list[i]
            item = spell(data[0])  # TempImages/5.jpg
            typeof = data[1]
            y_coord = data[2]
            # ensure that only data of 'text' type is inserted into text columns
            if typeof == 'text' and not any(data[5] in range(j[0][0], j[0][1]) for j in self.diag_list) and not any(
                    data[6] in range(j[1][0], j[1][1]) for j in self.diag_list):
                pseudo_text = spell(data[3])
            else:
                pseudo_text = ''
            base64img = data[4]
            self.diag_list.clear()

            # step 1: find qn options
            # use regex to identify key characteristics of a qn option; captures any characters(0-3 length) except s between any type of bracket,eg (1),{A},[3]
            # subsequent lines will identify postions of regex matches and segment options
            regex = re.compile('[\[\(\|\{][^s]{0,3}[\]\)\}\|]')  # |.{1,3}[\]\)\}\|]
            matches = regex.finditer(pseudo_text)
            match_list = []
            # send matching text (identified as option) to match_list
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

            # sort out the options correctly based on current_ans_list
            # regex sub to remove qn options eg.(A)/{b} by specifying any characters(1<length<3) bet brackets, and stripping whitespace
            ans_a = "-" if len(current_ans_list) <= 0 else current_ans_list[0]
            ans_a = re.sub('[\[\(\|\{].{1,3}[\]\)\}\|]', '', ans_a, 1).strip()
            ans_b = "-" if len(current_ans_list) <= 1 else current_ans_list[1]
            ans_b = re.sub('[\[\(\|\{].{1,3}[\]\)\}\|]', '', ans_b, 1).strip()
            ans_c = "-" if len(current_ans_list) <= 2 else current_ans_list[2]
            ans_c = re.sub('[\[\(\|\{].{1,3}[\]\)\}\|]', '', ans_c, 1).strip()
            ans_d = "-" if len(current_ans_list) <= 3 else current_ans_list[3]
            ans_d = re.sub('[\[\(\|\{].{1,3}[\]\)\}\|]', '', ans_d, 1).strip()
            answer = "-"

            # step 2: sorts out question header and images to be sent to final DataFrame
            if typeof == "text" and item != "":
                if first_ans_pos == -1:
                    # qn header not correctly identified yet
                    final_text = final_text + item
                    # for non-math papers, remove trailing qn number from the header, e.g. "1. John..." -> "John..."
                    if not re.search(r'math', self.filename, re.I):
                        final_text = re.sub(r'[0-9][0-9]\.|[0-9]\.|[0-9][0-9]|[0-9]', '', final_text, 1).strip()
                    else:
                        final_text = re.sub(r'^[0-9][0-9]\.|^[0-9]\.|^[0-9][0-9]|^[0-9]', '', final_text, 1).strip()
                else:
                    # qn header correctly identified
                    final_text = final_text + item[:first_ans_pos]
                    # same operation to remove trailing qn number
                    if not re.search(r'math', self.filename, re.I):
                        final_text = re.sub(r'[0-9][0-9]\.|[0-9]\.|[0-9][0-9]|[0-9]', '', final_text, 1).strip()
                    else:
                        final_text = re.sub(r'^[0-9][0-9]\.|^[0-9]\.|^[0-9][0-9]|^[0-9]', '', final_text, 1).strip()

            elif typeof == "image":
                # concatenate string of base64img associated with that one qn (adds image to qn)
                final_image = final_image + base64img + " "

        contains_image = "No"
        if final_image != "":
            contains_image = "Yes"
        if final_text == "":
            final_text = "-"
        if final_image == "":
            final_image = "-"

        # step 3: send all essential, processed information for that question to the DataFrame -> one row in df
        self.global_df.loc[self.qn_num] = [paper_level, qn_coord[self.qn_num][0], final_text, "-", ans_a, ans_b, ans_c,
                                           ans_d,
                                           answer, paper_subject,
                                           paper_year, paper_school, paper_exam_type, self.qn_num, contains_image,
                                           final_image]

        # insert question type under comments column based on pg_cnt_ls list (all questions will be labelled 'MCQ' as default at the moment as logic only works for english papers with 'unsupported' qn type)
        for index, row in self.global_df.iterrows():
            if len(self.pg_cnt_ls) == 0:
                self.global_df.at[index, 'question_type'] = 'MCQ'
            else:
                if row['Page'] < min(self.pg_cnt_ls):
                    self.global_df.at[index, 'question_type'] = 'MCQ'
                elif row['Page'] > max(self.pg_cnt_ls):
                    self.global_df.at[index, 'question_type'] = 'Structured Qn'
                for x in self.pg_cnt_ls:
                    if row['Page'] == x:
                        self.global_df.at[index, 'question_type'] = 'Unsupported Question Type'

    # this function will remove horizontal lines at paper margins and call other fns(get_thresh_and_contours(),merge_contours(), draw_contours()) involving contours and also write_data_to_document() to finally create a dataframe
    def generate_document(self, filename, qn_coord):
        # the higher these two thresholds, the further the max distance before two contours will merge
        x_tolerance_threshold = 0.18138  # previously 0.18
        y_tolerance_threshold = 0.014964  # previously 0.009
        if self.is_session_killed():
            return True

        print("STAGE 3 (Output Generation): QN " + str(self.qn_num - 1) + "/" + str(self.total_qns) +
              ", Filename: " + self.filename + ", SessionID: " + self.sessionID)
        entry = {'stage': 3, 'page': self.qn_num - 1, 'total': self.total_qns, 'output': [],
                 'filename': self.filename, 'level': self.file_attribute_list[0],
                 'subject': self.file_attribute_list[1],
                 'year': self.file_attribute_list[2], 'school': self.file_attribute_list[3],
                 'exam': self.file_attribute_list[4]}

        with open('Sessions/' + self.sessionID + ".json", 'w') as outfile:
            json.dump(entry, outfile)

        image_name = filename.replace(".jpg", "")
        # step 1: get the initial thresh and contours
        img = cv2.imread(image_name + ".jpg")
        height, width, channels = img.shape
        # Some image preprocessing steps before drawContours()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        remove_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        # remove vertical lines on extreme left and right margins of pages that are prominent in math papers
        if re.search(r'math', filename, re.I):
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                # target lines at the extreme left and right margins
                if x / width > 0.7 or x / width < 0.1:
                    # fn that draws white line covering unwanted black lines on paper
                    cv2.drawContours(img, [c], -1, (255, 255, 255), 20)  # 20 is the thickness
        else:
            # eliminate unwanted horizontal lines at paper margins due to scanning (for all other papers)
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if x / width > 0.9 or x / width < 0.1:
                    # fn that draws white line covering unwanted black lines on paper
                    cv2.drawContours(img, [c], -1, (255, 255, 255), 20)
        thresh, cntrs, result, morph = self.get_thresh_and_contours(img, self.filename)

        # step 2: merge contours that are close together
        # Modify the x and y tolerance to change how far it must be before it will merge!
        x_tolerance = m.floor(x_tolerance_threshold * width)
        y_tolerance = m.floor(y_tolerance_threshold * height)

        # call merge_contours() that merges cntrs in close proximity
        thresh, cntrs = self.merge_contours(thresh, cntrs, x_tolerance, y_tolerance)

        # step 3: draw the contours on the image
        '''
        Overview:
        1. ordered_value_tuples contains ordered tuples of (text, y_coord)
        2. document_data_list contains list of tuples of (data, type, y_coord)
        3. data contains actual string if it is a text, and the image path in TempImages if it contains an image.
        4. type is "text" or "image"
        5. elements in document_data_list are tuples of (text, "text", y, pseudo_text, "", y+h/2, x+w/2)
        '''
        document_data_list = self.draw_contours(result, img, cntrs, image_name)

        # step 4: call write_data_to_document fn to create the dataframe
        self.write_data_to_document(document_data_list, qn_coord)
        # Remove /images from image_name. example image_name is images/P6_English_2019_CA1_CHIJ/pg_1_P6_English_2019_CA1_CHIJ.jpg
        image_name = image_name.split('/', 1)[1]
        # Test paper name found in /images, example parentdir is P6_English_2019_CA1_CHIJ
        parentdir = image_name.split('/', 1)[0]

        # uncomment out following 2 lines to display results
        # ims = cv2.resize(result, (700, 850))
        # cv2.imshow('result',ims)

        cv2.imwrite("TempContours/" + self.sessionID + "_" + str(self.pg_num) + ".jpg", ims)
        self.pg_num = self.pg_num + 1
        return False

    # this fn copies all files from the src directory to destination directory
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

    # this fn will take in each page as an image, then identify its paper section (eng support)
    # this fn is currently unused since it is integrated in find_qn_coords()
    def section_chk(self, image, j, k):
        # file here refers to a single page (img)
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

    # this fn is called by save_qn_images(); imgs are cropped to individual qns based on y-coords found in qn_coord,
    # file path of each image is appended to qn_images_list
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
            # save img,change dpi parameters to alter resolution of images
            im1.save(new_image_path, dpi=(500, 500))
            if not new_image_path in self.qn_images_list:
                # image of each qn is appended to list
                self.qn_images_list.append(new_image_path)
        else:
            # save img,change dpi parameters to alter resolution of images
            im1.save("TempImages/" + self.sessionID + "_" + "temp.jpg", dpi=(500, 500))

    # this fn takes in qn_coord and calls crop_image function, saving qn numbers captured under /TempImages
    def save_qn_images(self, qn_coord):
        self.total_qns = len(qn_coord) - 2
        for qn_num in range(1, len(qn_coord)):
            qn = qn_coord[qn_num]
            # For last qn
            if qn_num == len(qn_coord) - 1:
                image_path = self.filenames_list[qn[0] - 1]
                new_image_path = "TempImages/" + self.sessionID + "_" + "qn_" + str(qn_num) + ".jpg"
                # img cropped from q[1] to bottom of pg(since it's the last qn)
                self.crop_image(image_path, new_image_path, qn[1], 0, True, False)
            else:
                next_qn = qn_coord[qn_num + 1]
                if qn[0] == next_qn[0]:
                    # Current qn on same page as next qn
                    image_path = self.filenames_list[qn[0] - 1]
                    new_image_path = "TempImages/" + self.sessionID + "_" + "qn_" + str(qn_num) + ".jpg"
                    # img cropped from current qn[1] to next y-coord in the list, not ignoretop/bottom
                    self.crop_image(image_path, new_image_path, qn[1], next_qn[1], False, False)
                else:
                    # Current qn on different page from next qn, means qn spans across multiple pages
                    image_path = self.filenames_list[qn[0] - 1]
                    new_image_path = "TempImages/" + self.sessionID + "_" + "qn_" + str(qn_num) + ".jpg"
                    self.crop_image(image_path, new_image_path, qn[1], 0, True, False)
                    for pg_num in range(qn[0] + 1, next_qn[0] + 1):
                        if pg_num == next_qn[0]:
                            im1 = cv2.imread(new_image_path)
                            self.crop_image(self.filenames_list[pg_num - 1], "", 0, next_qn[1], False, False)
                            im2 = cv2.imread("TempImages/" + self.sessionID + "_" + "temp.jpg")
                            h1, w1, channels = im1.shape
                            h2, w2, channels1 = im2.shape
                            # resize 2nd image if imgs are of different sizes
                            im2 = cv2.resize(im2, (w1, h2))
                            # vconcat fn appends the 2 imgs together(across multiple pages)
                            im_v = cv2.vconcat([im1, im2])
                            cv2.imwrite(new_image_path, im_v)
                        else:
                            im1 = cv2.imread(new_image_path)
                            self.crop_image(self.filenames_list[pg_num - 1], "", 0, 0, True, True)
                            im2 = cv2.imread("TempImages/" + self.sessionID + "_" + "temp.jpg")
                            h1, w1, channels = im1.shape
                            h2, w2, channels1 = im2.shape
                            # resize 2nd image if imgs are of different sizes
                            im2 = cv2.resize(im2, (w1, h2))
                            # vconcat fn appends the 2 imgs together(across multiple pages)
                            im_v = cv2.vconcat([im1, im2])
                            cv2.imwrite(new_image_path, im_v)

    # this fn identifies the important details of the paper
    def find_paper_attributes(self, paper_name):
        paper_name = paper_name.lower()
        paper_subject = ""
        paper_level = ""
        paper_exam_type = ""
        paper_year = ""
        paper_school = ""

        # identify the paper subject
        if re.search(r'english', paper_name, re.I):
            paper_subject = "english"
        elif re.search(r'math', paper_name, re.I):
            paper_subject = "math"
        elif re.search(r'science', paper_name, re.I):
            paper_subject = "science"

        # identify the paper level (e.g. Primary 6)
        if re.search(r'p[0-9]', paper_name, re.I):
            match = re.search(r'p[0-9]', paper_name, re.I)
            startpos = match.regs[0][0]
            endpos = match.regs[0][1]
            paper_level = paper_name[startpos:endpos]

        # identify the exam
        if re.search(r'ca1', paper_name, re.I):
            paper_exam_type = "ca1"
        elif re.search(r'ca2', paper_name, re.I):
            paper_exam_type = "ca2"
        elif re.search(r'sa1', paper_name, re.I):
            paper_exam_type = "sa1"
        elif re.search(r'sa2', paper_name, re.I):
            paper_exam_type = "sa2"

        # identify the paper year
        if re.search(r'[0-9][0-9][0-9][0-9]', paper_name, re.I):
            match = re.search(r'[0-9][0-9][0-9][0-9]', paper_name, re.I)
            startpos = match.regs[0][0]
            endpos = match.regs[0][1]
            paper_year = paper_name[startpos:endpos]

        # split papers with name in the following format: e.g. "CHIJ_KATONG_MATH_P6_SA2.pdf"
        paper_name_split = paper_name.split("_")
        if len(paper_name_split) <= 1:
            # paper name is probably like this: e.g. "CHIJ-KATONG-MATH-P6-SA2.pdf"
            paper_name_split = paper_name.split("-")

        # mark all other attributes except paper school as illegal, unless the attribute was not found
        illegal_paper_name_strings = [paper_subject, paper_level, paper_exam_type, paper_year]
        for i in illegal_paper_name_strings:
            if i == "":
                illegal_paper_name_strings.remove(i)

        # identify paper school (by removing all other attributes from the paper name)
        for part in paper_name_split:
            contains_illegal_paper_name_string = any(ele in part.lower() for ele in illegal_paper_name_strings)
            if not contains_illegal_paper_name_string:
                paper_school = paper_school + part + "_"

        paper_school = paper_school[:-1]
        return paper_level, paper_subject, paper_year, paper_school, paper_exam_type

    # this is the main function that will be called from app.py, which calls all the other essential fns
    def main(self, pdfname, sessionID):
        global total_pages
        global global_df
        global file_attribute_list
        print(pdfname)

        self.sessionID = sessionID

        # dataframe with specified columns are created
        self.global_df = pd.DataFrame(
            columns=['Level', 'Page', 'Question', 'question_type', 'A', 'B', 'C', 'D', 'Answer', 'Subject', 'Year',
                     'School',
                     'Exam',
                     'Number',
                     'Image', 'Image File'])

        if not os.path.exists("Sessions"):
            os.makedirs("Sessions")

        if not os.path.exists("Output"):
            os.makedirs("Output")

        if not os.path.exists("TempImages"):
            os.makedirs("TempImages")

        if not os.path.exists("TempContours"):
            os.makedirs("TempContours")

        paper_name = pdfname.replace(".pdf", "")
        self.filename = paper_name

        pdf_path = ""
        if os.path.exists("ReactPDF/" + paper_name + ".pdf"):
            pdf_path = "ReactPDF/" + paper_name + ".pdf"
        elif os.path.exists("/datassd/pdf_downloader-master/pdfs/" + paper_name + ".pdf"):
            pdf_path = "/datassd/pdf_downloader-master/pdfs/" + paper_name + ".pdf"
        elif os.path.exists("/pdfs/" + paper_name + ".pdf"):
            pdf_path = "/pdfs/" + paper_name + ".pdf"

        # pdf is converted to images
        pages = convert_from_path(pdf_path)
        pg_cntr = 1
        self.filenames_list = []
        # attributes of exam paper are extracted from the file name
        self.file_attribute_list = self.find_paper_attributes(paper_name)

        sub_dir = str("images/" + self.sessionID + "_" + pdf_path.split('/')[-1].replace('.pdf', '') + "/")
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        # iterate through every page
        for index, page in enumerate(pages):
            if self.is_session_killed():
                return True

            print("STAGE 1 (Converting to images): PG " + str(index + 1) + "/" + str(len(paige)) +
                  ", Filename: " + self.filename + ", SessionID: " + self.sessionID)

            entry = {'stage': 1, 'page': str(index + 1), 'total': str(len(paige)), 'output': [],
                     'filename': self.filename, 'level': self.file_attribute_list[0],
                     'subject': self.file_attribute_list[1],
                     'year': self.file_attribute_list[2], 'school': self.file_attribute_list[3],
                     'exam': self.file_attribute_list[4]}

            with open('Sessions/' + self.sessionID + ".json", 'w') as outfile:
                json.dump(entry, outfile)

            filename = "pg_" + str(pg_cntr) + '_' + pdf_path.split('/')[-1].replace('.pdf', '.jpg')
            page.save(sub_dir + filename)
            pg_cntr = pg_cntr + 1
            image_name = (sub_dir + filename).replace('.jpg', '')
            # convert negative images
            if not self.is_white_image(image_name):
                image_name = image_name + "_inverted"
            self.filenames_list.append(image_name + ".jpg")

        self.total_pages = len(self.filenames_list)
        # call find_qn_coords fn to extract y coordinates of question numbers on pgs, returning qn_coord
        qn_coord = self.find_qn_coords(self.filenames_list)

        if qn_coord == True:
            # Session is killed
            return
        # qn_coord = ast.literal_eval("[(0, 0, 0, 0), (2, 1365, 1, ''),  (2, 1703, 2, ''), (3, 1131, 3, ''), (3, 1819, 4, ''), (4, 966, 5, ''), (4, 1779, 6, ''), (5, 2056, 7, ''), (6, 744, 8, ''), (6, 1934, 9, ''), (7, 757, 10, ''), (7, 1924, 11, ''), (8, 905, 12, ''), (8, 1710, 13, ''), (9, 1077, 14, ''), (9, 1914, 15, ''), (10, 1256, 16, ''), (11, 1630, 17, ''), (12, 1385, 18, ''), (13, 1432, 19, ''), (14, 1401, 20, ''), (15, 1292, 21, ''), (16, 1047, 22, ''), (17, 1295, 23, ''), (18, 1169, 24, ''), (19, 1005, 25, ''), (19, 1527, 26, ''), (20, 1535, 27, ''), (21, 1186, 28, ''), (21, 1968, 29, ''), (24, 1630, 30, 2), (26, 1591, 31, 2), (27, 1584, 32, 2), (29, 268, 33, 3), (30, 1935, 34, 2), (31, 1858, 35, 3), (32, 1035, 36, 3), (33, 1711, 37, 1), (34, 1553, 38, 1), (35, 1395, 39, 1), (36, 1739, 40, 3)]")

        # pass qn_coord list into save_qn_images fn, cropping and saving images containing individual questions
        self.save_qn_images(qn_coord)

        self.qn_num = 1

        # iterate through every img (containing each qn) in list, calling generate_document()
        for filename in self.qn_images_list:
            isKilled = self.generate_document(filename, qn_coord)
            if isKilled == True:
                # Session is killed
                return
            self.qn_num = self.qn_num + 1

        self.global_df.to_csv("Output/" + self.sessionID + "_output.csv")
        entry = {'stage': 4, 'page': 0, 'total': 0, 'output': [], 'filename': self.filename,
                 'level': self.file_attribute_list[0], 'subject': self.file_attribute_list[1],
                 'year': self.file_attribute_list[2], 'school': self.file_attribute_list[3],
                 'exam': self.file_attribute_list[4]}
        with open('Sessions/' + self.sessionID + ".json", 'w') as outfile:
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

        # comment out next 3 blocks to retain imgs and screenshots
        items = os.listdir(dirpath + "/TempImages")
        for item in items:
            if sessionID in item:
                os.remove(os.path.join(dirpath + "/TempImages", item))

        items = os.listdir(dirpath + "/TempContours")
        for item in items:
            if sessionID in item:
                os.remove(os.path.join(dirpath + "/TempContours", item))

        if path.exists(dirpath + "/images/" + sessionID + "_" + pdfname):
            shutil.rmtree(dirpath + "/images/" + sessionID + "_" + pdfname)

# uncomment these last 3 lines to run MainV10.py to process a single pdf

# process = Process()
# filename = "P6-Maths-SA2-2017-Red-Swastika-2pgs"
# process.main(filename, "redswast2017")