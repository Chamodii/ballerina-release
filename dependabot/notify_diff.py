from json import dumps
import os

from github import Github, GithubException

from httplib2 import Http

import constants
import utils

ballerina_bot_token = os.environ[constants.ENV_BALLERINA_BOT_TOKEN]
github = Github(ballerina_bot_token)

older_version = []
updated_version = []


def send_message(message):
    """Hangouts Chat incoming webhook quickstart."""
    url = 'https://chat.googleapis.com/v1/spaces/AAAAgpdeMqg/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=cOsWPAnu71Y32PwSou9otK8seOkGsW3SlHnf8w0aGRo%3D'
    bot_message = {
        'text' : message}

    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

    http_obj = Http()

    response = http_obj.request(
        uri=url,
        method='POST',
        headers=message_headers,
        body=dumps(bot_message),
    )


def remove_statement_changes():
    global older_version
    global updated_version   
    for i in range(min(2,len(older_version))):
        if(any(x in older_version[0] for x in ["`ballerina-distribution`","`ballerina-lang`"])):
            del older_version[0]
            del updated_version[0]

    # print(older_version)


def create_message():
    global older_version
    global updated_version

    for i in range(len(older_version)):
        old_row = older_version[i].split("|")[1:-1]
        updated_row = updated_version[i].split("|")[1:-1]

        if(old_row[3]!= updated_row[3]):
            pr_link = updated_row[3].split("(")[1][:-2]
            print(pr_link)
            send_message(pr_link)
    






def send_chat(commit):
    global older_version
    global updated_version
    repo = github.get_repo("ballerina-platform" + '/' + "ballerina-release")

    diff_string = utils.open_url("https://github.com/ballerina-platform/ballerina-release/commit/"+commit+".diff").read().decode("utf-8")

    
    for line in diff_string.splitlines():
        if(line.startswith("-")):
            older_version.append(line[1:])
        elif(line.startswith("+")):
            updated_version.append(line[1:])

    older_version = older_version[1:]
    updated_version = updated_version[1:]

    # print(older_version)
    # print(updated_version)

    remove_statement_changes()

    create_message()

 

# send_chat("00b5d8c4696c3181ae7e8eb2470f6652e2b43f5c")

send_chat("7e71937b52e84e8dd77c721d060d16796857396a")
