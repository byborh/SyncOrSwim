import processing
import representations
import data_inout

class CorrelationDataframe:
    def __init__(self):
        self.Fs = 100
        ''' Parameters '''
        self.autobake = True
        self.parameters = {}
        self.parameters["evt_tolerance_s"] = 0.5
        self.parameters["correlation_tolerance"] = 0.4
        self.parameters["window_s"] = 60.
        ''' Initialize data '''
        self.resetTimestampData()
        self.resetWaveformData()
        self.resetCorrelationData()
        self.resetClusteringData()
        self.resetRollingCorrelationData()
    def resetTimestampData(self):
        self.timestamps_s = None
        self.timestamps   = None
    def resetWaveformData(self):
        self.waveforms = None
    def resetCorrelationData(self):
        self.correlation_data = None
    def resetRollingCorrelationData(self):
        self.rolling_correlation_data = None
    def resetClusteringData(self):
        self.clusters = None
        self.linkage  = None
    def loadFile(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        if datatype in data_inout.EVENTS:
            self.loadTimestamps(path, **kwargs)
        if datatype in data_inout.WAVEFORMS:
            self.loadWaveforms(path, **kwargs)
        if datatype == -1:
            print("Unrecognized data type")
    def loadTimestamps(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        import_methods = {}
        import_methods[data_inout.SPIKE2EVENTS] = data_inout.fromSpike2
        import_methods[data_inout.PYBSAEVENTS ] = data_inout.fromPyBiosignalAnalysis
        ''' Check input file type and load it '''
        timestamps_s = import_methods[datatype](path, **kwargs)
        ''' Clean timestamps and store '''
        timestamps_s = processing.clean_timestamps(timestamps_s)
        self.timestamps_s = timestamps_s
        ''' Convert to indexes and store '''
        timestamps_i = processing.s2idx(timestamps_s, self.Fs)
        self.timestamps = timestamps_i
    def loadWaveforms(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        import_methods = {}
        import_methods[data_inout.H5WAVEFORMS] = data_inout.fromH5
        ''' Check input file type and load it '''
        waveforms = import_methods[datatype](path, **kwargs)
        self.waveforms = waveforms
    def bakeWaveforms(self):
        ''' Check input data '''
        needed_data = [self.timestamps]
        messages    = ["No timestamp data loaded."]
        bakers      = None
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        self.waveforms = processing.eventWaveforms(self.timestamps)
    def bakeCorrelation(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute Pearson correlation matrix '''
        correlation_data = processing.correlationMatrix(self.waveforms)
        self.correlation_data = correlation_data
        return True
    def checkDependencies(self, data, message, baker=None):
        output = True
        if baker is None:
            baker = [None for _ in data]
        for d,m,b in zip(data, message, baker):
            if not(d):
                print("Unsatisfied dependency : {}".format(m))
                if self.autobake:
                    print("  Attempting autobaking ...")
                    if not(b):
                        print("  No baker found. Could not proceed.")
                        output = False
                    else:
                        if b():
                            print("  Autobaking succeeded.")
                        else:
                            print("  Autobaking failed.")
                            output = False
                else:
                    print("Could not proceed.")
                    output = False
        return output
    def bakeClustering(self):
        ''' Check input data '''
        needed_data = [self.correlation_data]
        messages    = ["Correlation data not baked."]
        bakers      = [self.bakeCorrelation]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Bake clustering '''
        corr_tolerance = self.parameters["correlation_tolerance"]
        clustering = processing.getClustering(self.correlation_data.matrix, tolerance=corr_tolerance)
        self.clusters = clustering.clusters
        self.linkage  = clustering.linkage
        return True
    def bakeRollingCorrelation(self):
        ''' Check input data '''
        needed_data = [self.timestamps]
        messages    = ["No timestamp data loaded."]
        bakers      = None
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        window_samples = int(self.Fs * self.parameters["window_s"])
        rolling_correlation = processing.rollingCorrelation(self.waveforms, window_samples=window_samples, overlap_percent=50)
        self.rolling_correlation_data = rolling_correlation
        return True
    def __repr__(self):
        string = "=== CORRELATION DATAFRAME SUMMARY ===\n"
        ''' Timestamp data description '''
        if self.timestamps_s is None:
            string += "No timestamp data loaded.\n"
        else:
            string += "Timestamp data :\n"
            for ch in self.timestamps:
                string += "  - {} : {} timestamps\n".format(ch, len(self.timestamps[ch]))
        string += "\n"
        ''' Correlation data '''
        if self.correlation_data is None:
            string += "Correlation not baked.\n"
        else:
            string += "Correlation data :\n"
            for l in str(self.correlation_data.matrix).splitlines():
                string += ("  " + l + "\n")
        string += "\n"
        ''' Clustering data '''
        if self.linkage is None:
            string += "Clustering not baked.\n"
        else:
            string += "Identified clusters :\n"
            for c in self.clusters:
                string += "  - " + ", ".join(c) + "\n"
            string += "Linkage :\n"
            for l in str(self.linkage).splitlines():
                string += ("  " + l + "\n")
        string += "\n"
        ''' Rolling correlation data '''
        if self.rolling_correlation_data is None:
            string += "Rolling correlation not baked.\n"
        else:
            string += "Rolling correlation baked.\n"

        return string


if __name__ == "__main__":
    CDF = CorrelationDataframe()
    # CDF.loadFile("./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt")
    CDF.loadFile("../Data/20160120/h5/G8 late 6680-6980 s.h5", import_parameters={"analog_stream_idx": 1})
    CDF.bakeCorrelation()
    CDF.bakeClustering()
    CDF.bakeRollingCorrelation()
    print(CDF)
