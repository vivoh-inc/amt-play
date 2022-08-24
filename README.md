Requires git, python3.6

# Running

```
git clone https://github.com/vivoh-inc/amt-play
cd amt-play
git submodule init
git submodule update
sudo pip3 install threefive
sudo pip3 install scapy
AMT_URL="xxx" sudo python3 -E amt-play.py
open http://localhost:8080
```

Please determine your AMT_URL and change xxx to that. Make sure to wrap the AMT_URL value in quotes to prevent the shell
from interpreting ampersands as shell characters.

NB: You must provide the -E switch to sudo so that it pulls the AMT_URL into the root environment.)

You should see this:

```
$ AMT_URL="amt://232.162.250.138?relay=162.250.137.254&timeout=2&source=162.250.138.201" \
  sudo -E python3 amt-play.py 
  
Starting segmenter
Starting AMT tunnel: 162.250.137.254
Starting web server
Sending AMT relay discovery
Serving at port 8080
.
Sent 1 packets.
Sending AMT relay advertisement
.
Sent 1 packets.
Sending AMT multicast membership query
.
Sent 1 packets.
..................................................Finished printing packets
 files/seg0.ts  start:  229.433322      duration:  5.333334     stream diff:  -3.962531
 files/seg1.ts  start:  234.766656      duration:  2.533333     stream diff:  -4.02043
127.0.0.1 - - [12/Aug/2022 13:50:56] "GET /index.m3u8 HTTP/1.1" 200 -
127.0.0.1 - - [12/Aug/2022 13:50:57] "GET /seg32.ts HTTP/1.1" 200 -
127.0.0.1 - - [12/Aug/2022 13:50:57] "GET /seg33.ts HTTP/1.1" 200 -
127.0.0.1 - - [12/Aug/2022 13:50:57] "GET /seg34.ts HTTP/1.1" 200 -
```

This indicates the packets are coming from the tunnel (`......Finished printing packets`), the segmenter
has started (`files/seg0.ts  start:  229.433322      duration:  5.333334     stream diff:  -3.962531`) and
the web server is delivering to the browser (`127.0.0.1 - - [12/Aug/2022 13:50:56] "GET /index.m3u8 HTTP/1.1" 200 -`)


# Usage

```
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

AMT_URL="amt://232.162.250.138?relay=162.250.137.254&timeout=2&source=162.250.138.201" \\
    sudo -E python3 amt-play.py 

The query parameters should be:

* relay
* timeout (ignored for now)
* source

(you may pass a relay IP with the parameterized AMT_URL and that will
override the relay from the query string)
```

# Developer Notes

Start in amt-play.py. This has four functions: `parse_arguments`, `start_segmenter`, `start_amt_tunnel(relay, source, multicast)` and `start_web_server`. 

The `parse_arguments` code is straightforwar: we parse the arguments (the AMT_URL and AMT_RELAY variables). 

Each of the next set of functions starts a thread to handle functionality for the segmenter, amt tunnel and the web server.

The segmenter code relies on a fork of a project called [X9K3](https://github.com/futzu/x9k3) which converts UDP video packets into HLS streams and then dumps the index.m3u8 and TS files into a directory (currently hardcoded to "files"). 

The AMT tunnel code does the AMT dance: sending a relay discovery, sending the relay advertisement, and then
issuing the multicast join. If you use VLC (4.0+) with an AMT URL and watch traffic in Wireshark, you will see the equivalent
network calls recorded by Wireshark to what we do in code here. Once the AMT tunnel is created, the script loops
to receiving the packets and sends them to 127.0.0.1:3000 (and the segmenter picks them up and converts them).

The web code sets up a simple web server on 127.0.0.1:8080 to serve the index.html, JS and CSS files, and the m3u8 file
which points to TS files. The only thing special about the server code is that it disables caching so that when the
browser requests the m3u8 file it is always delivered with the latest content.

# To Do

- [ ] Refactor to handle ctrl-c correctly
- [ ] Correctly shutdown tunnel when exit event occurs

# Running Tests

Please run tests when working on the code, and add tests as much as possible.

```
python3 argument_parser_test.py 
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK

```
