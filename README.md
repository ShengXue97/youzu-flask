## Overview
This repository hosts the back-end framework for the React web-page, as part of the Digitization Project. The back-end 
is built with [flask](https://palletsprojects.com/p/flask/ "flask Home Page"), a lightweight Web Server Gateway 
Interface web application framework optimized for the Python Language.

## Digitisation Pipeline
![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/Pipeline%20and%20Prototype.jpg 'Illustration of Pipeline')
1. **PDF to Image** 
Uploaded pdf will be converted to images, and the attributes of the exam paper will be extracted. Negative-scale images will be converted to white if they fall below a certain threshold.
2. **Question Detection**
Using Tesseract-OCR and our algorithm, small images of question numbers and their y-coordinates on each page of the paper will be extracted. 
3. **Image Cropping**
Based on the y-coordinates of the question numbers extracted from the previours step, each page of the paper will be cropped to fit only the contents of a single question. They will be subsequently saved under the /TempImages folder.
4. **Image Pre-processing**
Several image-preprocessing techniques available in the OpenCV computer vision library will be utilised to improve the quality before being passed to the OCR. Below techniques are also used to remove unwanted long lines along margins present in some pages of papers.

*Examples of techniques used (not exhaustive):*
    * Gaussian Blurring
    * Grayscaling
    * Morphological operations like erosion, dilation, opening, closing etc
5. **Contour Detection**
After image is cleaned and denoised, cv2.findContours() function is used to obtains countours wrapping blocks of text on the image. Contours extremely close in proximity will then be merged, while very small contours will be erased. These contours will be passed into our defined draw_contours() function, which will use the cv2.boundingRect() function to outline (rectangular in shape) blocks of text/diagrams. Blank lines in the question will be detected, and a '_______' text will be inserted in the corresponding position in the processed text thereafter. Based on the x,y,w,h coordinates of the blocks obtained from cv2.boundingRect() function, the region will be cropped out and subsequently passed into the OCR to be converted to text strings. 
Illustration of bounding box:![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/contour.jpg)
6. **Diagram/Text Classification**
Using Gibberish Detector module, Hough Lines and aspect ratio of the contours, the cropped region will be deemed to be readable text or diagram. For text that passes the filters, it will be appended to a list. Otherwise, digrams will be saved under the /TempImages folder and the base64 string will be appended to the same list.
7. **Diagram/Text Segmentation**
Diagrams under /TempImages folder:![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/tempimages.PNG)
Base64 strings of diagrams sorted under the /TempImages folder will be accessed and appended to the corresponding questions while text will be segmented into the question title and options using regular expressions. 
8. **Create Pandas Dataframe**
All essential and processed content will be inserted into a pandas dataframe, with each question taking up one row. The output will be saved as a csv file, and user can modify MainV10.py script to retain the csv file for inspection. The information and processed content will then be pushed to the front end for user edit and viewing.



## Breakdown
This repository holds many folders that contain highly important data, and are the backbone of many of the functions 
observed in the React UI. Arguably, the most important directory/modules are:

#### ./Workspaces
This directory contains the data of all previously processed PDFs for that particular server (contents differ for 
production and development builds). In short, it is responsible for the user being able to save his workspace or return 
to its most recent edit to download the .csv version of the output and even upload questions to the DataBase.

Without this folder and its essential sub-folders (./attribute, ./csv and ./pdf), there would be no saved output and 
users would have to do all the work in that one session.

#### `app.py`
This module is responsible for connecting all back-end logic to the front-end UI, and vice-versa. It is the middle-man 
be it in re-directing the user to another page, or in receiving the POST request upon the user's PDF upload, before 
sending it to `MainV10.py` for effective processing and sending it back to the front-end web-page.

Some important helper modules that are used are:
* `GibberishDetector.py` *(Detects whether contour boxes found are gibberish or actual text, and is part of diagram-text 
segmentation/analysis)*
* `WorkspaceGenerator.py` *(Helper function that holds the logic for generating a saved workspace in the ./Workspaces 
directory)*

#### `MainV10.py`
This module is the backbone of the entire project. As the core of the Digitization project, it takes in the user's 
uploaded/selected PDF(s) and processes it entirely, distinguishing images from text and segmenting questions from one another. 
The pipeline makes use of the Tesseract Open Source OCR to extract text from images. Its output 
comes in the form of a triple-nested list that `app.py` retrieves, stores and sends it to the front-end UI for the user 
to mutate this data to his/her liking. Any core adjustments to the back-end code regarding paper output are done here.

### `/extraFiles`
This folder contains several scripts that are either used for testing or to generate files in the background on the virtual machine

* #### `jsonsql.py`
This python script contains MySQL queries to alter and change the database using the PyMySQL library. Developer can change
the queries to be executed and run this script to mutate and change the sql database. 

* #### `WorkspaceGenerator.py` 
This is a script that calls MainV10.py to convert pdfs in the 'Avaliable pdfs' into csv files and subsequently saved under Workspaces.
The script is continually running in the background on the virtual machine in a tmux session. 

* #### `update-pdfbank.py`
This is a script that establishes a connection with the MySQL database and updates the 'inLibrary' status of respective files present in
the Workspace folder. The SHA-2 hash for each file is obtained from /Workspace/hash directory and inserted as a row entry in the 'pdfbank'
table. A '1' value will also be inserted in the 'inLibrary' column to indicate positive status. 

#### `MainV10.html`
Documentation of functions under MainV10.py. For more detailed explanation, please view the MainV10.py script itself.

## Dependencies
The relevant dependencies and libraries used are listed in the requirements.txt file

## Future updates and improvements
* Modularise OCR sections - Such that Tesseract-OCR can be substituted with other compatible OCR modules
* Adding of image/diagram to individual options under every question
* Enable processing and user editing of Structured (open-ended) questions 

######*`MainV9.py` is an older version of this module, while `MainV11.py` has no support yet. Their uses have been deprecated since.*
