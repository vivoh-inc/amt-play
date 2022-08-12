from x9k3.x9k3 import X9K3
import threading
from new_reader import reader

def _segmenter():
    print("Starting segmenter")
    x9k3 = X9K3("udp://127.0.0.1:3000")
    # print(x9k3)
    x9k3.live = True
    # x9k3._tsdata = reader()
    x9k3.output_dir = "files"
    x9k3.decode()

    # print(x9k3.live)
    # print(version())

def start_segmenter():
    x = threading.Thread(target=_segmenter)
    x.start()
    
