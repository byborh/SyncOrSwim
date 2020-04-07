import numpy as np
import seaborn as sb
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

def animate_rollingCorrelation(rolling_correlation):
    fig = plt.figure()

    def init():
        plt.cla()
        plt.clf()
        data = rolling_correlation['dataframe'][0]
        sb.heatmap(data, cmap ="YlGnBu", vmin=-1.0, vmax=1.0)

    def animate(i):
        plt.cla()
        plt.clf()
        i = i % len(rolling_correlation['dataframe'])
        data = rolling_correlation['dataframe'][i]
        sb.heatmap(data, cmap ="YlGnBu", vmin=-1.0, vmax=1.0)

    anim = animation.FuncAnimation(fig, animate, init_func=init, interval=500)

    plt.show()
