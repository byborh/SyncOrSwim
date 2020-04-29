import numpy as np
import pandas as pd
import seaborn as sb
from scipy import signal
from scipy import stats
import scipy.cluster.hierarchy as spc
from matplotlib import pyplot as plt
from collections import namedtuple
import progressbar

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

def eventWaveforms(timestamps={}, sigma_samples=1):
    ''' <timestamps> is a dictionary of timestamp lists  '''
    ''' (one item is all the timestamps from one source) '''
    ''' Everything is unitless (indexes)                 '''
    Nsources = len(timestamps)
    Nsigma = 10 # This multiplied by sigma_samples is the number of points generated left and right of the gaussian's center

    ''' Get max timestamp '''
    all_timestamps = [t for sublist in timestamps.values() for t in sublist]
    Np = int(max(all_timestamps) + 1 + sigma_samples*Nsigma)

    ''' Generate gaussian signals '''
    allGaussEvents = {}
    Ng = int((2*Nsigma) * sigma_samples + 1)
    gaussSignal = signal.gaussian(Ng, std=sigma_samples)
    diracEvents = np.zeros(Np)
    gaussEvents = np.zeros(Np)
    for k in timestamps:
        t = timestamps[k]
        diracEvents = np.zeros(Np)
        diracEvents[t] = 1.
        gaussEvents = signal.fftconvolve(diracEvents, gaussSignal, mode='same')
        allGaussEvents[k] = 1.*gaussEvents
    return allGaussEvents

def correlationMatrix(signals={}):
    data = pd.DataFrame.from_dict(signals)
    correlationMatrix = data.corr()
    correlationMatrix = correlationMatrix.fillna(0)
    correlation_data = namedtuple("Correlation_Data", "matrix")
    return correlation_data(correlationMatrix)

def eventCorrelationMatrix(timestamps={}, sigma_samples=1):
    ''' <timestamps> is a dictionary of timestamp lists  '''
    ''' (one item is all the timestamps from one source) '''
    ''' Everything is unitless (indexes)                 '''
    Nsources = len(timestamps)
    Nsigma = 5 # This multiplied by sigma_samples is the number of points generated left and right of the gaussian's center

    ''' Get max timestamp '''
    all_timestamps = [t for sublist in timestamps.values() for t in sublist]
    Np = int(max(all_timestamps) + 1 + sigma_samples*Nsigma)

    ''' Generate gaussian signals '''
    allGaussEvents = {}
    Ng = int((2*Nsigma) * sigma_samples + 1)
    gaussSignal = signal.gaussian(Ng, std=sigma_samples)
    diracEvents = np.zeros(Np)
    gaussEvents = np.zeros(Np)
    for k in timestamps:
        t = timestamps[k]
        diracEvents = np.zeros(Np)
        diracEvents[t] = 1.
        gaussEvents = signal.fftconvolve(diracEvents, gaussSignal, mode='same')
        allGaussEvents[k] = 1.*gaussEvents

    ''' Generate correlation matrix '''
    # correlationMatrix = np.corrcoef(gaussEvents)
    correlation_data = correlationMatrix(allGaussEvents)
    event_correlation_data = namedtuple("Event_correlation_Data", ["matrix", "signals"])
    return event_correlation_data(correlation_data.matrix, gaussEvents)

def rollingCorrelation(signals={}, window_samples=10, overlap_percent=50):
    for k in signals:
        N = len(signals[k])
    output = []

    overlap_samples = int(window_samples * overlap_percent/100.)
    skip_samples    = int(window_samples - overlap_samples)
    rolling_correlation_data = namedtuple("Rolling_Correlation_Data", ["matrix", "interval"])

    i = 0
    j = i + window_samples
    while j < N:
        ''' Apply window to samples '''
        windowed_signals = {}
        for k in signals:
            windowed_signals[k] = signals[k][i:j]
        ''' Compute correlation '''
        event_correlation = correlationMatrix(signals=windowed_signals)
        output.append(rolling_correlation_data(event_correlation.matrix, (i, j)))
        ''' Advance window '''
        i += skip_samples
        j = i + window_samples
        progressbar.inlineCycles(j, N, prefix='Rolling correlation')

    return output

def rollingEventCorrelation(timestamps={}, sigma_samples=1, window_samples=10, overlap_percent=50):
    ''' Get max timestamp '''
    all_timestamps = [t for sublist in timestamps.values() for t in sublist]
    max_timestamp = max(all_timestamps)

    output = []

    overlap_samples = int(window_samples * overlap_percent/100.)
    skip_samples    = int(window_samples - overlap_samples)
    rolling_correlation_data = namedtuple("Rolling_Event_Correlation_Data", ["matrix", "signals", "interval"])

    i = 0
    j = i + window_samples
    while j < max_timestamp:
        ''' Apply window to samples '''
        windowed_timestamps = {}
        for k in timestamps:
            windowed_timestamps[k] = [t for t in timestamps[k] if ((t >= i) and (t < j))]
        ''' Compute correlation '''
        event_correlation = eventCorrelationMatrix(timestamps=windowed_timestamps, sigma_samples=sigma_samples)
        output.append(rolling_correlation_data(event_correlation.matrix, event_correlation.signals, (i, j)))
        ''' Advance window '''
        i += skip_samples
        j = i + window_samples
        progressbar.inlineCycles(j, max_timestamp, prefix='Rolling correlation')

    return output

def getClustering(dataframe, tolerance=0.3):
    matrix = dataframe.values
    labels = dataframe.columns
    linkage = spc.linkage(matrix, method='average')
    clustering = pd.Series(spc.fcluster(linkage, t=tolerance, criterion='distance'), index=labels)
    Nclusters = max(clustering)
    clusters = []
    for i in range(Nclusters):
        j = i+1
        clusters.append([ch for ch in clustering.index[clustering==j]])
    clustering_data = namedtuple("Clustering_Data", ["linkage", "clusters", "labels"])
    return clustering_data(linkage, clusters, dataframe.columns)

def filter_channels(data={}, filter=[]):
    data_out = {}
    for k in data:
        if k in filters:
            data_out[k] = data[k]
    return data_out

def exclude_channels(data={}, filter=[]):
    data_out = {}
    for k in data:
        if k not in filters:
            data_out[k] = data[k]
    return data_out

def s2idx(timestamps, Fs):
    ''' Takes timestamps in [s] and converts them to integer indexes, assuming they are sampled at Fs [Hz] '''
    indexes = {}
    for k in timestamps:
        indexes[k] = [int(t*Fs) for t in timestamps[k]]
    return indexes

def clean_timestamps(timestamps, verbose=True):
    ''' Removes empty channels if need be '''
    ''' (Creates deep copy of original)   '''
    new_timestamps = {}
    for k in timestamps:
        if timestamps[k] != []:
            new_timestamps[k] = [t for t in timestamps[k]]
        else:
            verbosePrint("Warning : Removed channel {} because it was empty.".format(k), verbose)
    return new_timestamps

if __name__ == "__main__":
    corrmat = eventCorrelationMatrix({'c0':[100,200,300], 'c1':[100,200,300], 'c2':[50, 150, 250]}, 10.)['dataframe']
    cg = sb.clustermap(corrmat, cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6))
    plt.show()
