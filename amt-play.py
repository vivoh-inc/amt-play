from amt import start_amt_tunnel
from web import start_web_server
from segmenter import start_segmenter
import time
import sys
import os
from argparser import process_amt_url

# Valid AMT URLS are:

# amt://SOURCE_IP@GROUP_ADDD (hidden is the RELAY IP) a part of VLC configuration

# amt://162.250.138.201@232.162.250.138:1234 

# amt://<Group_ID>:<Port>?relay=<RELAY_ARRAY_VIA_COMMAS>&timeout=[INT_SEC]&source=<Source_IP>

# amt://232.162.250.140:_PORT_?relay=162.250.137.254&timeout=2&source=162.250.138.201

def usage():
    explanation="""
You must provide an environment variable named AMT_URL. 

You can optionally use AMT_RELAY to provide a relay URL. 

AMT_URL supports two formats:
  a legacy URL (like that used in VLC)
  a parameterized URL (with URL query parameters)

Legacy AMT URL:

AMT_URL=amt://162.250.138.201@232.162.250.138:1234 \\
    AMT_RELAY=162.250.137.254 \\
    sudo -E python3 amt-play.py

Parameterized AMT URL:

AMT_URL=amt://232.162.250.138:1234?relay=162.250.137.254&timeout=2&source=162.250.138.201 \\
    sudo -E python3 amt-play.py 

The query parameters should be:

* relay
* timeout (ignored for now)
* source

(you may pass a relay IP with the parameterized AMT_URL and that will
override the relay from the query string)

"""
    print(explanation)

relay = "162.250.137.254"
multicast = '232.162.250.140'
source = "162.250.138.201"


def parse_arguments():
    amt = os.getenv('AMT_URL')
    if not amt:
        usage()
        sys.exit(1)
    else:
        relay_tmp = os.getenv('AMT_RELAY')
        r, m, s, t = process_amt_url(amt, relay_tmp)
        return r, m, s, t

def main():
    relay, multicast, source, _timeout = parse_arguments()
    start_segmenter()
    time.sleep(1)
    start_amt_tunnel(relay, source, multicast)
    start_web_server()

main()
