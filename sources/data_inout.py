import re
import os
import pathlib
import pandas as pd
import progressbar

from datamanager import manager

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

''' DATATYPES '''
UNRECOGNIZED  = -1
SPIKE2EVENTS  =  0
PYBSAEVENTS   =  1
H5WAVEFORMS   =  2
RHDWAVEFORMS  =  3
BINWAVEFORMS  =  4

EVENTS    = [SPIKE2EVENTS, PYBSAEVENTS]
WAVEFORMS = [H5WAVEFORMS, RHDWAVEFORMS, BINWAVEFORMS]

class Timestamps:
    def __init__(self, timestamps, Fs):
        self.data = timestamps
        self.Fs   = Fs

class Waveforms:
    def __init__(self, waveforms, Fs):
        self.data = waveforms
        self.Fs   = Fs


def recognize(path):
    extension = os.path.splitext(path)[1]
    if extension == ".rhd":
        return RHDWAVEFORMS
    if extension == ".h5":
        return H5WAVEFORMS
    if extension == ".txt":
        with open(path) as f:
            lines = f.readlines()
            if lines[0].startswith('"CHANNEL"'):
                return SPIKE2EVENTS
            if lines[0].startswith('"INFORMATION"'):
                return SPIKE2EVENTS
            if lines[0].startswith('"Generated via Matlab."'):
                return SPIKE2EVENTS
            if lines[0].startswith('# SP detection timestamp list'):
                return PYBSAEVENTS
            if lines[0].startswith('# AP detection timestamp list'):
                return PYBSAEVENTS
    if extension == ".bin":
        return BINWAVEFORMS
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
        verbosePrint("Reading pyBiosignalAnalysis timestamp file {}...".format(path), verbose)
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
    channels = datasource.getChannels()
    for i,ch in enumerate(channels):
        signals[ch] = datasource.getSignal(ch)
        progressbar.inlineCycles(i, len(channels), prefix="Loading MCS H5 data")
    Fs = datasource.getFs()
    datasource.unload()
    return signals, Fs

def fromRHD(path, import_parameters={}, verbose=True):
    datasource = manager.DataSource(path)
    datasource.setImportParameters(import_parameters)
    datasource.load()
    signals = {}
    Ndiscarded = 0
    channels = datasource.getChannels()
    for ch in channels:
        signal = datasource.getSignal(ch)
        if len(signal) > 1:
            signals[ch] = signal
        else:
            Ndiscarded += 1
    if Ndiscarded > 0:
        verbosePrint(f"Warning : discarded {Ndiscarded} channels because {'it has' if Ndiscarded == 1 else 'they have'} length 1.", verbose)
    Fs = datasource.getFs()
    datasource.unload()
    return signals, Fs

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
def fromBIN(path, import_parameters={}, verbose=True):
    datasource = manager.DataSource(path)
    datasource.setImportParameters(import_parameters)
    datasource.load()
    signals = {}
    channels = datasource.getChannels()
    for i,ch in enumerate(channels):
        signals[ch] = datasource.getSignal(ch)
        progressbar.inlineCycles(i, len(channels), prefix="Loading BIN data")
    Fs = datasource.getFs()
    datasource.unload()
    return signals, Fs

def exportCSV(path="example.csv", vectors=([1,2,3],[0.1,0.2,0.3]), labels=("Time", "Data"), separator=";"):
    directory = os.path.dirname(path)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    if len(vectors) < 1:
        return False
    if len(vectors) != len(labels):
        return False
    def line_format(elements):
        return ((('{}' + separator + ' ') * N).format(*elements))[:-2] # '{}, {}, ', apply format with elements of tuple "labels", remove last ', '
    with open(path, "w+") as fid:
        N = len(vectors)

        ''' Write header '''
        header = line_format(labels)
        fid.write(header + "\n")

        ''' Write data '''
        M = len(vectors[0])
        for j in range(M):
            data_line = [vectors[i][j] for i in range(N)]
            line = line_format(data_line)
            fid.write(line + "\n")
    return True

def df2xlsx(df, title, destination):
    directory = os.path.dirname(destination)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(destination) as writer:
        sheet_name = "Sheet"
        df.to_excel(writer, sheet_name=sheet_name, startrow=2)
        worksheet = writer.sheets[sheet_name]
        worksheet.write_string(0, 0, title)

def df2xlsx_multisheet(dfs, sheet_names, titles, destination, analyzer=None):
    directory = os.path.dirname(destination)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(destination) as writer:
        if analyzer != None:
            info   = pd.DataFrame({'Software version': [str(analyzer.version)], 'input file': [str(analyzer.file)], 'Fs (Hz)': [str(analyzer.Fs)]})
            params = pd.DataFrame({p: [str(analyzer.parameters[p])] for p in analyzer.parameters})
            info.transpose().to_excel(writer  , sheet_name="Information")
            params.transpose().to_excel(writer, sheet_name="Parameters" )
        for df,sheet_name,title in zip(dfs,sheet_names,titles):
            df.to_excel(writer, sheet_name=sheet_name, startrow=2)
            worksheet = writer.sheets[sheet_name]
            worksheet.write_string(0, 0, title)

def linkage2df(linkage_matrix, channels):
    N = linkage_matrix.shape[0] + 1
    cluster_names = [f"C{i}" for i in range(N-1)]
    column_names  = ["Channel or Cluster A", "Channel or Cluster B", "Distance", "# of observations in the cluster"]
    df     = pd.DataFrame(linkage_matrix, columns=column_names, index=cluster_names)
    df_out = pd.DataFrame({column_names[0]: pd.Series(['']*(N-1), dtype='str'),
                           column_names[1]: pd.Series(['']*(N-1), dtype='str'),
                           column_names[2]: pd.Series([ 0]*(N-1), dtype='float'),
                           column_names[3]: pd.Series([ 0]*(N-1), dtype='int')},
                           index=cluster_names,
                           columns=column_names)
    ''' Channel names in two first columns '''
    for j in range(2):
        for i in range(N-1):
            row = cluster_names[i]
            col = column_names[j]
            value = df.loc[row,col]
            newvalue = channels[int(value)] if value < N else cluster_names[int(value)-N]
            df_out.at[row, col] =  newvalue
    ''' Distance in third column '''
    for i in range(N-1):
        df_out.iat[i,2] = df.iloc[i,2]
    ''' Number of observations in cluster in fourth column '''
    for i in range(N-1):
        df_out.iat[i,3] = df.iloc[i,3]
    return df_out

if __name__ == "__main__":
    def test_fromSpike2():
        timestamps = fromSpike2("./test_data/test_Spike2.txt")
        expected_response = {'m1':[1.1,2.2,3.3],'m2':[],'m3':[0.01],'m4':[2.2222,4.4444,6.6666,8.8888],'m5':[]}
        assert timestamps == expected_response, f"FromSpike2 : Expected {expected_response} (got {timestamps})"
    def test_fromPBA():
        timestamps = fromPyBiosignalAnalysis("./test_data/test_PBA.txt")
        expected_response = {'D2':[],'H3':[1.1,2.2,3.3],'F6':[0.01],'D8':[2.2222,4.4444,6.6666,8.8888],'D5':[],'F3':[]}
        assert timestamps == expected_response, f"fromPyBiosignalAnalysis : Expected {expected_response} (got {timestamps})"
    test_fromSpike2()
    test_fromPBA()

    print("All passed")

    import processing
    timestamps = fromPyBiosignalAnalysis("./test_data/test_PBA.txt")
    print(processing.resample_timestamps(timestamps, 1., 100.) == processing.s2idx(timestamps, 100.))
