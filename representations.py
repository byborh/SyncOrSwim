import numpy as np
import seaborn as sb
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import animation as animation
import scipy.cluster.hierarchy as spc

def drawClusterTimestamps(timestamps, cluster):
    if len(cluster) > 1:
        all_timestamps = [t for sublist in timestamps.values() for t in sublist]
        Np = int(max(all_timestamps) + 1)

        f, ax = plt.subplots(figsize =(7, 4))
        plots = []
        for i,k in enumerate(cluster):
            t = timestamps[k]
            diracEvents = np.zeros(Np)
            diracEvents[t] = 1.
            p, = ax.plot(diracEvents + i*1.1)
            plots.append(p)
        plt.title("Events in cluster " + ', '.join(cluster))
        plt.legend(plots, cluster)
        # plt.show()

def drawClusteredEvents(timestamps, linkage):
    labels = [k for k in timestamps.keys()]
    f = plt.figure(figsize=(7,5))
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

def drawClustersSpatial(correlation_data, cluster_data, layout):
    h = plt.figure()
    a = h.add_subplot(111)
    a.set_title("Identified clusters (unpolished)")
    cmap = mpl.cm.get_cmap('YlGnBu')
    for cluster in cluster_data["clusters"]:
        for label0 in cluster:
            for label1 in cluster:
                if label0 != label1:
                    pos0 = layout.getElectrode(label0).position
                    pos1 = layout.getElectrode(label1).position
                    color = cmap(correlation_data["dataframe"][label0][label1])
                    plt.plot([pos0.x, pos1.x],[pos0.y, pos1.y], color=color)
    for e in layout.electrodes:
        a.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=1.0)
        # a.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')
    return h

def drawCorrelationSpatial(correlation_data, layout, threshold=0.5, ax=None):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    cmap = mpl.cm.get_cmap('YlGnBu')
    ax.set_title("All correlations > {}".format(threshold))

    for label0 in correlation_data["labels"]:
        for label1 in correlation_data["labels"]:
            if label0 != label1:
                corr = correlation_data["dataframe"][label0][label1]
                if abs(corr) >= threshold:
                    pos0 = layout.getElectrode(label0).position
                    pos1 = layout.getElectrode(label1).position
                    color = cmap(corr)
                    ax.plot([pos0.x, pos1.x], [pos0.y, pos1.y], "o-", color=color)
    for e in layout.electrodes:
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=0.0)
        ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')



def animate_rollingCorrelation(rolling_correlation):
    fig = plt.figure()

    def init():
        plt.cla()
        plt.clf()
        data = rolling_correlation['dataframe'][0]
        sb.heatmap(data, cmap ="YlGnBu", vmin=-1.0, vmax=1.0)
        plt.title("t = [{:.2f}, {:.2f}]".format(*rolling_correlation["intervals"][0]))

    def animate(i):
        plt.cla()
        plt.clf()
        i = i % len(rolling_correlation['dataframe'])
        data = rolling_correlation['dataframe'][i]
        sb.heatmap(data, cmap ="YlGnBu", vmin=-1.0, vmax=1.0)
        plt.title("t = [{:.2f}, {:.2f}]".format(*rolling_correlation["intervals"][i]))

    anim = animation.FuncAnimation(fig, animate, init_func=init, interval=500)

    plt.show()

def animate_rollingCorrelationSpatial(rolling_correlation, layout, threshold=0.5):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    def drawFrame(i,rolling_correlation,ax):
        i = i % len(rolling_correlation['dataframe'])
        data = {
            "dataframe": rolling_correlation['dataframe'][i],
            "labels": rolling_correlation['labels'][i]
            }
        drawCorrelationSpatial(data, layout, threshold, ax=ax)
        ax.set_title("t = [{:.2f}, {:.2f}]".format(*rolling_correlation["intervals"][i]))
    drawFrame(0, rolling_correlation, ax)

    def animate(i):
        plt.cla()
        plt.clf()
        ax=fig.gca()
        drawFrame(i, rolling_correlation, ax)

    anim = animation.FuncAnimation(fig, animate, interval=500)

    plt.show()
