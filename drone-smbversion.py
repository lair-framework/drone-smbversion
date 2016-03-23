#!/usr/bin/env python
"""drone-smbversion

Usage:
    drone-smbversion [options] <id> <file>
    drone-smbversion --version

Options:
    -h --help       Show usage.
    --version       Show version.
    -k              Allow insecure SSL connections.

"""
import os
from sys import exit
from urlparse import urlparse
from netaddr import IPAddress, AddrFormatError
from docopt import docopt
from pylair import models
from pylair import client


def main():
    arguments = docopt(__doc__, version='drone 1.0.0')
    lair_url = ''
    try:
        lair_url = os.environ['LAIR_API_SERVER']
    except KeyError:
        print "Fatal: Missing LAIR_API_SERVER environment variable"
        exit(1)

    u = urlparse(lair_url)
    if u.username is None or u.password is None:
        print "Fatal: Missing username and/or password"
        exit(1)

    project_id = arguments['<id>']
    project = dict(models.project)
    project['id'] = project_id
    project['commands'] = [{'command': 'smbversion', 'tool': 'smbversion'}]
    project['tool'] = 'drone-smbversion'

    opts = client.Options(u.username, u.password, u.hostname + ":" + str(u.port), project_id, scheme=u.scheme,
                          insecure_skip_verify=arguments['-k'])


    lines = []
    cidrs = set()
    try:
        lines = [line.rstrip('\n') for line in open(arguments['<file>'])]
    except IOError as e:
        print "Fatal: Could not open file. Error: {0}".format(e)
        exit(1)
    for line in lines:
        if 'name' in line:
            osver=""
            found=False
            for word in line.split(" "):
                if 'Windows' in word:
                    found = True
                if 'build' in word:
                    found = False
                if found == True:
                    osver = osver + word + " "

            entry = line.split(":")
            ip = entry[0].split(" ")
            hostname = entry[3].split(")")

            host = dict(models.host)
            host['projectId'] = project_id
            host['hostnames'] = hostname[0].split()
            host['ipv4'] = ip[1]
            host['os'] = {'tool': 'smb', 'weight': 100, 'fingerprint': osver}
            project['hosts'].append(host)

    res = client.import_project(project, opts)
    if res['status'] == 'Error':
        print "Fatal: " + res['message']
        exit(1)
    print "Success: Operation completed successfully"


if __name__ == '__main__':
    main()

