#!/usr/bin/env python

DEFAULTS = {}

configf = './uaks.json'
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
    full_url = "%s/%s" %(API_URL, url)
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

def main():
    print "nope"

if __name__ == '__main__':
    main()
