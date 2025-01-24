#!/usr/bin/python3
import sys
import getopt
import getpass
import requests
import json
import time
import os
import keyring
from datetime import datetime, timezone
from dateutil import tz
import urllib3
urllib3.disable_warnings()
import pprint
pp = pprint.PrettyPrinter(indent=4)

def usage():
    sys.stderr.write("Usage: q_capacity_dump.py [-hD] [-c creds] [-t token] [-f token_file [-o output_file] -s start [-e end] -i inverval [-u unit] qumulo\n")
    sys.stderr.write('-h | --help: Prints usage\n')
    sys.stderr.write("-D | --DEBUG : Generated info for debugging\n")
    sys.stderr.write("-c | --creds : Specify credentials format is user[:password]\n")
    sys.stderr.write("-t | --token : Specify an access token\n")
    sys.stderr.write("-f | --token-file : Specify is token file [def: .qfds_cred]\n")
    sys.stderr.write("-s | -- start : Specify start time period. Format: YY-MM-DD[THH:MM]\n")
    sys.stderr.write("-e | --end : Specify end time.  Format YY-MM-DD[THH:MM].  Default is current time\n")
    sys.stderr.write("-i | --interval: Specify a time interval [hourly, daily, weekly]\n")
    sys.stderr.write('-u | --unit : Specify a unit of size in the report. [kb, mb, gb, tb, pb] [def: bytes]\n')
    sys.stderr.write("-o | --output-file : Specify an output file for the report [def: stdout]\n")
    sys.stderr.write("qumulo : Name or IP of a Qumulo node\n")
    exit(0)

def dprint(message):
    if DEBUG:
        dfh = open('debug.out', 'a')
        dfh.write(message + "\n")
        dfh.close()

def oprint(fp, message):
    if fp:
        fp.write(message + '\n')
    else:
        print(message)
    return
def api_login(qumulo, user, password, token):
    in_keyring = True
    headers = {'Content-Type': 'application/json'}
    if not token:
        if not user:
            user = input("User: ")
        if not password:
            password = keyring.get_password(RING_SYSTEM, user)
        if not password:
            in_keyring = False
            password = getpass.getpass("Password: ")
        payload = {'username': user, 'password': password}
        payload = json.dumps(payload)
        autht = requests.post('https://' + qumulo + '/api/v1/session/login', headers=headers, data=payload,
                              verify=False, timeout=timeout)
        dprint(str(autht.ok))
        auth = json.loads(autht.content.decode('utf-8'))
        dprint(str(auth))
        if autht.ok:
            auth_headers = {'accept': 'application/json', 'Content-type': 'application/json', 'Authorization': 'Bearer ' + auth['bearer_token']}
            if not in_keyring:
                use_ring = input("Put these credentials into keyring? [y/n]: ")
                if use_ring.startswith('y') or use_ring.startswith('Y'):
                    keyring.set_password(RING_SYSTEM, user, password)
        else:
            sys.stderr.write("ERROR: " + auth['description'] + '\n')
            exit(2)
    else:
        auth_headers = {'accept': 'application/json', 'Content-type': 'application/json', 'Authorization': 'Bearer ' + token}
    dprint("AUTH_HEADERS: " + str(auth_headers))
    return(auth_headers)

def qumulo_get(addr, api):
    dprint("API_GET: " + api)
    good = False
    while not good:
        good = True
        try:
            res = requests.get('https://' + addr + '/api' + api, headers=auth, verify=False, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("Connection Error: Retrying..")
            time.sleep(5)
            good = False
            continue
        if res.content == b'':
            print("NULL RESULT[GET]: retrying..")
            good = False
            time.sleep(5)
    if res.status_code == 200:
        dprint("RESULTS: " + str(res.content))
        results = json.loads(res.content.decode('utf-8'))
        return(results)
    elif res.status_code == 404:
        return("404")
    else:
        sys.stderr.write("API ERROR: " + str(res.status_code) + "\n")
        sys.stderr.write(str(res.content) + "\n")
        exit(3)

def get_token_from_file(file):
    with open(file, 'r') as fp:
        tf = fp.read().strip()
    fp.close()
    t_data = json.loads(tf)
    dprint(t_data['bearer_token'])
    return(t_data['bearer_token'])

def convert_from_bytes(bytes, unit):
    if unit == '':
        return(bytes)
    if unit == 'k':
        return(int(bytes/1000))
    if unit == 'm':
        return(int(bytes/1000/1000))
    if unit == 'g':
        return(int(bytes/1000/1000/1000))
    if unit == 't':
        return(int(bytes/1000/1000/1000/1000))
    if unit == 'p':
        return(int(bytes/1000/1000/1000/1000/1000))
    sys.stderr.write("Unsupported unit: " + unit + ".  Supported: kb, mb, gb, tb, pb\n")
    exit(2)

def convert_from_localtime(time_s):
    c_time = time_s.split('.')
    if 'T' in c_time[0]:
        cts = datetime.strptime(c_time[0], "%Y-%m-%dT%H:%M")
    else:
        cts = datetime.strptime(c_time[0], '%Y-%m-%d')
    cts_utc = str(int(cts.astimezone(timezone.utc).timestamp()))
    return(cts_utc)

def convert_to_localtime(unix_time):
    cts = datetime.fromtimestamp(unix_time)
    cts = cts.replace(tzinfo=utc_tz)
    cts_local = cts.astimezone(local_tz)
    if DATE_ONLY:
        return(datetime.strftime(cts_local, '%Y-%m-%d'))
    else:
        return (datetime.strftime(cts_local, '%Y-%m-%d %H:%M'))

if __name__ == "__main__":
    DEBUG = False
    VERBOSE = False
    default_token_file = ".qfsd_cred"
    timeout = 30
    token_file = ""
    token = ""
    user = ""
    password = ""
    qumulo = ""
    RING_SYSTEM = "q_capacity_dump"
    fp = ""
    outfile = ""
    unit = ''
    ofp = ""
    local_tz = tz.tzlocal()
    utc_tz = tz.tzutc()
    start = ""
    start_utc = ""
    end = ""
    end_utc = ""
    interval = ""
    DATE_ONLY = True

    optlist, args = getopt.getopt(sys.argv[1:], 'hDc:t:f:o:s:e:i:u:', ['help', 'DEBUG', 'creds=', 'token=', 'token-file=',
                                                'output-file=', 'start=', 'end=', 'interval=', 'unit='])
    for opt, a in optlist:
        if opt in ['-h,', '--help']:
            usage()
        if opt in ['-D', '--DEBUG']:
            DEBUG = True
        if opt in ['t', '--token']:
            token = a
        if opt in ['-c', '--creds']:
            if ':' in a:
                (user, password) = a.split(':')
            else:
                user = a
        if opt in ('-f', '--token-file'):
            token_file = a
        if opt in ('-o', '--output-file'):
            outfile = a
        if opt in ('-s', '--start'):
            start = a
            if 'T' in start:
                DATE_ONLY = False
            start_utc = convert_from_localtime(a)
        if opt in ('-e', '--end'):
            end = a
            end_utc = convert_from_localtime(a)
        if opt in ('-i', '--interval'):
            interval = a.lower()
            if interval not in ['hourly', 'weekly', 'daily']:
                usage()
        if opt in ('-u', '--unit'):
            unit = a[0].lower()

    try:
        qumulo = args.pop(0)
    except:
        usage()
    if not start or not interval:
        sys.stderr.write("start and interval are required\n")
        usage()
    if not user and not token:
        if not token_file:
            token_file = default_token_file
        if os.path.isfile(token_file):
            token = get_token_from_file(token_file)
    auth = api_login(qumulo, user, password, token)
    dprint(str(auth))
    url = '/v1/analytics/capacity-history/?begin-time=' + start_utc + '&interval=' + interval
    if end_utc:
        url = url + "&end-time=" + end_utc
    cap_data = qumulo_get(qumulo, url)
    if outfile:
        ofp = open(outfile, "w")
    oprint(ofp, 'Date:,Total Usable:,Capacity Used:,Data Used:,Metadata Used,Snapshot Used:')
    for cd in cap_data:
        total_usable = str(convert_from_bytes(int(cd['total_usable']), unit))
        capacity_used = str(convert_from_bytes(int(cd['capacity_used']), unit))
        data_used = str(convert_from_bytes(int(cd['data_used']), unit))
        metadata_used = str(convert_from_bytes(int(cd['metadata_used']), unit))
        snapshot_used = str(convert_from_bytes(int(cd['snapshot_used']), unit))
        oprint(ofp, str(convert_to_localtime(cd['period_start_time'])) + ',' + total_usable + ',' +
               capacity_used + ',' + data_used + ',' + metadata_used + ',' + snapshot_used)
    if outfile:
        ofp.close()



