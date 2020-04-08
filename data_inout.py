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

def generateTestEvents(T, Fs, family="static"):
    from random import randint
    timestamps = {}

    def tstrain(samples_max, period_samples, jitter_samples):
        train = []
        i = 0
        while i < samples_max:
            if i != 0:
                ts = i + randint(-jitter_samples, jitter_samples)
                if (ts > 0) and (ts < samples_max):
                    train.append(ts)
            i += period_samples
        return train

    N = int(T * Fs)
    if family == "static":
        ch = 0
        ''' events at frequency F1 '''
        F1 = 0.7
        T1_s = 1./F1
        T1_samples = int(T1_s * Fs)
        for i in range(5):
            k = "CH{}".format(ch)
            timestamps[k] = tstrain(N, T1_samples, int(i*T1_samples*0.05))
            ch += 1
        ''' events at frequency F2 '''
        F2 = 0.2
        T2_s = 1./F2
        T2_samples = int(T2_s * Fs)
        for i in range(5):
            k = "CH{}".format(ch)
            timestamps[k] = tstrain(N, T2_samples, int(i*T2_samples*0.05))
            ch += 1

    if family == "spatial":
        ch = 0
        ''' events at frequency F1 '''
        jitter_pc = 5
        F1 = 0.7
        T1_s = 1./F1
        T1_samples = int(T1_s * Fs)
        for i,label in enumerate(["D2", "E1", "E2", "F2", "F3"]):
            timestamps[label] = tstrain(N, T1_samples, int(T1_samples*jitter_pc/100.))
            ch += 1
        ''' events at frequency F2 '''
        F2 = 0.2
        T2_s = 1./F2
        T2_samples = int(T2_s * Fs)
        for i,label in enumerate(["G5", "G6", "F6"]):
            timestamps[label] = tstrain(N, T2_samples, int(T1_samples*jitter_pc/100.))
            ch += 1

    return timestamps


if __name__ == "__main__":
    timestamps = fromTxt("./Timestamps/correl 2nd phase.txt")
    print(timestamps)
