#!/usr/bin/env python3
"""
Author: Steve Göring

style: black file_utils.py -l 140

"""
import os
import sys
import shutil
import json
import logging
import subprocess


def get_basename(filename):
    """
    returns the filename without extension
    TODO: name is missleading (not the filebasename is created)
    """
    return os.path.splitext(filename)[0]


def flat_name(filename):
    """
    converts a given filename to a version without pathes
    """
    return filename.replace("../", "").replace("/", "_").replace("./", "").replace(".", "")
