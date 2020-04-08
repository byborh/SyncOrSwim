import processing
import data_inout
import representations
import layouts

import seaborn as sb
from matplotlib import pyplot as plt

"""
TODO
  * Processing:
    o
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
if True:
    ''' Generate timestamps (static) '''
    timestamps_i = data_inout.generateTestEvents(300, Fs, "static")

    ''' Test overall correlation & clustering '''
    correlation = processing.eventCorrelationMatrix(timestamps_i, evt_tolerance_i)
    clustering  = processing.getClustering(correlation['dataframe'], tolerance=corr_tolerance)
    cg = sb.clustermap(correlation['dataframe'], cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClusteredEvents(timestamps_i, clustering['linkage'])
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelationMatrix(timestamps_i, evt_tolerance_i, window_samples=window_samples, overlap_percent=50, Fs=Fs)
    representations.animate_rollingCorrelation(rolling_correlation)

""" SPATIAL TESTS """
if True:
    ''' Generate timestamps (spatial) '''
    timestamps_i = data_inout.generateTestEvents(300, Fs, "spatial")

    ''' Test overall correlation & clustering '''
    correlation = processing.eventCorrelationMatrix(timestamps_i, evt_tolerance_i)
    clustering  = processing.getClustering(correlation['dataframe'], tolerance=corr_tolerance)
    cg = sb.clustermap(correlation['dataframe'], cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClustersSpatial(correlation, clustering, layouts.HDMEA)
    representations.drawCorrelationSpatial(correlation, layouts.HDMEA, threshold=0.4)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelationMatrix(timestamps_i, evt_tolerance_i, window_samples=window_samples, overlap_percent=50, Fs=Fs)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, layouts.HDMEA, threshold=0.4)

""" SPATIAL TESTS - REAL DATA """
if True:
    ''' Use real data '''
    # file_in = "./Timestamps/correl 2nd phase.txt"
    # file_in = "./Timestamps/Enregistrement 7 min milieu 2ème phase text.txt"
    # file_in = "./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt"
    # file_in = "./Timestamps/détection d'évènements text.txt"
    file_in = "./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt"
    timestamps_s = data_inout.fromSpike2(file_in)
    timestamps_s = processing.clean_timestamps(timestamps_s)
    timestamps_i = processing.s2idx(timestamps_s, Fs)

    ''' Test overall correlation & clustering '''
    correlation = processing.eventCorrelationMatrix(timestamps_i, evt_tolerance_i)
    clustering  = processing.getClustering(correlation['dataframe'], tolerance=corr_tolerance)
    cg = sb.clustermap(correlation['dataframe'], cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')
    representations.drawClustersSpatial(correlation, clustering, layouts.MEA_ElTesto)
    representations.drawCorrelationSpatial(correlation, layouts.MEA_ElTesto, threshold=0.4)
    plt.show()

    ''' Test windowed correlation '''
    window_s = 60.
    window_samples = int(Fs * window_s)
    rolling_correlation = processing.rollingCorrelationMatrix(timestamps_i, evt_tolerance_i, window_samples=window_samples, overlap_percent=50, Fs=Fs)
    representations.animate_rollingCorrelationSpatial(rolling_correlation, layouts.MEA_ElTesto, threshold=0.4)
