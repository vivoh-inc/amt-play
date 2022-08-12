from audioop import mul


def process_amt_url(amt, relay_tmp = None):
    multicast = ""
    source = ""
    relay = ""
    timeout = 1000

    if "?" in amt:
        # process with query parameters
        mpre, queries = amt.split("?")
        multicast = mpre.replace("amt://", "")
        qs = queries.split('&')
        for q in qs:
            k,v = q.split("=")
            if k == "source":
                source = v
            elif k == "multicast":
                multicast = v
            elif k == "timeout":
                timeout = v
            elif k == "relay":
                relay = v

    else:
        a, m = amt.split("@")
        source = a.replace("amt://", "")
        multicast = m
    
    if relay_tmp:
        relay = relay_tmp
        
    return [ relay, multicast, source, timeout] 
