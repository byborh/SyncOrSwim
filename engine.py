import processing
import representations
import data_inout
import json
from Hardware import MEAs
from Hardware import recipients
from Hardware import setups

from biosignal_analysis.analyses import processing as signalprocessing
import numpy as np

from matplotlib import pyplot as plt

class CorrelationDataframe:
    def printFs(self, msg = ""):
        print(msg + (" " if msg else "") + f".Fs : {self.Fs} / .Fs_raw : {self.Fs_raw} / .parameters['processing_Fs'] : {self.parameters['processing_Fs']}")
    def printWaveforms(self, msg=""):
        print(msg + (" " if msg else "") + f".waveforms : len={[len(self.waveforms[k]) for k in self.waveforms][0]} / .waveforms_raw : {[len(self.waveforms_raw[k]) for k in self.waveforms_raw][0]}")
    def __init__(self):
        self.Fs = None
        self.file = None
        ''' Parameters '''
        self.autobake = True
        self.parameters = {}
        self.parameters["normalize"] = {"enable": False}
        self.parameters["RMS"] = {"enable": False, "window_s": 15.}
        self.parameters["GLR"] = {"enable": False, "distribution": "normal", "reference_region_s":(0,300)}
        self.parameters["time_range_s"] = None
        self.parameters["evt_tolerance_s"] = 0.5
        self.parameters["correlation_tolerance"] = 0.4
        self.parameters["rolling_window_s"] = 30.
        self.parameters["channel_filters"] = []
        self.parameters["filters"] = {"family": "BPfilters", "args": {"hp": [[0.2, 1]], "lp": [[2.0, 2]], "filtertype": "bessel"}}
        self.parameters["processing_Fs"] = 100.
        self.parameters["MEA_layout"] = 'MEA_60HexaMEA_40_10'
        self.parameters["hub_reference"] = None
        self.parameters["environment"] = None
        ''' Initialize data '''
        self.resetTimestampData()
        self.resetWaveformData()
        self.resetProcessedData()
    def _onBakeFinish(self, *args, **kwarks):
        pass
    def resetProcessedData(self):
        self.resetCorrelationData()
        self.resetTimeshiftData()
        self.resetClusteringData()
        self.resetRollingCorrelationData()
        self.resetRollingTimeshiftData()
    def resetTimestampData(self):
        self.timestamps_raw = None
        self.timestamps = None
        self.Fs_raw = None
    def resetWaveformData(self):
        self.waveforms_raw = None
        self.waveforms = None
    def resetCorrelationData(self):
        self.correlation_data = None
        self.granger_data = None
    def resetTimeshiftData(self):
        self.timeshift_data = None
        self.order_data = None
    def resetRollingCorrelationData(self):
        self.rolling_correlation_data = None
    def resetRollingTimeshiftData(self):
        self.rolling_timeshift_data = None
        self.rolling_order_data = None
        self.order_stats = None
    def resetClusteringData(self):
        self.clusters = None
        self.linkage  = None

    def loadFile(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        if datatype in data_inout.EVENTS:
            self.loadTimestamps(path, **kwargs)
            self.file = path
        if datatype in data_inout.WAVEFORMS:
            self.loadWaveforms(path, **kwargs)
            self.file = path
        if datatype == -1:
            print("Unrecognized data type")
    def loadTimestamps(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        import_methods = {}
        import_methods[data_inout.SPIKE2EVENTS] = data_inout.fromSpike2
        import_methods[data_inout.PYBSAEVENTS ] = data_inout.fromPyBiosignalAnalysis
        ''' Check input file type and load it '''
        timestamps_s = import_methods[datatype](path, **kwargs)
        ''' Clean timestamps '''
        timestamps_s = processing.clean_timestamps(timestamps_s)
        ''' Convert to indexes and store '''
        timestamps_i = processing.resample_timestamps(timestamps_s, fs_origin=1., fs_destination=self.parameters["processing_Fs"])
        self.timestamps_raw = processing.deepcopy_data(timestamps_i)
        self.timestamps     = processing.deepcopy_data(timestamps_i)
        self.Fs = self.parameters["processing_Fs"]
    def loadWaveforms(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        import_methods = {}
        import_methods[data_inout.H5WAVEFORMS]  = data_inout.fromH5
        import_methods[data_inout.RHDWAVEFORMS] = data_inout.fromRHD
        ''' Check input file type and load it '''
        waveforms, Fs = import_methods[datatype](path, **kwargs)
        self.waveforms_raw = processing.deepcopy_data(waveforms)
        self.waveforms     = processing.deepcopy_data(waveforms)
        self.Fs = Fs if Fs else float(input("What was the sampling frequency ? I can't tell yet."))
        self.Fs_raw = 1. * self.Fs

    def preprocessWaveforms(self):
        if self.timestamps_raw:
            ''' Timestamp data is loaded, so we are working with generated sigals; no need for waveforms_raw and filtering '''
            ''' Filter channels '''
            channels = self.parameters["channel_filters"] if self.parameters["channel_filters"] else self.waveforms.keys()
            waveforms = processing.filter_channels(self.waveforms, channels)
            ''' RMS filter '''
            if self.parameters["RMS"]["enable"]:
                window_rms_samples = int(self.Fs * self.parameters["RMS"]["window_s"])
                self.waveforms = processing.rolling_RMS(self.waveforms, window_samples=window_rms_samples)
        else:
            """ Here we are at native Fs (self.Fs_raw) """
            ''' Filter channels '''
            channels = self.parameters["channel_filters"] if self.parameters["channel_filters"] else self.waveforms_raw.keys()
            waveforms = processing.filter_channels(self.waveforms_raw, channels)
            ''' Apply digital filters '''
            self.parameters["filters"]["args"]["Fs"] = self.Fs_raw
            filters = signalprocessing.generate_filter(self.parameters["filters"])
            waveforms = processing.map_to_dict(filters.run, waveforms, progress_message='Filtering')
            ''' RMS filter '''
            if self.parameters["RMS"]["enable"]:
                window_rms_samples = int(self.Fs_raw * self.parameters["RMS"]["window_s"])
                waveforms = processing.rolling_RMS(waveforms, window_samples=window_rms_samples)
            ''' Time range '''
            if self.parameters["time_range_s"]:
                T0 = self.parameters["time_range_s"][0]
                T1 = self.parameters["time_range_s"][1]
                i0 = int(T0 * self.Fs_raw)
                i1 = int(T1 * self.Fs_raw)
                waveforms_cropped = processing.crop_waveforms(waveforms, (i0,i1))
            else:
                waveforms_cropped = waveforms
            ''' Time range for GLR reference '''
            if self.parameters["GLR"]["enable"]:
                R0 = self.parameters["GLR"]["reference_region_s"][0]
                R1 = self.parameters["GLR"]["reference_region_s"][1]
                r0 = int(R0 * self.Fs_raw)
                r1 = int(R1 * self.Fs_raw)
                waveforms_reference = processing.crop_waveforms(waveforms, (r0,r1))
            ''' GLR filter '''
            if self.parameters["GLR"]["enable"]:
                mle_results       = processing.map_to_dict(processing.MLE, waveforms_reference, distribution=self.parameters["GLR"]["distribution"], progress_message="MLE")
                waveforms_cropped = {k: processing.LRT(waveforms_cropped[k], distribution=self.parameters["GLR"]["distribution"], distribution_parameters=mle_results[k].x) for k in waveforms_cropped}
            ''' Normalization '''
            if self.parameters["normalize"]["enable"]:
                if self.parameters["RMS"]["enable"]:
                    waveforms_cropped = processing.percentile_superimposition(waveforms_cropped, keys=waveforms, min_pc=5, max_pc=95)
                else:
                    waveforms_cropped = processing.percentile_superimposition(waveforms_cropped, keys=waveforms, max_pc=95)
            ''' Assign '''
            self.waveforms = waveforms_cropped
            ''' Resampling '''
            if self.Fs_raw != self.parameters["processing_Fs"]:
                self.waveforms = processing.fast_downsample_waveforms(self.waveforms, fs_origin=self.Fs_raw, fs_destination=self.parameters["processing_Fs"])
                self.Fs = self.parameters["processing_Fs"]
                """ Now we are at true Fs (self.Fs = self.parameters["processing_Fs"]) """
    def preprocessTimestamps(self):
        ''' Filter channels '''
        channels = self.parameters["channel_filters"] if self.parameters["channel_filters"] else self.timestamps_raw.keys()
        timestamps = processing.filter_channels(self.timestamps_raw, channels)
        ''' Resample timestamps '''
        timestamps = processing.resample_timestamps(timestamps, self.Fs, self.parameters["processing_Fs"])
        self.timestamps = timestamps
        self.Fs = self.parameters["processing_Fs"]
        ''' Time range '''
        if self.parameters["time_range_s"]:
            T0 = self.parameters["time_range_s"][0]
            T1 = self.parameters["time_range_s"][1]
            self.timestamps = processing.crop_timestamps(self.timestamps, (T0,T1))

    def bakeWaveforms(self):
        ''' Check input data '''
        needed_data = [self.timestamps]
        messages    = ["No timestamp data loaded."]
        bakers      = None
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        evt_tolerance_i = int(self.parameters["evt_tolerance_s"] * self.Fs)
        self.preprocessTimestamps()
        self.waveforms = processing.eventWaveforms(self.timestamps, evt_tolerance_i)
        self._onBakeFinish()
        return True
    def bakeCorrelation(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute Pearson correlation matrix '''
        self.preprocessWaveforms()
        correlation_data = processing.correlationMatrix(self.waveforms)
        self.correlation_data = correlation_data
        self._onBakeFinish()
        return True
    def bakeGranger(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute Pearson correlation matrix '''
        self.preprocessWaveforms()
        granger_data = processing.granger_causality_matrix(self.waveforms)
        self.granger_data = granger_data
        self._onBakeFinish()
        return True
    def bakeTimeshift(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute time shift matrix '''
        self.preprocessWaveforms()
        timeshift_data = processing.timeshiftMatrix(self.waveforms)
        self.timeshift_data = timeshift_data
        self._onBakeFinish()
        return True
    def bakeOrder(self):
        ''' Check input data '''
        needed_data = [self.timeshift_data]
        messages    = ["Timeshift data not baked."]
        bakers      = [self.bakeTimeshift]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute order vector '''
        self.preprocessWaveforms()
        order_data = processing.timeshiftOrder(self.timeshift_data.matrix, reference=self.parameters["hub_reference"])
        self.order_data = order_data
        self._onBakeFinish()
        return True
    def bakeActivationOrder(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute activation '''
        pass
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
        self._onBakeFinish()
        return True
    def bakeRollingCorrelation(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveform data loaded."]
        bakers      = None
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        self.preprocessWaveforms()
        window_samples = int(self.Fs * self.parameters["rolling_window_s"])
        overlap_percent = 75.
        overlap_samples = int(window_samples * overlap_percent/100.)
        rolling_correlation = processing.rollingCorrelation(self.waveforms, window_samples=window_samples, overlap_samples=overlap_samples)
        self.rolling_correlation_data = rolling_correlation
        self._onBakeFinish()
        return True
    def bakeRollingTimeshift(self):
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveform data loaded."]
        bakers      = None
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        self.preprocessWaveforms()
        window_samples = int(self.Fs * self.parameters["rolling_window_s"])
        overlap_percent = 75.
        overlap_samples = int(window_samples * overlap_percent/100.)
        rolling_timeshift = processing.rollingTimeshift(self.waveforms, window_samples=window_samples, overlap_samples=overlap_samples)
        self.rolling_timeshift_data = rolling_timeshift
        self._onBakeFinish()
        return True
    def bakeRollingOrder(self):
        ''' Check input data '''
        needed_data = [self.rolling_timeshift_data]
        messages    = ["Rolling timeshift not baked."]
        bakers      = [self.bakeRollingTimeshift]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        self.preprocessWaveforms()
        rolling_order = processing.rollingOrder(self.rolling_timeshift_data, reference=self.parameters["hub_reference"])
        self.rolling_order_data = rolling_order
        self.order_stats = processing.order_matrix(rolling_order)
        self._onBakeFinish()
        return True
    def exportRollingOrder(self, destination=None):
        if not(self.rolling_order_data):
            print("No data found")
            return False
        order_stats = self.order_stats
        datasets = []; sheet_names = []; titles = []
        datasets.append(order_stats.percentage)                  ; sheet_names.append("percentage"); titles.append("Fraction of time at rank #i (%)")
        datasets.append(1000. * order_stats.dt / self.Fs)        ; sheet_names.append("dt_avg")    ; titles.append("Average lag behind leader (ms)")
        datasets.append(1000. * order_stats.dt_std / self.Fs)    ; sheet_names.append("dt_std")    ; titles.append("STD lag behind leader (ms)")
        datasets.append(order_stats.N)                           ; sheet_names.append("N")         ; titles.append(f"Number of times at rank #i (out of {order_stats.Ntotal} total)")
        destination = (self.file + '.order_stats.xlsx') if destination is None else destination
        data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
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
    def __repr__(self):
        string = "=== CORRELATION DATAFRAME SUMMARY ===\n"
        ''' Timestamp data description '''
        if self.timestamps is None:
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
        ''' Rolling timeshift data '''
        if self.rolling_timeshift_data is None:
            string += "Rolling timeshift not baked.\n"
        else:
            channels = self.parameters["channel_filters"] if self.parameters["channel_filters"] else self.waveforms.keys()
            string += "Rolling timeshift data :\n"
            for k1 in channels:
                for k2 in channels:
                    if k1 == k2:
                        continue
                    data = [rtd.matrix[k1][k2] for rtd in self.rolling_timeshift_data]
                    avg = np.mean(data) / self.parameters["processing_Fs"]
                    std = np.std(data) / self.parameters["processing_Fs"]
                    string += f"  {k1} - {k2} : {avg:>10.4f} +/- {std:>10.4f} ms\n"
        ''' Rolling order data '''
        if self.rolling_order_data is None:
            string += "Rolling order not baked.\n"
        else:
            string += "Rolling order data :\n"
            order_stats = processing.order_matrix(self.rolling_order_data)
            string += "  Percentage at each rank (xcorr) : \n"
            header_format = "{:^5} " + "{:^7} "  *len(order_stats.percentage.columns) + "\n"
            line0_format   = "{:^5} " + "{:6.2f}% "*len(order_stats.percentage.columns) + "\n"
            string += header_format.format("", *order_stats.percentage.columns)
            for rank in order_stats.percentage.index:
                line0 = [order_stats.percentage[c][rank] for c in order_stats.percentage.columns]
                string += line0_format.format(rank, *line0)
            header_format = "{:^5} " + "{:^7} "  *len(order_stats.percentage.columns) + "\n"

            string += "\n  Average timeshift for each rank (xcorr, relative to identified first) : \n"
            header_format = "{:^5} " + "{:^11} "  *len(order_stats.percentage.columns) + "\n"
            string += header_format.format("", *order_stats.percentage.columns)
            for rank in order_stats.percentage.index:
                line1_txt = ["{:^5} ".format(rank)] + ["{:+8.2f} ms ".format(1000.*order_stats.dt[c][rank]/self.Fs)                            if (order_stats.N[c][rank] > 0)  else "{:^11} ".format("") for c in order_stats.dt.columns] + ["\n"]
                line2_txt = ["{:^5} ".format("")  ] + [     "{:^11} ".format("(±{:.2f} ms)".format(1000.*order_stats.dt_std[c][rank]/self.Fs)) if (order_stats.N[c][rank] > 0)  else "{:^11} ".format("") for c in order_stats.dt.columns] + ["\n"]
                line3_txt = ["{:^5} ".format("")  ] + [     "{:^11} ".format("(N={:.0f})".format(order_stats.N[c][rank]))                      if (order_stats.N[c][rank] > 0)  else "{:^11} ".format("") for c in order_stats.dt.columns] + ["\n"]
                string += ''.join(line1_txt)
                string += ''.join(line2_txt)
                string += ''.join(line3_txt)
        return string
    """ Plots """
    def drawCorrelation(self):
        if self.correlation_data:
            representations.drawCorrelation(self.correlation_data.matrix, title='Correlation matrix')
        if self.timestamps and self.clusters: # self.clusters is generated at the same time as self.linkage
            representations.drawClusteredEvents(self.timestamps, self.linkage)
        if self.granger_data:
            representations.drawCorrelation(self.granger_data.matrix, title='Granger causality matrix', bounds=(None,None))
        if self.correlation_data and self.clusters:
            representations.drawDendrogram(self.correlation_data.matrix, self.linkage)
        plt.show()
    def drawRollingCorrelation(self):
        representations.animate_rollingCorrelation(self.rolling_correlation_data, self.waveforms, Fs=self.Fs)

    def drawRollingTimeshift(self):
        MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
        # if self.rolling_timeshift_data and self.waveforms:
        #     representations.animate_rollingTimeshift(self.rolling_timeshift_data, self.waveforms, Fs=self.Fs)
        # if self.rolling_timeshift_data and self.waveforms:
        #     representations.animate_rollingTimeshiftSpatial(self.rolling_timeshift_data, MEA_layout, self.waveforms, Fs=self.Fs)
        if self.rolling_order_data and self.waveforms:
            representations.animate_rollingOrderSpatial(self.rolling_order_data, self.rolling_timeshift_data, MEA_layout, self.waveforms, Fs=self.Fs, speed=False, env=self.parameters['environment'])
    def drawRollingOrderStats(self):
        if self.order_stats:
            representations.drawOrderBargraph(self.order_stats, timeinfo=True, Fs=self.parameters["processing_Fs"])
            representations.drawOrderPie(self.order_stats, self.parameters["MEA_layout"], timeinfo=False, Fs=self.parameters["processing_Fs"])
    def drawTimeshift(self):
        MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
        representations.drawTimeshiftSpatial(self.timeshift_data.matrix, MEA_layout, Fs=self.Fs)
        plt.show()
    ''' Parameter handling '''
    def importParameters(self, path):
        with open(path, 'r') as fid:
            json_string = fid.read()
            parameters = json.loads(json_string)
            self.loadParameters(parameters)
    def exportParameters(self, path):
        with open(path, 'w') as fid:
            json_string = self.stringifyParameters()
            fid.write(json_string)
    def stringifyParameters(self, pretty=True):
        if pretty:
            return json.dumps(self.parameters, sort_keys=True, indent=2, separators=(',', ': '))
        else:
            return json.dumps(self.parameters)
    def loadParameters(self, parameters):
        """ parameters is a dictionary """
        for k in parameters:
            self.parameters[k] = parameters[k]


if __name__ == "__main__":
    def test_paramImportExport():
        """ Tests 4 methods at a time : """
        """   - importParameters """
        """   - exportParameters """
        """   - stringifyParameters """
        """   - loadParameters """
        ENG = CorrelationDataframe()
        path = './test_data/test_Params.json'
        default_parameters = {k: ENG.parameters[k] for k in ENG.parameters}
        ENG.exportParameters(path)
        ENG.parameters = {}
        ENG.importParameters(path)
        imported_parameters = json.loads(json.dumps(ENG.parameters))
        assert default_parameters == imported_parameters, f"Parameter import/export : expected {default_parameters} (got {imported_parameters})"
        print("Parameter import/export passed.")
    def test_fromSpike2():
        ENG = CorrelationDataframe()
        ENG.parameters["processing_Fs"] = 100.
        ENG.loadFile("./test_data/test_Spike2.txt")
        expected_timestamps = {'m1':[110,220,330],'m3':[1],'m4':[222,444,666,888]}
        assert ENG.timestamps == expected_timestamps, f"loadTimestamps : Expected {expected_timestamps} (got {ENG.timestamps})"
        print("Spike2 import passed.")
    def test_fromPBA():
        ENG = CorrelationDataframe()
        ENG.parameters["processing_Fs"] = 100.
        ENG.loadFile("./test_data/test_PBA.txt")
        expected_timestamps = {'H3':[110,220,330],'F6':[1],'D8':[222,444,666,888]}
        assert ENG.timestamps == expected_timestamps, f"loadTimestamps : Expected {expected_timestamps} (got {ENG.timestamps})"
        print("PBA import passed.")
    test_paramImportExport()
    test_fromSpike2()
    test_fromPBA()
    print("All passed.")
