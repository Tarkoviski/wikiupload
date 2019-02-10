#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import logging
import os
from os import listdir
from os.path import isfile, join
import time
from time import strftime
import requests

config = configparser.ConfigParser()
config.read("config.ini")

username = config["USER"]["Username"]
password = config["USER"]["Password"]
wiki_url = config["WIKI"]["Url"]
upload_delay = float(config["WIKI"]["UploadDelay"])

session = requests.Session()

logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)


def get_token(token_type):
    params = {
        "action": "query",
        "meta": "tokens",
        "type": token_type,
        "format": "json"
    }

    request = session.post(wiki_url, params)

    json = request.json()
    return json["query"]["tokens"][token_type + "token"]


def log_in():
    params = {
        "action": "login",
        "lgname": config["USER"]["Username"],
        "lgpassword": config["USER"]["Password"],
        "lgtoken": get_token("login"),
        "format": "json",
    }

    session.post(wiki_url, params)


def upload_files(files, summary):
    progress = 0
    errors = 0

    for currentfile in files:
        progress += 1
        filecontents = open("upload/" + currentfile, "rb")

        print(
            "[{0}][File {1} of {2}] Uploading {3}".format(
                strftime("%H:%M"), progress, len(files), currentfile
            )
        )

        payload_data = {
            "action": "upload",
            "filename": currentfile,
            "comment": summary,
            "text": summary,
            "ignorewarnings": True,
            "token": get_token("csrf"),
            "format": "json",
        }

        payload_file = {
            "file": (currentfile, filecontents)
        }

        request = session.post(wiki_url, data=payload_data, files=payload_file)

        res = request.json()

        filecontents.close()

        if "error" in res:
            logging.error(
                "Failed to upload '{0}': Got {1}: {2}".format(
                    currentfile, res["error"]["code"], res["error"]["info"]
                )
            )

            errors += 1
        else:
            if res["upload"]["result"] == "Warning":
                logging.warning(
                    "Failed to upload '{0}': Got {1}".format(
                        currentfile, str(res["upload"]["warnings"])
                    )
                )
                
                errors += 1
            elif res["upload"]["result"] == "Success":
                os.rename("upload/" + currentfile, "done/" + currentfile)

        if progress != len(files):
            time.sleep(upload_delay)

    if errors != 0:
        print(
            "\nUpload complete with {0} error(s)! Please check your logs for more details.".format(
                errors
            )
        )
    else:
        print("\nUpload complete with no errors!")


def check_files():
    # Creates the directories if they don't exist
    if not os.path.exists("upload"):
        print("Creating directory for uploads...")
        os.makedirs("upload")

    if not os.path.exists("done"):
        print("Creating directory for completed uploads...")
        os.makedirs("done")

    print("Searching upload directory for files...")

    # Add each file in the "upload" directory to filelist.
    filelist = [f for f in listdir("upload") if isfile(join("upload", f))]

    # If 0 files are found, give error and exit.
    if not filelist:
        print("No files found, exiting.")
        exit()

    filelist.sort(key=str.lower)

    # If files are found, continue and ask for upload summary.
    print("Found {0} file(s)!".format(len(filelist)))

    summary = input("Upload summary: ")

    upload_files(filelist, summary)


log_in()
check_files()
