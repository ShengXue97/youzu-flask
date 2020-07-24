# Moolde LMS Setup and Installation
This guide will only list out the key points of the installation and setup process of Moodle.
For more detailed explanation and a step-by-step Installation Guide for Ubuntu, please refer to https://docs.moodle.org/39/en/Step-by-step_Installation_Guide_for_Ubuntu 
Additional resources:https://linuxhostsupport.com/blog/how-to-install-moodle-on-ubuntu-18-04/

Moodle site for YooAcademy can be accessed via: http://ycampus.southeastasia.cloudapp.azure.com/moodle/
## Section A: Installation

## Prerequisites:
* Ubuntu 18.04
* Apache 2.0 for web server
* PHP 7.0 for moodle
* MySQL for database server

### Install by running the following commands on terminal
1. `sudo apt install apache2 mysql-client mysql-server php libapache2-mod-php`
2. `sudo apt install graphviz aspell ghostscript clamav php7.2-pspell php7.2-curl php7.2-gd php7.2-intl php7.2-mysql php7.2-xml php7.2-xmlrpc php7.2-ldap php7.2-zip php7.2-soap php7.2-mbstring`

### Download Moodle
Setup your local repository and download the latest stable version of Moodle from https://download.moodle.org/. The version used at this point in time is *Moodle 3.9.1*

### Copy local repository to /var/www/html/ on virtual machine
Also, create a Moodledata directory which stores files that are uploaded or created by the Moodle interface. Site administrators can see the actual moodledata directory name and location in the config.php file later on.
Make the webroot writable such that config.php can be created when installer runs:
`sudo chmod -R 777 /var/www/html/moodle`
### Setup MySQL server
You may choose to create a new Moodle database and Moodle MySQL User with the correct permissions. Otherwise, you can choose to maintain and use the 'youzu' database created during the setup of flask repository which contains table of uploaded and processed questions.
* To create new database:
`mysql>CREATE DATABASE moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
* To create new user:
`mysql>create user 'moodledude'@'localhost' IDENTIFIED BY 'passwordformoodledude';`
* Grant permission for new user:
`mysql>GRANT ALL PRIVILEGES ON * . * TO 'newuser'@'localhost';`
* Reload privileges:
`mysql> FLUSH PRIVILIGES;`

### Configure Apache2 (Optional):
If you wish to configure the Apache2 site configuration file for moodle, access /etc/apache2/sites-available/<conf file name> and edit it. Otherwise, the default conf file is '000-default.conf'.
After editing the configuration file, enable it by running the commands below:
* `sudo a2enmod rewrite`
* `sudo a2ensite <conf file name>`

### Run through installation process on browser
1. Open browser and go to http://IP.ADDRESS.OF.SERVER/moodle
![Alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/moodle_home.png)
2. Configure the following settings as prompted
* Path for moodledata
* Database type
* Database Settings
* Environment Checks
Database Settings:![Alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/moodle_db_setting.png)
**Note:** In the event that error w.r.g. to 'mysql_native_password native authentication' is shown during attempt to connect to database, run the following command on mysql shell:
`ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '<password>';`
3. Ensure all plugins requirements are met and success messages are shown
4. Once installation is completed, contine to create an administrator account. Setup password, username and email credentials.

### Edit config.php for moodle
Navigate to the /var/www/html/moodle/ directory and access the config.php file in order to test your site from other machines. Under `$CFG-> wwwroot`, change ipaddress to designated website address.
Illustration: ![Alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/cfg.PNG)

## Section B: Customisation of Moodle site
For detailed instructions on how to modify and customise site appearance, refer to official moodle documentation at https://docs.moodle.org/39/en/Site_appearance.
__Note: Most of appearance customisation can be achieved by modifying settings under Site Administration->Appearance/Plugins as an admin user.__

Illustration:![Alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/appearance.PNG)

## Change Theme
Refer to:https://docs.moodle.org/24/en/Installing_a_new_theme
1. Download zip file of theme 
2. Extract files and upload to /theme folder in the Moodle directory on virtual machine
3. Change Read/Write permissions for files and folder
4. Navigate to Settings > Site administration > Appearance > Themes > Theme Selector after logging into moodle site as administrator
5. Select the newly uploaded theme and click 'use theme' button
6. Refresh browser to see changes.

## To modify (increase) file upload size for course content
Refer to : https://docs.moodle.org/39/en/File_upload_size
Errors may arise when the administrator attempts to upload course content that exceeds default limit set in moodle. Take note of the following steps to change settings (.htaccess method):
1. Create a file called .htaccess in Moodle's main directory (where 'index.php' is located, not the 'moodledata' directory) that contains the following information:
`php_value upload_max_filesize 20971520` --> 20971520 is 20Mb
`php_value post_max_size 20971520`
`php_value max_execution_time 600`
2. Configure the /etc/apache2/apache2.conf file to allow Allow Overrides
Illustration:![Alt text](https://github.com/ShengXue97/youzu-flask/blob/master/Additonalmages/Capture.PNG)






