import github
from github import Github, InputGitAuthor, GithubException
import json
import sys
import os
from datetime import datetime
import urllib.request
import base64
import matplotlib.image as mpimg

packageUser = os.environ["packageUser"]
packagePAT = os.environ["packagePAT"]
packageEmail = os.environ["packageEmail"]

ENCODING = "utf-8"
ORGANIZATION = "ballerina-platform"
EXTENSIONS_LIST_FILE = "dependabot/resources/extensions.json"
BALLERINA_LANG_VERSION_FILE = "dependabot/resources/latest_ballerina_lang_version.json"
PROPERTIES_FILE = "gradle.properties"
README_FILE = "README.md"
LANG_VERSION_KEY = "ballerinaLangVersion"
BALLERINA_DISTRIBUTION = "ballerina-distribution"
github = Github(packagePAT)

all_modules = []

MODULE_NAME = "name"
ballerina_timestamp = ""
ballerina_lang_version = ""

import notify_diff


def open_url(url):
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github.v3+json")
    request.add_header("Authorization", "Bearer " + packagePAT)

    return urllib.request.urlopen(request)


def get_latest_lang_version():
    # Read this from the file that Niveathika would update, for now have the latest version
    try:
        version_string = open_url(
            "https://api.github.com/orgs/ballerina-platform/packages/maven/org.ballerinalang.jballerina-tools/versions").read()
    except Exception as e:
        print('[Error] Failed to get ballerina packages version', e)
        sys.exit(1)
    latest_version = json.loads(version_string)[0]
    return latest_version["name"]

def get_lang_version_lag():
    global ballerina_timestamp
    lag_string=""
    # try:
    #     version_string = open_url(
    #         'https://api.github.com/orgs/ballerina-platform/packages/maven/org.ballerinalang.jballerina-tools/versions').read()
    #     lang_version = (version_string).split("-")
    #     timestamp = create_timestamp(lang_version[2], lang_version[3])
    #     ballerina_lag = timestamp-ballerina_timestamp
    #     days, hrs = days_hours_minutes(ballerina_lag)
    #     if(days>0):
    #         lag_string = format_lag(ballerina_lag)
    #     else:
    #         lag_string = str(hrs)+" h"

    # except Exception as e:
    #     print('[Error] Failed to get ballerina packages version', e)
    #     sys.exit(1)
    version_string = get_latest_lang_version()
    lang_version = (version_string).split("-")
    timestamp = create_timestamp(lang_version[2], lang_version[3])
    ballerina_lag = timestamp-ballerina_timestamp
    days, hrs = days_hours_minutes(ballerina_lag)
    if(days>0):
        lag_string = str(format_lag(ballerina_lag)) + " days"
    else:
        lag_string = str(hrs)+" h"

    return lag_string

def get_lang_version():
    global ballerina_lang_version
    repo = github.get_repo(ORGANIZATION + "/ballerina-release")
    lang_version_file = repo.get_contents(BALLERINA_LANG_VERSION_FILE)
    lang_version_json = lang_version_file .decoded_content.decode(ENCODING)

    data = json.loads(lang_version_json)
    ballerina_lang_version = data["version"]


def days_hours_minutes(td):
    return td.days, td.seconds//3600


def create_timestamp(date, time):
    timestamp = datetime(int(date[0:4]),
            int(date[4:6]),
            int(date[6:8]),
            int(time[0:2]),
            int(time[2:4]),
            int(time[4:6]))
    return timestamp


def format_lag(delta):
    days, hours = days_hours_minutes(delta)
    hrs = round((hours/24) * 2) / 2
    days = days + hrs
    if((days).is_integer()):
        days = int(days)
    return days


def get_lag_info(module_name):
    global ballerina_timestamp
    repo = github.get_repo(ORGANIZATION + "/" + module_name)
    properties_file = repo.get_contents(PROPERTIES_FILE)
    properties_file = properties_file.decoded_content.decode(ENCODING)

    for line in properties_file.splitlines():
        if line.startswith(LANG_VERSION_KEY):
            current_version = line.split("=")[-1]
            timestampString = current_version.split("-")[2:4]
            timestamp = create_timestamp(timestampString[0], timestampString[1])

    lang_version = (ballerina_lang_version).split("-")
    ballerina_timestamp = create_timestamp(lang_version[2], lang_version[3])
    update_timestamp = ballerina_timestamp-timestamp
    delta = format_lag(update_timestamp)
    days = str(delta)

    if(delta==0):
        color = "brightgreen"
    elif(delta<2):
        color = "yellow"
    else:
        color = "red"

    return days, color


def update_modules(updated_readme, module_details_list):
    module_details_list.sort(reverse=True, key=lambda s: s['level'])
    last_level = module_details_list[0]['level']
    updated_modules = 0

    for i in range(last_level):
        current_level = i + 1
        # global current_level_modules
        current_level_modules = list(filter(lambda s: s['level'] == current_level, module_details_list))

        for idx, module in enumerate(current_level_modules):
            name = ""
            pending_pr = ""
            pr_id = ""

            pending_pr_link = ""

            if(module[MODULE_NAME].startswith("module")):
                name = module[MODULE_NAME].split("-")[2]
            else:
                name = module[MODULE_NAME]
    

            lag_status, color = get_lag_info(module[MODULE_NAME])
            lag_status += "%20days"
            if(color!="red"):
                updated_modules +=1
            lag_button = "[![Lag](https://img.shields.io/badge/lag-" + lag_status + "-" + color + ")](#)"
            pr_number = check_pending_pr_checks(module[MODULE_NAME])
            
            if(pr_number!=None):
                pr_id = "#" + str(pr_number)
                pending_pr_link = "https://github.com/ballerina-platform/"+module[MODULE_NAME]+"/pull/" + str(pr_number)
            pending_pr = "[" + pr_id + "](" + pending_pr_link + ")"
            
            level = ""
            if(idx==0):
                level = str(current_level)
   

            table_row = "| " + level + " | [" + name + "](https://github.com/ballerina-platform/"+module[MODULE_NAME]+") | " + lag_button + " | " + pending_pr + " | "
            updated_readme += table_row + "\n"
    return updated_readme, updated_modules


def make_pie(val):
    import matplotlib.pyplot as plt
    import numpy as np

    colors = [(60,121,189), (212, 241, 249)]
    sizes = [val,100-val]
    text = str(val) + "%"

    col = [[i/255. for i in c] for c in colors]

    fig, ax = plt.subplots()
    ax.axis('equal')
    width = 0.35
    kwargs = dict(colors=col, startangle=180)
    outside, _ = ax.pie(sizes, radius=1, pctdistance=1-width/2,**kwargs)
    plt.setp( outside, width=width, edgecolor='white')

    kwargs = dict(size=20, fontweight='bold', va='center')
    ax.text(0, 0, text, ha='center', **kwargs)
    plt.savefig('foo.png')


def return_updated_readme(readme):
    updated_readme = ""
    global all_modules

    all_modules = get_module_list()

    module_details_list = all_modules["modules"]

   
    updated_readme += "# Ballerina Repositories Update Status" + "\n"
    distribution_lag = get_lag_info(BALLERINA_DISTRIBUTION)[0] + " days"
    ballerina_lang_lag = get_lang_version_lag()
    
    distribution_pr_number = check_pending_pr_checks(BALLERINA_DISTRIBUTION)
    distribution_pr_link = "https://github.com/ballerina-platform/"+BALLERINA_DISTRIBUTION+"/pull/" + str(distribution_pr_number)

    if(distribution_lag.startswith("0")):
        distribution_lag_statement = "`ballerina-distribution` repository is up to date."
    else:
        if(str(distribution_pr_number)=="None"):
            distribution_lag_statement = "`ballerina-distribution` repository lags by " + distribution_lag
        else:
            distribution_lag_statement = "`ballerina-distribution` repository lags by " + distribution_lag + " and pending PR [#" + str(distribution_pr_number) + "](" + distribution_pr_link + ") is available"

    if(ballerina_lang_lag.startswith("0")):
        lang_version_statement  = "`ballerina-lang` repository version **" + ballerina_lang_version + "** has been updated as follows"
    else:
        lang_version_statement  = "`ballerina-lang` repository version **" + ballerina_lang_version + "** ("+ballerina_lang_lag+") has been updated as follows"

    updated_readme += distribution_lag_statement + "<br>"
    updated_readme += "\n" + "<br>"
    updated_readme += lang_version_statement + "\n"

    updated_readme += "## Modules and Extensions Packed in Distribution" + "\n"
    updated_readme += "| Level | Modules | Lag Status | Pending PR |" + "\n"
    updated_readme += "|:---:|:---:|:---:|:---:|" + "\n"

    updated_readme, updated_modules_number = update_modules(updated_readme, module_details_list)
    print(updated_modules_number)
    
    updated_readme += "## Modules Released to Central" + "\n"

    updated_readme += "| Level | Modules | Lag Status | Pending PR |" + "\n"
    updated_readme += "|:---:|:---:|:---:|:---:|" + "\n"

    central_modules = all_modules["central_modules"]

    updated_readme, updated_modules_number_central = update_modules(updated_readme, central_modules)
    updated_modules_number += updated_modules_number_central
    repositories_updated = round((updated_modules_number/(len(module_details_list)+len(central_modules)))*100)
    # make_pie(repositories_updated)

    return updated_readme


def upload_image(repo, image):
    # contents = repo.get_contents("")

    all_files = []
    contents = repo.get_contents("", ref="dashboards")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))

    # with open('/tmp/file.txt', 'r') as file:
    content = base64.b64encode(image)

    # Upload to github
    git_prefix = ''
    git_file = git_prefix + 'foo.png'
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(contents.path, "committing files", content, contents.sha, branch="dashboards")
        print(git_file + ' UPDATED')
    else:
        repo.create_file(git_file, "committing files", content, branch="dashboards")
        print(git_file + ' CREATED')



def commit_changes(repo, updated_file):
    author = InputGitAuthor(packageUser, packageEmail)
    LANG_VERSION_UPDATE_BRANCH = "dashboards"
    branch = LANG_VERSION_UPDATE_BRANCH 
    
    remote_file = repo.get_contents(README_FILE, ref="dashboards")
    remote_file_contents = remote_file.decoded_content.decode("utf-8")

    # remote_graph = repo.get_contents("foo.png", ref="dashboards")
    # image = base64.b64encode(graph_image)


    if remote_file_contents == updated_file:
        print("[Info] Branch with the lang version is already present.")
    else:
        current_file = repo.get_contents(README_FILE, ref=branch)
        

        update = repo.update_file(
            current_file.path,
            "update readme commit message",
            updated_file,
            current_file.sha,
            branch=branch,
            author=author
        )


        update_branch = repo.get_git_ref("heads/" + branch)
        update_branch.edit(update["commit"].sha, force=True)

        notify_diff.main()

        # img_file = repo.get_contents("foo.png", ref=branch)

        # img_update = repo.update_file(
        #     img_file.path,
        #     "update image commit message",
        #     image,
        #     img_file.sha,
        #     branch=branch,
        #     author=author
        # )
        # update_branch = repo.get_git_ref("heads/" + branch)
        # update_branch.edit(img_update["commit"].sha, force=True)

def get_readme_file():
    # readMe_repo = github.get_repo(ORGANIZATION + "/ballerina-release")

    readMe_repo = github.get_repo("Chamodii" + "/ballerina-release")
    readme_file = readMe_repo.get_contents(README_FILE, ref="dashboards")
    readme_file = readme_file.decoded_content.decode(ENCODING)

    return readme_file


def get_module_list():
    readMe_repo = github.get_repo(ORGANIZATION + "/ballerina-release")

    module_list_json = readMe_repo.get_contents(EXTENSIONS_LIST_FILE)
    module_list_json = module_list_json.decoded_content.decode(ENCODING)

    data = json.loads(module_list_json)

    return data


def check_pending_pr_checks(module_name):
   
    repo = github.get_repo(ORGANIZATION + "/" + module_name)

    pulls = repo.get_pulls(state="open")

    for pull in pulls:
        if pull.head.ref == "automated/dependency_version_update":
            sha = pull.head.sha
            status = repo.get_commit(sha=sha).get_statuses()
            print(status)
            return pull.number
    return None


readMe_repo = github.get_repo("Chamodii" + "/ballerina-release")

readme_file = get_readme_file()
updated_readme = readme_file

get_lang_version()
module_list = get_module_list()

updated_readme = return_updated_readme(readme_file)

import matplotlib.pyplot as plt

img = mpimg.imread("foo.png")

commit_changes(readMe_repo,updated_readme)

