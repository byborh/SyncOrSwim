import numpy as np
import pandas as pd
import seaborn as sb
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as patches
from matplotlib import animation as animation
from matplotlib import widgets as widgets
from matplotlib import tri as tri
import scipy.cluster.hierarchy as spc
from scipy import stats
import itertools
from player import Player
import progressbar

EMBED_LIMIT_MB = 100
CMAP_CORRELATION_MATRIX = "jet"
CMAP_PHASE_MATRIX = "jet"
CMAP_ISOCHRONES = "rainbow_r"
CMAP_ORDER_PIE = 'rainbow'
CMAP_ORDER_BARGRAPH = 'rainbow'
CMAP_ORDER_SPATIAL = 'copper'
CMAP_ORDER_SUCCESSION = 'jet'

def _unitmgr(Fs, unit="s", magnitude="m"):
    prefixes = {}
    prefixes["Y"]  = 1e24
    prefixes["2"]  = 1e21
    prefixes["3"]  = 1e18
    prefixes["P"]  = 1e15
    prefixes["T"]  = 1e12
    prefixes["G"]  = 1e9
    prefixes["M"]  = 1e6
    prefixes["k"]  = 1e3
    prefixes["h"]  = 1e2
    prefixes["da"] = 1e1
    prefixes[" "]  = 1e0
    prefixes["d"]  = 1e-1
    prefixes["c"]  = 1e-2
    prefixes["m"]  = 1e-3
    prefixes["u"]  = 1e-6
    prefixes["µ"]  = 1e-6
    prefixes["n"]  = 1e-9
    prefixes["p"]  = 1e-12
    prefixes["f"]  = 1e-15
    prefixes["a"]  = 1e-18
    prefixes["z"]  = 1e-21
    prefixes["y"]  = 1e-24
    assert magnitude in prefixes, "Unknown unit prefix."
    if Fs == None:
        Fs = 1.
        unit = "u"
        unit_prefix = 1.
    else:
        unit = f"{magnitude}{unit}"
        unit_prefix = prefixes[magnitude]
    return Fs,unit,unit_prefix


def drawCorrelation(correlation_matrix, title='', bounds=(-1.0, 1.0)):
    cmap = CMAP_CORRELATION_MATRIX
    h = sb.clustermap(correlation_matrix, cmap = cmap, linewidths = 0.1, figsize=(6,6), method='average', vmin=bounds[0], vmax=bounds[1])
    if title:
        h.figure.suptitle(title)
    # plt.show()
    return h

def drawDendrogram(correlation_matrix, linkage):
    h = plt.figure(figsize=(12,4))
    a = h.add_subplot(111)
    labels = correlation_matrix.columns
    dg = spc.dendrogram(linkage, labels=labels, orientation="top", ax=a, leaf_font_size=10)
    a.set_ylabel("Distance")
    plt.tight_layout()
    return h

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
        ax.set_title("Events in cluster " + ', '.join(cluster))
        ax.legend(plots, cluster)
        plt.tight_layout()
        # plt.show()
        return f

def drawClusteredEvents(timestamps, linkage):
    labels = [k for k in timestamps.keys()]
    f = plt.figure(figsize=(10,5))
    a0 = plt.subplot2grid((1,3), (0,0), rowspan=1, colspan=1, fig=f)
    a1 = plt.subplot2grid((1,3), (0,1), rowspan=1, colspan=2, fig=f)
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
    return f

def drawRollingCorrelation(rolling_correlation, Fs=1.):
    labels = rolling_correlation[0].matrix.columns
    f = plt.figure(figsize=(7,5))
    ax = f.add_subplot(111)

    for l0,l1 in itertools.combinations(labels, 2):
        corr = [rc.matrix[l0][l1] for rc in rolling_correlation]
        ax.plot(corr, label=f"{l0}-{l1}")
    xticks = [int(i) for i in ax.get_xticks()]
    time_ranges = [[t/Fs for t in rc.interval] for rc in rolling_correlation]
    xtl = ["{} - {} s".format(*time_ranges[i]) if ((i>=0) and (i < len(rolling_correlation))) else "" for i in xticks]
    ax.set_xticklabels(xtl, rotation=45, ha="right")

    ax.set_title("Rolling correlation")
    ax.legend()

    plt.tight_layout()
    # plt.show()
    return f

def drawAverageRollingCorrelation(rolling_correlation, Fs=1., ax=None):
    if ax is None:
        h = plt.figure(figsize=(7,5))
        ax = h.add_subplot(111)
    labels = rolling_correlation[0].matrix.columns
    correlation = np.zeros(len(rolling_correlation))
    time        = np.asarray([rc.interval[0]/Fs for rc in rolling_correlation])
    N = 0

    for l0,l1 in itertools.combinations(labels, 2):
        correlation += np.asarray([rc.matrix[l0][l1] for rc in rolling_correlation])
        N += 1
    correlation /= N
    ax.plot(time, correlation)
    ax.set_title("Rolling correlation (averaged)")
    return ax.get_figure()

def drawClusteredRollingCorrelation(rolling_correlation, clusters):
    labels = rolling_correlation[0].matrix.columns
    f = plt.figure(figsize=(7,5))
    ax = f.add_subplot(111)

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
    ax.legend()

    plt.tight_layout()
    # plt.show()
    return f

def drawClustersSpatial(correlation_data, cluster_data, layout, ax=None):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    ax.set_title("Identified clusters")
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    clusters_started = set()
    for e in layout.electrodes:
        if not(e.draw):
            continue
        for i,c in enumerate(cluster_data.clusters):
            if e.label in c:
                color = colors[i%len(colors)]
                break
        else:
            # print(f"{e} not in {c}")
            color = "grey"
            i = -1
        if i not in clusters_started:
            ax.plot([], [], 'o', color=color, ms=10, alpha=0.5, label=f"Cluster #{i}") # Dummy legend for first element of cluster only
        clusters_started.add(i)
        ax.plot(e.position.x, e.position.y, 'o', color=color, ms=10, alpha=0.5)
        # ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')
    ax.legend()
    ax.axis('equal')
    return h

def drawPhaseSpatial(phase, layout, ax=None, Fs=1.):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    channels = phase.columns
    ax.set_title("Phase (ms)")
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_PHASE_MATRIX)
    except:
        cmap = mpl.cm.get_cmap(CMAP_PHASE_MATRIX)
    for ch0 in channels:
        for ch1 in channels:
            if (ch0 != ch1) and (phase[ch0][ch1] > 0):
                pos0 = layout.getElectrode(ch0).position
                pos1 = layout.getElectrode(ch1).position
                color = cmap(phase[ch0][ch1])
                dt_s = phase[ch0][ch1]/Fs
                dt_ms = dt_s * 1000.
                distance_um = np.sqrt((pos1.x-pos0.x)**2 + (pos1.y-pos0.y)**2)
                distance_m = distance_um / 1e6
                speed_mps = distance_m / dt_s
                arrowprops = dict(arrowstyle="->, head_width=0.2, head_length=0.8", shrinkA=0, shrinkB=0, linewidth=2.0, color=color)
                ax.annotate("", xytext=(pos0.x, pos0.y), xy=(pos1.x, pos1.y), arrowprops=arrowprops)
                ax.text(*(.5*(pos0+pos1))._to_tuple(), f"{dt_ms:.2f}")
                ax.plot([pos0.x, pos1.x], [pos0.y, pos1.y], "o-", color=color)
    for e in layout.electrodes:
        if not(e.draw):
            continue
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=1.0)
    ax.axis('equal')
    return ax.get_figure()

def drawOrderSpatial(order, layout, ax=None, Fs=1., speed=False):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    channels = order.index
    values = [x for x in order if not(np.isnan(x))]
    title = "(Order) +/- dt [ms]" if not(speed) else "(Order) +/- speed [µm/s]"
    ax.set_title(title)
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_ORDER_SPATIAL)
    except:
        cmap = mpl.cm.get_cmap(CMAP_ORDER_SPATIAL)
    for i,ch in enumerate(channels):
        if i==0:
            pos0 = layout.getElectrode(ch).position
        pos1 = layout.getElectrode(ch).position
        distance_um = np.sqrt((pos1.x-pos0.x)**2 + (pos1.y-pos0.y)**2)
        distance_m = distance_um / 1e6
        dt_s = order[ch] / Fs
        dt_ms = 1000. * dt_s
        if np.isnan(dt_ms):
            continue
        speed_mps = distance_m / dt_s if dt_s > 0 else 0
        speed_umps = 1e6 * speed_mps
        weight = 'bold' if i==0 else 'normal'
        # color = 'red' if (order[ch] == np.max(values)) else 'black'
        color = cmap(0.25*(order[ch]/len(values)))
        ax.text(*pos1._to_tuple(), f"({i+1})", ha='center', va='bottom', weight=weight, color=color)
        dt_or_speed = dt_ms if not(speed) else distance_um
        ax.text(*pos1._to_tuple(), f"{dt_or_speed:+2.1f}", ha='center', va='top', weight=weight, size='smaller', color=color)
    for e in layout.electrodes:
        if not(e.draw):
            continue
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=1.0)
        # ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')
    ''' Contour '''
    x = []
    y = []
    z = []
    for e in layout.electrodes:
        if not(e.draw):
            continue
        ch = e.label
        dt_ms = 1000. * order[ch] / Fs if ch in channels else np.nan
        if not(np.isnan(dt_ms)):
            x.append(e.position.x)
            y.append(e.position.y)
            z.append(dt_ms)
    if len(x) > 2:
        xi = np.linspace(min(x), max(x), 1000)
        yi = np.linspace(min(y), max(y), 1000)
        try:
            triang = tri.Triangulation(x, y)
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)
            ax.contourf(xi,yi,zi, cmap='Greys_r', alpha=0.5)
        except:
            pass
            # print("Triangulation or interpolation error")
    ax.axis('equal')
    return ax.get_figure()

def drawRollingPhaseSpatial(phase_data, layout, ax=None, Fs=1., reference_channel=None, speed=False,
                                contour=True, contourlabels=True, contourmap=None,
                                fill=False, fillmap=CMAP_ISOCHRONES):
    print("Drawing isochrones ... (may take a while)")
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    else:
        h = ax.get_figure()
    channels = phase_data[0].matrix.columns
    title = "Isochrones"
    ax.set_title(title)
    ''' Prep data '''
    reference_channel = channels[0] if reference_channel is None else reference_channel
    values = {str(td.interval): td.matrix[reference_channel] for td in phase_data}
    df_values = pd.DataFrame(values)
    dt_mean = df_values.mean(axis=1, skipna=True)
    dt_std  = df_values.std(axis=1, skipna=True)
    series_dt    = dt_mean     # Measure time offset
    series_speed = dt_mean*0   # Calculated propagation speed (preallocation)
    channels = series_dt.index # List of channels
    # Calculate propagation speed
    for i,ch in enumerate(channels):
        if i==0:
            pos0 = layout.getElectrode(ch).position
        pos1 = layout.getElectrode(ch).position
        distance_um = np.sqrt((pos1.x-pos0.x)**2 + (pos1.y-pos0.y)**2)
        distance_m = distance_um / 1e6
        dt_s = series_dt[ch] / Fs
        dt_ms = 1000. * dt_s
        if np.isnan(dt_ms):
            continue
        speed_mps = distance_m / dt_s if dt_s > 0 else 0
        speed_umps = 1e6 * speed_mps
        series_speed.at[ch] = speed_umps

    ''' Draw isochrones '''
    # Draw electrodes
    for e in layout.electrodes:
        if not(e.draw):
            continue
        fillstyle = 'full' if e.label in channels else 'none'
        ax.plot(e.position.x, e.position.y, marker=e.shape, color="black", ms=5, alpha=1.0, fillstyle=fillstyle)
    # Draw contour (isochrones)
    x = []
    y = []
    z = []
    bounds_x = (np.nan, np.nan)
    bounds_y = (np.nan, np.nan)
    for i,e in enumerate(layout.electrodes):
        if not(e.draw):
            continue
        ch = e.label
        bounds_x = (min(e.position.x, bounds_x[0]), max(e.position.x, bounds_x[1]))
        bounds_y = (min(e.position.y, bounds_y[0]), max(e.position.y, bounds_y[1]))
        zvalue = (1000. * series_dt[ch] / Fs if ch in channels else np.nan) if not speed else (series_speed[ch] if ch in channels else np.nan)
        if not(np.isnan(zvalue)):
            x.append(e.position.x)
            y.append(e.position.y)
            z.append(zvalue)
    if len(x) > 2:
        print("  Interpolating ...")
        xi = np.linspace(*bounds_x, 10000)
        yi = np.linspace(*bounds_y, 10000)
        try:
            # Interpolation
            triang = tri.Triangulation(x, y)
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)
            # Draw contour
            # Params :
                # contour (bool) ; contourlabels (bool) ; contourmap (None/str)
                # fill (bool), fillmap (str)
            if fill:
                fillparams = {"cmap" : fillmap, "alpha":0.75}
                contourf = ax.contourf(xi,yi,zi, **fillparams)
            if contour:
                contourparams = {"colors" : "black"} if contourmap is None else {"cmap" : contourmap}
                contourc = ax.contour(xi,yi,zi, **contourparams)
                if contourlabels :
                    ax.clabel(contourc, inline=True, fontsize=10, fmt="%1.0f ms", inline_spacing=25)
            if fill and fillmap:
                cbar = h.colorbar(contourf, ax=ax)
                cbar.ax.set_ylabel('[ms]', rotation=270)
            elif contour and contourmap:
                cbar = h.colorbar(contourc, ax=ax)
                cbar.ax.set_ylabel('[ms]', rotation=270)
        except:
            pass
            # print("Triangulation or interpolation error")
    h = ax.get_figure()
    ax.set_xlabel("[µm]")
    ax.set_ylabel("[µm]")

    ''' xlim/ylim '''
    xcenter = (bounds_x[0] + bounds_x[1])/2.
    ycenter = (bounds_y[0] + bounds_y[1])/2.
    delta_x = bounds_x[1] - xcenter
    delta_y = bounds_y[1] - ycenter
    margin = 1.2
    ax.axis('equal')
    if delta_x > delta_y:
        ax.set_xlim([xcenter - delta_x*margin, xcenter + delta_x*margin])
    else:
        ax.set_ylim([ycenter - delta_y*margin, ycenter + delta_y*margin])
    print("  All done.")
    return h

def drawOrderBargraph(order_stats, timeinfo=False, Fs=None, highlight_ranks=0):
    N = len(order_stats.percentage.columns)
    fig_width = 0.7 * N
    fig_width = 6.4 if fig_width < 6.4 else fig_width
    fig_width = 12  if fig_width > 12  else fig_width
    h = plt.figure(figsize=(fig_width,4.8))
    a0 = h.add_subplot(111)
    # Custom colormap
    from matplotlib.colors import ListedColormap
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_ORDER_BARGRAPH)
    except:
        cmap = mpl.cm.get_cmap(CMAP_ORDER_BARGRAPH)
    cmap_colors = cmap(np.linspace(0, 1, N))[::-1]
    if highlight_ranks > 0:
        highlight_color = np.array([1,1,0,1]) # Yellow
        cmap_colors[:highlight_ranks, :] = highlight_color
    cmap = ListedColormap(cmap_colors)

    if not(order_stats):
        a0.text(0.5,0.5, "No data to display")
        return h
    percentages = order_stats.percentage
    ''' Order labels '''
    scores = {}
    for col in percentages.columns:
        scores[col] = 0
        for i,idx in enumerate(percentages.index):
            scores[col] += percentages[col][idx] * (1/(i+1))
    ordered_labels = [k for k,_ in sorted(scores.items(), key=lambda item: item[1], reverse=True)]
    N = len(ordered_labels)
    ''' Generate stacked data memory for bar plot '''
    bottom = np.zeros(N)
    ''' Sort out units '''
    Fs, unit, unit_prefix = _unitmgr(Fs, unit="s", magnitude="m")
    ''' Bar plot '''
    percentages_at_ranks = [np.asarray([percentages[col].iloc[i] for col in ordered_labels]) for i in range(percentages.index.size)]
    for i,line in enumerate(percentages_at_ranks):
        color = cmap(i)
        a0.bar(np.arange(N), line, color=color, label=f"#{i+1}", edgecolor=None, bottom=bottom)
        for j,value in enumerate(line):
            if value > 15:
                x = j
                y0 = bottom[j]
                y1 = y0 + value
                col = ordered_labels[j]
                dt     = order_stats.dt[col].iloc[i]     / (Fs * unit_prefix)
                dt_std = order_stats.dt_std[col].iloc[i] / (Fs * unit_prefix)
                txt_idx = f"#{i+1}"
                txt_pc = f"{value:.1f}%"
                txt_N  = f"N={order_stats.N[col].iloc[i]:.0f}"
                txt_dt = f"+{dt:.1f} {unit}"
                txt_std = f"±{dt_std:.1f} {unit}"
                text = f"{txt_idx}: {txt_pc}\n({txt_N})\n{txt_dt}\n{txt_std}" if timeinfo else f"{txt_idx}\n{txt_pc}\n({txt_N})"
                a0.text(x, .5*(y0+y1), text, ha="center", va="center", fontsize=8)
        bottom = bottom + line
    ''' Cosmetics '''
    a0.set_xticks(np.arange(N))
    a0.set_xticklabels(ordered_labels)
    a0.legend(title="Ranks", labelspacing=0.25)
    a0.set_title("Channel ranking repartition")
    a0.set_xlabel("Channel")
    a0.set_ylabel("%")
    a0.set_ylim([0,110])
    plt.tight_layout(pad=0.2)
    return h

def drawOrderPie(order_stats, layout, timeinfo=False, Fs=None, ax=None, distance=0.25, labels=True, highlight_ranks=0):
    N = len(order_stats.percentage.columns)
    ''' Create figure '''
    if ax is None:
        h  = plt.figure(figsize=(6.4*1.1 , 6.4))
        ax = h.add_subplot(111)
    # Custom colormap
    from matplotlib.colors import ListedColormap
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_ORDER_PIE)
    except:
        cmap = mpl.cm.get_cmap(CMAP_ORDER_PIE)
    cmap_colors = cmap(np.linspace(0, 1, N))[::-1]
    if highlight_ranks > 0:
        highlight_color = np.array([1,1,0,1]) # Yellow
        cmap_colors[:highlight_ranks, :] = highlight_color
    cmap = ListedColormap(cmap_colors)

    if not(order_stats):
        ax.text(0.5,0.5, "No data to display")
        return h
    ''' Define pie '''
    def pie(center_x, center_y, radius, data_pc, colors, ax):
        center = (center_x,center_y)
        theta1=0
        theta2=0
        for value,color in zip(data_pc,colors):
            dtheta = 360. * (value/100.)
            if dtheta == 0:
                continue
            theta2 = theta1 + dtheta
            wedge = patches.Wedge(center, radius, theta1, theta2, color=color)
            ax.add_artist(wedge)
            theta1 += dtheta
        circle = patches.Circle(center, radius, color='black', alpha=0.5, lw=.5,fill=False)
        ax.add_artist(circle)
    ''' Sort out units '''
    Fs, unit, unit_prefix = _unitmgr(Fs, unit="s", magnitude="m")
    ''' Draw '''
    channels = order_stats.percentage.columns
    N = len(channels)
    ''' Get min. distance between electrodes '''
    min_distance = np.inf
    for e0 in layout.electrodes:
        for e1 in layout.electrodes:
            if (e1.position - e0.position).norm() != 0:
                min_distance = min(min_distance, (e1.position - e0.position).norm())
    radius = min_distance/(2. + 2.*distance)
    minx= np.inf
    miny= np.inf
    maxx=-np.inf
    maxy=-np.inf
    # colors = [cmap(1-i/N) for i in range(N)]
    colors = [cmap(i) for i in range(N)]
    if not(labels):
        layout.draw(ax=ax, text=False, color="#AAAAAA")
    for e in layout.electrodes:
        if not(e.draw):
            continue
        pos = e.position
        minx = min(minx,pos.x)
        miny = min(miny,pos.y)
        maxx = max(maxx,pos.x)
        maxy = max(maxy,pos.y)
        ax.plot(pos.x, pos.y, 'o', color='black', ms=radius*2, alpha=0.0) #Placeholders for auto x-ylims
        if e.label in channels:
            data_pc = [order_stats.percentage[e.label][i] for i in order_stats.percentage.index]
            pie(pos.x, pos.y, radius, data_pc, colors, ax)
            dt = np.mean([order_stats.dt[e.label][i] for i in order_stats.dt.index]) / (Fs * unit_prefix)
            std = np.std([order_stats.dt[e.label][i] for i in order_stats.dt.index]) / (Fs * unit_prefix)
            if labels:
                text = f"{e.label}\n+{dt:.1f}±{std:.1f} {unit}" if (dt > 0 and std > 0 and timeinfo) else f"{e.label}"
            else:
                text = f"+{dt:.1f}±{std:.1f} {unit}" if (dt > 0 and std > 0 and timeinfo) else ""
            ax.text(pos.x, pos.y, text, color='black', horizontalalignment='center', verticalalignment='center')
        else:
            if labels:
                ax.text(pos.x, pos.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center')

    ''' Cosmetics '''
    box = ax.get_position()
    for i,color in enumerate(colors):
        ax.bar([0],[0], color=color, label=f"#{i+1}")
    ax.bar([0],[0],color="white", label="N/A")
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height]) # Shrink MEA view by 10% to leave space for legend outside
    ax.legend(title="Ranks", labelspacing=0.25, loc='center left', bbox_to_anchor=(1, 0.5)) # Legend outside
    ax.axis('equal')
    ax.set_xlim([minx-1.1*radius,maxx+1.1*radius])
    ax.set_ylim([miny-1.1*radius,maxy+1.1*radius])
    ax.set_xlabel("[µm]")
    ax.set_ylabel("[µm]")
    ax.set_title("Channel ranking repartition (spatial)")
    return ax.get_figure()

def drawLeaderSuccession(rolling_order_data, Fs=1.):
    channels = rolling_order_data[0].series.index
    Nchannels = len(channels)
    h = plt.figure(figsize=(6.4, 0.7 + .2*Nchannels))
    a = h.add_subplot(111)

    Ts = 1. / Fs
    lead_vector = [x.order[0] if x.order else None for x in rolling_order_data] # What channel was ther leader at each time step
    time_vector = [x.interval[1]*Ts for x in rolling_order_data]
    yticks = []
    for i,ch in enumerate(channels) :
        islead_vector = np.asarray([1. * (leader == ch) for leader in lead_vector])
        islead_indexes = np.where(islead_vector)[0]
        yticks.append(i*1.5)
        # a.step(time_vector, yticks[-1] + islead_vector, color="black")
        a.plot(time_vector, [yticks[-1]]*len(time_vector), color='lightgrey', ls=':')
        a.scatter([time_vector[x] for x in islead_indexes], [yticks[-1]]*len(islead_indexes), color='black')
    a.set_title("Leaders over time")
    a.set_xlabel("Time (s)")
    a.set_ylabel("Channels")
    a.set_yticks(yticks)
    a.set_yticklabels(channels)
    return h

def drawLeaderSuccession2D(rolling_order_data, layout, mode="arrows", Fs=1., ax=None):
    """ Draws the path taken by leaders over time
    mode = arrows / path
        arrows : draws arrows between channels ; plain line means direct succession of leaders, dotted line means that succession was discontinuous (no leader between successive leaders)
        path   : draws the path taken by leaders, smoothed a little bit
    """
    channels = rolling_order_data[0].series.index
    Nchannels = len(channels)
    Nsamples = len(rolling_order_data)
    lead_vector = [x.order[0] if x.order else None for x in rolling_order_data] # What channel was ther leader at each time step

    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    ax.set_title("Leader progression")
    """ Draw MEA """
    for e in layout.electrodes:
        if not(e.draw):
            continue
        for i,c in enumerate(rolling_order_data[0].series.index):
            if e.label in c:
                color = "black"
                break
        else:
            color = "lightgrey"
            i = -1
        ax.plot(e.position.x, e.position.y, 'o', color=color, ms=10, alpha=1.0)
    ax.axis('equal')
    """ Draw arrows """
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_ORDER_SUCCESSION)
    except:
        cmap = mpl.cm.get_cmap(CMAP_ORDER_SUCCESSION)
    if len(rolling_order_data) > 1:
        # init start channel, if it exists at step 0
        start_ch = None
        end_ch = None
        if rolling_order_data[0].order:
            start_ch = rolling_order_data[0].order[0]
        discontinuous = False
        path_xpoints = []
        path_ypoints = []
        Nsmooth = 10
        # iterate through result steps
        for i,step in enumerate(rolling_order_data[1:]):
            if step.order:
                end_ch = step.order[0]
            else:
                discontinuous = True
                continue
            if end_ch:
                coords_start = layout.getElectrode(start_ch).position
                coords_end   = layout.getElectrode(end_ch).position
                coords_diff  = coords_end - coords_start
                if mode == "arrows" :
                    ax.arrow(coords_start.x, coords_start.y, coords_diff.x, coords_diff.y, color=cmap(i/Nsamples), width=2, linestyle='--' if discontinuous else '-', length_includes_head=True, zorder=100, alpha=.75)
                path_xpoints.extend(np.linspace(coords_start.x, coords_end.x, Nsmooth).tolist())
                path_ypoints.extend(np.linspace(coords_start.y, coords_end.y, Nsmooth).tolist())
                start_ch = end_ch
                end_ch = None
                discontinuous = False # Reset discontinuous
        # Filter path for visibility
        box_pts = Nsmooth
        box = np.ones(box_pts)/box_pts
        if not(path_xpoints) or not(path_ypoints):
            print("drawLeaderSuccession2D : no data to plot")
            return h
        path_xpoints = np.convolve(path_xpoints, box, mode='same')
        path_ypoints = np.convolve(path_ypoints, box, mode='same')

        if mode == "path":
            ax.plot(path_xpoints, path_ypoints, color='red')
            ax.quiver(path_xpoints[:-1], 
                      path_ypoints[:-1], 
                      path_xpoints[1:]-path_xpoints[:-1], 
                      path_ypoints[1:]-path_ypoints[:-1], 
                      scale_units='xy', angles='xy', scale=1, width=0.005, color="red")

        if mode == "arrows":
            norm = mpl.colors.Normalize(vmin=rolling_order_data[0].interval[1]/Fs, vmax=rolling_order_data[-1].interval[1]/Fs)
            plt.colorbar(mappable=mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label="Time [s]")
        ax.set_xlabel("[µm]")
        ax.set_ylabel("[µm]")
    return h

def drawCorrelationSpatial(correlation_data, layout, threshold=0.5, ax=None, labels=True, lw=1.):
    if ax is None:
        h  = plt.figure()
        ax = h.add_subplot(111)
    try: # HACK : Handle older versions of matplotlib constrained by Python 3.7
        cmap = mpl.colormaps.get_cmap(CMAP_CORRELATION_MATRIX)
    except:
        cmap = mpl.cm.get_cmap(CMAP_CORRELATION_MATRIX)
    ax.set_title("All correlations > {}".format(threshold))

    for label0 in correlation_data.columns:
        for label1 in correlation_data.columns:
            if label0 != label1:
                corr = correlation_data[label0][label1]
                if abs(corr) >= threshold:
                    pos0 = layout.getElectrode(label0).position
                    pos1 = layout.getElectrode(label1).position
                    color = cmap(corr)
                    ax.plot([pos0.x, pos1.x], [pos0.y, pos1.y], "o-", color=color, lw=lw, zorder=int(100*abs(corr)))
    if not(labels):
        layout.draw(ax=ax, text=False, color="#AAAAAA")
    for e in layout.electrodes:
        if not(e.draw):
            continue
        ax.plot(e.position.x, e.position.y, 'o', color='black', ms=1, alpha=0.0)
        if labels:
            ax.text(e.position.x, e.position.y, str(e.label), color='black', horizontalalignment='center', verticalalignment='center', zorder=101)
    # Dummies for legend
    for x in np.linspace(1,-1,21):
        if x >= threshold:
          ax.plot([],[],color=cmap(x), label=f"{x}")
    ax.legend()
    ax.axis('equal')

def _draw_waveforms_region_stacked(waveforms, interval, Fs, ax, normalize=False):
    minalpha = 0.25
    for i,k in enumerate(waveforms):
        waveform = 1 * np.asarray(waveforms[k])[interval[0]:interval[1]]
        if normalize:
            def rescale(x, x0, x1, y0, y1):
                xrel = (x - x0) / (x1 - x0)
                return y0 + xrel * (y1 - y0)
            waveform = rescale(waveform, min(waveform), max(waveform), 0, 1)
        alpha = max(2./len(waveforms), minalpha)
        time_range = [idx/Fs for idx in interval]
        time = np.linspace(*time_range, len(waveform), endpoint=False)
        ax.plot(time, waveform, lw=1., alpha=alpha, color='black')
    ax.set_yticks([])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signals (normalized)')

def _draw_waveforms_region_inline(waveforms, interval, Fs, ax, shift=None, color='black', linestyle='-', highlight=[], channels=[]):
    yt = [] # yticks
    ytl = [] # yticklabels
    if type(highlight) != list:
        highlight = [highlight]
    if shift == None:
        shift = [0 for _ in waveforms]
    normalization_factors = {}
    if not(channels):
        channels = [k for k in waveforms]
    for k in channels:
        normalization_factors[k] = np.percentile(waveforms[k], 95) - np.percentile(waveforms[k], 5)
    for i,k in enumerate(channels):
        waveform = 1 * np.asarray(waveforms[k])[interval[0]:interval[1]]
        # normalization_factor = max(np.abs(waveform))
        # normalization_factor = normalization_factor if normalization_factor > 1e-9 else 1.
        normalization_factor = normalization_factors[k] * 1.1
        waveform = waveform/normalization_factor
        time_range = [idx/Fs for idx in interval]
        time = np.linspace(*time_range, len(waveform), endpoint=False)
        time += shift[i]
        lw = 1. if k in highlight else 0.5
        ax.plot(time, i+waveform, lw=lw, color=color, linestyle=linestyle)
        yt.append(i)
        ytl.append(k)
    ax.set_yticks(yt)
    ax.set_yticklabels(ytl)
    ax.set_ylabel('Signals')
    ax.set_xlabel('Time (s)')


def animate_rollingCorrelation(rolling_correlation, waveforms, Fs=1., autorun=True, env=None):
    fig = plt.figure(figsize=(8,5))
    aa = fig.add_axes([0.10, 0.70, 0.80, 0.20])
    a0 = fig.add_axes([0.10, 0.10, 0.35, 0.55])
    a1 = fig.add_axes([0.55, 0.10, 0.35, 0.55])
    N = len(rolling_correlation)
    ''' init '''
    drawAverageRollingCorrelation(rolling_correlation, Fs, aa)
    cursor0, = aa.plot([0], [0], color='red')
    cursor1, = aa.plot([0], [0], color='red')
    ylim = [0,1]
    aa.set_ylim(ylim)
    aa.set_xticks([])
    aa.set_yticks([])
    aa.set_title('')
    aa.set_ylabel('Av. correlation [0,1]')
    ''' Determine signal ylim '''
    Wmax = []
    Wmin = []
    for k in waveforms:
        Wmax.append(np.percentile(waveforms[k], 99)) # using percentiles instead of max/min to ignore rarely occuring points
        Wmin.append(np.percentile(waveforms[k],  1)) # using percentiles instead of max/min to ignore rarely occuring points
    wmax = np.percentile(Wmax, 99)
    wmin = np.percentile(Wmin,  1)
    minalpha = 0.33
    def drawFrame(i):
        i = i % len(rolling_correlation)
        interval = rolling_correlation[i].interval
        ''' overview '''
        cursor0.set_data([interval[0]/Fs]*2, ylim)
        cursor1.set_data([interval[1]/Fs]*2, ylim)
        ''' heatmap '''
        data = rolling_correlation[i].matrix
        sb.heatmap(data, cmap=CMAP_CORRELATION_MATRIX, vmin=-1.0, vmax=1.0, ax=a0, cbar=False)
        ''' waveforms '''
        _draw_waveforms_region_stacked(waveforms, interval, Fs, a1)
        a1.set_ylim((wmin, wmax))
        plt.title("t = [{:.2f}, {:.2f}]".format(*[idx/Fs for idx in rolling_correlation[i].interval]))


    drawFrame(0)

    def animate(i):
        a0.clear()
        a1.clear()
        drawFrame(i)

    anim = Player(fig, animate, maxi=N-1, pos=(0.125, 0.95), interval=500, blit=False, save_count=N)

    if env == "jupyter-notebook":
        plt.close()
        from IPython.display import HTML,display
        from matplotlib import rc
        rc('animation', html='jshtml')
        rc('animation', embed_limit=EMBED_LIMIT_MB)
        display(HTML(anim.to_jshtml()))

    if autorun:
        plt.show()
    return anim

def animate_rollingPhase(rolling_phase, waveforms, Fs=1., autorun=True, env=None):
    fig = plt.figure(figsize=(8,4))
    a0 = fig.add_subplot(121)
    a1 = fig.add_subplot(122)
    N = len(rolling_phase)
    def drawFrame(i,rolling_phase):
        i = i % len(rolling_phase)
        data = rolling_phase[i].matrix
        interval = rolling_phase[i].interval
        # Heatmap
        heatmap = sb.heatmap(data, cmap=CMAP_PHASE_MATRIX, vmin=-250.0, vmax=250.0, ax=a0, cbar=(i==0), cbar_kws={"orientation":"horizontal", "label":"[ms]"})
        # Waveforms
        _draw_waveforms_region_inline(waveforms, interval, Fs, a1)
        # Titles & axes
        plt.title("t = [{:.2f}, {:.2f}]".format(*[idx/Fs for idx in rolling_phase[i].interval]))
    drawFrame(0, rolling_phase)

    def animate(i):
        a0.clear()
        a1.clear()
        drawFrame(i, rolling_phase)

    anim = Player(fig, animate, maxi=N-1, pos=(0.125, 0.95), interval=500, blit=False, save_count=N)

    if env == "jupyter-notebook":
        plt.close()
        from IPython.display import HTML,display
        from matplotlib import rc
        rc('animation', html='jshtml')
        rc('animation', embed_limit=EMBED_LIMIT_MB)
        display(HTML(anim.to_jshtml()))

    if autorun:
        plt.show()
    return anim

def animate_rollingCorrelationSpatial(rolling_correlation, waveforms, layout, threshold=0.5, Fs=1., autorun=True, env=None):
    fig = plt.figure(figsize=(8,4))
    a0 = fig.add_subplot(121)
    a1 = fig.add_subplot(122)
    N = len(rolling_correlation)
    def drawFrame(i,rolling_correlation):
        i = i % len(rolling_correlation)
        data = rolling_correlation[i].matrix
        drawCorrelationSpatial(data, layout, threshold, ax=a0)
        for j,k in enumerate(waveforms):
            interval = rolling_correlation[i].interval
            waveform = 1 * np.asarray(waveforms[k])[interval[0]:interval[1]]
            normalization_factor = max(np.abs(waveform))
            normalization_factor = normalization_factor if normalization_factor > 1e-9 else 1.
            waveform /= normalization_factor
            a1.plot(j+waveform, lw=.5)
        a0.set_title("t = [{:.2f}, {:.2f}]".format(*[idx/Fs for idx in rolling_correlation[i].interval]))
    drawFrame(0, rolling_correlation)

    def animate(i):
        a0.clear()
        a1.clear()
        # a0=fig.gca()
        drawFrame(i, rolling_correlation)

    anim = Player(fig, animate, maxi=N-1, pos=(0.125, 0.95), interval=500, blit=False, save_count=N)

    if env == "jupyter-notebook":
        plt.close()
        from IPython.display import HTML,display
        from matplotlib import rc
        rc('animation', html='jshtml')
        rc('animation', embed_limit=EMBED_LIMIT_MB)
        display(HTML(anim.to_jshtml()))

    if autorun:
        plt.show()
    return anim

def animate_rollingPhaseSpatial(rolling_phase, layout, waveforms, Fs=1., autorun=True, env=None):
    fig = plt.figure(figsize=(8,4))
    a0 = fig.add_subplot(121)
    a1 = fig.add_subplot(122)
    N = len(rolling_phase)
    def drawFrame(i):
        i = i % len(rolling_phase)
        data = rolling_phase[i].matrix
        drawPhaseSpatial(data, layout=layout, ax=a0, Fs=Fs)
        interval = rolling_phase[i].interval
        _draw_waveforms_region_inline(waveforms, interval, Fs, a1)
        time_range = [idx/Fs for idx in interval]
        a0.set_xlabel('[um]')
        a0.set_ylabel('[um]')
        a1.set_title("t = [{:.2f}, {:.2f}]".format(*time_range))
        a1.set_xlabel('Time (s)')
    drawFrame(0)

    def animate(i):
        a0.clear()
        a1.clear()
        drawFrame(i)

    anim = Player(fig, animate, maxi=N-1, pos=(0.125, 0.95), interval=500, blit=False, save_count=N)

    if env == "jupyter-notebook":
        plt.close()
        from IPython.display import HTML,display
        from matplotlib import rc
        rc('animation', html='jshtml')
        rc('animation', embed_limit=EMBED_LIMIT_MB)
        display(HTML(anim.to_jshtml()))

    if autorun:
        plt.show()
    return anim

def animate_rollingOrderSpatial(rolling_order, rolling_phase, layout, waveforms, Fs=1., stack=False, speed=False, autorun=True, env=None):
    fig = plt.figure(figsize=(10,6))
    aa = fig.add_axes([0.10, 0.70, 0.80, 0.20])
    a0 = fig.add_axes([0.10, 0.10, 0.35, 0.55])
    a1 = fig.add_axes([0.55, 0.10, 0.35, 0.55])
    ''' init '''
    N = len(rolling_order)
    confidence_avg = np.asarray([np.average([x for x in rt.correlation.values]) for rt in rolling_phase])
    confidence_std = np.asarray([    np.std([x for x in rt.correlation.values]) for rt in rolling_phase])
    time           = np.asarray([rt.interval[0]/Fs                              for rt in rolling_phase])
    aa.fill_between(time, confidence_avg+confidence_std, confidence_avg-confidence_std, color='grey')
    aa.plot(time, confidence_avg, color='black')
    cursor0, = aa.plot([0], [0], color='red')
    cursor1, = aa.plot([0], [0], color='red')
    ylim = [0,1]
    aa.set_ylim(ylim)
    aa.set_xticks([])
    aa.set_yticks([])
    aa.set_title('')
    aa.set_ylabel('Av. correlation [0,1]')
    def drawFrame(i):
        i = i % len(rolling_order)
        interval = rolling_order[i].interval
        ''' overview '''
        cursor0.set_data([interval[0]/Fs]*2, ylim)
        cursor1.set_data([interval[1]/Fs]*2, ylim)
        ''' order '''
        data = rolling_order[i].series
        drawOrderSpatial(data, layout=layout, ax=a0, Fs=Fs, speed=speed)
        ''' waveforms '''
        time_range = [idx/Fs for idx in interval]
        if stack:
            _draw_waveforms_region_stacked(waveforms, interval, Fs, a1, normalize = True)
        else:
            _draw_waveforms_region_inline(waveforms, interval, Fs, a1, highlight=data.index[0])
            shift_values = [-data[k]/Fs if not(np.isnan(data[k])) else 0 for k in waveforms]
            _draw_waveforms_region_inline(waveforms, interval, Fs, a1, shift=shift_values, linestyle=':', highlight=data.index[0])
        a1.set_xlim(time_range)
        a0.set_xlabel('[um]')
        a0.set_ylabel('[um]')
        a1.set_title("t = [{:.2f}, {:.2f}]".format(*time_range))
        a1.set_xlabel('Time (s)')
        progressbar.inlineCycles(i,N, prefix="Generating animation")
    # drawFrame(0)

    def animate(i):
        a0.clear()
        a1.clear()
        drawFrame(i)

    anim = Player(fig, animate, maxi=N-1, pos=(0.125, 0.95), interval=500, blit=False, save_count=N, init_func=lambda:drawFrame(0))

    if env == "jupyter-notebook":
        plt.close()
        from IPython.display import HTML,display
        from matplotlib import rc
        rc('animation', html='jshtml')
        rc('animation', embed_limit=EMBED_LIMIT_MB)
        display(HTML(anim.to_jshtml()))

    if autorun:
        plt.show()

    return anim
