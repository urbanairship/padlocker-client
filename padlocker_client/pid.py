#
#   Copyright 2013 Urban Airship
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import re

def pids_with_fifo(fifo):
    """
    find pids that have a fifo open

    params:
    
      - fifo: path to a fifo

    returns:

      - list of pids
    """
    pids = []
    for root, _, files in os.walk("/proc"):
        for f in files:
            if re.search(r"^/proc/\d+/fd$", root):
                try:
                    link = os.readlink("%s/%s" % (root, f))
                    if link == os.path.abspath(fifo):
                        pids.append(int(re.sub(r"/proc/(\d+)/fd$", r"\1", root)))
                except OSError:
                    continue
    return pids

def pid_cmdline(pid):
    """
    get the commandline of a running process

    params:

      - pid: pid of a running proc

    returns:

      - list of commandline elements
    """
    p = open("/proc/%s/cmdline" % pid)
    cmdline = p.readline()
    return cmdline

def fifo_pid_info(fifo):
    """
    get info for running processes that have a fifo open

    params:

      - fifo: path to a fifo

    returns:

      - hash of pid: cmdlines
    """
    info  = {}
    for pid in pids_with_fifo(fifo):
        if pid != os.getpid():
            info[pid] = pid_cmdline(pid).split('\0')[:-1]
    return info
