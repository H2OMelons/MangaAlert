### Description

MangaAlert is a combination of lambda functions and python functions that utilizes AWS SNS, AWS DynamoDB,
AWS CloudWatch rules, and AWS Lambda to alert the user via SMS when a new chapter of the manga they are
following is posted to Reddit. MangaAlert contains 4 main python scripts:
1. **create_manga_list_table.py:** When run, creates a dynamodb table for MangaAlert
2. **add_manga_list.py:** Allows the user to input the mangas they want to be tracked. When the user indicates
that they are finished inputting, the script uploads all the info to dynamodb
3. **view_update_delete_dynamodb.py:** Allows the user to view, update, and delete any items from dynamodb
4. **scheduler.py:** Allows the user to add CloudWatch rules that trigger the lambda function

### Setup

There's quite a bit of set up and for now, this section will focus on how to
set up MangaAlert for MacOS (Windows coming soon)

#### Set up python

1. Install homebrew by copy pasting the below code onto your terminal and running it
```
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```
2. Install python
```
brew install python3
```
3. Install relevant packages
```
pip3 install boto3
pip3 install aioboto3
pip3 install praw
```

#### Set up Reddit api

MangaAlert utilizes Reddit api so you will either have to use your existing account or create a new one.

1. [Register](https://www.reddit.com/prefs/apps/) the application with Reddit
	1. Click 'create app'
	2. Name: Anything you want
	3. Select script
	4. Description: Anything you want
	5. About url: Leave blank
	6. Redirect url: ```http://localhost:8000```
2. Client ID: Note down the client id. It should be a string of letters and numbers 2 lines down from the name of the application on the top left
3. Client Secret: If you don't see a section called 'secret' click on 'edit'

#### Set up AWS

If you don't have an AWS account, go ahead and sign up for one. It's free and you get a bunch of free
services for the first 12 months: [aws.amazon.com](https://aws.amazon.com/)

1. Download the AWS command line interface (cli)
```
pip3 install awscli
```
2. Get AWS credentials
	1. Go to [aws security credentials](https://console.aws.amazon.com/iam/home?region=us-west-2#/security_credentials)  
	2. Click 'Create New Access Key'  
	3. Click 'Show Access Key'  
	4. Click 'Download Key File' (Keep this in a secure location)  
	5. DO NOT EXIT THE PROMPT  
3. Configure AWS CLI
	1. Go to the terminal and enter ```aws configure```
	2. When it asks for access key/secret access key, copy the corresponding info from the prompt from step 2
	3. For 'Default Region Name' set ```us-west-2```

#### Set up AWS SNS

1. Go to [AWS SNS](https://us-west-2.console.aws.amazon.com/sns/v3/home?region=us-west-2#/topics)
2. Click 'Create topic'
	1. Name: MangaAlert
	2. Click 'Create topic'
3. Click 'Create subscription'
	1. Under 'protocol' select 'SMS'
	2. Enter your phone number. EX: 1-123-4567 (without the dashes)
	3. Click 'Create subscription'
4. Under 'Details' locate 'ARN' and note the value

#### Set up AWS Lambda

1. Open your terminal and navigate to the MangaAlert directory
2. Run
```
$ mkdir package
$ cd package
$ pip install praw --target .
$ zip -r9 ../function.zip .
$ cd ../
$ zip -g function.zip lambda_function.py
```
3. Go to [AWS IAM](https://console.aws.amazon.com/iam/home?region=us-west-2#/home)
	1. On the left hand side click 'Roles'
	2. Click 'Create Role'
	3. Select 'Lambda' then click 'Next: Permissions' on the bottom right
	4. Search for 'dynamodb' and select the item that has 'Full Access'
	5. Search for 'sns' and select the item that has 'Full Access'
	6. Select 'Next: Tags'
	7. Select 'Next: Review'
	8. Make sure everything is correct and select 'Create role'
4. Go to [AWS Lambda](https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/functions)
	1. Click 'Create Function'
	2. Name: MangaAlert
	3. Runtime: Python 3.7
	4. Click 'Choose or create an execution role'
	5. Select 'Use an existing role' and select the one you created in step 3
	6. Click create function
	7. Scroll down and look for the section that says 'Code entry type' and select 'Upload a .zip file'
	8. Select 'Upload' and choose the function.zip file
5. Scroll down a bit to get to the 'Environment variables' section and set the following key:value pairs:
	1. Key: ENV, Value: PROD
	2. Key: REDDIT_CLIENT_ID, Value: <Your Reddit Client ID>
	3. Key: REDDIT_CLIENT_SECRET, Value: <Your Reddit Client Secret>
	4. Key: REDDIT_PASSWORD, Value: <Your Reddit password>
	5. Key: REDDIT_USERNAME, Value: <Your Reddit Username>
	6. Key: REDDIT_USER_AGENT, Value: MangaAlert by <Your Reddit Username>
	7. Key: MANGA_ALERT_ARN, Value: <Your SNS MangaAlert ARN>
6. Note the value of the ARN at the top right of the page

#### Set up AWS DynamoDB
1. Go back to the terminal and to the MangaAlert directory
2. Run
```
python3 create_manga_list_table.py
```

#### Set up AWS CloudWatch rules

AWS CloudWatch rules is used to trigger AWS Lambda. You can use this to change the frequency that Lambda is invoked
1. Go back to the terminal and to the MangaAlert directory
2. Run
```
python3 scheduler.py
```
3. Choose '2: Add'
4. Enter any name (only letters and underscore)
5. Go to http://www.cronmaker.com/ and create a valid cron expression and copy paste it into the terminal
6. Enter 'enabled'
7. Enter a description
8. Enter any number
9. Enter the ARN of the MangaAlert lambda function
