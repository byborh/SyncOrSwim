import processing
import data_inout
import representations
import layouts

import seaborn as sb
from matplotlib import pyplot as plt

from biosignal_analysis.analyses import processing as signalprocessing

"""
TODO
  * Processing:
    o Time offset measurement
    x DONE Rolling linkage/clusters
    x DONE correlation
    x DONE Rolling correlation
    x DONE linkage
  * Representations:
    X DONE Electrode representation w/ clusters
    x DONE Top linkage on MEA view
  o
"""


Fs = 100.
evt_tolerance_s = 0.5
evt_tolerance_i = int(evt_tolerance_s*Fs)
corr_tolerance = 0.4


""" STATIC TESTS """
if False:
    ''' Generate timestamps (static) '''
    timestamps_i = data_inout.generateTestEvents(300, Fs, "static")
    waveforms = processing.eventWaveforms(timestamps_i, evt_tolerance_i)

    ''' Test overall correlation & clustering '''
    correlation = processing.correlationMatrix(waveforms)
    clustering  = processing.getClustering(correlation.matrix, tolerance=corr_tolerance)
    cg = sb.clustermap(correlation.matrix, cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClusteredEvents(timestamps_i, clustering.linkage)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelation(waveforms, window_samples=window_samples, overlap_percent=50)
    representations.animate_rollingCorrelation(rolling_correlation, Fs=Fs)

""" SPATIAL TESTS """
if False:
    ''' Generate timestamps (spatial) '''
    timestamps_i = data_inout.generateTestEvents(300, Fs, "spatial")
    waveforms = processing.eventWaveforms(timestamps_i, evt_tolerance_i)

    ''' Test overall correlation & clustering '''
    correlation = processing.correlationMatrix(waveforms)
    clustering  = processing.getClustering(correlation.matrix, tolerance=corr_tolerance)
    cg = sb.clustermap(correlation.matrix, cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClustersSpatial(correlation, clustering, layouts.HDMEA)
    representations.drawCorrelationSpatial(correlation.matrix, layouts.HDMEA, threshold=0.4)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelation(waveforms, window_samples=window_samples, overlap_percent=50)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, waveforms, layouts.HDMEA, threshold=0.4, Fs=Fs)

""" SPATIAL TESTS - REAL DATA """
if False:
    ''' Use real data '''
    # file_in = "./Timestamps/correl 2nd phase.txt"
    # file_in = "./Timestamps/Enregistrement 7 min milieu 2ème phase text.txt"
    # file_in = "./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt"
    # file_in = "./Timestamps/détection d'évènements text.txt"
    file_in = "./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt"
    timestamps_s = data_inout.fromSpike2(file_in)
    timestamps_s = processing.clean_timestamps(timestamps_s)
    timestamps_i = processing.s2idx(timestamps_s, Fs)
    waveforms = processing.eventWaveforms(timestamps_i, evt_tolerance_i)

    ''' Test overall correlation & clustering '''
    correlation = processing.correlationMatrix(waveforms)
    clustering  = processing.getClustering(correlation.matrix, tolerance=corr_tolerance)
    cg = sb.clustermap(correlation.matrix, cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClustersSpatial(correlation, clustering, layouts.MEA_ElTesto)
    representations.drawCorrelationSpatial(correlation.matrix, layouts.MEA_ElTesto, threshold=0.4)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelation(waveforms, window_samples=window_samples, overlap_percent=50)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, waveforms, layouts.MEA_ElTesto, threshold=0.4, Fs=Fs)

""" SPATIAL TESTS - REAL DATA PROCESSED FROM SCRATCH """
if True:
    ''' Use real data '''
    file_in = "../Data/Preanalysis/100Hz/G8_late_6680-6980_s/Results/SP0.txt"
    timestamps_s = data_inout.fromPyBiosignalAnalysis(file_in)
    timestamps_s = processing.clean_timestamps(timestamps_s)
    timestamps_i = processing.s2idx(timestamps_s, Fs)
    waveforms = processing.eventWaveforms(timestamps_i, evt_tolerance_i)

    ''' Test overall correlation & clustering '''
    # cmap = "YlGnBu"
    cmap = "jet"
    correlation = processing.correlationMatrix(waveforms)
    clustering  = processing.getClustering(correlation.matrix, tolerance=corr_tolerance)
    cg = sb.clustermap(correlation.matrix, cmap = cmap, linewidths = 0.1, figsize=(6,6), method='average', vmin=-1.0, vmax=1.0)
    representations.drawClustersSpatial(correlation, clustering, layouts.HDMEA)
    representations.drawCorrelationSpatial(correlation.matrix, layouts.HDMEA, threshold=0.7)
    representations.drawClusteredEvents(timestamps_s, clustering.linkage)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    overlap_percent = 90.
    rolling_correlation = processing.rollingCorrelation(waveforms, window_samples=window_samples, overlap_percent=overlap_percent)
    representations.drawClusteredRollingCorrelation(rolling_correlation, clustering.clusters)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, waveforms, layouts.HDMEA, threshold=0.7, Fs=Fs)
    plt.show()

""" TEST CONTINUOUS DATA """
if False:
    file_in = "../Data/20160120/h5/G8 late 6680-6980 s.h5"
    filters = signalprocessing.BPfilters(hp=[(0.2, 1)], lp=[(2.0, 2)], filtertype="bessel", Fs=100.)
    signals = data_inout.fromH5(file_in, import_parameters={"analog_stream_idx": 1})
    for ch in signals:
        signals[ch] = filters.run(signals[ch])

    cmap = "jet"
    correlation = processing.correlationMatrix(signals)
    cg = sb.clustermap(correlation.matrix, cmap = cmap, linewidths = 0.1, figsize=(6,6), method='average', vmin=-1.0, vmax=1.0)
    plt.show()

    window_s = 60.
    window_samples = int(Fs * window_s)
    overlap_percent = 90.
    rolling_correlation = processing.rollingCorrelation(signals, window_samples=window_samples, overlap_percent=overlap_percent)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, signals, layouts.HDMEA, threshold=0.7, Fs=Fs)
