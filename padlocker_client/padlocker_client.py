#!/usr/bin/env python

import traceback
import httplib2
import getopt
import socket
import nltk
import stat
import json
import time
import sys
import pwd
import grp
import os
import re

from pid import *

DEFAULTS = {}

configf = './client.json'
debug = False

try:
    opts,args = getopt.getopt(sys.argv[1:], "hcd", ["help", "config=", "debug"])
except getopt.GetoptError as err:
    sys.stderr.write("%s\n" % (str(err), ))
    usage()
    sys.exit(2)
for o, a in opts:
    if o in ('-h', '--help') :
        usage()
        sys.exit(0)
    elif o in ('-c', '--config'):
        configf = a
    elif o in ('-d', '--debug'):
        debug = True
    else:
        assert False, "unhandled exception"

json_config = open(configf)

# Start with defaults; allow json config to override
config = dict(DEFAULTS, **json.load(json_config))

client = httplib2.Http()

def usage():
    print "usage: %s [--config=file.json] [--debug] [--help]" % os.path.basename(sys.argv[0])

def deboog(msg):
    if not debug:
        return

    first = u"\u2503"
    start = u"\u2523"
    depth = (len(traceback.extract_stack()) - 3)
    indent = depth * u"\u2501\u2501"
    end = u"\u257E"
    lmsg = re.sub(r"\n", "\n" + (" " * (13+depth)), msg)
    sys.stdout.write((u"%s % 5s %s%s%s %s\n" % (first, os.getpid(), start, indent, end, lmsg)).encode('utf8'))

def padlocker_post(url, data):
    """
    make a post request to the api_url with all relevant information
    
    params:

    - url: path under api_url to post to
    - data: JSONable data structure for post data

    returns:

    - tuple of status code and http body
    """
    full_url = "%s/%s" %(config["api_url"], url)

    while 1:
        deboog("POSTing %s to %s" % (json.dumps(data, indent=1), full_url))
        try:
            headers, resp = client.request(
                full_url,
                "POST",
                json.dumps(data),
                headers={'Content-type': 'application/json'}
            )
        except httplib2.HttpLib2Error as e:
            deboog("%s gave error %s" % (full_url, e))
            return ""
        except socket.error, msg:
            deboog("%s gave error %s" % (full_url, msg))
            return ""

        if headers.status < 500:
            return (headers.status, resp)
        else:
            deboog("%s gave error %s\n" % (full_url, headers.status))
            return(headers.status, nltk.clean_html(resp))

def checkfifo(path):
    """
    safely check/create the fifo
    """

    try:
        stat.S_ISFIFO(os.stat(path).st_mode)
    except:
        if os.path.isfile(path):
            sys.stderr.write("%s exists but isn't a fifo\n" % (path, ))
            sys.exit(1)
        else:
            try:
                deboog("making fifo at %s" % (path, ))
                os.mkfifo(path)
            except OSError, e:
                sys.stderr.write("can't create %s as a fifo: %s\n" % (path, e))
                sys.exit(1)

    return 1

def childmain(cn):
    """
    run a child

    tasks::

    - try to make a fifo at child_config["path"] if it isn't already one
    - detect read attempts on the fifo

      - collect information about the surrounding environment
      - make requests to the api_url with all known info
    """
    lconfig = config["keys"][cn]

    deboog("%s: %s" % (cn, lconfig))

    checkfifo(lconfig["path"])

    try:
        while 1:
            deboog("%s: waiting for %s" % (cn, lconfig["path"],))

            fd = os.open(lconfig["path"], os.O_ASYNC | os.O_WRONLY)

            deboog("%s: %s just went writeable" % (cn, lconfig["path"],))

            key = ""
            while key == "":
                fifo_stat = os.stat(lconfig['path'])
                lconfig['fifo_uid'] = fifo_stat.st_uid
                lconfig['fifo_gid'] = fifo_stat.st_gid
                lconfig['fifo_mode'] = stat.S_IMODE(fifo_stat.st_mode)
                lconfig['fifo_owner'] = pwd.getpwuid(lconfig['fifo_uid'])[0]
                lconfig['fifo_group'] = grp.getgrgid(lconfig['fifo_gid'])[0]
                lconfig['fifo_pids'] = fifo_pid_info(lconfig['path'])

                code, ret = padlocker_post('api/%s' % cn, lconfig)

                deboog("%s: got http %s" % (cn, code))
                if code == 200:
                    deboog("%s: got key from server" % cn)
                    key = ret
                elif code == 201:
                    deboog("%s: server asked us to come back soon" % cn)
                    time.sleep(5)
                elif 400 <= code < 500:
                    deboog("%s: server denied request for key" % cn)
                    key = "padlocker: server denied request for key %s\n" % cn
                else:
                    deboog("unknown status code, bailing")
                    break
                    
            if key != "":
                deboog("%s: feeding server response to fifo" % cn)
                os.write(fd, key)

            deboog("%s: closing fifo" % (cn, ))
            os.close(fd)
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        deboog("child exiting")
        sys.exit(1)
    
    sys.exit(0)


def main():

    # start a child for each config
    children = []

    for cn in config["keys"]:
        child = os.fork()
        if child:
            children.append(child)
            deboog("%s watcher forked as %s" % (cn, child))
        else:
            childmain(cn)
            sys.exit(0)

    for child in children:
            try:
                os.waitpid(child, 0)
            except (KeyboardInterrupt, SystemExit):
                deboog("parent exiting")
                sys.exit(1)

    deboog("all children died, exiting")

if __name__ == '__main__':
    main()
