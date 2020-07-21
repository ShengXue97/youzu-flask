## Overview
This repository hosts the back-end framework for the React web-page, as part of the Digitization Project. The back-end 
is built with [flask](https://palletsprojects.com/p/flask/ "flask Home Page"), a lightweight Web Server Gateway 
Interface web application framework optimized for the Python Language.

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
uploaded/selected PDF(s) and processes it entirely, sorting images from text and questions from one another. Its output 
comes in the form of a triple-nested list that `app.py` retrieves, stores and sends it to the front-end UI for the user 
to mutate this data to his/her liking. Any core adjustments to the back-end code regarding paper output are done here.

#### `jsonsql.py`
This python script contains MySQL queries to alter and change the database using the PyMySQL library. Developer can change
the queries to be executed and run this script to mutate and change the sql database. 

######*`MainV9.py` is an older version of this module, while `MainV11.py` has no support yet. Their uses have been deprecated since.*
