import numpy as np
import pandas as pd
import seaborn as sb
from scipy import signal
from scipy import stats
from scipy import optimize
from scipy.optimize import minimize
import scipy.cluster.hierarchy as spc
from inspect import signature
from statsmodels.tsa import stattools
from matplotlib import pyplot as plt
from collections import namedtuple
import progressbar
import itertools

def pbar(*args, **kwargs):
    """ Definition of a progressbar that can easily be overloaded """
    progressbar.inlineCycles(*args, **kwargs)

def verbosePrint(str, verbose=True):
    if verbose:
        print(str)

def map_to_dict(function, dictionary, *args, **kwargs):
    if 'progress_message' in kwargs:
        progress_message = kwargs['progress_message']
        kwargs.pop('progress_message')
    else:
        progress_message = ""
    output = {}
    for i,k in enumerate(dictionary):
        output[k] = function(dictionary[k], *args, **kwargs)
        if progress_message:
            pbar(i, len(dictionary), prefix=progress_message)
    return output

def apply_rolling(func1d, array1d, window_samples, shift_samples, *args, **kwargs):
    ''' Very memory-intensive '''
    array1d = np.asarray(array1d)
    N = len(array1d)
    vert_idx_list = np.arange(0, N - window_samples, shift_samples)
    hori_idx_list = np.arange(window_samples)
    A, B = np.meshgrid(hori_idx_list, vert_idx_list)
    idx_array = A + B
    array2d = array1d[idx_array]
    return func1d(array2d, *args, **kwargs)
    # return np.apply_along_axis(func1d, arr=array2d, axis=1, *args, **kwargs)

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

def granger_causality_matrix(signals={}, maxlag_samples=150):
    data = pd.DataFrame.from_dict(signals)
    N = len(signals)
    channels = [k for k in signals]
    matrix = pd.DataFrame(np.zeros((N,N)), columns=channels, index=channels)
    test = 'ssr_chi2test'
    for c in matrix.columns:
        for r in matrix.index:
            if c == r:
                continue
            print(c,r)
            result = stattools.grangercausalitytests(data[[r,c]], maxlag=maxlag_samples, verbose=False, addconst=True)
            p_values = [result[i+1][0][test][1] for i in range(maxlag_samples)]
            min_p_value = min(p_values)
            matrix.loc[r,c] = min_p_value
    correlation_data = namedtuple("Correlation_Data", "matrix")
    return correlation_data(matrix)

def rollingCorrelation(signals={}, window_samples=10, overlap_samples=5):
    N = 0
    for k in signals:
        N = len(signals[k])
    output = []

    skip_samples    = int(window_samples - overlap_samples)
    rolling_correlation_data = namedtuple("Rolling_Correlation_Data", ["matrix", "interval"])

    i = 0
    j = i + window_samples
    while j < N:
        ''' Apply window to samples '''
        windowed_signals = {}
        for k in signals:
            windowed_signals[k] = 1 * np.asarray(signals[k])[i:j]
        ''' Compute correlation '''
        event_correlation = correlationMatrix(signals=windowed_signals)
        output.append(rolling_correlation_data(event_correlation.matrix, (i, j)))
        ''' Advance window '''
        i += skip_samples
        j = i + window_samples
        pbar(j, N, prefix='Rolling correlation')

    return output

def rollingTimeshift(signals={}, window_samples=10, overlap_samples=7):
    L = len(signals)
    for k in signals:
        N = len(signals[k])
    output = []

    skip_samples    = int(window_samples - overlap_samples)
    rolling_timeshift_data = namedtuple("Rolling_Timeshift_Data", ["matrix", "correlation", "interval"])

    i = 0
    j = i + window_samples
    if L <= 1: # Prevent some weird printing behaviour caused by pandas (?)
        print(f"Rolling timeshift ... ", end="")
    while j < N:
        ''' Apply window to samples '''
        windowed_signals = {}
        for k in signals:
            windowed_signals[k] = 1 * np.asarray(signals[k])[i:j]
        ''' Compute correlation '''
        timeshift = timeshiftMatrix(signals=windowed_signals)
        output.append(rolling_timeshift_data(timeshift.matrix, timeshift.correlation, (i, j)))
        ''' Advance window '''
        i += skip_samples
        j = i + window_samples
        if L > 1: # Prevent some weird printing behaviour caused by pandas (?)
            pbar(j, N, prefix='Rolling timeshift', done=f"Done (discarded {N-i} samples)")
    if L <= 1: # Prevent some weird printing behaviour caused by pandas (?)
        print(f"Done (discarded {N-i} samples)")
    return output

def rollingOrder(rolling_timeshift, reference=None):
    N = len(rolling_timeshift)
    output = []

    rolling_order_data = namedtuple("Rolling_Order_Data", ["series", "order", "values", "interval"])

    for i,timeshift in enumerate(rolling_timeshift):
        order_data = timeshiftOrder(timeshift.matrix, reference=reference)
        output.append(rolling_order_data(order_data.series, order_data.order, order_data.values, timeshift.interval))
        pbar(i, N, prefix='Rolling order')
    return output

def getClustering(dataframe, tolerance=None):
    matrix = dataframe.values
    labels = dataframe.columns
    linkage = spc.linkage(matrix, method='average')
    if tolerance is None:
        tolerance = 0.7 * np.max(linkage[:,2]) # Same as spc.dendrogram
    clustering = pd.Series(spc.fcluster(linkage, t=tolerance, criterion='distance'), index=labels)
    Nclusters = max(clustering)
    clusters = []
    for i in range(Nclusters):
        j = i+1
        clusters.append([ch for ch in clustering.index[clustering==j]])
    clustering_data = namedtuple("Clustering_Data", ["linkage", "clusters", "labels"])
    return clustering_data(linkage, clusters, dataframe.columns)

def timeshiftMatrix(signals={}, correlation_threshold=0.7):
    N = len(signals)
    DT = np.zeros((N,N))
    CO = np.zeros((N,N))
    for i,k1 in enumerate(signals):
        for j,k2 in enumerate(signals):
            sig1 = 1. * np.asarray(signals[k1])
            sig2 = 1. * np.asarray(signals[k2])
            dt, co = get_timeshift(sig1, sig2)
            DT[i,j] = dt if np.abs(co) > correlation_threshold else np.nan
            CO[i,j] = co

    timeshift_data = namedtuple("Timeshift_MatrixData", ["matrix", "correlation"])
    matrix      = pd.DataFrame(DT, columns=signals.keys(), index=signals.keys())
    correlation = pd.DataFrame(CO, columns=signals.keys(), index=signals.keys())
    return timeshift_data(matrix, correlation)

def timeshiftOrder(timeshift_matrix, reference=None):
    if reference == None:
        reference = timeshift_matrix.columns[0]
    timeshift_vector = timeshift_matrix[reference]
    ''' Check that at least one element other than reference is not nan '''
    valid = False
    for k in timeshift_vector.index:
        if (k != reference) and not(np.isnan(timeshift_vector[k])):
            valid = True
    if not(valid):
        timeshift_vector[reference] = np.nan
    ''' continue '''
    timeshift_values = [x for x in timeshift_vector if not(np.isnan(x))]
    if len(timeshift_values) == 0:
        timeshift_values.append(0)
    timeshift_vector_pos = timeshift_vector - min(timeshift_values)
    timeshift_vector_pos_sorted = timeshift_vector_pos.sort_values()
    order_data = namedtuple("Timeshift_OrderData", ["series", "order", "values", "average", "std"])
    order = [idx for idx in timeshift_vector_pos_sorted.index if not(np.isnan(timeshift_vector_pos_sorted[idx]))]
    timeshift_values = [timeshift_vector_pos_sorted[idx] for idx in order]
    timeshift_values_without_reference = [x for x,idx in zip(timeshift_values, order) if idx != reference]
    average = np.average(timeshift_values_without_reference) if len(timeshift_values_without_reference) else np.nan
    std     =     np.std(timeshift_values_without_reference) if len(timeshift_values_without_reference) else np.nan
    return order_data(timeshift_vector_pos_sorted, order, timeshift_values, average, std)

def order_matrix(rolling_order):
    # print(rolling_order)
    N = len(rolling_order[0].series) # Number of channels
    channels = rolling_order[0].series.index
    orders   = [f"#{i+1}" for i in range(N)]
    percentage = pd.DataFrame(np.zeros((N,N)), columns=channels, index=orders)
    dt_avg     = pd.DataFrame(np.zeros((N,N)), columns=channels, index=orders)
    dt_std     = pd.DataFrame(np.zeros((N,N)), columns=channels, index=orders)
    occurences = pd.DataFrame(np.zeros((N,N)), columns=channels, index=orders)
    for i,n in enumerate(orders):
        for ch in channels:
            # We are checking, for each window, if current channel ch is at rank n
            is_current_channel = [(ro.order[i] == ch) if len(ro.order) > i else False for ro in rolling_order]
            dt_values = [ro.values[i] for icc,ro in zip(is_current_channel, rolling_order) if icc]
            pc = 100. * sum(is_current_channel) / len(rolling_order)
            avg = np.mean(dt_values) if dt_values else 0
            std = np.std (dt_values) if dt_values else 0
            occ = sum(is_current_channel)
            percentage[ch][n] = pc
            dt_avg[ch][n]     = avg
            dt_std[ch][n]     = std
            occurences[ch][n] = occ
    order_stats = namedtuple("Order_Stats", ["percentage", "dt", "dt_std", "N", "Ntotal"])
    return order_stats(percentage, dt_avg, dt_std, occurences, len(rolling_order))

def rolling_RMS(waveforms, window_samples=10):
    N = 0
    for i,k in enumerate(waveforms):
        if i > 0:
            assert (len(waveforms[k]) == N), "Waveforms must be of equal lengths"
        N = len(waveforms[k])

    window = np.ones(window_samples)
    # window = signal.triang(window_samples)
    window = window / sum(window) # normalize window

    ''' Compute Square, Mean, and Root separately for better performance '''
    waveforms___s = {}
    waveforms__ms = {}
    waveforms_rms = {}
    for i,k in enumerate(waveforms):
        waveforms___s[k] = np.square(waveforms[k]) # Compute square of signal
        pbar(i, len(waveforms), prefix='Rolling RMS (S)')
    for i,k in enumerate(waveforms___s):
        waveforms__ms[k] = np.convolve(waveforms___s[k], window, 'valid') # Rolling mean using convolution for better performance
        pbar(i, len(waveforms), prefix='Rolling RMS (M)')
    for i,k in enumerate(waveforms__ms):
        waveforms_rms[k] = np.sqrt(waveforms__ms[k]) # Compute sqrt of rolling mean
        pbar(i, len(waveforms), prefix='Rolling RMS (R)')

    return waveforms_rms

def rolling_normalization(waveforms, window_samples=10, overlap_samples=5):
    N = 0
    for i,k in enumerate(waveforms):
        if i > 0:
            assert (len(waveforms[k]) == N), "Waveforms must be of equal lengths"
        N = len(waveforms[k])

    skip_samples    = int(window_samples - overlap_samples)

    i = 0
    j = i + window_samples
    output = {k:1. * np.asarray(waveforms[k]) for k in waveforms}
    while j < N:
        ''' Apply window to samples & Compute RMS '''
        for k in waveforms:
            windowed_waveform = 1 * np.asarray(waveforms[k])[i:j]
            output[k][i:j] = windowed_waveform/np.max(windowed_waveform)
        ''' Advance window '''
        i += skip_samples
        j = i + window_samples
        pbar(j, N, prefix='Rolling normalization')

    return output

def percentile_threshold(waveforms, threshold=50):
    return {k:(1.*(np.asarray(waveforms[k]) > np.percentile(waveforms[k], threshold))) for k in waveforms}

def percentile_hysteresis(waveforms, threshold_up=70, threshold_dn=30):
    output = {k:[] for k in waveforms}
    for k in waveforms:
        W = np.asarray(waveforms[k])
        state = 0
        for w in W:
            if (state == 0) and (w > threshold_up):
                state = 1
            if (state == 1) and (w < threshold_dn):
                state = 0
            output[k].append(state)
    return output


def get_timeshift(X, Y):
    """ Fast, but not a real correlation output (?) """
    ''' Normalize data '''
    x = 0 + np.asarray(X)
    y = 0 + np.asarray(Y)
    x -= np.mean(x)
    y -= np.mean(y)
    x /= np.std(x)
    y /= np.std(y)
    Nx = len(x)
    Ny = len(y)
    n1 = min(Nx,Ny)
    n2 = max(Nx,Ny)
    Nmin = (n1 - 1) + np.ceil((n2 - n1)/2)
    Nmax = (n1 - 1) + np.floor((n2 - n1)/2)
    minheight = int(0.1)
    ''' Compute xcorr '''
    xcorr = signal.correlate(x, y)
    xcorr = xcorr/n2
    ''' Retrieve shift '''
    dt = np.arange(-Nmin, Nmax+1)
    i = xcorr.argmax()
    shift = dt[i]
    value = xcorr[i]
    ''' Debug '''
    # h = plt.figure(figsize=(9,4))
    # a0 = h.add_subplot(121)
    # a1 = h.add_subplot(122)
    # a0.plot(dt,xcorr)
    # a0.plot([shift], [value], 'o')
    # a0.set_title(f"Shift = {shift} samples")
    # timex = np.linspace(0, len(x), len(x))
    # timey = np.linspace(0, len(y), len(y))
    # a1.plot(timex, x, ':', color='red')
    # a1.plot(timey, y, ':', color='green')
    # a1.plot(timex, x, '-', color='red')
    # a1.plot(timey+shift, y, '-', color='green')
    # plt.show()
    xco_data = namedtuple("xco", ["dt", "correlation"])
    return xco_data(shift, value)

def get_timeshift2(X, Y):
    """ Extremely slow """
    ''' Normalize data '''
    x = pd.Series(X)
    y = pd.Series(Y)
    def xco(x, y, percentage_covered=100.0):
        ''' Assuming both series have the same size '''
        N = int((percentage_covered/100.) * len(x))
        lag   = list(range(-N, N+1))
        output = [x.corr(y.shift(dt)) for dt in lag]
        return pd.Series(output, index=lag)


    ''' Compute xcorr '''
    xcorr_series = xco(x, y, percentage_covered=50)
    ''' Retrieve shift '''
    xcorr = xcorr_series.values
    dt = xcorr_series.index
    peak_idx = xcorr.argmax()
    peak_t = dt[peak_idx]
    shift = peak_t
    value = xcorr[peak_idx]
    # peaks_idx = signal.find_peaks(xcorr, height=minheight)[0]
    # peaks_t = dt[peaks_idx]
    # if peaks_t.any():
    #     shift = peaks_t[np.abs(peaks_t).argmin()]
    #     value = xcorr[np.where(dt == shift)[0]]
    # else:
    #     shift = 0
    #     value = 0

    ''' Debug '''
    # plt.figure()
    # plt.plot(dt,xcorr)
    # plt.plot([shift], [value], 'o')
    # plt.title(f"Shift = {shift} samples")
    # plt.show()
    xco_data = namedtuple("xco", ["dt", "correlation"])
    return xco_data(shift, value)

def detect_rising_edges(waveforms, window_samples):
    window_samples = int(window_samples)
    window = np.zeros(window_samples) - 1
    half_point =int(window_samples/2)
    window[half_point:] = 1
    output = {}
    for k in waveforms:
        output[k] = signal.correlate(waveforms[k], window, mode="valid")
    return output

def hysteresis_comparator(x, threshold_lo, threshold_hi, init=False):
    if threshold_lo != threshold_hi:
        x = np.asarray(x)
        ''' Handle reversed thresholds mode '''
        if threshold_lo > threshold_hi:
            x = x[::-1]
            threshold_lo, threshold_hi = threshold_hi, threshold_lo
            reversed = True
        else:
            reversed = False
        ''' Compute hysteresis (fast) '''
        hi = (x >= threshold_hi)
        lo_or_hi = ((x <= threshold_lo) | hi)
        ind = np.nonzero(lo_or_hi)[0]
        if not ind.size:
            x_hyst = np.zeros_like(x, dtype=bool) | init
        else:
            cnt = np.cumsum(lo_or_hi)
            x_hyst = np.where(cnt, hi[ind[cnt-1]], init)
        ''' Handle reversed thresholds mode '''
        if reversed:
            x_hyst = x_hyst[::-1]
        return x_hyst
    else:
        return x >= threshold_lo

def adaptive_hysteresis(waveforms, pc_lo=75, pc_hi=25):
    output = {}
    for k in waveforms:
        pc0 = np.percentile(waveforms[k], pc_lo)
        pc1 = np.percentile(waveforms[k], pc_hi)
        output[k] = hysteresis_comparator(waveforms[k], threshold_lo=pc0, threshold_hi=pc1)
    return output

def adaptive_simpleThreshold(waveforms, threshold_relative=0.1, max_pc=100.):
    output = {}
    for k in waveforms:
        threshold = threshold_relative * np.percentile(waveforms[k], max_pc)
        output[k] = (np.asarray(waveforms[k]) > threshold)
    return output

def adaptive_threshold_value(x, relative_threshold=0.5, min_pc=0, max_pc=100):
    y0 = np.percentile(x, min_pc)
    y1 = np.percentile(x, max_pc)
    return y0 + relative_threshold*(y1-y0)

def percentile_superimposition(waveforms, reference=None, min_pc=None, max_pc=100, keys=None):
    if keys == None:
        keys = waveforms
    waveforms = {k: 0+np.asarray(waveforms[k]) for k in waveforms} # Deep copy
    keys      = {k: 0+np.asarray(keys[k]     ) for k in keys     } # Deep copy
    if min_pc != None:
        waveforms = {k: waveforms[k] - np.percentile(keys[k], min_pc) for k in waveforms}
        keys      = {k: keys[k]      - np.percentile(keys[k], min_pc) for k in waveforms}
    reference_key = keys[reference] if reference else np.average([np.asarray(keys[k]) for k in waveforms], axis=0)
    ''' Get linear relationship '''
    A = {} # As in ax + b
    B = {} # As in ax + b
    for k in waveforms:
        popt, pcov = optimize.curve_fit(lambda x,a,b: a*x+b, keys[k], reference_key)
        A[k] = popt[0]
        B[k] = popt[1]
    upper_value = np.percentile(reference_key, max_pc)
    normalization = 1./upper_value
    ''' Scale & offset & assign '''
    output = {}
    for k in waveforms:
        if k==reference:
            output[k] = np.asarray(waveforms[k]) * normalization
        else:
            output[k] = (np.asarray(waveforms[k]) * A[k] + B[k]) * normalization
    return output

def percentile_normalization(waveform, min_pc=0, max_pc=100, symmetric=True):
    assert symmetric, "Asymmetric not yet supported."
    waveform = 0+np.asarray(waveform) # Deep copy
    if symmetric:
        y_pos = np.percentile(waveform, max_pc)
        y_neg = np.percentile(waveform, min_pc)
        y_ref = max(abs(y_pos), abs(y_neg))
        waveform = waveform / y_ref
    else:
        pass
    return waveform

def get_best_distribution(data):
    continuous_distributions = {}
    continuous_distributions["alpha"] = stats.alpha
    continuous_distributions["anglit"] = stats.anglit
    continuous_distributions["arcsine"] = stats.arcsine
    continuous_distributions["argus"] = stats.argus
    continuous_distributions["beta"] = stats.beta
    continuous_distributions["betaprime"] = stats.betaprime
    continuous_distributions["bradford"] = stats.bradford
    continuous_distributions["burr"] = stats.burr
    continuous_distributions["burr12"] = stats.burr12
    continuous_distributions["cauchy"] = stats.cauchy
    continuous_distributions["chi"] = stats.chi
    continuous_distributions["chi2"] = stats.chi2
    continuous_distributions["cosine"] = stats.cosine
    continuous_distributions["crystalball"] = stats.crystalball
    continuous_distributions["dgamma"] = stats.dgamma
    continuous_distributions["dweibull"] = stats.dweibull
    continuous_distributions["erlang"] = stats.erlang
    continuous_distributions["expon"] = stats.expon
    continuous_distributions["exponnorm"] = stats.exponnorm
    continuous_distributions["exponweib"] = stats.exponweib
    continuous_distributions["exponpow"] = stats.exponpow
    continuous_distributions["f"] = stats.f
    continuous_distributions["fatiguelife"] = stats.fatiguelife
    continuous_distributions["fisk"] = stats.fisk
    continuous_distributions["foldcauchy"] = stats.foldcauchy
    continuous_distributions["foldnorm"] = stats.foldnorm
    continuous_distributions["frechet_r"] = stats.frechet_r
    continuous_distributions["frechet_l"] = stats.frechet_l
    continuous_distributions["genlogistic"] = stats.genlogistic
    continuous_distributions["gennorm"] = stats.gennorm
    continuous_distributions["genpareto"] = stats.genpareto
    continuous_distributions["genexpon"] = stats.genexpon
    continuous_distributions["genextreme"] = stats.genextreme
    continuous_distributions["gausshyper"] = stats.gausshyper
    continuous_distributions["gamma"] = stats.gamma
    continuous_distributions["gengamma"] = stats.gengamma
    continuous_distributions["genhalflogistic"] = stats.genhalflogistic
    # continuous_distributions["geninvgauss"] = stats.geninvgauss
    continuous_distributions["gilbrat"] = stats.gilbrat
    continuous_distributions["gompertz"] = stats.gompertz
    continuous_distributions["gumbel_r"] = stats.gumbel_r
    continuous_distributions["gumbel_l"] = stats.gumbel_l
    continuous_distributions["halfcauchy"] = stats.halfcauchy
    continuous_distributions["halflogistic"] = stats.halflogistic
    continuous_distributions["halfnorm"] = stats.halfnorm
    continuous_distributions["halfgennorm"] = stats.halfgennorm
    continuous_distributions["hypsecant"] = stats.hypsecant
    continuous_distributions["invgamma"] = stats.invgamma
    continuous_distributions["invgauss"] = stats.invgauss
    continuous_distributions["invweibull"] = stats.invweibull
    continuous_distributions["johnsonsb"] = stats.johnsonsb
    continuous_distributions["johnsonsu"] = stats.johnsonsu
    continuous_distributions["kappa4"] = stats.kappa4
    continuous_distributions["kappa3"] = stats.kappa3
    continuous_distributions["ksone"] = stats.ksone
    # continuous_distributions["kstwo"] = stats.kstwo
    continuous_distributions["kstwobign"] = stats.kstwobign
    continuous_distributions["laplace"] = stats.laplace
    continuous_distributions["levy"] = stats.levy
    continuous_distributions["levy_l"] = stats.levy_l
    # continuous_distributions["levy_stable"] = stats.levy_stable
    continuous_distributions["logistic"] = stats.logistic
    continuous_distributions["loggamma"] = stats.loggamma
    continuous_distributions["loglaplace"] = stats.loglaplace
    continuous_distributions["lognorm"] = stats.lognorm
    # continuous_distributions["loguniform"] = stats.loguniform
    continuous_distributions["lomax"] = stats.lomax
    continuous_distributions["maxwell"] = stats.maxwell
    continuous_distributions["mielke"] = stats.mielke
    continuous_distributions["moyal"] = stats.moyal
    continuous_distributions["nakagami"] = stats.nakagami
    continuous_distributions["ncx2"] = stats.ncx2
    continuous_distributions["ncf"] = stats.ncf
    continuous_distributions["nct"] = stats.nct
    continuous_distributions["norm"] = stats.norm
    continuous_distributions["norminvgauss"] = stats.norminvgauss
    continuous_distributions["pareto"] = stats.pareto
    continuous_distributions["pearson3"] = stats.pearson3
    continuous_distributions["powerlaw"] = stats.powerlaw
    continuous_distributions["powerlognorm"] = stats.powerlognorm
    continuous_distributions["powernorm"] = stats.powernorm
    continuous_distributions["rdist"] = stats.rdist
    continuous_distributions["rayleigh"] = stats.rayleigh
    continuous_distributions["rice"] = stats.rice
    continuous_distributions["recipinvgauss"] = stats.recipinvgauss
    continuous_distributions["semicircular"] = stats.semicircular
    continuous_distributions["skewnorm"] = stats.skewnorm
    continuous_distributions["t"] = stats.t
    continuous_distributions["trapz"] = stats.trapz
    continuous_distributions["triang"] = stats.triang
    continuous_distributions["truncexpon"] = stats.truncexpon
    continuous_distributions["truncnorm"] = stats.truncnorm
    continuous_distributions["tukeylambda"] = stats.tukeylambda
    continuous_distributions["uniform"] = stats.uniform
    continuous_distributions["vonmises"] = stats.vonmises
    continuous_distributions["vonmises_line"] = stats.vonmises_line
    continuous_distributions["wald"] = stats.wald
    continuous_distributions["weibull_min"] = stats.weibull_min
    continuous_distributions["weibull_max"] = stats.weibull_max
    continuous_distributions["wrapcauchy"] = stats.wrapcauchy
    results = {}
    for i,k in enumerate(continuous_distributions):
        pbar(i,len(continuous_distributions), prefix="Getting best distribution", suffix=k)
        try:
            mle_results = MLE(data, continuous_distributions[k])
            success = mle_results.success
        except:
            success = False
        if success:
            results[k] = np.sum(continuous_distributions[k].logpdf(data, *mle_results.x))
        else:
            results[k] = -np.inf
    # print(results)
    for k in results:
        if results[k] == max(list(results.values())):
            print(f"Best distribution found : {k}")
            return continuous_distributions[k]



def MLE(data, distribution="norm"):
    ''' Maximum Likelihood Estimation '''
    if type(distribution) is str:
        assert distribution.lower() in ["norm", "normal", "chi2", "chisq", "chisquare", "laplace", "levy_stable"], "Unsupported probability distribution function."
        if distribution.lower() in ["norm", "normal"]:
            distribution = stats.norm
        elif distribution.lower() in ["chi2", "chisq", "chisquare"]:
            distribution = stats.chi2
        elif distribution.lower() in ["laplace"]:
            distribution = stats.laplace
        elif distribution.lower() in ["levy_stable"]:
            distribution = stats.levy_stable
    N_params = len(signature(distribution.logpdf).parameters)
    LL = lambda params : np.sum(distribution.logpdf(data, *params))
    negLL = lambda params : -LL(params)
    results = minimize(negLL, np.random.rand(N_params - 1), method='Nelder-Mead', options={'disp': False, 'maxiter': 1000})
    # print(f"MLE : Distribution is maximum at x={results.x[0]}")
    return results

def LRT(data, distribution="norm", distribution_parameters=()):
    ''' Likelihood Ratio Test '''
    if type(distribution) is str:
        assert distribution.lower() in ["norm", "normal", "chi2", "chisq", "chisquare", "laplace", "levy_stable"], "Unsupported probability distribution function."
        if distribution.lower() in ["norm", "normal"]:
            distribution = stats.norm
        elif distribution.lower() in ["chi2", "chisq", "chisquare"]:
            distribution = stats.chi2
        elif distribution.lower() in ["laplace"]:
            distribution = stats.laplace
        elif distribution.lower() in ["levy_stable"]:
            distribution = stats.levy_stable
    # plt.figure()
    # plt.hist(data, bins=1000, density=True)
    # x = np.linspace(min(data),max(data),1000,False)
    # plt.plot(x,distribution.pdf(x, *distribution_parameters))
    # plt.show()
    N_params = len(signature(distribution.pdf).parameters)
    negpdf = lambda x : -distribution.logpdf(x, *distribution_parameters)
    sup_results = minimize(negpdf, np.random.rand(), method='Nelder-Mead', options={'disp': False})
    max_llx = sup_results.x[0]
    # print(f"LRT : Distribution is maximum at x={sup_results.x[0]}")
    return 2*(distribution.logpdf(max_llx, *distribution_parameters) - distribution.logpdf(data, *distribution_parameters))

def filter_channels(data={}, filter=[]):
    data_out = {}
    for k in data:
        if k in filter:
            data_out[k] = data[k]
    return data_out

def exclude_channels(data={}, filter=[]):
    data_out = {}
    for k in data:
        if k not in filter:
            data_out[k] = data[k]
    return data_out

def resample(data, fs_origin, fs_destination):
    ratio = fs_destination / fs_origin
    N_origin = len(data)
    N_destination = int(N_origin * ratio)
    return signal.resample(data, N_destination)

def resample_timestamps(timestamps, fs_origin, fs_destination):
    resampled_timestamps = {}
    for k in timestamps:
        resampled_timestamps[k] = [int(ts * (fs_destination / fs_origin)) for ts in timestamps[k]]
    return resampled_timestamps

def resample_waveforms(waveforms, fs_origin, fs_destination):
    return map_to_dict(resample, waveforms, fs_origin=fs_origin, fs_destination=fs_destination, progress_message="Resampling waveforms")

def crop_waveforms(waveforms, bounds_samples):
    i0 = bounds_samples[0]
    i1 = bounds_samples[1]
    return {k: (1.*np.asarray(waveforms[k]))[i0:i1] for k in waveforms}

def crop_timestamps(timestamps, bounds):
    i0 = bounds[0]
    i1 = bounds[1]
    return {k: [ts-i0 for ts in timestamps[k] if ((ts >= i0) and (ts < i1))] for k in timestamps}

def fast_downsample_waveforms(waveforms, fs_origin, fs_destination):
    ratio = fs_origin/fs_destination
    assert (int(ratio) == ratio), "downsampling ratio must be an integer."
    def fast_downsample(x, ratio):
        x = 1. * np.asarray(x)
        ratio = int(ratio)
        return x[::ratio]
    return map_to_dict(fast_downsample, waveforms, ratio=ratio, progress_message="Downsampling waveforms (fast)")

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

def deepcopy_data(data={}):
    data_out = {}
    for k in data:
        data_out[k] = [d for d in data[k]]
    return data_out

def relabel_data(data, rule):
    return {rule[k]: data[k] for k in data}
    # output = {}
    # for k in data:
    #     if k in rule:
    #         output[rule[k]] = data[k]
    #     else:
    #         print(f"Could not find key {k} in rule")

""" FILTERING """

class BPfilters:
    def __init__(self, lp=[], hp=[], notch=[], filtertype='butterworth', Fs=0.5):
        ''' lp = [(Fc0 , order0 ), ..., (Fcn , ordern )] '''
        ''' hp = [(Fc0', order0'), ..., (Fcn', ordern')] '''
        ''' notch = [(Fc0', Q0'), ..., (Fcn', Qn')] '''
        ''' filtertype = butterworth, bessel '''
        self.Fs = Fs
        self.filters = {}
        self.filters['lp'] = lp
        self.filters['hp'] = hp
        self.filters['notch'] = notch

        self.filtertypes = {}
        self.filtertypes['butterworth'] = signal.butter
        self.filtertypes['butter']      = signal.butter
        self.filtertypes['bessel']      = signal.bessel
        try:
            self.filtertype = self.filtertypes[filtertype.lower()]
        except:
            print("Warning : unknown filter type {}, defaulted to Butterworth.")
            self.filtertype = signal.butter
    def run(self, sig):
        filtered = 1. * np.asarray(sig)
        for hp in self.filters['hp']:
            (Fc, order) = hp
            sos = self.filtertype(N=order, Wn=Fc, btype='hp', fs=self.Fs, output='sos')
            filtered = signal.sosfiltfilt(sos, filtered)
        for lp in self.filters['lp']:
            (Fc, order) = lp
            sos = self.filtertype(N=order, Wn=Fc, btype='lp', fs=self.Fs, output='sos')
            filtered = signal.sosfiltfilt(sos, filtered)
        for notch in self.filters['notch']:
            (Fc, Q) = notch
            b, a = signal.iirnotch(w0=Fc, Q=Q, fs=self.Fs)
            filtered = signal.filtfilt(b, a, filtered)
        return filtered
    def getConfig(self):
        return self.filters
    def getConfigTex(self):
        return ""

class DWT:
    def __init__(self, levels, wlttype='haar'):
        self.coeffs = {}
        self.coeffs['db4']     = {'lp' : [-0.0105974018, 0.0328830117, 0.0308413818, -0.1870348117, -0.0279837694, 0.6308807679, 0.7148465706, 0.2303778133], 'hp' : [-0.2303778133, 0.7148465706, -0.6308807679, -0.0279837694, 0.1870348117, 0.0308413818, -0.0328830117, -0.0105974018]}
        self.coeffs['haar']    = {'lp' : [0.7071067812, 0.7071067812, 0., 0., 0., 0., 0., 0.], 'hp' : [-0.7071067812, 0.7071067812, 0., 0., 0., 0., 0., 0.]}
        self.coeffs['bior1.3'] = {'lp' : [-0.088388347648318447, 0.088388347648318447, 0.70710678118654757, 0.70710678118654757, 0.088388347648318447, -0.088388347648318447], 'hp' : [0., 0., -0.70710678118654757, 0.70710678118654757, 0., 0.]}
        self.coeffs['sym2']    = {'lp' : [-0.12940952255092145, 0.22414386804185735, 0.83651630373746899, 0.48296291314469025], 'hp' : [-0.48296291314469025, 0.83651630373746899, -0.22414386804185735, -0.12940952255092145]}
        self.coeffs['coif1.1'] = {'lp' : [-0.01565572813546454, 0.072732619512853897, .38486484686420286, .85257202021225542, .33789766245780922, 0.072732619512853897], 'hp' : [0.072732619512853897, 0.33789766245780922, -0.85257202021225542, 0.38486484686420286, 0.072732619512853897, -0.01565572813546454]}
        self.wlt    = wlttype
        self.levels = levels
    def run(self, sig):
        filtered = sig
        N = len(sig)
        coeffs_hp = [c for c in self.coeffs[self.wlt]['lp']]
        coeffs_lp = [c for c in self.coeffs[self.wlt]['hp']]
        for l in range(self.levels):
            hipass = signal.convolve(filtered, coeffs_hp, mode="full", method='fft')
            lopass = signal.convolve(filtered, coeffs_lp, mode="full", method='fft')
            hipass *= (1./np.sqrt(2)) # Normalization
            lopass *= (1./np.sqrt(2)) # Normalization
            coeffs_hp = [item for item in coeffs_hp for i in range(2)] # Duplicate coeff elements
            coeffs_lp = [item for item in coeffs_lp for i in range(2)] # Duplicate coeff elements
            filtered = lopass
        filtered = lopass
        return filtered

class CWT:
    def __init__(self, levels, wlttype='mexh'):
        self.wlt    = wlttype
        self.levels = levels
    def run(self, sig):
        wavelet_output = pywt.cwt(sig, self.levels, self.wlt)
        return wavelet_output[0][0]

class WLTdenoise:
    def __init__(self, threshold=0.04, wlttype="mexh", minlevel=None, maxlevel=None):
        self.wlt = wlttype
        self.threshold = threshold
        self.minlevel = minlevel
        self.maxlevel = maxlevel
    def run(self, sig):
        print("    Running wavelet denoise")
        w = pywt.Wavelet(self.wlt)
        if self.maxlevel is None:
            self.maxlevel = pywt.dwt_max_level(len(sig), w.dec_len)
            print('      Max decomposition level set to {}'.format(self.maxlevel))
        if self.minlevel is None:
            self.minlevel = 0
        coeffs   = pywt.wavedec(sig, self.wlt, level=self.maxlevel)
        for i in range(0, self.minlevel):
            coeffs[i] = pywt.threshold(coeffs[i], np.inf)
        for i in range(self.minlevel, len(coeffs)):
            print('      Decomposition level {} range : {:.3f} - {:.3f}'.format(i, min(coeffs[i]), max(coeffs[i])))
            coeffs[i] = pywt.threshold(coeffs[i], self.threshold * max(coeffs[i]))
        print('    Filtered coefficients :')
        for i,c in enumerate(coeffs):
            print('      #{} : {:.3f} - {:.3f}'.format(i, min(c), max(c)))
        datarec = pywt.waverec(coeffs, self.wlt)
        return datarec

def generate_filter(filter_description):
    family = filter_description['family']
    if type(family) == str:
        if family in ['BP', 'bp', 'band-bass', 'BPfilters']:
            family = BPfilters
        if family in ['dwt', 'DWT']:
            family = DWT
        if family in ['cwt', 'CWT']:
            family = CWT
        if family in ['wltdenoise', 'WLTdenoise', 'wlt', 'WLT']:
            family = WLTdenoise

    args = filter_description['args']
    return family(**args)

if __name__ == "__main__":
    import time
    def test_map_to_dict():
        labels = ["a", "b", "c"]
        signals = {k: np.random.rand(100) for k in labels}
        def f(x,k):
            return x*k
        param = 2
        expected_output = {k: f(signals[k], k=2) for k in labels}
        def isequal(a,b):
            ''' Function to check equality of dicts of np arrays '''
            if a.keys() != b.keys():
                ''' Check keys '''
                return False
            for k in a:
                ''' Check each numpy array couple '''
                if not(np.array_equal(a[k],b[k])):
                    return False
            return True
        computed_output0 = map_to_dict(f, signals, param)   # *args
        computed_output1 = map_to_dict(f, signals, k=param) # **kwargs
        assert isequal(computed_output0, expected_output), f"map_to_dict : expected {expected_output} (got {computed_output0})"
        assert isequal(computed_output1, expected_output), f"map_to_dict : expected {expected_output} (got {computed_output1})"
        print("map_to_dict passed.")
    def test_fast_downsample():
        input = {"data":[0,1,2,3,4,5,6,7,8,9]}
        expected_output = {"data":[0,2,4,6,8]}
        fs_origin = 2
        fs_destination = 1
        computed_output = fast_downsample_waveforms(input, fs_origin, fs_destination)
        computed_output = {k: computed_output[k].tolist() for k in computed_output}
        assert computed_output == expected_output, f"fast_downsample_waveforms : expected {expected_output} (got {computed_output})"
        print("fast_downsample_waveforms passed.")
    def test_apply_rolling():
        N = 100000
        array1d = np.random.random(N)
        window = 100
        shift = 1
        func   = lambda x : np.sqrt(np.sum(np.square(x)))
        func1d = lambda x : np.sqrt(np.sum(np.square(x), axis=1))
        expected_output = []
        ''' Simple loop '''
        te0 = time.time()
        i = 0
        j = i + window
        while j < len(array1d):
            expected_output.append(func(array1d[i:j]))
            i += shift
            j += shift
        te1 = time.time()
        ''' Numpy broadcast '''
        tc0 = time.time()
        computed_output = apply_rolling(func1d, array1d, window, shift)
        tc1 = time.time()
        computed_output = computed_output.tolist()
        assert len(computed_output) == len(expected_output), f"apply_rolling failed : dimensions do not match (expected {len(expected_output)} but got {len(computed_output)})"
        mse = (np.square(np.asarray(computed_output) - np.asarray(expected_output))).mean()
        assert mse < 1e-6, f"apply_rolling failed (error = {mse})"
        tpce = 1000 * (te1 - te0) / N
        tpcc = 1000 * (tc1 - tc0) / N
        print(f'apply_rolling passed (np broadcast : {tpcc:.4f} ms/cycle vs Simple loop : {tpce:.4f} ms/cycle, mse={mse:.4f})')
    test_map_to_dict()
    test_fast_downsample()
    test_apply_rolling()
    print("All passed.")
