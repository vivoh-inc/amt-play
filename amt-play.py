from amt import start_amt_tunnel
from web import start_web_server
from segmenter import start_segmenter
import time
import threading

# Valid AMT URLS are:

# amt://SOURCE_IP@GROUP_ADDD (hidden is the RELAY IP) a part of VLC configuration

# amt://162.250.138.201@232.162.250.138:1234 

# amt://<Group_ID>:<Port>?relay=<RELAY_ARRAY_VIA_COMMAS>&timeout=[INT_SEC]&source=<Source_IP>

# amt://232.162.250.140:_PORT_?relay=162.250.137.254&timeout=2&source=162.250.138.201

def usage():
    explanation="""

Legacy AMT URL:

sudo python3 amt-play.py legacy-AMT-URL relay-IP

example: 
sudo python3 amt-play.py amt://162.250.138.201@232.162.250.138:1234 162.250.137.254

Parameterized AMT URL:

sudo python3 amt-play.py parameterized-AMT-URL

example: 
sudo python3 amt-play.py amt://232.162.250.138:1234?relay=162.250.137.254&timeout=2&source=162.250.138.201
(you may pass a relay IP with the parameterized AMT URL it will override the relay from the query string)

"""
    print(explanation)

def parse_arguments():
    # usage()
    # raise "Bad arguments"
    print("Getting the arguments")

relay = "162.250.137.254"
multicast = '232.162.250.140'
source = "162.250.138.201"
    
def main():
    try:
        # parse_arguments()
        start_segmenter()
        time.sleep(1)
        event = threading.Event()
        amt_thread = start_amt_tunnel(relay, source, multicast, event)
        start_web_server()
    except KeyboardInterrupt:
        print("interrupted by keyboard!")
        event.set()

main()
