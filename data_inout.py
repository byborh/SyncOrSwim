import re
import os

from biosignal_analysis.datamanager import manager

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

''' DATATYPES '''
UNRECOGNIZED = -1
SPIKE2EVENTS =  0
PYBSAEVENTS  =  1
H5WAVEFORMS  =  2

EVENTS    = [SPIKE2EVENTS, PYBSAEVENTS]
WAVEFORMS = [H5WAVEFORMS]

def recognize(path):
    extension = os.path.splitext(path)[1]
    if extension == ".h5":
        return H5WAVEFORMS
    if extension == ".txt":
        with open(path) as f:
            lines = f.readlines()
            if lines[0].startswith('"CHANNEL"'):
                return SPIKE2EVENTS
            if lines[0].startswith('"Generated via Matlab."'):
                return SPIKE2EVENTS
            if lines[0].startswith('# SP detection timestamp list'):
                return PYBSAEVENTS
    return UNRECOGNIZED

def fromSpike2(path, verbose=True):
    timestamps = {}
    current_channel = ""
    regex_ch = re.compile(r'^"CHANNEL".*"(?P<channel>.*)"') # Channel Header
    regex_ts = re.compile(r'[+-]?[0-9]*[.]?[0-9]+')        # Timestamp line

    with open(path, 'r') as f:
        verbosePrint("Reading Spike2 timestamp file {}...".format(path), verbose)
        lines = f.readlines()
        for l in lines :
            CH = regex_ch.match(l)
            TS = regex_ts.match(l)
            if CH != None:
                verbosePrint("  Found channel {}".format(CH.group('channel')), verbose)
                current_channel = CH.group('channel')
                timestamps[current_channel] = []
            if TS != None:
                if current_channel != "":
                    timestamps[current_channel].append(float(TS.group()))

    return timestamps

def fromPyBiosignalAnalysis(path, verbose=True):
    timestamps = {}
    current_channel = ""
    regex_ch  = re.compile(r'^Channel.(?P<channel>.*) \(.*\)') # Channel Header
    regex_ts = re.compile(r'[+-]?[0-9]*[.]?[0-9]+')        # Timestamp line

    with open(path, 'r') as f:
        verbosePrint("Reading Spike2 timestamp file {}...".format(path), verbose)
        lines = f.readlines()
        for l in lines :
            CH = regex_ch.match(l)
            TS = regex_ts.match(l)
            if CH != None:
                verbosePrint("  Found channel {}".format(CH.group('channel')), verbose)
                current_channel = CH.group('channel')
                timestamps[current_channel] = []
            if TS != None:
                if current_channel != "":
                    timestamps[current_channel].append(float(TS.group()))

    return timestamps

def fromH5(path, import_parameters={}, verbose=True):
    datasource = manager.DataSource(path)
    datasource.setImportParameters(import_parameters)
    datasource.load()
    signals = {}
    for ch in datasource.getAllChannels():
        signal_idx = datasource.translateChannel(ch)
        signals[ch] = datasource.getSignal(signal_idx)
    datasource.unload()
    return signals


def generateTestEvents(T, Fs, family="static"):
    from random import randint
    timestamps = {}

    def tstrain(samples_max, period_samples, jitter_samples):
        train = []
        i = 0
        while i < samples_max:
            if i != 0:
                regex_ts = i + randint(-jitter_samples, jitter_samples)
                if (regex_ts > 0) and (regex_ts < samples_max):
                    train.append(regex_ts)
            i += period_samples
        return train

    N = int(T * Fs)
    if family == "static":
        regex_ch = 0
        ''' events at frequency F1 '''
        F1 = 0.7
        T1_s = 1./F1
        T1_samples = int(T1_s * Fs)
        for i in range(5):
            k = "CH{}".format(regex_ch)
            timestamps[k] = tstrain(N, T1_samples, int(i*T1_samples*0.05))
            regex_ch += 1
        ''' events at frequency F2 '''
        F2 = 0.2
        T2_s = 1./F2
        T2_samples = int(T2_s * Fs)
        for i in range(5):
            k = "CH{}".format(regex_ch)
            timestamps[k] = tstrain(N, T2_samples, int(i*T2_samples*0.05))
            regex_ch += 1

    if family == "spatial":
        regex_ch = 0
        ''' events at frequency F1 '''
        jitter_pc = 5
        F1 = 0.7
        T1_s = 1./F1
        T1_samples = int(T1_s * Fs)
        for i,label in enumerate(["D2", "E1", "E2", "F2", "F3"]):
            timestamps[label] = tstrain(N, T1_samples, int(T1_samples*jitter_pc/100.))
            regex_ch += 1
        ''' events at frequency F2 '''
        F2 = 0.2
        T2_s = 1./F2
        T2_samples = int(T2_s * Fs)
        for i,label in enumerate(["G5", "G6", "F6"]):
            timestamps[label] = tstrain(N, T2_samples, int(T1_samples*jitter_pc/100.))
            regex_ch += 1

    return timestamps


if __name__ == "__main__":
    print("================= Test Spike 2 =================")
    timestamps = fromSpike2("./Timestamps/correl 2nd phase.txt")
    print(timestamps)

    print("================= Test PyBiosignalAnalysis =================")
    timestamps = fromPyBiosignalAnalysis("../Data/Recon/Tests/Results/SP0.txt")
    print(timestamps)
