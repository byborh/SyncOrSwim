# Devnotes SPcorrelation 2020

## Etat transfert de compétences

### Todo

* [ ] Faire une doc utilisateur
* [ ] Terminer l'interface
* [ ] Eprouver l'interface
* [ ] Préparer une install python mobile OU générer un éxécutable
  * [ ] Lister les dépendances
* [X] Mettre en place le versioning pour la première version déployée
* [ ] Compléter les exports

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
