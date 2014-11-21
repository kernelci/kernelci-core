#!/usr/bin/env python
#
# error/warn formatting, css, colors etc. stolen from Olof Johansson <olof@lixom.net>
#
import os
import sys
import subprocess
import json
import re

headers = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
<head>
  <title>Boot log: %s</title>
  <style type="text/css">
  body { background-color: black; color: white; }
  pre warn { color: #F88017; }
  pre err { color: red; }
  pre pass { color: green; }
  pre pyboot { color: yellow; }
  pre offline { color: darkgray; }
  A:link {text-decoration: none }
  A:visited {text-decoration: none }
  A:active {text-decoration: none }
  A:hover {text-decoration: bold; color: red; }
  </style>
</head>
<body>

"""

log = sys.argv[1]
if not os.path.exists(log):
    print "ERROR: logfile %s doesn't exist." %log
    sys.exit(1)

base,ext = os.path.splitext(log)
html = base + ".html"
jsn = base + ".json"
base = os.path.basename(base)
board = base
if base.startswith("boot-"):
    board = base[5:]

log_f = open(log, "r")
html_f = open(html, "w")
json_f = open(jsn, "r+")
boot_json = json.load(json_f)
json_f.seek(0)

boot_result = None
if boot_json.has_key("boot_result"):
    boot_result = boot_json["boot_result"]

html_f.write(headers %board)
html_f.write("<h1>Boot log: %s</h1>\n" %(board))

errors = subprocess.check_output('grep "^\[ERR\]" %s | cat' %log, shell=True).splitlines()
num_errors = len(errors)
warnings = subprocess.check_output('grep "^\[WARN\]" %s | cat' %log, shell=True).splitlines()
num_warnings = len(warnings)

html_f.write("<font size=-2><pre>\n")

html_f.write("<h2>Boot result: ")
if boot_result == "PASS":
    html_f.write("<pass>PASS</pass></h2>")
elif boot_result == "FAIL":
    html_f.write("<err>FAIL</err></h2>")
else:
    html_f.write("<warn>%s</warn></h2>" %boot_result)

html_f.write("<h2>Errors: %d</h2>" %num_errors)
if num_errors:
    for e in errors:
        html_f.write("<err>%s</err>\n" %e.rstrip())
    html_f.write("\n")

html_f.write("<h2>Warnings: %d</h2>" %num_warnings)
if num_warnings:
    for e in warnings:
        html_f.write("<warn>%s</warn>\n" %e.rstrip())
    html_f.write("\n")

html_f.write("<h2>Full boot log:</h2>\n")
for line in log_f:
    warn = err = pyboot = False
    if line.startswith("[WARN]"):
        warn = True
        html_f.write("<warn>")
    elif line.startswith("[ERR]"):
        err = True
        html_f.write("<err>")
    m = re.search("^# PYBOOT:", line)
    if m:
        line = "<pyboot>%s</pyboot>" %line
    html_f.write(line)
    if warn:
        html_f.write("</warn>")
    elif err:
        html_f.write("</err>")

html_f.write("</pre></font></body></html>")

log_f.close()
html_f.close()
