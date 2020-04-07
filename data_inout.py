import re

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

def fromSpike2(path, verbose=True):
    timestamps = {}
    current_channel = ""
    ch = re.compile(r'^"CHANNEL".*"(?P<channel>.*?)"') # Channel Header
    ts = re.compile(r'[+-]?([0-9]*[.])?[0-9]+')        # Timestamp line

    with open(path, 'r') as f:
        verbosePrint("Reading Spike2 timestamp file {}...".format(path), verbose)
        lines = f.readlines()
        for l in lines :
            CH = ch.match(l)
            TS = ts.match(l)
            if CH != None:
                verbosePrint("  Found channel {}".format(CH.group('channel')), verbose)
                current_channel = CH.group('channel')
                timestamps[current_channel] = []
            if TS != None:
                if current_channel != "":
                    timestamps[current_channel].append(float(TS.group()))

    return timestamps

if __name__ == "__main__":
    timestamps = fromTxt("./Timestamps/correl 2nd phase.txt")
    print(timestamps)
