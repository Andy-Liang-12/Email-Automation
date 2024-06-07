# PipelineCRM Task List Querying and Automated Gmail Replying

This program queries PipelineCRM (PD) API for your daily tasks and filters out follow-up tasks. It then queries GmailAPI to search your inbox for your follow-ups, and automatically drafts a reply from a template, filling in the NAME, CLIENT, and COMPANY fields for you.

## Getting Started

### Dependencies/Setup

* This program is written in python and requires the installation of the google, email, and requests modules.
* When I offboard, my GmailAPI client will stop functioning. You need to create a new Google Cloud project with GmailAPI enabled. Nothing special needed, straightforward process.
* Once the Google Cloud project is running, pass the credentials as you see fit. I have the credentials file saved in the same directory as the program.
* It will ask you to login once through your google account, and save your access token.json locally.

### Executing program

* The program is split into two files/sections.
    * PD_Query handles querying PD API for your daily follow-up tasks.
    * draft_send_reply_PD takes in a list of queries, searches your Gmail inbox, and replies using a template to the first email it finds. Note: this does not work 100% of the time: analysts must always double check that the information and email chain is correct, as well as personalize follow-up emails.

## Help/Disclaimer    
* Non-comprehensive comments and tester code are provided in each section.
* I am not a first-class programmer; much of the code written for this project was learned during its completion. There will be inefficiencies and mistakes, as well as plenty of room for improvement. Reach out if you have questions.

## Authors

Contributors and Contact Info

[@Andy Liang](email.andy.liang@gmail.com)
