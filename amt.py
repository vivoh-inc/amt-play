"""
    Implementation of the AMT protocol (https://datatracker.ietf.org/doc/html/rfc7450)
    in Python. While AMT is designed to support both IPV4 and IPV6 traffic,
    as of Aug 2022 Scapy does not fully support IPV6. This implementation relies on Scapy.
"""

from ctypes import sizeof
import socket
import struct
import sys
from scapy.all import *
# import scapy.contrib.igmpv3
from unittest.mock import DEFAULT
from urllib import request
from scapy.contrib.igmpv3 import *
import secrets
import time
import threading

ttl = 2

################################################
# Various Lengths of Msgs or Hdrs
################################################
VERSION_LEN = 4            # length of version in packet
MSG_TYPE_LEN = 4           # length of msg type 

################################################
# Different AMT Message Types
################################################
AMT_RELAY_DISCO = 1        # relay discovery
AMT_RELAY_ADV = 2          # relay advertisement
AMT_REQUEST = 3            # request
AMT_MEM_QUERY = 4          # memebership query
AMT_MEM_UPD = 5            # membership update
AMT_MULT_DATA = 6          # multicast data
AMT_TEARDOWN = 7           # teardown (not currently supported)

MCAST_ANYCAST = "0.0.0.0"
MCAST_ALLHOSTS = "224.0.0.22"
LOCAL_LOOPBACK = "127.0.0.1"
AMT_PORT = 2268

DEFAULT_MTU = (1500 - (20 + 8))
# DEFAULT_MTU = 1600 # (1500 - (20 + 8))

class AMT_Discovery(Packet):
    name = "AMT_Discovery"
    fields_desc = [ 
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_RELAY_DISCO, MSG_TYPE_LEN),
        BitField("rsvd", 0, 24),
        XStrFixedLenField("nonce", 0, 4)
    ]

class AMT_Relay_Advertisement(Packet):
    name = "AMT_Relay_Advertisement"
    fields_desc = [
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_RELAY_ADV, MSG_TYPE_LEN),
        BitField("rsvd", 0, 24),
        XStrFixedLenField("nonce", 0, 4),
        IPField("relay_addr", MCAST_ANYCAST)
    ]
class AMT_Relay_Request(Packet):
    name = "AMT_Relay_Request"
    fields_desc = [ 
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_REQUEST, MSG_TYPE_LEN),
        BitField("rsvd1", 0, 7),
        BitField("p_flag", 0, 1),
        BitField("rsvd2", 0, 16),
        XStrFixedLenField("nonce", 0, 4)
    ]

"""
    A relay sends a Membership Query message to a gateway to solicit a
    Membership Update response, but only after receiving a Request
    message from the gateway.
"""
class AMT_Membership_Query(Packet):
    name = "AMT_Membership_Query"
    fields_desc = [
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_MEM_QUERY, MSG_TYPE_LEN),
        BitField("rsvd1", 0, 6),
        BitField("l_flag", 0, 1),
        BitField("g_flag", 0, 1),
        MACField("response_mac", 0),
        XStrFixedLenField("nonce", 0, 4),
        #encapsulated IGMPv3 or MLDv2, defaults to IGMP
        PacketListField("amt_ip", None, IP),
        PacketListField("amt_igmpv3", None, scapy.contrib.igmpv3.IGMPv3)
        # BitField("igmp_mld_type", 0x11, 8),
        # ConditionalField(BitField("igmp_max_resp_code", 0, 8), lambda pkt: pkt.igmp_mld_type == 0x11 ),
        # # ConditionalField(BitField("mld_code", 0, 0), lambda pkt: pkt.igmp_mld_type == 130),   #IPV6
        # XShortField("checksum", None),
        # ConditionalField(IPField("igmp_group_addr", MCAST_ANYCAST), lambda pkt: pkt.igmp_mld_type == 0x11),
        # # ConditionalField(BitField("mld_rsvd1", 0, 16), lambda pkt: pkt.igmp_mld_type == 130),     #IPV6
        # # ConditionalField(IP6Field("mld_addr", "::"), lambda pkt: pkt.igmp_mld_type == 130),       #IPV6
        # BitField("rsvd3", 0, 4),
        # BitField("s_flag", 0, 1),
        # BitField("qrv", 0, 3),
        # BitField("qqic", 0, 8),
        # IntField("num_of_srcs", 0),
        # ConditionalField(FieldListField("src_addrs", [], IPField("", MCAST_ANYCAST), count_from = lambda pkt: pkt.num_of_srcs), 
        #     lambda pkt: pkt.igmp_mld_type == 0x11),
        # # ConditionalField(FieldListField("src_addrs", [], IPField("", "::1"), count_from = lambda pkt: pkt.num_of_srcs), 
        # #     lambda pkt: pkt.igmp_mld_type == 130) #IPV6
    ]

"""
    A gateway sends a Membership Update message to a relay to report a
   change in group membership state, or to report the current group
   membership state in response to receiving a Membership Query message.
"""
class AMT_Membership_Update(Packet):
    name = "AMT_Membership_Update"

    fields_desc = [
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_MEM_UPD, MSG_TYPE_LEN),
        BitField("rsvd1", 0, 8),
        MACField("response_mac", 0),
        XStrFixedLenField("nonce", 0, 4),
        #encapsulated IGMPv3 or MLDv2, defaults to IGMP
        PacketListField("amt_igmpv3", None, scapy.contrib.igmpv3.IGMPv3)
        # ByteEnumField("igmp_mld_type", 0x16, igmptypes),
        # ConditionalField(BitField("igmp_max_resp_code", 0, 8), lambda pkt: pkt.igmp_mld_type == 0x11 ),
        # # ConditionalField(BitField("mld_code", 0, 0), lambda pkt: pkt.igmp_mld_type == 130), #IPV6
        # XShortField("checksum", None),
        # ConditionalField(IPField("igmp_group_addr", MCAST_ANYCAST), lambda pkt: pkt.igmp_mld_type == 0x11),
        # # ConditionalField(BitField("mld_rsvd1", 0, 16), lambda pkt: pkt.igmp_mld_type == 130), #IPV6
        # # ConditionalField(IP6Field("mld_addr", "::"), lambda pkt: pkt.igmp_mld_type == 130),   #IPV6
        # BitField("rsvd2", 0, 4),
        # BitField("s_flag", 0, 1),
        # BitField("qrv", 0, 3),
        # BitField("qqic", 0, 8),
        # IntField("num_of_srcs", 0),
        # ConditionalField(FieldListField("src_addrs", [], IPField("", MCAST_ANYCAST), count_from = lambda pkt: pkt.num_of_srcs), 
        #     lambda pkt: pkt.igmp_mld_type == 0x11),
        # # ConditionalField(FieldListField("src_addrs", [], IPField("", "::"), count_from = lambda pkt: pkt.num_of_srcs), 
        # #     lambda pkt: pkt.igmp_mld_type == 130) #IPV6
    ]

class AMT_Multicast_Data(Packet):
    name = "AMT_Multicast_Data"
    fields_desc = [
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_MULT_DATA, 4),
        BitField("rsvd", 0, 8),
        PacketListField("amt_ip", None, scapy.layers.inet.IP)
    ]

"""
    A gateway sends a Teardown message to a relay to request that it stop
    sending Multicast Data messages to a tunnel endpoint created by an
    earlier Membership Update message.
"""
class AMT_Teardown(Packet):
    name = "AMT_Teardown"
    fields_desc = [
        BitField("version", 0, VERSION_LEN),
        BitField("type", AMT_TEARDOWN, 4),
        BitField("rsvd", 0, 8),
        MACField("response_mac", 0),
        XStrFixedLenField("nonce", 0, 4),
        ShortField("gw_port_num", 0),
        IPField("gw_ip_addr", MCAST_ANYCAST)
    ]

def verbose(msg):
    if os.getenv('VERBOSE'):
        print(msg)
    
def send_data(buf):
    try: 
        amt_packet = AMT_Multicast_Data(buf)
        # verbose(amt_packet.show())
        raw_udp = bytes(amt_packet[UDP].payload)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        verbose(f"Packet Size: {len(raw_udp)}")
        sock.sendto(raw_udp, ("127.0.0.1", 3000))
        
    except Exception as err:
        print(f"Error occurred in processing packet {err}")

def amt_mem_update(nonce, response_mac, relay, source, multicast, join_leave):
    # ip_layer = IP(dst="162.250.137.254")
    ip_layer = IP(dst=relay)
    udp_layer = UDP(sport=AMT_PORT, dport=AMT_PORT)
    amt_layer = AMT_Membership_Update()
    amt_layer.setfieldval("nonce", nonce)
    amt_layer.setfieldval("response_mac", response_mac)
    options_pkt = Packet(b"\x00")       # add IP options to match working C implementation
    ip_layer2 = IP(src="0.0.0.0", dst="224.0.0.22", options=[options_pkt])
    igmp_layer = IGMPv3()
    igmp_layer.type = 34        # {17: 'Membership Query', 34: 'Version 3 Membership Report', 48: 'Multicast Router Advertisement', 49: 'Multicast Router Solicitation', 50: 'Multicast Router Termination'}

    # amt://162.250.138.201@232.162.250.140
    
    # {1: 'Mode Is Include', 2: 'Mode Is Exclude', 3: 'Change To Include Mode', 
    # 4: 'Change To Exclude Mode', 5: 'Allow New Sources', 6: 'Block Old Sources'}
    if join_leave is True:
        igmp_layer2 = IGMPv3mr(records=[IGMPv3gr(maddr=multicast, srcaddrs=[source], rtype=1)])
    else:
        igmp_layer2 = IGMPv3mr(records=[IGMPv3gr(maddr=multicast, srcaddrs=[source], rtype=6)])
   
    # igmp_layer2 = IGMPv3mr(records=[IGMPv3gr(maddr='232.162.250.140', srcaddrs=["162.250.138.201"])])    
    update = ip_layer / udp_layer / amt_layer / ip_layer2 / igmp_layer / igmp_layer2
    # verbose(update.show())
    return update

def setup_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(('', AMT_PORT))
    return s

def send_amt_relay_discovery(s, relay):
    print("Sending AMT relay discovery")

    # Get this IP by doing nslookup amt-relay.m2icast.net
    ip_top_layer = IP(dst=relay)        #relay addr
    # ip_top_layer = IP(dst="162.250.137.254")        #relay addr    
    # udp_rand_port = RandShort()
    # print(udp_rand_port)
    udp_top_layer = UDP(sport=AMT_PORT, dport=AMT_PORT)
    amt_layer = AMT_Discovery()    
    nonce = secrets.token_bytes(4)
    amt_layer.setfieldval("nonce", nonce)
    # bind_layers(UDP, AMT_Discovery, dport=AMT_PORT)
    packet =  ip_top_layer / udp_top_layer / amt_layer
    verbose(packet)

    # Send relay discovery message and wait for response
    p = send(packet)
    data, _ = s.recvfrom(DEFAULT_MTU)        # receive the membership query
    # print(data)
    return data, nonce

def send_amt_relay_advertisement(s, data, nonce, relay):
    print("Sending AMT relay advertisement")
    # print(data)
    relay_adv = AMT_Relay_Advertisement(data)
    verbose(relay_adv.fields) 
    relay_request = AMT_Relay_Request()
    relay_request.setfieldval("nonce", nonce)  # keep same nonce!
    ip_top_layer = IP(dst=relay) #relay addr
    udp_top_layer = UDP(sport=AMT_PORT, dport=AMT_PORT)
    amt_layer = AMT_Discovery()    
    packet =  ip_top_layer / udp_top_layer / relay_request
    p = send(packet)
    data, _ = s.recvfrom(DEFAULT_MTU)
    # print(data)
    return data

def send_amt_multicast_membership_query(s, data, nonce, relay, source, multicast):
    print("Sending AMT multicast membership query")
    membership_query = AMT_Membership_Query(data)
    response_mac = membership_query.response_mac
    mq = membership_query.getlayer(IGMPv3mq)
    # verbose(membership_query.show())
    # received the membership query, send a membership update
    # req = struct.pack("=4sl", socket.inet_aton("232.198.38.1"), socket.INADDR_ANY)
    req = struct.pack("=4sl", socket.inet_aton(multicast), socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    # s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 1)
    update = amt_mem_update(nonce, response_mac, relay, source, multicast, True)
    timer = threading.Timer(mq.qqic, send, args=update)
    timer.daemon = True
    timer.start()
    send(update)
    return update


def loop_for_data(s, event):
    count = 0
    notified = False
    while True:
        if event.is_set():
            return
        else:
            # receive the multicast data!
            data, addr = s.recvfrom(DEFAULT_MTU)        # receive the membership query
            send_data(data)
            if count < 50:
                print(".", flush=True, end="")
                count += 1
            else:
                if not notified:
                    print("Finished printing packets")
                    notified = True
                    
        # print(data)
        # s.close()

def _tunnel(event, relay, source, multicast):
    print("Starting AMT tunnel: " + relay)
    s = setup_socket()
    data, nonce = send_amt_relay_discovery(s, relay)
    data = send_amt_relay_advertisement(s, data, nonce, relay)
    update = send_amt_multicast_membership_query(s, data, nonce, relay, source, multicast)
    loop_for_data(s, event) 
    print("Finished with receiver loop, cleaning up")
    s.close()
    send(amt_mem_update(nonce, update.response_mac, relay, source, multicast, False))
               
def start_amt_tunnel(relay,
                     source,
                     multicast,
                     event,
                     timeout=1000):
    x = threading.Thread(target=_tunnel, args=(event, relay, source, multicast))
    x.start()
    return x
        

