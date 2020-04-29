# Sources
## engine.py
High-level analysis management. Input data (timestamps), analysed data (correlation, linkage, etc.), and data representation are all bundled in a single object. This facilitates workflow as its methods permit all necessary data manipulation (loading, processing, exporting) in a streamlined and error-free manner. Processing is handled in a “baking” manner: “baking” refers to retrieving available data, processing it, and storing it locally for further processing without duplicate analyses. The engine either handles auto-baking (baking all dependencies) or alerts which intermediary bakes must be conducted before the current bake.

## processing.py
All data processing functions. As a convention, all inputs are independent of local data types (no custom classes), and all time-dependent arguments are expressed in samples.

### processing.eventWaveforms
```python
waveforms = eventWaveforms(timestamps, sigma_samples)
```
Generates waveforms from events, allowing to account for a gaussian tolerance region around each event.
* Arguments
  * `timestamps` *(dict)* is a dictionnary of timestamps. Defaults to `{}`.
  * `sigma_samples` *(int)* is the standard deviation, in number of samples, of the tolerance region generated around each event. Defaults to `1`
* Returned values
    * `waveforms` *(dict)* is a dictionnary of waveforms, with the same keys as `timestamps`.

### processing.correlationMatrix
```python
correlation_data = eventCorrelationMatrix(signals)
```
Computes the correlation matrix for the specified signals.
* Arguments
  * `signals` *(dict)* is a dictionnary of signals. Defaults to `{}`.
* Returned values
  * `correlation_data` *(`namedtuple("Correlation_Data", ["matrix"])`)* This could indeed not be a tuple, as only one value is returned. But it follows the nomenclature of all other processing functions.
    * `correlation_data.matrix` *(pandas.DataFrame)* is the computed correlation matrix

### processing.rollingCorrelation
```python
rolling_correlation_data = rollingCorrelation(signals, window_samples, overlap_percent, Fs)
```
* Arguments
  * `signals` *(dict)* is a dictionnary of signals. Passed to `processing.correlationMatrix`. Defaults to `{}`.
  * `window_samples` *(int)* is the size (in samples) of the rolling window. Defaults to `10`
  * `overlap_percent` *(float)* is the amount of overlap (in percent) between two successive windows. Defaults to `50`
  * `Fs` *(float)* is the sampling frequency (utilized to compute window timestamps [s]). Defaults to `1.0`
* Returned values
  * `rolling_correlation_data` *(list of namedtuple("Rolling_Correlation_Data", ["matrix", "signals", "interval"]))*. The elements in the list are successive windowed correlation measurements identical to the values returned by `processing.correlationMatrix`, except for an extra field `interval` that specifies the bounds of the corresponding window.
    * `rolling_correlation_data[i].matrix` *(pandas.DataFrame)* is the computed windowed correlation matrix at index i
    * `rolling_correlation_data[i].interval` *(tuple)* is the bounds, in seconds, of the window at index i

### processing.getClustering
```python
clustering_data = getClustering(dataframe, tolerance)
```
* Arguments
  * `dataframe` *(panda.DataFrame)* is the correlation matrix computed by pandas
  * `tolerance` *(float)* is the linkage threshold above which items get clustered
* Returned values
  * `clustering_data` *(namedtuple("Clustering_Data", ["linkage", "clusters", "labels"]))*
    * `clustering_data.linkage` *(scipy.ndarray)* is the hierarchical clustering encoded as a linkage matrix, returned by `scipy.cluster.hierarchy.linkage`
    * `clustering_data.clusters` *(list)* is the list of detected clusters (each cluster is a list of labels)
    * `clustering_data.labels` *(pandas.core.indexes.bas.Index)* is the list of labels. May very well be unnecessary and will be removed in the future.
