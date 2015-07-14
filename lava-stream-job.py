#!/usr/bin/env python
#
# This file is part of lava-hacks.  lava-hacks is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Tyler Baker 2015

import sys
import argparse
import urlparse
import datetime
import time
import xmlrpclib
import curses
import re

from lib import configuration
from lib import text_output


class FileOutputHandler(object):
    def __init__(self, file_obj, outputter, interval):
        self.file_obj = file_obj
        self.outputter = outputter
        self.interval = interval

        self.full_output = ""
        self.printed_output = ""


    def run(self):
        while True:
            self._update_output()
            self._print_output()

            if not self.outputter.is_running(): break

            time.sleep(self.interval)

        self.file_obj.write("Job has finished.")


    def _update_output(self):
        self.full_output = self.outputter.get_output()


    def _print_output(self):
        if not self.full_output:
            self.file_obj.write("No job output...\n")

        new_output = self.full_output[len(self.printed_output):]

        self.file_obj.write(new_output)
        self.file_obj.write(' \b') #HACK: force detection of broken pipe
        self.file_obj.flush()
        self.printed_output = self.full_output


class CursesOutput(object):
    def __init__(self, outputter, interval, follow=True):
        self.outputter = outputter
        self.textblock = text_output.TextBlock()
        self.interval = interval
        self.follow = follow

        self.win_height = 0
        self.win_width = 0
        self.win_changed = False
        self.cur_line = 0
        self.status_win = None
        self.state_win_height = 2
        self.output = ""
        self.text_changed = False


    def run(self):
        curses.wrapper(self._run)


    def _run(self, stdscr):
        self.stdscr = stdscr
        self._setup_win()
        self.stdscr.nodelay(1)

        while True:
            key = self.stdscr.getch()
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.outputter.cancel_job()

            self._update_win()
            self._poll_state()

            self._redraw_output()
            self._redraw_status()

            self._refresh()
            time.sleep(self.interval)


    def _setup_win(self):
        self.win_height, self.win_width = self.stdscr.getmaxyx()
        self.status_win = curses.newwin(self.state_win_height, self.win_width, self.win_height-self.state_win_height, 0)
        self.status_win.bkgdset(' ', curses.A_REVERSE)
        self.textblock.set_width(self.win_width, reflow=False)
        self.win_changed = True


    def _update_win(self):
        if curses.is_term_resized(self.win_height, self.win_width):
            self.win_height, self.win_width = self.stdscr.getmaxyx()
            curses.resizeterm(self.win_height, self.win_width)

            self.status_win.resize(self.state_win_height, self.win_width)
            self.status_win.mvwin(self.win_height-self.state_win_height, 0)

            self.textblock.set_width(self.win_width, reflow=False)

            self.win_changed = True


    def _poll_state(self):
        old_output_len = len(self.output)

        self.output = self.outputter.get_output()

        if len(self.output) != old_output_len:
            self.textblock.set_text(self.output, reflow=False)
            self.text_changed = True


    def _redraw_output(self):
        if self.text_changed or self.win_changed:
            output_lines = None

            self.textblock.reflow()
            if self.follow:
                output_lines = self.textblock.get_block(-1, self.win_height-self.state_win_height)
            else:
                output_lines = self.textblock.get_block(self.cur_line, self.win_height-self.state_win_height)

            self.stdscr.clear()
            self._draw_text(output_lines)

            self.win_changed = False
            self.text_changed = False


    def _redraw_status(self):
        details = "description: %s" % self.outputter.get_description()
        details += "   device_type: %s" % self.outputter.get_device_type_id()
        details += "   hostname: %s" % self.outputter.get_hostname()
        self.status_win.addstr(0, 0, details[:self.win_width-1])

        status = "active: %s" % self.outputter.is_running()
        status += "   action: %s" % self.outputter.last_action()
        self.status_win.addstr(1, 0, status[:self.win_width-1])


    def _draw_text(self, lines):
        for index, line in enumerate(lines):
            self.stdscr.addstr(index, 0, line)


    def _refresh(self):
        self.stdscr.refresh()
        self.status_win.refresh()


def handle_connection(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpclib.ProtocolError as e:
            if e.errcode == 502:
                print "Protocol Error: 502 Bad Gateway, retrying..."
            elif e.errcode == 401:
                print "Server authentication error."
                print e
                exit(1)
            else:
                print "Unknown XMLRPC error."
                print e
                exit(1)
        except xmlrpclib.Fault as e:
            if e.faultCode == 404 and e.faultString == \
                    "Job output not found.":
                pass
    return inner


class LavaConnection(object):
    def __init__(self, config):
        self.config = config
        self.connection = None


    @handle_connection
    def connect(self):
        url = self.construct_url()
        print "Connecting to Server with URL '%s'" % url

        self.connection = xmlrpclib.ServerProxy(url)
        # Here we make a call to ensure the connection has been made.
        self.connection.system.listMethods()
        print "Connection Successful."


    @handle_connection
    def get_job_status(self, job_id):
        return self.connection.scheduler.job_status(job_id)


    @handle_connection
    def get_job_details(self, job_id):
        return self.connection.scheduler.job_details(job_id)


    @handle_connection
    def get_job_output(self, job_id):
        return self.connection.scheduler.job_output(job_id)


    @handle_connection
    def cancel_job(self, job_id):
        return self.connection.scheduler.cancel_job(job_id)


    def has_enough_config(self):
        return (self.config.get('username') and
                self.config.get('token') and
                self.config.get('server'))


    def construct_url(self):
        if not self.has_enough_config():
            raise Exception("Not enough configuration to construct the URL")

        url = urlparse.urlparse(self.config.get('server'))

        if not url.path.endswith(('/RPC2', '/RPC2/')):
            print "LAVA Server URL must end with /RPC2 or /RPC2/"
            exit(1)

        return (url.scheme + '://' +
                self.config.get('username') + ':' +
                self.config.get('token') +
                '@' + url.netloc + url.path)


class LavaRunJob(object):
    def __init__(self, connection, job_id, poll_interval):
        self.END_STATES = ['Complete', 'Incomplete', 'Canceled']
        self.job_id = job_id
        self.connection = connection
        self.poll_interval = poll_interval or 2
        self.output = ""
        self.state = dict()
        self.details = dict()
        self.raw_details = dict()
        self.actions = list()
        self.last_poll_time = None
        self.next_poll_time = datetime.datetime.now()
        self._is_running = True


    def cancel_job(self):
        self.state = self.connection.cancel_job(self.job_id)


    def get_description(self):
        self._get_state()
        return self.details.get('description', '')


    def get_hostname(self):
        self._get_state()
        return self.details.get('hostname', '')


    def get_device_type_id(self):
        self._get_state()
        return self.details.get('device_type_id', '')


    def get_output(self):
        self._get_state()
        return self.output


    def is_running(self):
        self._get_state()
        return self._is_running


    def last_action(self):
        if not self.actions:
            return "-"
        return self.actions[-1]


    def all_actions(self):
        return self.actions


    def connect(self):
        self.connection.connect()


    def _get_state(self):
        if self._is_running and datetime.datetime.now() > self.next_poll_time:
            self.state = self.connection.get_job_status(self.job_id)
            self.raw_details = self.connection.get_job_details(self.job_id)
            self.output = self.connection.get_job_output(self.job_id)

            self.last_poll_time = self.next_poll_time
            self.next_poll_time = self.last_poll_time + datetime.timedelta(seconds=self.poll_interval)

            if not self.output:
                self.output = ""
            else:
                self.output = str(self.output)

            self._parse_output()
            self._parse_details()

            self._is_running = self.state['job_status'] not in self.END_STATES


    def _parse_details(self):
        description = self.raw_details.get('description', None)
        if description:
            self.details['description'] = description

        device_cache = self.raw_details.get('_actual_device_cache', None)
        if device_cache:
            hostname = device_cache.get('hostname', None)
            if hostname:
                self.details['hostname'] = hostname

            device_type_id = device_cache.get('device_type_id', None)
            if device_type_id:
                self.details['device_type_id'] = device_type_id


    def _parse_output(self):
        del self.actions[:]
        for line in self.output.splitlines():
            if 'ACTION-B' in line:
                self.actions.append(self._parse_actions(line))


    def _parse_actions(self, line):
        substr = line[line.find('ACTION-B')+len('ACTION-B')+2:]
        if substr.startswith('deploy_linaro_'):
            deployment_elems = list()
            re_elems = re.compile('u\'[a-z]+\'')
            for elem in re_elems.findall(substr):
                deployment_elems.append(elem[2:-1])
            return "deploy " + ','.join(deployment_elems)
        elif substr.startswith('lava_test_shell'):
            substr = substr[substr.find('testdef\': u')+len('testdef\': u')+1:]
            substr = substr[:substr.find('.yaml')]
            return "test_shell " + substr

        return "unknown (%s)" % substr[:substr.find(' ')]


def main(args):
    config = configuration.get_config(args)
    lava_connection = LavaConnection(config)

    lava_job = LavaRunJob(lava_connection,
                          config.get('job'),
                          2)
    lava_job.connect()

    if config.get("curses"):
        output_handler = CursesOutput(lava_job, config.get("interval"))
    else:
        output_handler = FileOutputHandler(sys.stdout, lava_job, config.get("interval"))

    output_handler.run()

    exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default", help="section in the LAVA config file")
    parser.add_argument("--username", help="username for the LAVA server")
    parser.add_argument("--token", help="token for LAVA server api")
    parser.add_argument("--server", help="server url for LAVA server")
    parser.add_argument("--job", help="job to fetch console log from")
    parser.add_argument("--curses", help="use curses for output", action="store_true")
    parser.add_argument("--interval", default=2, help="log polling interval")
    args = vars(parser.parse_args())
    main(args)

# vim: set sw=4 sts=4 et fileencoding=utf-8 :
