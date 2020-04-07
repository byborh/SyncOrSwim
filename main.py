import processing
import data_inout
import representations

import seaborn as sb
from matplotlib import pyplot as plt

""" TODO """
""" * ELectrode representation w/ clusters """
""" * Rolling correlation + clusters       """
""" * """

# file_in = "./Timestamps/correl 2nd phase.txt"
# file_in = "./Timestamps/Enregistrement 7 min milieu 2ème phase text.txt"
# file_in = "./Timestamps/Enregistrement_5_min_G3_40_min_G8_2_TIMESTAMPS.txt"
file_in = "./Timestamps/détection d'évènements text.txt"

Fs = 100.
evt_tolerance_s = 0.5
evt_tolerance_i = int(evt_tolerance_s*Fs)
corr_tolerance = 0.4

timestamps_s = data_inout.fromSpike2(file_in)
timestamps_s = processing.clean_timestamps(timestamps_s)
timestamps_i = processing.s2idx(timestamps_s, Fs)

correlation = processing.eventCorrelationMatrix(timestamps_i, evt_tolerance_i)

clustering = processing.getClustering(correlation['dataframe'], tolerance=corr_tolerance)

# cg = sb.clustermap(correlation['dataframe'], cmap ="YlGnBu", linewidths = 0.1, figsize=(6,6), method='average')

# representations.drawClusteredEvents(timestamps_i, clustering['linkage'])

# plt.show()

window_s = 10.
window_samples = int(Fs * window_s)
rolling_correlation = processing.rollingCorrelationMatrix(timestamps_i, evt_tolerance_i, window_samples=window_samples, overlap_percent=50)

representations.animate_rollingCorrelation(rolling_correlation)
