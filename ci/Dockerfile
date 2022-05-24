# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021 University of New Hampshire Interoperability Laboratory
# Copyright(c) 2021 Intel Corporation
#

# This container should be build in the ci directory, and then the
# DTS directory should be mounted as a volume at /dts/
FROM python:3.9-slim-buster

ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.txt .
COPY dts_requirements.txt dts_requirements.txt

RUN apt-get update && apt-get install --no-install-recommends -y \
    # Add a C compiler for all of the c modules in DTS
    build-essential make gcc git libpcap-dev\
    python3-pip

RUN pip3 install -r requirements.txt
RUN pip3 install -r dts_requirements.txt
# install formatter
RUN pip3 install black