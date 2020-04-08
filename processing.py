import numpy as np
import pandas as pd
import seaborn as sb
from scipy import signal
from scipy import stats
import scipy.cluster.hierarchy as spc
from matplotlib import pyplot as plt
import progressbar

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

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
    data = pd.DataFrame.from_dict(allGaussEvents)
    correlationMatrix = data.corr()
    correlationMatrix = correlationMatrix.fillna(0)

    ''' Return values '''
    output = {}
    output['dataframe'] = correlationMatrix
    output['matrix']    = correlationMatrix.values
    output['labels']    = correlationMatrix.columns
    output['signals']   = gaussEvents

    return output

def rollingCorrelationMatrix(timestamps={}, sigma_samples=1, window_samples=10, overlap_percent=50, Fs=1.):
    ''' Get max timestamp '''
    all_timestamps = [t for sublist in timestamps.values() for t in sublist]
    max_timestamp = max(all_timestamps)

    output = {}
    output['dataframe'] = []
    output['matrix']    = []
    output['labels']    = []
    output['signals']   = []
    output['intervals'] =  []

    overlap_samples = int(window_samples * overlap_percent/100.)
    skip_samples    = int(window_samples - overlap_samples)

    i = 0
    while i < max_timestamp:
        ''' Apply window to samples '''
        windowed_timestamps = {}
        for k in timestamps:
            windowed_timestamps[k] = [t for t in timestamps[k] if ((t >= i) and (t < i + window_samples))]
        ''' Compute correlation '''
        event_correlation = eventCorrelationMatrix(timestamps=windowed_timestamps, sigma_samples=sigma_samples)
        output['dataframe'].append(event_correlation['dataframe'])
        output['matrix'].append(event_correlation['matrix'])
        output['labels'].append(event_correlation['labels'])
        output['signals'].append(event_correlation['signals'])
        output['intervals'].append((i/Fs, (i + window_samples)/Fs))
        ''' Advance window '''
        i += skip_samples
        progressbar.inlineCycles(i, max_timestamp, prefix='Rolling correlation')

    return output

def getClustering(dataframe, tolerance=0.3):
    matrix = dataframe.values
    labels = dataframe.columns
    link = spc.linkage(matrix, method='average')
    clustering = pd.Series(spc.fcluster(link, t=tolerance, criterion='distance'), index=labels)
    Nclusters = max(clustering)
    clusters = []
    for i in range(Nclusters):
        j = i+1
        clusters.append([ch for ch in clustering.index[clustering==j]])

    # spc.dendrogram(link)
    # plt.show()

    outputs = {}
    outputs['linkage']  = link
    outputs['labels']   = dataframe.columns
    outputs['clusters'] = clusters
    return outputs

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
