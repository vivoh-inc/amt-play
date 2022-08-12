Requires git, python3.6

# Running

```
git clone https://github.com/vivoh-inc/amt-play
cd amt-play
git submodule init
git submodule update
sudo pip3 install threefive
sudo pip3 install scapy
AMT_URL=xxx sudo python3 -E amt-play.py
open http://localhost:8080
```

Please determine your AMT_URL and change xxx to that.

(NB: You must provide the -E switch to sudo so that it pulls the AMT_URL into the root environment.)

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

AMT_URL=amt://232.162.250.138:1234?relay=162.250.137.254&timeout=2&source=162.250.138.201 \\
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

# Running Tests

Please run tests when working on the code, and add tests as much as possible.

```
python3 argument_parser_test.py 
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK

```
