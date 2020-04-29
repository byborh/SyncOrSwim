import numpy as np
import seaborn as sb
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import animation as animation
import scipy.cluster.hierarchy as spc
import itertools

def drawClusterTimestamps(timestamps, cluster):
    if len(cluster) > 1:
        all_timestamps = [t for sublist in timestamps.values() for t in sublist]
        Np = int(max(all_timestamps) + 1)

        f, ax = plt.subplots(figsize =(10, 4))
        plots = []
        for i,k in enumerate(cluster):
            t = timestamps[k]
            diracEvents = np.zeros(Np)
            diracEvents[t] = 1.
            p, = ax.plot(diracEvents + i*1.1)
            plots.append(p)
        plt.title("Events in cluster " + ', '.join(cluster))
        plt.legend(plots, cluster)
        plt.tight_layout()
        # plt.show()

def drawClusteredEvents(timestamps, linkage):
    labels = [k for k in timestamps.keys()]
    f = plt.figure(figsize=(10,5))
    a0 = plt.subplot2grid((1,3), (0,0), rowspan=1, colspan=1)
    a1 = plt.subplot2grid((1,3), (0,1), rowspan=1, colspan=2)
    dg = spc.dendrogram(linkage, labels=labels, orientation="left", ax=a0)
    ordered_labels = [labels[i] for i in dg['leaves']]
    for i,k in enumerate(ordered_labels):
        y = timestamps[k]
        x = [i for _ in y]
        a1.plot(y,x, '.', ms=1)

    a0.spines['top'].set_visible(False)
    a0.spines['right'].set_visible(False)
    a0.spines['bottom'].set_visible(False)
    a0.spines['left'].set_visible(False)
    a0.get_xaxis().set_ticks([])
    a0.get_yaxis().set_ticks([])
    a1.get_yaxis().set_ticks(range(len(ordered_labels)))
    a1.set_yticklabels(ordered_labels)

    plt.tight_layout()
    # plt.show()

def drawRollingCorrelation(rolling_correlation):
    labels = rolling_correlation[0].matrix.columns
    f = plt.figure(figsize=(7,5))
    ax = plt.subplot(111)

    for l0,l1 in itertools.combinations(labels, 2):
        corr = [rc.matrix[l0][l1] for rc in rolling_correlation]
        ax.plot(corr, label=f"{l0}-{l1}")
    xticks = [int(i) for i in ax.get_xticks()]
    xtl = ["{} - {} s".format(*rolling_correlation[i].interval) if ((i>=0) and (i < len(rolling_correlation))) else "" for i in xticks]
    ax.set_xticklabels(xtl, rotation=45, ha="right")

    ax.set_title("Rolling correlation")
    plt.legend()

    plt.tight_layout()
    # plt.show()

def drawClusteredRollingCorrelation(rolling_correlation, clusters):
    labels = rolling_correlation[0].matrix.columns
    f = plt.figure(figsize=(7,5))
    ax = plt.subplot(111)

    for cluster in clusters:
        if len(cluster) == 1:
            continue
        corr = np.zeros(len(rolling_correlation))
        combinations = list(itertools.combinations(cluster, 2))
        for l0,l1 in combinations:
            corr += np.asarray([rc.matrix[l0][l1] for rc in rolling_correlation])
        corr /= len(combinations)
        ax.plot(corr, label=f"{cluster}")
    xticks = [int(i) for i in ax.get_xticks()]
    xtl = ["{} - {} s".format(*rolling_correlation[i].interval) if ((i>=0) and (i < len(rolling_correlation))) else "" for i in xticks]
    ax.set_xticklabels(xtl, rotation=45, ha="right")

    ax.set_title("Rolling correlation")
    plt.legend()

    plt.tight_layout()
    # plt.show()

def drawClustersSpatial(correlation_data, cluster_data, layout, ax=None):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    ax.set_title("Identified clusters (unpolished)")
    cmap = mpl.cm.get_cmap('YlGnBu')
    for cluster in cluster_data.clusters:
        for label0 in cluster:
            for label1 in cluster:
                if label0 != label1:
                    pos0 = layout.getElectrode(label0).position
                    pos1 = layout.getElectrode(label1).position
                    color = cmap(correlation_data.matrix[label0][label1])
                    ax.plot([pos0.x, pos1.x],[pos0.y, pos1.y], color=color)
    for e in layout.electrodes:
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=1.0)
        # ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')
    return h

def drawCorrelationSpatial(correlation_data, layout, threshold=0.5, ax=None):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    cmap = mpl.cm.get_cmap('YlGnBu')
    ax.set_title("All correlations > {}".format(threshold))

    for label0 in correlation_data.columns:
        for label1 in correlation_data.columns:
            if label0 != label1:
                corr = correlation_data[label0][label1]
                if abs(corr) >= threshold:
                    pos0 = layout.getElectrode(label0).position
                    pos1 = layout.getElectrode(label1).position
                    color = cmap(corr)
                    ax.plot([pos0.x, pos1.x], [pos0.y, pos1.y], "o-", color=color)
    for e in layout.electrodes:
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=0.0)
        ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')



def animate_rollingCorrelation(rolling_correlation, Fs=1.):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    def drawFrame(i,rolling_correlation,ax):
        i = i % len(rolling_correlation)
        data = rolling_correlation[i].matrix
        sb.heatmap(data, cmap ="YlGnBu", vmin=-1.0, vmax=1.0, ax=ax)
        plt.title("t = [{:.2f}, {:.2f}]".format(*[idx/Fs for idx in rolling_correlation[i].interval]))
    drawFrame(0, rolling_correlation, ax)

    def animate(i):
        plt.cla()
        plt.clf()
        ax=fig.gca()
        drawFrame(i, rolling_correlation, ax)

    anim = animation.FuncAnimation(fig, animate, interval=500)
    plt.show()

def animate_rollingCorrelationSpatial(rolling_correlation, waveforms, layout, threshold=0.5, Fs=1.):
    fig = plt.figure(figsize=(8,4))
    a0 = fig.add_subplot(121)
    a1 = fig.add_subplot(122)
    def drawFrame(i,rolling_correlation,a0):
        i = i % len(rolling_correlation)
        data = rolling_correlation[i].matrix
        drawCorrelationSpatial(data, layout, threshold, ax=a0)
        for j,k in enumerate(waveforms):
            interval = rolling_correlation[i].interval
            waveform = np.asarray(waveforms[k][interval[0]:interval[1]])
            normalization_factor = max(np.abs(waveform))
            normalization_factor = normalization_factor if normalization_factor > 1e-9 else 1.
            waveform /= normalization_factor
            a1.plot(j+waveform, lw=.5)
        a0.set_title("t = [{:.2f}, {:.2f}]".format(*[idx/Fs for idx in rolling_correlation[i].interval]))
    drawFrame(0, rolling_correlation, a0)

    def animate(i):
        a0.clear()
        a1.clear()
        # a0=fig.gca()
        drawFrame(i, rolling_correlation, a0)

    anim = animation.FuncAnimation(fig, animate, interval=500)
    plt.show()
