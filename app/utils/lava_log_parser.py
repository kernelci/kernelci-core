#!/usr/bin/env python
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Based on log2html.py:
# https://github.com/khilman/lab/blob/master/log2html.py
#
# Error/warning formatting, css, colors etc. stolen from
# Olof Johansson <olof@lixom.net>

import argparse
import cgi
import dateutil.parser
import json
import yaml
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

HTML_HEAD = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
<head>
  <title>Boot log: {board}</title>
  <style type="text/css">
  body {{ background-color: black; color: white; }}
  pre {{ font-size: 0.8em; }}
  span.pass {{ color: green; }}
  span.err {{ color: red; }}
  span.warn {{ color: #F88017; }}
  span.timestamp {{ color: #AAFFAA; }}
  a:link {{text-decoration: none }}
  a:visited {{text-decoration: none }}
  a:active {{text-decoration: none }}
  a:hover {{text-decoration: bold; color: red; }}
  ul.results {{
    list-style-type: none;
    padding-left: 0;
    font-weight: bold;
    font-size: 1.3em;
    font-family: "Courier New", Courier, monospace;
  }}
  li.result {{ padding: 5px 0 5px 0; }}
  </style>
</head>
<body>
<h1>Boot log: {board}</h1>
"""


def run(log, boot, txt, html):
    boot_result = boot.get("boot_result", "Unknown")
    if boot_result == "PASS":
        boot_result_html = "<span class=\"pass\">PASS</span>"
    elif boot_result == "FAIL":
        boot_result_html = "<span class=\"err\">FAIL</span>"
    else:
        boot_result_html = "<span class=\"warn\">{}</span>".format(boot_result)

    formats = {
        "warning": "<span class=\"warn\">{}</span>\n",
        "error": "<span class=\"err\">{}</span>\n",
    }
    numbers = {"warning": 0, "error": 0}
    start_ts = None
    log_buffer = StringIO.StringIO()

    for line in log:
        iso_ts = dateutil.parser.parse(line["dt"])
        raw_ts = iso_ts.strftime("%H:%M:%S.%f%z  ")
        timestamp = "<span class=\"timestamp\">{}</span>".format(raw_ts)

        level, msg = (line.get(k) for k in ["lvl", "msg"])

        fmt = formats.get(level, None)
        if fmt:
            log_buffer.write(timestamp)
            log_buffer.write(fmt.format(cgi.escape(msg)))
            numbers[level] += 1
        elif level == "target":
            log_buffer.write(timestamp)
            log_buffer.write(cgi.escape(msg))
            log_buffer.write("\n")
            txt.write(msg)
            txt.write("\n")
        elif level == "info" and msg.startswith("Start time: "):
            start_ts = msg

    html.write(HTML_HEAD.format(board=boot["board"]))
    html.write("<ul class=\"results\">")
    results = {
        "Boot result": boot_result_html,
        "Errors": numbers["error"],
        "Warnings": numbers["warning"],
    }
    for title, value in results.iteritems():
        html.write("<li class=\"result\">{}: {}</li>".format(title, value))
    if start_ts:
        html.write("<li class=\"result\">{}</li>".format(start_ts))
    html.write("</ul><pre>\n")
    html.write(log_buffer.getvalue())
    html.write("</pre></body></html>\n")


def main(args):
    with open(args.log, "r") as log_yaml:
        log = yaml.load(log_yaml, Loader=yaml.CLoader)

    with open(args.meta, "r") as boot_json:
        boot = json.load(boot_json)

    with open(args.txt, "w") as txt, open(args.html, "w") as html:
        run(log, boot, txt, html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate HTML page from kernel boot log")
    parser.add_argument("--log", required=True,
                        help="Path to a YAML file with the kernel boot log")
    parser.add_argument("--meta", required=True,
                        help="Path to a JSON file with the boot meta-data")
    parser.add_argument("--txt", required=True,
                        help="Path to the output text file")
    parser.add_argument("--html", required=True,
                        help="Path to the output HTML file")
    args = parser.parse_args()
    main(args)
