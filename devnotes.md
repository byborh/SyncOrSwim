# Devnotes SyncOrSwim

## Etat transfert de compétences

### Todo

* [ ] Faire une doc utilisateur
* [X] Terminer l'interface
* [ ] Eprouver l'interface
* [X] Préparer une install python mobile OU générer un éxécutable
  * [X] Lister les dépendances
* [X] Mettre en place le versioning pour la première version déployée
* [ ] Compléter les exports
* [ ] FIXME : issue with autobaking and the gui : if an analysis is run and prompts autobaking (meaning a dependency is not ticked), re-running analyses doesn't recurse, meaning that the engine utilizes pre-computed results that will not get updated : if a parameter has changed inbetween, it will not be taken into account. Possible fixes : add a --recurse flag to analyses ? disable autobaking with gui ? (which would defeat the purpose because it was specifically added to be more user-friendly ...) Reset processed data before running analysis ?
* [ ] replace success/failure routines returning `True`/`False` values with exception handling
* [ ] switch from setup using python + pip to setup using python only
* [ ] re-use colorama
* [ ] Changer la couleur des animations (correlation matrix)
* [ ] Plot rolling timeshit spatial ne marche pas ?
* [ ] Isochrones ?
* [ ] Enlever les infos de temps sur bar plot

## Etat GUI

### General

* [X] Colored info messages

### Panel "File"

* [X] Load (with file type recognition)
* [X] Display file info

### Panel "Source data"

* [X] Time range
* [X] MEA layout
* [X] Processing Fs
* [X] Channels
* [X] Hub reference

### Panel "Pre-processing (xxx)"

#### Timestamps :
* [X] Tolerance
* [X] RMS window

#### Raw data :
* [X] Filters
* [X] RMS window

### Panel "Analyses"

#### Analysis selection :

* [X] Analysis selection

#### Plots (based on all declared plots in engine.py) :

* [X] PLOTS["CORRELATIONMATRIX"]
* [X] PLOTS["CLUSTEREDEVENTS"]
* [X] PLOTS["GRANGERCAUSALITYMATRIX"] <<< unused
* [X] PLOTS["DENDROGRAM"]
* [X] PLOTS["TIMESHIFT"]
* [X] PLOTS["ROLLINGCORRELATION"]
* [X] PLOTS["ROLLINGTIMESHIFT"]
* [X] PLOTS["ROLLINGTIMESHIFTSPATIAL"]
* [X] PLOTS["ROLLINGORDERSPATIAL"]
* [X] PLOTS["ROLLINGORDERBAR"]
* [X] PLOTS["ROLLINGORDERPIE"]  

#### Exports (based on all declared exports in engine.py) :

* [X] EXPORTS["CORRELATIONMATRIX"]
* [X] EXPORTS["GRANGERCAUSALITYMATRIX"] <<< unused
* [X] EXPORTS["TIMESHIFT"]
* [X] EXPORTS["ORDER"]
* [X] EXPORTS["CLUSTERING"]
* [X] EXPORTS["ROLLINGCORRELATION"]
* [X] EXPORTS["ROLLINGTIMESHIFT"]
* [X] EXPORTS["ROLLINGORDER"]
* [ ] **Export all**

### Panel "Control"

#### Take into account :

##### From panel "Source data"

* [X] Time range
* [X] MEA layout
* [X] Processing Fs
* [X] Channels
* [X] Hub reference

##### From panel "Pre-processing (xxx)"

* [X] Differenciate timestamps & raw data

###### From "Timestamps" :

* [X] Tolerance
* [X] RMS enable
* [X] RMS window

###### From "Raw data" :

* [X] Filters
* [X] RMS enable
* [X] RMS window

##### From panel "Analyses"

* [X] Handle analysis "Correlation"
* [X] Handle analysis "Timeshift"
* [X] Handle analysis "Order"
* [X] Handle analysis "Activation order"
* [X] Handle analysis "Clustering"
* [X] Handle analysis "Rolling correlation"
* [X] Handle analysis "Rolling timeshift"
* [X] Handle analysis "Rolling order"
