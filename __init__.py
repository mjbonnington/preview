#!/usr/bin/python

import os

os.environ['PREVIEW_USER_PREFS_LOCAL_PATH'] = os.path.expanduser('~/.mjbPreview')
os.environ['PREVIEW_RESOLUTION_X'] = "1920"
os.environ['PREVIEW_RESOLUTION_Y'] = "1080"
os.environ['PREVIEW_PROXY_SCALE'] = "0.5"
os.environ['PREVIEW_STARTFRAME'] = "1001"
os.environ['PREVIEW_ENDFRAME'] = "1125"
os.environ['PREVIEW_JOB'] = ""
os.environ['PREVIEW_SHOT'] = ""
os.environ['PREVIEW_VIEWER'] = "djv"
