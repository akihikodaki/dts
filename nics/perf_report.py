# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2017 Intel Corporation
#

import os
import re
import smtplib
import time
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jinja2

# install GitPython
from git import Repo

import framework.utils as utils

from .system_info import SystemInfo


def get_dpdk_git_info(repo_dir="/root/dpdk"):

    if not os.path.exists(repo_dir):
        return None

    commit = OrderedDict()

    git_repo = Repo(repo_dir)
    assert not git_repo.bare

    latest_commit = git_repo.active_branch.commit
    commit["branch"] = str(git_repo.active_branch)
    commit["commit"] = str(latest_commit)
    commit["author"] = latest_commit.author
    commit["date"] = time.ctime(latest_commit.authored_date)
    commit["summary"] = latest_commit.summary
    return commit


def generate_html_report(file_tpl, perf_data, git_info, nic_info, system_info):

    if not os.path.exists(file_tpl):
        return None

    templateLoader = jinja2.FileSystemLoader(searchpath="/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(file_tpl)

    templateVars = {
        "title": "Daily Performance Test Report",
        "test_results": perf_data,
        "system_infos": system_info,
        "nic_infos": nic_info,
        "git_info": git_info,
    }

    output = template.render(templateVars)
    return output


# sender = 'zzz@intel.com'
# mailto = ['xxx@intel.com', 'yyy@intel.com']
def html_message(sender, mailto, subject, html_msg):

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["to"] = ";".join(mailto)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_msg, "html"))

    return msg


# smtp = smtplib.SMTP('smtp.intel.com')
def send_email(sender, mailto, message, smtp_server):

    try:
        smtp = smtplib.SMTP(smtp_server)
        smtp.sendmail(sender, mailto, message.as_string())
        smtp.quit()
        print(utils.GREEN("Email sent successfully."))
    except Exception as e:
        print(utils.RED("Failed to send email " + str(e)))


def send_html_report(sender, mailto, subject, html_msg, smtp_server):

    message = html_message(sender, mailto, subject, html_msg)
    send_email(sender, mailto, message, smtp_server)
