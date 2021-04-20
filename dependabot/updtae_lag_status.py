import github
from github import Github, InputGitAuthor, GithubException
import json
import sys
import os
from datetime import datetime
import urllib.request

packageUser = os.environ["packageUser"]
packagePAT = os.environ["packagePAT"]
packageEmail = os.environ["packageEmail"]

ENCODING = "utf-8"
ORGANIZATION = "ballerina-platform"
EXTENSIONS_LIST_FILE = "dependabot/resources/extensions.json"
PROPERTIES_FILE = "gradle.properties"
README_FILE = "README.md"
LANG_VERSION_KEY = "ballerinaLangVersion"
github = Github(packagePAT)

MODULE_NAME="module-ballerinax-java.jdbc"

# print(properties_file)

def open_url(url):
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github.v3+json")
    request.add_header("Authorization", "Bearer " + packagePAT)

    return urllib.request.urlopen(request)

def get_lang_version():
    try:
        version_string = open_url(
            "https://api.github.com/orgs/ballerina-platform/packages/maven/org.ballerinalang.jballerina-tools/versions").read()
    except Exception as e:
        print('[Error] Failed to get ballerina packages version', e)
        sys.exit(1)
    latest_version = json.loads(version_string)[0]
    return latest_version["name"]


def days_hours_minutes(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60


def create_timestamp(date, time):
    timestamp = datetime(int(date[0:4]),
            int(date[4:6]),
            int(date[6:8]),
            int(time[0:2]),
            int(time[2:4]),
            int(time[4:6]))
    return timestamp


def get_lag_status(module_name):
    repo = github.get_repo(ORGANIZATION + "/" + module_name)
    properties_file = repo.get_contents(PROPERTIES_FILE)
    properties_file = properties_file.decoded_content.decode(ENCODING)

    for line in properties_file.splitlines():
        if line.startswith(LANG_VERSION_KEY):
            current_version = line.split("=")[-1]
            timestampString = current_version.split("-")[2:4]
            timestamp = create_timestamp(timestampString[0], timestampString[1])


    lang_version = get_lang_version().split("-")
    ballerina_timestamp = create_timestamp(lang_version[2], lang_version[3])
    update_timestamp = ballerina_timestamp-timestamp
    days, hours, minutes = days_hours_minutes(update_timestamp)

    if (days>0):
        delta = str(days) + " days, " + str(hours) + " hours, " + str(minutes) + " mins"
    else:
        delta = str(hours) + " hours, " + str(minutes) + " mins"

    return delta


def get_updated_readme_file(module_name, readme_file, timestamp):
    updated_readme_file = ""
    update = False

    for line in readme_file.splitlines():
        if update == False:
            if module_name in line:

                updated_readme_file += line + "\n"
                updated_readme_file += "    <td class=\"tg-2fdn\">"+timestamp+"</td>\n"
                update = True

            else:
                updated_readme_file += line + "\n"
        else:
            # updated_readme_file += line
            update = False

    return updated_readme_file


def commit_changes(repo, updated_file):
    author = InputGitAuthor(packageUser, packageEmail)
    LANG_VERSION_UPDATE_BRANCH = "dashboards"
    branch = LANG_VERSION_UPDATE_BRANCH 
    
    remote_file = repo.get_contents(README_FILE, ref="dashboards")
    remote_file_contents = remote_file.decoded_content.decode("utf-8")


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
        # if not branch == LANG_VERSION_UPDATE_BRANCH:
        #     update_branch = repo.get_git_ref("heads/" + LANG_VERSION_UPDATE_BRANCH)
        #     update_branch.edit(update["commit"].sha, force=True)
        #     repo.get_git_ref("heads/" + branch).delete()


def get_readme_file():
    # readMe_repo = github.get_repo(ORGANIZATION + "/ballerina-release")

    readMe_repo = github.get_repo("Chamodii" + "/ballerina-release")
    readme_file = readMe_repo.get_contents(README_FILE, ref="dashboards")
    readme_file = readme_file.decoded_content.decode(ENCODING)

    return readme_file


def get_module_list():
    readMe_repo = github.get_repo("Chamodii" + "/ballerina-release")

    module_list_json = readMe_repo.get_contents(EXTENSIONS_LIST_FILE)
    module_list_json = module_list_json.decoded_content.decode(ENCODING)

    data = json.loads(module_list_json)

    return data["modules"]


readMe_repo = github.get_repo("Chamodii" + "/ballerina-release")

readme_file = get_readme_file()
updated_readme = readme_file


module_list = get_module_list()

# module_name = module_list[0]["name"]
# update_timestamp = get_lag_status(module_name)
# # a = datetime(update_timestamp)
# # print(a)
# print(update_timestamp)

# updated_readme = get_updated_readme_file(module_name, updated_readme, update_timestamp)


for module in module_list:
    module_name = module["name"]
    update_timestamp = get_lag_status(module_name)
    updated_readme = get_updated_readme_file(module_name, updated_readme, update_timestamp)

commit_changes(readMe_repo,updated_readme)

# print(updated_readme)





