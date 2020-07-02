from MainV10 import Process
import threading
import pandas as pd
import os
import re
import base64

def generate_workspace(filename, sessionID):
    process.main(filename, sessionID)
    getresult(sessionID)
    find_paper_attributes(filename)
    get_pdf_base64(filename)

def get_pdf_base64(filename):
    pdf_path = ""
    if os.path.exists("ReactPDF/" + filename + ".pdf"):
        pdf_path = "ReactPDF/" + filename + ".pdf"
    elif os.path.exists("/datassd/pdf_downloader-master/pdfs/" + filename + ".pdf"):
        pdf_path = "/datassd/pdf_downloader-master/pdfs/" + filename + ".pdf"
    elif os.path.exists("/pdfs/" + filename + ".pdf"):
        pdf_path = "/pdfs/" + filename + ".pdf"

    if os.path.exists(pdf_path):
        encoded_string = ""
        with open(pdf_path, "rb") as pdf_file:
            encoded_string = "data:application/pdf;base64," + base64.b64encode(pdf_file.read()).decode("utf-8")

        if not os.path.exists("Workspaces/pdf"):
            os.makedirs("Workspaces/pdf")
        file1 = open("Workspaces/pdf/" + filename.replace(".pdf","") + ".txt", "wb")
        file1.write(encoded_string.encode('utf-8'))

def find_paper_attributes(filename):
    # global filename
    oldFilename = filename
    filename = filename.lower()
    paper_subject = ""
    paper_level = ""
    paper_exam_type = ""
    paper_year = ""
    paper_school = ""

    if re.search(r'english', filename, re.I):
        paper_subject = "english"
    elif re.search(r'math', filename, re.I):
        paper_subject = "math"
    elif re.search(r'science', filename, re.I):
        paper_subject = "science"

    if re.search(r'p[0-9]', filename, re.I):
        match = re.search(r'p[0-9]', filename, re.I)
        startpos = match.regs[0][0]
        endpos = match.regs[0][1]
        paper_level = filename[startpos:endpos]

    if re.search(r'ca1', filename, re.I):
        paper_exam_type = "ca1"
    elif re.search(r'ca2', filename, re.I):
        paper_exam_type = "ca2"
    elif re.search(r'sa1', filename, re.I):
        paper_exam_type = "sa1"
    elif re.search(r'sa2', filename, re.I):
        paper_exam_type = "sa2"

    if re.search(r'[0-9][0-9][0-9][0-9]', filename, re.I):
        match = re.search(r'[0-9][0-9][0-9][0-9]', filename, re.I)
        startpos = match.regs[0][0]
        endpos = match.regs[0][1]
        paper_year = filename[startpos:endpos]

    filename_split = filename.split("_")
    if len(filename_split) <= 1:
        filename_split = filename.split("-")

    illegal_filename_strings = [paper_subject, paper_level, paper_exam_type, paper_year]
    for i in illegal_filename_strings:
        if i == "":
            illegal_filename_strings.remove(i)

    for part in filename_split:
        contains_illegal_filename_string = any(ele in part.lower() for ele in illegal_filename_strings)
        if not contains_illegal_filename_string:
            paper_school = paper_school + part + "_"

    paper_school = paper_school[:-1]

    if not os.path.exists("Workspaces/attribute"):
        os.makedirs("Workspaces/attribute")
    file1 = open("Workspaces/attribute/" + oldFilename.replace(".pdf","") + ".txt", "wb")
    attrStr = oldFilename.replace(".pdf","") + ";" + paper_school + ";" + paper_subject + ";" + paper_level + ";" + paper_year + ";" + paper_exam_type
    file1.write(attrStr.encode('utf-8'))

def getresult(sessionID):
    df = pd.read_csv("Output/" + sessionID + "_output.csv")
    df = df.fillna("-")

    # Create required qn or pg lists
    thisPageList = []
    row_json = []  # [[[]]]
    # Iterate over each row
    currentPageNum = 1
    for index, rows in df.iterrows():
        check = False
        # Create list for the current row
        while check is False:
            pageNum = rows["Page"]
            if pageNum == currentPageNum:
                check = True
                page = rows["Question"].replace('"', "'") if rows["Question"] != "" else "-"
                ans_a = rows["A"] if rows["A"] != "" else "-"
                ans_b = rows["B"] if rows["B"] != "" else "-"
                ans_c = rows["C"] if rows["C"] != "" else "-"
                ans_d = rows["D"] if rows["D"] != "" else "-"
                qnNum = rows["Number"]
                base64imgs = rows["Image File"]
                answer = rows["Answer"]
                question_type = rows["question_type"]
                image = rows["Image"]
                qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type, image]
                # append question list to page list
                thisPageList.append(qn_list)
            # once page changes, append previous page list to the final list
            elif pageNum > currentPageNum:
                row_json.append(thisPageList)
                currentPageNum += 1
                thisPageList = []
                pageNum = rows["Page"]
                # append that particular first qn on the new page to the now empty PageList
                if pageNum == currentPageNum:
                    check = True
                    page = rows["Question"] if rows["Question"].replace('"', "'") != "" else "-"
                    ans_a = rows["A"] if rows["A"] != "" else "-"
                    ans_b = rows["B"] if rows["B"] != "" else "-"
                    ans_c = rows["C"] if rows["C"] != "" else "-"
                    ans_d = rows["D"] if rows["D"] != "" else "-"
                    qnNum = rows["Number"]
                    base64imgs = rows["Image File"]
                    answer = rows["Answer"]
                    question_type = rows["question_type"]
                    image = rows["Image"]
                    qn_list = [pageNum, page, ans_a, ans_b, ans_c, ans_d, qnNum, base64imgs, answer, question_type,
                               image]

                    # append question list to page list
                    thisPageList.append(qn_list)

    row_json.append(thisPageList)

    row_json_str = "["
    for page in row_json:
        row_json_str = row_json_str + "["
        for question in page:
            row_json_str = row_json_str + "["
            for attribute in question:
                if isinstance(attribute, str):
                    #attribute = attribute.replace("'", '"')
                    attribute = attribute.replace('"', "\\" + '"')
                    row_json_str = row_json_str + '\"' + attribute + '\",'
                else:
                    row_json_str = row_json_str + str(attribute) + ','

            row_json_str = row_json_str[:-1] + "],"

        row_json_str = row_json_str[:-1] + "],"
    row_json_str = row_json_str[:-1] + "]"
    row_json_str = row_json_str.replace('\n', '\\n')

    if not os.path.exists("Workspaces/csv"):
        os.makedirs("Workspaces/csv")
    file1 = open("Workspaces/csv/" + sessionID + ".txt", "wb")
    file1.write(row_json_str.encode('utf-8'))

process = Process()
filename = "P6_English_2019_CA1_CHIJ_2Pages.pdf"
thread = threading.Thread(target=generate_workspace, args=(filename, filename.replace(".pdf", "")))
thread.start()