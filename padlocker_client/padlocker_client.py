#!/usr/bin/env python

import httplib2
import getopt
import stat
import json
import time
import sys
import os
import re

DEFAULTS = {}

configf = './client.json'
debug = False

try:
    opts,args = getopt.getopt(sys.argv[1:], "hcd", ["help", "config=", "debug"])
except getopt.GetoptError as err:
    print str(err)
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

def padlocker_post(url, data):
    """make a post request to the api_url with all relevant information"""
    full_url = "%s/%s" %(config["api_url"], url)
    try:
        headers, resp = client.request(
            full_url,
            "POST",
            json.dumps(data),
            headers={'Content-type': 'application/x-www-form-urlencoded'}
        )
    except httplib2.HttpLib2Error as e:
        sys.exit(e)
    if headers.status == 200:
        return json.loads(resp)
    else:
        sys.stderr.write("%s gave error %s\n" % (full_url, headers.status))
        sys.stderr.write("input: %s\n" % json.dumps(data))
        sys.stderr.write("output: %s\n" % resp)
        return(resp, headers.status)

def checkfifo(path):
    """
    safely check/create the fifo
    """

    try:
        if not stat.S_ISFIFO(os.stat(path).st_mode):
            if os.path.isfile(path):
                sys.stderr.write("can't create %s as a fifo: %s\n" % (path, e))
                sys.exit(1)
        else:
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

    if debug: 
        print "    child: %s: %s" % (cn, lconfig)

    checkfifo(lconfig["path"])
    
    sys.exit(0)


def main():
    # start a child for each config
    children = []
    for cn in config["keys"]:
        if debug:
            print "forking child for %s" % cn
        child = os.fork()
        if child:
            children.append(child)
        else:
            childmain(cn)
            sys.exit(0)
    for child in children:
        os.waitpid(child, 0)
    if debug:
        print "all children died, exiting"

if __name__ == '__main__':
    main()
