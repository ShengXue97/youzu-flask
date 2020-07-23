
# Developer Guide

DEVELOPER GUIDE FOR YOUZU SINGAPORE


**Group members :** 
* Sim Sheng Xue
* Justin Yip Jia En
* Yu Ying Cheng



## Section A: Developer Guide for Flask

The back-end is built with [flask](https://palletsprojects.com/p/flask/ "flask Home Page"), a lightweight Web Server Gateway Interface web application framework optimized for the Python Language. 

## 1 Home Tab functions
### 1.1 Uploadfile
User clicked Choose PDF File or dropped files into the dotted box area. The user’s files will be saved under /ReactPDF folder. If a custom page is defined, PyPDF2 is used to truncate the pdf file. After this, the file is saved under the same folder. The MainV10 script is started using a new thread, while returning success to React. React will then call Stream(method below).

### 1.2 Pushfile
User clicked Process PDF in one or more files in the pdf table. The appropriate directory where the pdfs are stored will be indicated, which is under /datassd in Azure, and under /pdfs in the developer’s local drive. What happens after is similar to Uploadfile. Custom page range selection is taken into account, and MainV10 script will be called. React will then call Stream(method below).

### 1.3 Getpdfpages
User either uploaded or pushed a file, and selected to use custom pdf page range. This method is used to feedback to React the number of pages this pdf has, allowing the user to select a range from this pdf page range given.

### 1.4 Killsession
Every Session call of the MainV10 script listens to the event whereby the Session is killed. The Killsession method is called when the user uploads or pushes a new file, thereby killing the previous session to save resources. The Session call identifies that it is killed based on its sessionID.

### 1.5 Get_message
Every Session call of the MainV10 script is given an unique sessionID based on the IP address, timestamp and a random string. The MainV10 script will save the progress of this session in a .json file with the sessionID. This shows the current question, page and stage. Get_message simply reads this .json file with the progress information and returns to Stream.

### 1.6 Stream
As mentioned above, Stream is called by React after the user uploads or pushes a file. Stream calls Get_message to monitor the progress of the digitisation process of MainV10 script. This progress information is returned to React, which updates its progress bar. When React detects that the progress is full, it will call Getresult.

### 1.7 Getresult
Reads the output CSV of the Session call of the MainV10 script. The correct output CSV file is identified based on the unique sessionID string. A triple nested list containing the pdf information is generated and returned to React. The first layer is each page, the second layer is each question in the page, and the third layer is the attributes of each question.

### 1.8 Listpdf
This populates the pdf table with information. The appropriate directory where the pdfs are stored will be indicated, which is under /datassd in Azure, and under /pdfs in the developer’s local drive. Note that since there are ~10,000 pdf files in the system, it will be slow to retrieve all of them in one batch. Hence, total_batches is specified as 10, where React will send 10 requests to Flask with each request returning ~1000 pdf files only. The pdf information will populate the pdf table as it arrives, reducing the latency time for the user.

Each pdf entry in the table has a Status attribute. This can be of four types: Not Processed, In Library Only, In Database Only or In Library and Database. Each pdf file is hashed using SHA512 from its Base64 string. This is stored as an entry in the pdfbank MySQL table, with attributes inDatabase and inLibrary. Listpdf will perform a Select query, and update the Status attribute of the pdf entry based on its inDatabase and inLibrary attributes.

### 1.9 Openpdf
The user clicks Download PDF on one or more pdf files in the pdf table. The appropriate directory where the pdfs are stored will be indicated, which is under /datassd in Azure, and under /pdfs in the developer’s local drive. The pdf file will be read and encoded in Base64 format, which is returned back to the user. React converts this Base64 string into a downloadable pdf file for the user.

## 2. Edit Tab functions
### 2.1 Findworkspace
First function called when the user clicks Save Workspace. If a workspace with the same name under Workspaces/csv/ already exists, the user will be prompted if the user wants to overwrite the existing workspace. Each Workspace is stored in three separate files, under Workspaces/csv/, Workspaces/pdf/, and Workspaces/attributes/. The csv file stores the questions data of the pdf file. The pdf file stores the Base64 string of the pdf file. The attribute file stores the exam paper data such as school name and type of exam.

### 2.2 renameworkspace
Second function called when the user clicks Save Workspace. The Workspace files under Workspaces/csv/, Workspaces/pdf/, and Workspaces/attributes/ will each be renamed accordingly.

### 2.3 Savecsv
Third function called when the user clicks Save Workspace. The csv file is stored under Workspaces/csv/. The csv file stores the questions data of the pdf file.
### 2.4 Savepdf
Fourth function called when the user clicks Save Workspace. The pdf file is stored under Workspaces/pdf/. The pdf file stores the Base64 string of the pdf file. Updates the inWorkspace attribute of the pdf file in pdfbank to 1.




### 2.5 Saveattribute
Fifth function called when the user clicks Save Workspace. The attribute file is stored under Workspaces/attributes/. The attribute file stores the exam paper data such as school name and type of exam.

### 2.6 Checkdatabase
First function called when the user clicks Upload all questions to database or Upload selected questions to database. The SHA512 hash of the pdf file that the user is trying to upload will be received from React. Flask will check the number of entries that exist in qbank with the specified SHA512 hash. This number is returned to React.

### 2.7 Updatedatabase
Second function called when the user clicks Upload all questions to database or Upload selected questions to database. Qbank stores all the questions that the user uploads. Each entry contains the question json information and the corresponding pdf SHA512 hash. All previous entries in qbank with the same pdf SHA512 hash will be deleted, as the user is already prompted under Checkdatabase. Updatedatabase creates the question json and pdf hash value based on the data received from React, and inserts these values into the qbank database. Furthermore, the entry with the corresponding pdf SHA512 hash in pdfbank will have its inDatabase attribute updated as 1.

## 3 Workspace Tab functions
### 3.1 Openworkspace
The user clicks open workspace button of a workspace entry in the workspace table. How a workspace is saved is explained under Findworkspace. Each of the three files corresponding to a single workspace is loaded into Flask, from Workspaces/csv/, Workspaces/pdf/ and Workspaces/attributes/. These data are passed back to React. React then opens the Edit tab based on these data. The csv data is used to produce the questions on the right, the pdf data is used to produce the pdf preview on the left, while the attribute data is used to produce the file information on the top.

### 3.2 Deleteworkspace
The user clicks delete workspace button of a workspace entry in the workspace table. All three files corresponding to the single workspace are deleted from Flask.The entry in pdfbank corresponding to the pdf SHA512 hash of this pdf file will have its inWorkspace attribute updated to 0. Note that this happens only if this Workspace is the only Workspace left with the pdf hash value.
### 3.3 Listworkspace
The user clicks on Refresh data in the workspace table, or is simply called when the user clicks the Library Tab. The Status attribute of the workspace is the same as explained under Listpdf. The attributes of the Workspaces(Name, Last Modified and Status) are received from the pdfbank table with a SELECT query. This Workspaces data is returned to React to populate the Workspaces table.

## 4 Database Tab functions
### 4.1 getdatabase
The user clicks on Refresh data in the database table, or is simply called when the user clicks the Database Tab. The various attributes of each question are received from the qbank table with a SELECT query. This database data is returned to React to populate the database table.


## Section B: Installation Guide

## 5 Cloning of Repositories
Log onto Microsoft Azure VirtualMachine using a FTP client such as WinSCP or MobaXTerm. Start a terminal session and navigate to the directory you prefer.

Repository for flask server:https://github.com/ShengXue97/youzu-flask
Repository for react files:https://github.com/ShengXue97/youzu-react
IMPORTANT: 
There are Production and Development builds. Development is for internal testing on the Azure platform, while Production is to publish for external user testing. Both builds consist of React and Flask.

react-production url:http://ycampus.southeastasia.cloudapp.azure.com:3000/#/
flask-production url:http://ycampus.southeastasia.cloudapp.azure.com:3001

react-development url: http://ycampus.southeastasia.cloudapp.azure.com:3002
flask-development url: http://ycampus.southeastasia.cloudapp.azure.com:3003

In the sections below describing setting up the React and Flask servers, highlighted `words in grey` are commands to enter in the FTP client terminal.
### 5.1 Setting up Flask Server
Note that for Flask to work on a new Virtual Machine, Poppler for Pytesseract and OpenCV will need to be installed.

Run the following commands in order:
1. `tmux`
2. ctrl+b then $
3. Type `flask-production`
4. `git clone https://github.com/ShengXue97/youzu-flask.git`
5. `cd  youzu-flask`
6. `python3 -m venv .venv`
7. `source .venv/bin/activate`
8. `pip3 install -r requirements.txt`
9. `python3 app.py`

### 5.2 Updating Flask Server from GitHub
Run the following commands in order:
1. `tmux attach-session -t flask-production`
2. `git stash`
3. `git pull origin master`
4. Ensure that the last line of app.py is app.run(threaded=True, host='0.0.0.0', port=3001)
5. `python3 app.py`

### 5.3 Setting up React Client
Run the following commands in order:
1. `tmux`
2. `ctrl+b` then `$`
3. Type `react-production`
4. `git clone https://github.com/ShengXue97/youzu-react.git`
5. `cd  youzu-react`
6. `npm install`
7. `npm start`

Note: In the event that required react package is missing, run ‘npm i <package-name>’ to install the package. Also take note of the version number of packages.

### 5.4 Updating React Client from GitHub
Run the following commands in order:
1. `tmux attach-session -t react-production`
2. `git stash`
3. `git pull origin master`
4. Ensure that the src\components\subcomponents\serverInfo.js has this line uncommented: var ServerInfo= "http://ycampus.southeastasia.cloudapp.azure.com,3001" 
And the other line of serverInfo commented. The other line is for testing on your local computer.
5. `npm install`
6. `npm start`


## 6 Tmux sessions
The digitisation pipeline enlists the usage of multiple tmux sessions running in the background to either keep the flask/react servers running or to continually run certain scripts. 

Info on tmux commands: https://tmuxcheatsheet.com/ 

List of tmux sessions that should be running:
Steps to set up tmux sessions (from terminal):
1. Enter `tmux new -s <session name>`
2. Execute scripts
3. Rename session using `ctrl+b` then `$`
4. `Ctrl+b`, then `d` to leave the session
5. To see list of session, enter `tmux list-sessions`
6. To attach to session, enter `tmux attach-session <session name>`

The flask and react sessions are responsible to keep the flask and react servers running on both the production and development sites, while the ‘workspace-generator’ and ‘update-pdfbank’ sessions will convert pdfs to csv files, and update statuses of files in the Library respectively.  

## 7 Changelog
The updates for each of the versions is shown here.


## Section C: Overview of Pipeline and files
Flask calls the MainV10 script, which is the script responsible for the digitisation of exam papers.

### 8. Digitisation Pipeline
![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/Pipeline%20and%20Prototype.jpg 'Illustration of Pipeline')

### 8.1 PDF to Image
Uploaded pdf will be converted to images, and the attributes of the exam paper will be extracted. Negative-scale images will be converted to white if they fall below a certain threshold.

### 8.2 Question Detection
Using Tesseract-OCR and our algorithm, small images of question numbers and their y-coordinates on each page of the paper will be extracted. 

### 8.3 Image Cropping
Based on the y-coordinates of the question numbers extracted from the previours step, each page of the paper will be cropped to fit only the contents of a single question. They will be subsequently saved under the /TempImages folder.

### 8.4 Image Pre-processing
Several image-preprocessing techniques available in the OpenCV computer vision library will be utilised to improve the quality before being passed to the OCR. Below techniques are also used to remove unwanted long lines along margins present in some pages of papers.

    *Examples of techniques used (not exhaustive):*
    * Gaussian Blurring
    * Grayscaling
    * Morphological operations like erosion, dilation, opening, closing etc
    
### 8.5 Contour Detection
After image is cleaned and denoised, cv2.findContours() function is used to obtains countours wrapping blocks of text on the image. Contours extremely close in proximity will then be merged, while very small contours will be erased. These contours will be passed into our defined draw_contours() function, which will use the cv2.boundingRect() function to outline (rectangular in shape) blocks of text/diagrams. Blank lines in the question will be detected, and a '_______' text will be inserted in the corresponding position in the processed text thereafter. Based on the x,y,w,h coordinates of the blocks obtained from cv2.boundingRect() function, the region will be cropped out and subsequently passed into the OCR to be converted to text strings. 
Illustration of bounding box:![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/contour.jpg)

### 8.6 Diagram/Text Classification
Using Gibberish Detector module, Hough Lines and aspect ratio of the contours, the cropped region will be deemed to be readable text or diagram. For text that passes the filters, it will be appended to a list. Otherwise, digrams will be saved under the /TempImages folder and the base64 string will be appended to the same list.

### 8.7 Diagram/Text Segmentation
Diagrams under /TempImages folder:![alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/tempimages.PNG)
Base64 strings of diagrams sorted under the /TempImages folder will be accessed and appended to the corresponding questions while text will be segmented into the question title and options using regular expressions. 

### 8.8 Create Pandas Dataframe
All essential and processed content will be inserted into a pandas dataframe, with each question taking up one row. The output will be saved as a csv file, and user can modify MainV10.py script to retain the csv file for inspection. The information and processed content will then be pushed to the front end for user edit and viewing.



## 9 Breakdown
This repository holds many folders that contain highly important data, and are the backbone of many of the functions 
observed in the React UI. Arguably, the most important directory/modules are:

### 9.1 ./Workspaces
This directory contains the data of all previously processed PDFs for that particular server (contents differ for 
production and development builds). In short, it is responsible for the user being able to save his workspace or return 
to its most recent edit to download the .csv version of the output and even upload questions to the DataBase.

Without this folder and its essential sub-folders (./attribute, ./csv and ./pdf), there would be no saved output and 
users would have to do all the work in that one session.

### 9.2 `app.py`
This module is responsible for connecting all back-end logic to the front-end UI, and vice-versa. It is the middle-man 
be it in re-directing the user to another page, or in receiving the POST request upon the user's PDF upload, before 
sending it to `MainV10.py` for effective processing and sending it back to the front-end web-page.

Some important helper modules that are used are:
* `GibberishDetector.py` *(Detects whether contour boxes found are gibberish or actual text, and is part of diagram-text 
segmentation/analysis)*
* `WorkspaceGenerator.py` *(Helper function that holds the logic for generating a saved workspace in the ./Workspaces 
directory)*

### 9.3 `MainV10.py`
This module is the backbone of the entire project. As the core of the Digitization project, it takes in the user's 
uploaded/selected PDF(s) and processes it entirely, distinguishing images from text and segmenting questions from one another. 
The pipeline makes use of the Tesseract Open Source OCR to extract text from images. Its output 
comes in the form of a triple-nested list that `app.py` retrieves, stores and sends it to the front-end UI for the user 
to mutate this data to his/her liking. Any core adjustments to the back-end code regarding paper output are done here.

### 9.4 `/extraFiles`
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

## 10. Dependencies
The relevant dependencies and libraries used are listed in the requirements.txt file

## 11. Future updates and improvements
* Modularise OCR sections - Such that Tesseract-OCR can be substituted with other compatible OCR modules
* Adding of image/diagram to individual options under every question
* Enable processing and user editing of Structured (open-ended) questions 

######*`MainV9.py` is an older version of this module, while `MainV11.py` has no support yet. Their uses have been deprecated since.*
