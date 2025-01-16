import processing
import representations
import data_inout
import colprint
import json
from Hardware import MEAs
from version import __version__, __version_info__

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt

PLOTS = {}
PLOTS["CORRELATIONMATRIX"]             =  0
PLOTS["CLUSTEREDEVENTS"]               =  1
PLOTS["GRANGERCAUSALITYMATRIX"]        =  2
PLOTS["DENDROGRAM"]                    =  3
PLOTS["PHASE"]                         =  4
PLOTS["ROLLINGCORRELATION"]            =  5
PLOTS["ROLLINGPHASE"]                  =  6
PLOTS["ROLLINGPHASESPATIAL"]           =  7
PLOTS["ROLLINGPHASESPATIALSTATIC"]     =  8
PLOTS["ROLLINGORDERSPATIAL"]           =  9
PLOTS["ROLLINGORDERBAR"]               = 10
PLOTS["ROLLINGORDERPIE"]               = 11
PLOTS["CLUSTERSSPATIAL"]               = 12
PLOTS["CORRELATIONSPATIAL"]            = 13
PLOTS["ROLLINGORDERTEMPORAL"]          = 14

EXPORTS = {}
EXPORTS["CORRELATIONMATRIX"]      = 0
EXPORTS["GRANGERCAUSALITYMATRIX"] = 1
EXPORTS["DENDROGRAM"]             = 2
EXPORTS["PHASE"]                  = 3
EXPORTS["ORDER"]                  = 4
EXPORTS["CLUSTERING"]             = 5
EXPORTS["ROLLINGCORRELATION"]     = 6
EXPORTS["ROLLINGPHASE"]           = 7
EXPORTS["ROLLINGORDER"]           = 8

TIMESTAMP_DATATYPES = [data_inout.SPIKE2EVENTS, data_inout.PYBSAEVENTS]
WAVEFORM_DATATYPES  = [data_inout.H5WAVEFORMS, data_inout.RHDWAVEFORMS, data_inout.BINWAVEFORMS]

MSG_EXPORT_FAILED = "Export is not ready"


def prompt_fs():
    """ User interaction - can be overloaded depending on working environment """
    return float(input("What was the sampling frequency ? I can't tell yet."))

class CorrelationDataframe:
    def printFs(self, msg = ""):
        print(msg + (" " if msg else "") + f".Fs : {self.Fs} / .Fs_raw : {self.Fs_raw} / .parameters['processing_Fs'] : {self.parameters['processing_Fs']}")
    def printWaveforms(self, msg=""):
        print(msg + (" " if msg else "") + f".waveforms : len={[len(self.waveforms[k]) for k in self.waveforms][0]} / .waveforms_raw : {[len(self.waveforms_raw[k]) for k in self.waveforms_raw][0]}")
    def __init__(self):
        self.Fs = None
        self.file = None
        self.datatype = None
        self.version = __version__
        ''' Parameters '''
        self.autobake = True
        self.parameters = {}
        self.parameters["normalize"] = {"enable": False}
        self.parameters["RMS"] = {"enable": False, "window_s": 15.}
        self.parameters["GLR"] = {"enable": False, "distribution": "normal", "reference_region_s":(0,300)}
        self.parameters["time_range_s"] = None
        self.parameters["evt_tolerance_s"] = 0.5
        self.parameters["correlation_tolerance"] = None
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
    def _checkBackwardsCompatibility(self):
        ''' RMS parameters '''
        if (type(self.parameters["RMS"]) is not dict) and ("RMS_window_s" in self.parameters):
            self.parameters["RMS"] = {"enable": self.parameters["RMS"], "window_s": self.parameters["RMS_window_s"]}
            del self.parameters["RMS_window_s"]
    def _onBakeFinish(self, *args, **kwarks):
        pass
    def resetProcessedData(self):
        self.resetCorrelationData()
        self.resetPhaseData()
        self.resetClusteringData()
        self.resetRollingCorrelationData()
        self.resetRollingPhaseData()
    def resetTimestampData(self):
        self.timestamps_raw = None
        self.timestamps = None
        self.Fs_raw = None
        self.duration_s = None
    def resetWaveformData(self):
        self.waveforms_raw = None
        self.waveforms = None
        self.Fs_raw = None
        self.duration_s = None
    def resetCorrelationData(self):
        self.correlation_data = None
        self.granger_data = None
    def resetPhaseData(self):
        self.phase_data = None
        self.order_data = None
    def resetRollingCorrelationData(self):
        self.rolling_correlation_data = None
    def resetRollingPhaseData(self):
        self.rolling_phase_data = None
        self.rolling_order_data = None
        self.order_stats = None
        self.leader_periods = None
    def resetClusteringData(self):
        self.clustering_data = None
        self.clusters = None # legacy; todo : remove me
        self.linkage  = None # legacy; todo : remove me

    def loadFile(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        if datatype in data_inout.EVENTS:
            self.loadTimestamps(path, **kwargs)
            self.file = path
        if datatype in data_inout.WAVEFORMS:
            self.loadWaveforms(path, **kwargs)
            self.file = path
        if datatype == -1:
            colprint.printerr("Unrecognized data type")
        self.datatype = datatype
        return datatype
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
        self.duration_s = max([max(timestamps_i[k]) for k in timestamps_i]) / self.parameters["processing_Fs"]
    def loadWaveforms(self, path, *args, **kwargs):
        datatype = data_inout.recognize(path)
        import_methods = {}
        import_methods[data_inout.H5WAVEFORMS]  = data_inout.fromH5
        import_methods[data_inout.RHDWAVEFORMS] = data_inout.fromRHD
        import_methods[data_inout.BINWAVEFORMS] = data_inout.fromBIN
        ''' Check input file type and load it '''
        waveforms, Fs = import_methods[datatype](path, **kwargs)
        self.waveforms_raw = processing.deepcopy_data(waveforms)
        self.waveforms     = processing.deepcopy_data(waveforms)
        self.Fs = Fs if Fs else prompt_fs()
        self.Fs_raw = 1. * self.Fs
        self.duration_s = max([len(self.waveforms_raw[k]) for k in self.waveforms_raw]) / self.Fs_raw

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
            filters = processing.generate_filter(self.parameters["filters"])
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
        self._checkBackwardsCompatibility()
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
        self._checkBackwardsCompatibility()
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
    def exportCorrelation(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["CORRELATIONMATRIX"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : correlation matrix '''
            datasets = []; sheet_names = []; titles = []
            datasets.append(self.correlation_data.matrix); sheet_names.append("matrix"); titles.append("Correlation matrix")
            destination = (self.file + '.correlation_matrix.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".correlation_matrix.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
        return True
    def bakeGranger(self):
        self._checkBackwardsCompatibility()
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
    def exportGranger(self, destination=None, which=-1):
        pass
    def bakePhase(self):
        self._checkBackwardsCompatibility()
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute time shift matrix '''
        self.preprocessWaveforms()
        phase_data = processing.phaseMatrix(self.waveforms)
        self.phase_data = phase_data
        self._onBakeFinish()
        return True
    def exportPhase(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["PHASE"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : phase data '''
            datasets = []; sheet_names = []; titles = []
            datasets.append(self.phase_data.matrix)      ; sheet_names.append("dt matrix"); titles.append("Computed dt matrix")
            datasets.append(self.phase_data.correlation) ; sheet_names.append("Correlation"); titles.append("Correlation matrix of re-aligned signals")
            destination = (self.file + '.phase.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".phase.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
        return True
    def bakeOrder(self):
        self._checkBackwardsCompatibility()
        ''' Check input data '''
        needed_data = [self.phase_data]
        messages    = ["Phase data not baked."]
        bakers      = [self.bakePhase]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute order vector '''
        self.preprocessWaveforms()
        order_data = processing.phaseOrder(self.phase_data.matrix, reference=self.parameters["hub_reference"])
        self.order_data = order_data
        self._onBakeFinish()
        return True
    def exportOrder(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["ORDER"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : order data '''
            datasets = []; sheet_names = []; titles = []
            datasets.append(self.order_data.series)            ; sheet_names.append("series")   ; titles.append("Phase vector sorted")
            datasets.append(pd.Series(self.order_data.order))  ; sheet_names.append("order")    ; titles.append("Order")
            datasets.append(pd.Series(self.order_data.values)) ; sheet_names.append("phase"); titles.append("Phase values")
            destination = (self.file + '.order.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".order.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
        return True
    def bakeActivationOrder(self):
        self._checkBackwardsCompatibility()
        ''' Check input data '''
        needed_data = [self.waveforms]
        messages    = ["No waveforms loaded or waveforms not baked."]
        bakers      = [self.bakeWaveforms]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Compute activation '''
        pass
    def exportActivationOrder(self, destination=None, which=-1):
        pass
    def bakeClustering(self):
        self._checkBackwardsCompatibility()
        ''' Check input data '''
        needed_data = [self.correlation_data]
        messages    = ["Correlation data not baked."]
        bakers      = [self.bakeCorrelation]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        ''' Bake clustering '''
        corr_tolerance = self.parameters["correlation_tolerance"]
        clustering = processing.getClustering(self.correlation_data.matrix, tolerance=corr_tolerance)
        self.clustering_data = clustering
        self.clusters = clustering.clusters # legacy; todo: remove me
        self.linkage  = clustering.linkage  # legacy; todo: remove me
        self._onBakeFinish()
        return True
    def exportClustering(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["CLUSTERING"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : clustering data '''
            datasets = []; sheet_names = []; titles = []
            datasets.append(pd.Series(self.clustering_data.clusters))                                          ; sheet_names.append("clusters")   ; titles.append("List of clusters")
            datasets.append(data_inout.linkage2df(self.clustering_data.linkage, self.clustering_data.labels))  ; sheet_names.append("linkage")    ; titles.append("Linkage")
            destination = (self.file + '.clustering.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".clustering.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
        return True
    def bakeRollingCorrelation(self):
        self._checkBackwardsCompatibility()
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
    def exportRollingCorrelation(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["ROLLINGCORRELATION"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : correlation for all couples '''
            N = len(self.rolling_correlation_data)
            channels = self.rolling_correlation_data[0].matrix.columns
            stacked_data = np.stack([instant.matrix.to_numpy() for instant in self.rolling_correlation_data])
            windows_samples = [instant.interval for instant in self.rolling_correlation_data]
            windows_s = [(interval[0]/self.parameters["processing_Fs"], interval[1]/self.parameters["processing_Fs"]) for interval in windows_samples]
            windows = [f"{interval[0]:.2f}-{interval[1]:.2f} s" for interval in windows_s]
            channel_couples = [f"{ch1}-{ch2}" for i,ch1 in enumerate(channels) for j,ch2 in enumerate(channels) if i>j]
            data = pd.DataFrame(data=None, index=windows, columns=channel_couples)
            for i,ch1 in enumerate(channels):
                for j,ch2 in enumerate(channels):
                    if i>j:
                        data[f"{ch1}-{ch2}"] = stacked_data[:,i,j]
            destination = (self.file + '.rolling_correlation.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".rolling_correlation.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx(data, "Rolling Correlation", destination)
        return True


    def bakeRollingPhase(self):
        self._checkBackwardsCompatibility()
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
        rolling_phase = processing.rollingPhase(self.waveforms, window_samples=window_samples, overlap_samples=overlap_samples)
        self.rolling_phase_data = rolling_phase
        self._onBakeFinish()
        return True
    def exportRollingPhase(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["ROLLINGPHASE"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        if which in [-1, 0]:
            ''' which=0 : all phase data (all windows)'''
            W = len(self.rolling_phase_data)
            datasets = []; sheet_names = []; titles = []
            # Data sheets
            datasets.append(pd.DataFrame({'Phase': [f"Phase {i+1}-{W}" for i in range(W)], 'Correlation': [f"Correlation {i+1}-{W}" for i in range(W)]}))
            sheet_names.append("Windowed data")
            titles.append("List of worksheets for windowed data")
            # Phase matrices
            for i,td in enumerate(self.rolling_phase_data):
                datasets.append(td.matrix) ; sheet_names.append(f"Phase {i+1}-{W}")   ; titles.append(f"Phase matrix (samples) in window #{i+1}/{W} : Samples {td.interval} / Period ({td.interval[0]/self.Fs},{td.interval[1]/self.Fs}) s")
                # Correlation matrices
            for i,td in enumerate(self.rolling_phase_data):
                datasets.append(td.correlation) ; sheet_names.append(f"Correlation {i+1}-{W}")   ; titles.append(f"Correlation matrix in window #{i+1}/{W} : Samples {td.interval} / Period ({td.interval[0]/self.Fs},{td.interval[1]/self.Fs}) s")
            destination = (self.file + '.rolling_phase.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".rolling_phase.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, analyzer=self)
        return True
    def bakeRollingOrder(self):
        self._checkBackwardsCompatibility()
        ''' Check input data '''
        needed_data = [self.rolling_phase_data]
        messages    = ["Rolling phase not baked."]
        bakers      = [self.bakeRollingPhase]
        if not(self.checkDependencies(needed_data, messages, bakers)):
            return False
        self.preprocessWaveforms()
        MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
        rolling_order = processing.rollingOrder(self.rolling_phase_data, reference=self.parameters["hub_reference"])
        self.rolling_order_data = rolling_order
        self.order_stats = processing.order_matrix(rolling_order)
        self.leader_periods = processing.get_periods_as_leader(rolling_order)
        self.leader_distances = processing.get_distance_between_successive_leaders(rolling_order, layout=MEA_layout)
        self._onBakeFinish()
        return True
    def exportRollingOrder(self, destination=None, which=-1):
        if not self._isExportReady(EXPORTS["ROLLINGORDER"]):
            colprint.printerr(MSG_EXPORT_FAILED)
            return False
        order_stats = self.order_stats
        leader_periods = self.leader_periods.copy()
        leader_periods["start"]    /= self.Fs
        leader_periods["end"]      /= self.Fs
        leader_periods["duration"] /= self.Fs
        leader_distances = self.leader_distances.copy()
        leader_distances["start"]    /= self.Fs
        leader_distances["end"]      /= self.Fs
        leader_distances["duration"] /= self.Fs
        if which in [-1, 0]:
            datasets = []; sheet_names = []; titles = []
            datasets.append(order_stats.percentage)                  ; sheet_names.append("percentage")       ; titles.append("Fraction of time at rank #i (%)")
            datasets.append(1000. * order_stats.dt / self.Fs)        ; sheet_names.append("dt_avg")           ; titles.append("Average lag behind leader (ms)")
            datasets.append(1000. * order_stats.dt_std / self.Fs)    ; sheet_names.append("dt_std")           ; titles.append("STD lag behind leader (ms)")
            datasets.append(order_stats.N)                           ; sheet_names.append("N")                ; titles.append(f"Number of times at rank #i (out of {order_stats.Ntotal} total)")
            datasets.append(leader_periods)                          ; sheet_names.append("leaders")          ; titles.append("List of periods where a channel remained the leader, with timesamps and durations (s)")
            datasets.append(leader_distances)                        ; sheet_names.append("leader_distances") ; titles.append("Distances between successive leaders ; timestamps and durations in seconds, distances typ. in micrometers (same units as MEA file)")
            destination = (self.file + '.order_stats.xlsx') if destination is None else destination.rsplit(".",1)[0] + ".order_stats.xlsx" if which == -1 else destination # 1. default filename if specified ELSE provided filename with individual fields if exporting all ELSE provided filename
            data_inout.df2xlsx_multisheet(datasets, sheet_names, titles, destination, self)
        return True
    def checkDependencies(self, data, message, baker=None):
        output = True
        if baker is None:
            baker = [None for _ in data]
        for d,m,b in zip(data, message, baker):
            if not(d):
                colprint.printwar("Unsatisfied dependency : {}".format(m))
                if self.autobake:
                    colprint.printwar("  Attempting autobaking ...")
                    if not(b):
                        colprint.printerr("  No baker found. Could not proceed.")
                        output = False
                    else:
                        if b():
                            colprint.printokg("  Autobaking succeeded.")
                        else:
                            colprint.printerr("  Autobaking failed.")
                            output = False
                else:
                    colprint.printerr("Could not proceed.")
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
            for c in self.clustering_data.clusters:
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
        ''' Rolling phase data '''
        if self.rolling_phase_data is None:
            string += "Rolling phase not baked.\n"
        else:
            channels = self.parameters["channel_filters"] if self.parameters["channel_filters"] else self.waveforms.keys()
            string += "Rolling phase data :\n"
            for k1 in channels:
                for k2 in channels:
                    if k1 == k2:
                        continue
                    data = [rtd.matrix[k1][k2] for rtd in self.rolling_phase_data]
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

            string += "\n  Average phase for each rank (xcorr, relative to identified first) : \n"
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
    def drawCorrelation(self, which=-1, show=True):
        if self._isPlotReady(PLOTS["CORRELATIONMATRIX"]) and which in [-1,0]:
            representations.drawCorrelation(self.correlation_data.matrix, title='Correlation matrix')
        if self._isPlotReady(PLOTS["GRANGERCAUSALITYMATRIX"]) and which in [-1,1]:
            representations.drawCorrelation(self.granger_data.matrix, title='Granger causality matrix', bounds=(None,None))
        if self._isPlotReady(PLOTS["CORRELATIONSPATIAL"]) and which in [-1,2]:
            MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
            representations.drawCorrelationSpatial(self.correlation_data.matrix, MEA_layout)
        if show and (which in [-1,0,1,2]):
            plt.show(block=False)
    def drawClustering(self, which=-1, show=True):
        if self._isPlotReady(PLOTS["CLUSTEREDEVENTS"]) and which in [-1,0]:
            representations.drawClusteredEvents(self.timestamps, self.linkage)
        if self._isPlotReady(PLOTS["DENDROGRAM"]) and which in [-1,1]:
            representations.drawDendrogram(self.correlation_data.matrix, self.linkage)
        if self._isPlotReady(PLOTS["CLUSTERSSPATIAL"]) and which in [-1,2]:
            MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
            representations.drawClustersSpatial(self.correlation_data, self.clustering_data, MEA_layout)
        if show and (which in [-1,0,1,2]):
            plt.show(block=False)
    def drawRollingCorrelation(self, which=-1, show=True):
        if self._isPlotReady(PLOTS["ROLLINGCORRELATION"]) and which in [-1,0]:
            representations.animate_rollingCorrelation(self.rolling_correlation_data, self.waveforms, Fs=self.Fs)
        if show and (which in [-1,0]):
            plt.show(block=False)
    def drawRollingPhase(self, which=-1, show=True):
        MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
        if self._isPlotReady(PLOTS["ROLLINGPHASE"]) and which in[-1,0]:
            representations.animate_rollingPhase(self.rolling_phase_data, self.waveforms, Fs=self.Fs)
        if self._isPlotReady(PLOTS["ROLLINGPHASESPATIAL"]) and which in[-1,1]:
            representations.animate_rollingPhaseSpatial(self.rolling_phase_data, MEA_layout, self.waveforms, Fs=self.Fs)
        if self._isPlotReady(PLOTS["ROLLINGPHASESPATIALSTATIC"]) and which in[-1,2]:
            representations.drawRollingPhaseSpatial(
                self.rolling_phase_data, MEA_layout, Fs=self.Fs, reference_channel=self.parameters["hub_reference"], speed=False,
                contour=True, contourlabels=True, contourmap=None,
                fill=False, fillmap=None)
        if self._isPlotReady(PLOTS["ROLLINGPHASESPATIALSTATIC"]) and which in[-1,3]:
            representations.drawRollingPhaseSpatial(
                self.rolling_phase_data, MEA_layout, Fs=self.Fs, reference_channel=self.parameters["hub_reference"], speed=False,
                contour=True, contourlabels=False, contourmap="rainbow_r",
                fill=False, fillmap="rainbow_r")
        if self._isPlotReady(PLOTS["ROLLINGPHASESPATIALSTATIC"]) and which in[-1,4]:
            representations.drawRollingPhaseSpatial(
                self.rolling_phase_data, MEA_layout, Fs=self.Fs, reference_channel=self.parameters["hub_reference"], speed=False,
                contour=True, contourlabels=False, contourmap=None,
                fill=True, fillmap="rainbow_r")
        if self._isPlotReady(PLOTS["ROLLINGPHASESPATIALSTATIC"]) and which in[-1,5]:
            representations.drawRollingPhaseSpatial(
                self.rolling_phase_data, MEA_layout, Fs=self.Fs, reference_channel=self.parameters["hub_reference"], speed=False,
                contour=False, contourlabels=False, contourmap=None,
                fill=True, fillmap="rainbow_r")
        if show and (which in [-1,0,1,2,3,4,5]):
            plt.show(block=False)
    def drawRollingOrderStats(self, which=-1, show=True):
        MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
        # BAR GRAPHS
        if self._isPlotReady(PLOTS["ROLLINGORDERBAR"]) and which in [-1,0]:
            representations.drawOrderBargraph(self.order_stats, timeinfo=True, Fs=self.parameters["processing_Fs"])
        if self._isPlotReady(PLOTS["ROLLINGORDERBAR"]) and which in [-1,1]:
            representations.drawOrderBargraph(
                self.order_stats, timeinfo=True, Fs=self.parameters["processing_Fs"],
                highlight_ranks=1
            )
        if self._isPlotReady(PLOTS["ROLLINGORDERBAR"]) and which in [-1,2]:
            representations.drawOrderBargraph(
                self.order_stats, timeinfo=True, Fs=self.parameters["processing_Fs"],
                highlight_ranks=2
            )
        if self._isPlotReady(PLOTS["ROLLINGORDERBAR"]) and which in [-1,3]:
            representations.drawOrderBargraph(
                self.order_stats, timeinfo=True, Fs=self.parameters["processing_Fs"],
                highlight_ranks=3
            )
        # PIE GRAPHS
        if self._isPlotReady(PLOTS["ROLLINGORDERPIE"]) and which in [-1,4]:
            representations.drawOrderPie(self.order_stats, MEA_layout, timeinfo=False, Fs=self.parameters["processing_Fs"])
        if self._isPlotReady(PLOTS["ROLLINGORDERPIE"]) and which in [-1,5]:
            representations.drawOrderPie(
                self.order_stats, MEA_layout, timeinfo=False, Fs=self.parameters["processing_Fs"],
                highlight_ranks=1
            )
        if self._isPlotReady(PLOTS["ROLLINGORDERPIE"]) and which in [-1,6]:
            representations.drawOrderPie(
                self.order_stats, MEA_layout, timeinfo=False, Fs=self.parameters["processing_Fs"],
                highlight_ranks=2
            )
        if self._isPlotReady(PLOTS["ROLLINGORDERPIE"]) and which in [-1,7]:
            representations.drawOrderPie(
                self.order_stats, MEA_layout, timeinfo=False, Fs=self.parameters["processing_Fs"],
                highlight_ranks=3
            )
        # SPATIAL
        if self._isPlotReady(PLOTS["ROLLINGORDERSPATIAL"]) and which in [-1,8]:
            representations.animate_rollingOrderSpatial(self.rolling_order_data, self.rolling_phase_data, MEA_layout, self.waveforms, Fs=self.parameters["processing_Fs"], speed=False, env=self.parameters['environment'])
        # TEMPORAL
        if self._isPlotReady(PLOTS["ROLLINGORDERTEMPORAL"]) and which in [-1,9]:
            representations.drawLeaderSuccession(self.rolling_order_data, Fs=self.parameters["processing_Fs"])
        if self._isPlotReady(PLOTS["ROLLINGORDERTEMPORAL"]) and which in [-1,10]:
            representations.drawLeaderSuccession2D(self.rolling_order_data, layout=MEA_layout, mode="arrows", Fs=self.parameters["processing_Fs"])
        # ---
        if show and (which in [-1,0,1,2,3,4,5,6,7,8,9,10]):
            plt.show(block=False)

    def drawPhase(self, which=-1, show=True):
        if self._isPlotReady(PLOTS["PHASE"]) and which in [-1,0]:
            MEA_layout = getattr(MEAs, self.parameters["MEA_layout"]) if type(self.parameters["MEA_layout"]) is str else self.parameters["MEA_layout"]
            representations.drawPhaseSpatial(self.phase_data.matrix, MEA_layout, Fs=self.Fs)
        if which in [-1,0]:
            plt.show(block=False)
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
    def _isPlotReady(self, which):
        if which == PLOTS["CORRELATIONMATRIX"]:
            return bool(self.correlation_data)
        if which == PLOTS["CLUSTEREDEVENTS"]:
            return bool(self.timestamps and self.clustering_data)
        if which == PLOTS["GRANGERCAUSALITYMATRIX"]:
            return bool(self.granger_data)
        if which == PLOTS["CORRELATIONSPATIAL"]:
            return bool(self.correlation_data)
        if which == PLOTS["DENDROGRAM"]:
            return bool(self.correlation_data and self.clustering_data)
        if which == PLOTS["PHASE"]:
            return bool(self.phase_data)
        if which == PLOTS["ROLLINGCORRELATION"]:
            return bool(self.rolling_correlation_data and self.waveforms)
        if which == PLOTS["ROLLINGPHASE"]:
            return bool(self.rolling_phase_data and self.waveforms)
        if which == PLOTS["ROLLINGPHASESPATIAL"]:
            return False # todo : refine this representation
            # return bool(self.rolling_phase_data and self.waveforms)
        if which == PLOTS["ROLLINGPHASESPATIALSTATIC"]:
            return bool(self.rolling_phase_data and self.waveforms)
        if which == PLOTS["ROLLINGORDERSPATIAL"]:
            return bool(self.rolling_order_data and self.rolling_phase_data and self.waveforms)
        if which == PLOTS["ROLLINGORDERBAR"]:
            return bool(self.order_stats)
        if which == PLOTS["ROLLINGORDERPIE"]:
            return bool(self.order_stats)
        if which == PLOTS["ROLLINGORDERTEMPORAL"]:
            return bool(self.rolling_order_data)
        if which == PLOTS["CLUSTERSSPATIAL"]:
            return bool(self.correlation_data and self.clustering_data)
        return False
    def _isExportReady(self, which):
        if which == EXPORTS["CORRELATIONMATRIX"]:
            return bool(self.correlation_data)
        if which == EXPORTS["GRANGERCAUSALITYMATRIX"]:
            return False
        if which == EXPORTS["DENDROGRAM"]:
            return False
        if which == EXPORTS["PHASE"]:
            return bool(self.phase_data)
        if which == EXPORTS["ORDER"]:
            return bool(self.order_data)
        if which == EXPORTS["CLUSTERING"]:
            return bool(self.clustering_data)
        if which == EXPORTS["ROLLINGCORRELATION"]:
            return bool(self.rolling_correlation_data)
        if which == EXPORTS["ROLLINGPHASE"]:
            return bool(self.rolling_phase_data)
        if which == EXPORTS["ROLLINGORDER"]:
            return bool(self.rolling_order_data)
        return False


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
