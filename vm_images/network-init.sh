#!/bin/bash

# Used to ensure networking is up for all images
# This is a brute-force approach to try to ensure it always works

ifconfig | grep -Po "^[^:\s]+:" | tr -d ':' | xargs -I % ip link set % up