import engine
import progressbar
import gui_assets as assets
import colprint

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as tkfd
from tkinter import simpledialog as tksd

from version import __version__, __version_info__

if __name__ == "__main__":
    WINDOW_TITLE = "SPcorrelation2020"
    VERSION = __version__

    COLORCODE_ERROR    = "red"
    COLORCODE_WARNING  = "orange"
    COLORCODE_SUCCESS  = "green"
    COLORCODE_NEUTRAL  = "black"
    COLORCODE_DISCRETE = "grey"

    LABELFRAMES_GRID_PARAMS = {"sticky": "nswe", "padx": 5, "pady": 5}

    root = tk.Tk()
    """ File handling """
    filehandling_labelframe      = ttk.Labelframe(root, text="File")
    filehandling_load_button     = tk.Button(filehandling_labelframe, text="Load")
    filehandling_status_strvar   = tk.StringVar()
    filehandling_fileinfo_strvar = tk.StringVar()
    filehandling_status_label    = tk.Label(filehandling_labelframe, textvariable=filehandling_status_strvar)
    filehandling_fileinfo_label  = tk.Label(filehandling_labelframe, textvariable=filehandling_fileinfo_strvar, wraplength=300, justify=tk.LEFT)
    ''' Pack '''
    filehandling_status_label.config(fg=COLORCODE_ERROR)
    filehandling_labelframe.grid(row=0, column=0, **LABELFRAMES_GRID_PARAMS)
    filehandling_load_button.pack()
    filehandling_status_label.pack()
    filehandling_fileinfo_label.pack()
    filehandling_status_strvar.set("No data loaded")
    filehandling_fileinfo_strvar.set("")

    """ Source data parameters """
    sourcedata_labelframe = ttk.Labelframe(root, text="Source data")
    ''' Time range '''
    sourcedata_timerange_label            = tk.Label(sourcedata_labelframe, text="Time range")
    sourcedata_timerange_checkbox_state   = tk.IntVar()
    sourcedata_timerange_checkbox         = tk.Checkbutton(sourcedata_labelframe, variable=sourcedata_timerange_checkbox_state)
    sourcedata_timerange_configframe      = tk.Frame(sourcedata_labelframe)
    sourcedata_timerange_entry1_doublevar = tk.IntVar()
    sourcedata_timerange_entry1           = tk.Entry(sourcedata_timerange_configframe, textvariable=sourcedata_timerange_entry1_doublevar, width=5)
    sourcedata_timerange_separator        = tk.Label(sourcedata_timerange_configframe, text="-")
    sourcedata_timerange_entry2_doublevar = tk.IntVar()
    sourcedata_timerange_entry2           = tk.Entry(sourcedata_timerange_configframe, textvariable=sourcedata_timerange_entry2_doublevar, width=5)
    sourcedata_timerange_unit             = tk.Label(sourcedata_timerange_configframe, text="s")
    ''' MEA layout '''
    sourcedata_mealayout_label             = tk.Label(sourcedata_labelframe, text="MEA layout")
    sourcedata_mealayout_dropdown_strvar   = tk.StringVar()
    sourcedata_mealayout_dropdown          = tk.OptionMenu(sourcedata_labelframe, sourcedata_mealayout_dropdown_strvar  , *engine.MEAs.LIST)
    sourcedata_mealabeling_label           = tk.Label(sourcedata_labelframe, text="MEA labeling")
    sourcedata_mealabeling_dropdown_strvar = tk.StringVar()
    sourcedata_mealabeling_dropdown        = tk.OptionMenu(sourcedata_labelframe, sourcedata_mealabeling_dropdown_strvar, *engine.MEAs.LIST)
    ''' Processing Fs '''
    sourcedata_processingfs_label           = tk.Label(sourcedata_labelframe, text="Processing Fs")
    sourcedata_processingfs_configframe     = tk.Frame(sourcedata_labelframe)
    sourcedata_processingfs_entry_doublevar = tk.DoubleVar()
    sourcedata_processingfs_entry           = tk.Entry(sourcedata_processingfs_configframe, textvariable=sourcedata_processingfs_entry_doublevar, width=5)
    sourcedata_processingfs_unit            = tk.Label(sourcedata_processingfs_configframe, text="Hz")
    ''' Channels '''
    sourcedata_channels_label = tk.Label(sourcedata_labelframe, text="Channels")
    sourcedata_channels_listbox = assets.MultiListbox(sourcedata_labelframe, [])
    ''' Reference '''
    sourcedata_hubreference_label           = tk.Label(sourcedata_labelframe, text="Hub reference")
    sourcedata_hubreference_listbox        = assets.RefListbox(sourcedata_labelframe, [])
    ''' Rolling window : not really source data but nowhere else to put it at the moment '''
    sourcedata_rollingwindow_label           = tk.Label(sourcedata_labelframe, text="Rolling window (s)")
    sourcedata_rollingwindow_entry_doublevar = tk.DoubleVar()
    sourcedata_rollingwindow_entry           = tk.Entry(sourcedata_labelframe, textvariable=sourcedata_rollingwindow_entry_doublevar, width=5)

    ''' Pack '''
    sourcedata_labelframe.grid(row=0, column=1, **LABELFRAMES_GRID_PARAMS) # Root grid
    sourcedata_timerange_label.grid(row=0, column=0, sticky='W')           # Local grid
    sourcedata_timerange_checkbox.grid(row=0, column=1, sticky='W')        # Local grid
    sourcedata_timerange_configframe.grid(row=0, column=2, sticky='W')     # Local grid
    sourcedata_timerange_entry1.pack(side=tk.LEFT)
    sourcedata_timerange_separator.pack(side=tk.LEFT)
    sourcedata_timerange_entry2.pack(side=tk.LEFT)
    sourcedata_timerange_unit.pack(side=tk.LEFT)
    sourcedata_mealayout_label.grid(row=1, column=0, sticky='W')          # Local grid
    sourcedata_mealayout_dropdown.grid(row=1, column=2, sticky='W')       # Local grid
    sourcedata_mealabeling_label.grid(row=2, column=0, sticky='W')          # Local grid
    sourcedata_mealabeling_dropdown.grid(row=2, column=2, sticky='W')       # Local grid
    sourcedata_processingfs_label.grid(row=3, column=0, sticky='W')       # Local grid
    sourcedata_processingfs_configframe.grid(row=3, column=2, sticky='W') # Local grid
    sourcedata_processingfs_entry.pack(side=tk.LEFT)
    sourcedata_processingfs_unit.pack(side=tk.LEFT)
    sourcedata_rollingwindow_label.grid(row=4, column=0)
    sourcedata_rollingwindow_entry.grid(row=4, column=2, sticky='W')
    sourcedata_channels_label.grid(row=5, column=0)
    sourcedata_hubreference_label.grid(row=5, column=2)
    sourcedata_channels_listbox.grid(row=6, column=0, sticky='N')
    sourcedata_hubreference_listbox.grid(row=6, column=2, sticky='N')

    """ Pre-processing (timestamps) """
    preproc_timestamps_labelframe = ttk.Labelframe(root, text="Pre-processing (timestamps)")
    ''' Correlation tolerance '''
    preproc_timestamps_tolerance_label           = tk.Label(preproc_timestamps_labelframe, text="Tolerance")
    preproc_timestamps_tolerance_configframe     = tk.Frame(preproc_timestamps_labelframe)
    preproc_timestamps_tolerance_entry_doublevar = tk.DoubleVar()
    preproc_timestamps_tolerance_entry           = tk.Entry(preproc_timestamps_tolerance_configframe, textvariable=preproc_timestamps_tolerance_entry_doublevar, width=5)
    preproc_timestamps_tolerance_unit            = tk.Label(preproc_timestamps_tolerance_configframe, text="s")

    ''' RMS '''
    preproc_timestamps_rms_label            = tk.Label(preproc_timestamps_labelframe, text="RMS window")
    preproc_timestamps_rms_configframe      = tk.Frame(preproc_timestamps_labelframe)
    preproc_timestamps_rms_checkbox_state   = tk.IntVar()
    preproc_timestamps_rms_checkbox         = tk.Checkbutton(preproc_timestamps_labelframe, variable=preproc_timestamps_rms_checkbox_state)
    preproc_timestamps_rms_entry_doublevar  = tk.DoubleVar()
    preproc_timestamps_rms_entry            = tk.Entry(preproc_timestamps_rms_configframe, textvariable=preproc_timestamps_rms_entry_doublevar, width=5)
    preproc_timestamps_rms_unit             = tk.Label(preproc_timestamps_rms_configframe, text="s")

    ''' Pack '''
    preproc_timestamps_labelframe.grid(row=1, column=0, **LABELFRAMES_GRID_PARAMS)
    preproc_timestamps_tolerance_label.grid(row=0, column=0, sticky='W')
    preproc_timestamps_tolerance_configframe.grid(row=0, column=2, sticky='W')
    preproc_timestamps_tolerance_entry.pack(side=tk.LEFT)
    preproc_timestamps_tolerance_unit.pack(side=tk.LEFT)
    preproc_timestamps_rms_label.grid(row=1, column=0, sticky='W')
    preproc_timestamps_rms_checkbox.grid(row=1, column=1, sticky='W')
    preproc_timestamps_rms_configframe.grid(row=1, column=2, sticky='W')
    preproc_timestamps_rms_entry.pack(side=tk.LEFT)
    preproc_timestamps_rms_unit.pack(side=tk.LEFT)

    """ Pre-processing (raw data) """
    preproc_rawdata_labelframe = ttk.Labelframe(root, text="Pre-processing (raw data)")

    ''' Filters '''
    preproc_rawdata_filters_label    = tk.Label(preproc_rawdata_labelframe, text="Filters")
    preproc_rawdata_filters_HP_label = tk.Label(preproc_rawdata_labelframe, text="> High-pass (Fc [Hz], order)")
    preproc_rawdata_filters_LP_label = tk.Label(preproc_rawdata_labelframe, text="> Low-pass (Fc [Hz], order)")
    preproc_rawdata_filters_HP_configframe = tk.Frame(preproc_rawdata_labelframe)
    preproc_rawdata_filters_LP_configframe = tk.Frame(preproc_rawdata_labelframe)
    preproc_rawdata_filters_entry_HP_cutoff_doublevar = tk.DoubleVar()
    preproc_rawdata_filters_entry_HP_order_intvar     = tk.IntVar()
    preproc_rawdata_filters_entry_LP_cutoff_doublevar = tk.DoubleVar()
    preproc_rawdata_filters_entry_LP_order_intvar     = tk.IntVar()
    preproc_rawdata_filters_entry_HP_cutoff_entry = tk.Entry(preproc_rawdata_filters_HP_configframe, textvariable=preproc_rawdata_filters_entry_HP_cutoff_doublevar, width=8)
    preproc_rawdata_filters_entry_HP_order_entry  = tk.Entry(preproc_rawdata_filters_HP_configframe, textvariable=preproc_rawdata_filters_entry_HP_order_intvar    , width=2)
    preproc_rawdata_filters_entry_LP_cutoff_entry = tk.Entry(preproc_rawdata_filters_LP_configframe, textvariable=preproc_rawdata_filters_entry_LP_cutoff_doublevar, width=8)
    preproc_rawdata_filters_entry_LP_order_entry  = tk.Entry(preproc_rawdata_filters_LP_configframe, textvariable=preproc_rawdata_filters_entry_LP_order_intvar    , width=2)


    ''' RMS '''
    preproc_rawdata_rms_label            = tk.Label(preproc_rawdata_labelframe, text="RMS window")
    preproc_rawdata_rms_configframe      = tk.Frame(preproc_rawdata_labelframe)
    preproc_rawdata_rms_checkbox_state   = tk.IntVar()
    preproc_rawdata_rms_checkbox         = tk.Checkbutton(preproc_rawdata_labelframe, variable=preproc_rawdata_rms_checkbox_state)
    preproc_rawdata_rms_entry_doublevar  = tk.DoubleVar()
    preproc_rawdata_rms_entry            = tk.Entry(preproc_rawdata_rms_configframe, textvariable=preproc_rawdata_rms_entry_doublevar, width=5)
    preproc_rawdata_rms_unit             = tk.Label(preproc_rawdata_rms_configframe, text="s")

    ''' Pack '''
    preproc_rawdata_labelframe.grid(row=1, column=1, **LABELFRAMES_GRID_PARAMS)
    preproc_rawdata_filters_label.grid(row=0, column=0, sticky='W')
    preproc_rawdata_filters_HP_label.grid(row=1, column=0, sticky='W')
    preproc_rawdata_filters_LP_label.grid(row=2, column=0, sticky='W')
    preproc_rawdata_filters_HP_configframe.grid(row=1, column=2, sticky='W')
    preproc_rawdata_filters_LP_configframe.grid(row=2, column=2, sticky='W')
    preproc_rawdata_filters_entry_HP_cutoff_entry.pack(side=tk.LEFT)
    preproc_rawdata_filters_entry_HP_order_entry.pack(side=tk.LEFT)
    preproc_rawdata_filters_entry_LP_cutoff_entry.pack(side=tk.LEFT)
    preproc_rawdata_filters_entry_LP_order_entry.pack(side=tk.LEFT)
    preproc_rawdata_rms_label.grid(row=3, column=0, sticky='W')
    preproc_rawdata_rms_checkbox.grid(row=3, column=1, sticky='W')
    preproc_rawdata_rms_configframe.grid(row=3, column=2, sticky='W')
    preproc_rawdata_rms_entry.pack(side=tk.LEFT)
    preproc_rawdata_rms_unit.pack(side=tk.LEFT)

    """ Analyses """
    analyses_widgets = {}
    def add_analysis(reference, parent, column, row, text):
        widgets = {}
        widgets["checkbox_state"] = tk.IntVar(value=0)
        widgets["checkbox"]       = tk.Checkbutton(parent, text=text, variable=widgets["checkbox_state"])
        widgets["show_button"]    = assets.CallbackOptionMenu(parent, "Show ..."  , [])
        widgets["export_button"]  = assets.CallbackOptionMenu(analyses_labelframe, "Export ...", [])
        n_utility_columns = 3
        widgets["checkbox"].grid(     row=row, column=column*n_utility_columns + 0, sticky='W')
        widgets["show_button"].grid(  row=row, column=column*n_utility_columns + 1, sticky='W')
        widgets["export_button"].grid(row=row, column=column*n_utility_columns + 2, sticky='W')
        analyses_widgets[reference] = widgets
        pass
    analyses_labelframe = ttk.Labelframe(root, text="Analyses")
    analyses_labelframe.grid(row=2, column=0, columnspan=2, **LABELFRAMES_GRID_PARAMS)

    add_analysis("CORRELATION"       , parent=analyses_labelframe, column=0, row=0, text="Correlation")
    add_analysis("TIMESHIFT"         , parent=analyses_labelframe, column=0, row=1, text="Timeshift")
    add_analysis("ORDER"             , parent=analyses_labelframe, column=0, row=2, text="Order")
    add_analysis("ACTIVATIONORDER"   , parent=analyses_labelframe, column=0, row=3, text="Activation order")
    add_analysis("CLUSTERING"        , parent=analyses_labelframe, column=0, row=4, text="Clustering")
    add_analysis("ROLLINGCORRELATION", parent=analyses_labelframe, column=1, row=0, text="Rolling correlation")
    add_analysis("ROLLINGTIMESHIFT"  , parent=analyses_labelframe, column=1, row=1, text="Rolling timeshift")
    add_analysis("ROLLINGORDER"      , parent=analyses_labelframe, column=1, row=2, text="Rolling order")

    """ Analysis controls """
    analysisctrl_labelframe = ttk.Labelframe(root, text="Control")
    analysisctrl_import_params_button = tk.Button(analysisctrl_labelframe, text="Import parameters")
    analysisctrl_export_params_button = tk.Button(analysisctrl_labelframe, text="Export parameters")
    analysisctrl_run_button = tk.Button(analysisctrl_labelframe, text="Run")
    analysisctrl_run_button.configure(state="disabled")

    ''' Pack '''
    analysisctrl_labelframe.grid(row=3, column=0, columnspan=2, **LABELFRAMES_GRID_PARAMS)    # Root grid
    analysisctrl_import_params_button.grid(row=0, column=0)                                   # Local grid
    analysisctrl_export_params_button.grid(row=0, column=1)                                   # Local grid
    analysisctrl_run_button.grid(row=0, column=2)                                             # Local grid

    """ Signature """
    signature_label = tk.Label(root, text=f"Version {__version__} - antoine.pirog@ims-bordeaux.fr", justify=tk.CENTER)
    signature_label.config(fg=COLORCODE_DISCRETE)
    signature_label.grid(row=4, column=0, columnspan=3)

    ENGINE = engine.CorrelationDataframe()
    ENGINE.parameters["environment"] = "tkinter"

    def message(text=""):
        if text:
            root.title(f"{WINDOW_TITLE} - {text}")
        else:
            root.title(f"{WINDOW_TITLE}")

    def get_file_info_string():
        path     = ENGINE.file
        datatype = ENGINE.datatype
        Fs       = ENGINE.Fs_raw
        duration = ENGINE.duration_s

        string_path     = f"File : {path}\n"
        string_datatype = ""
        string_Fs       = f"Fs : {Fs:.2f} Hz\n"            if Fs       else ""
        string_duration = f"Duration : {duration:.2f} s\n" if duration else ""
        string = ""
        string += string_path
        string += string_datatype
        string += string_Fs
        string += string_duration

        return string

    def load_data():
        def reset_engine():
            ENGINE.resetProcessedData()
            ENGINE.resetTimestampData()
            ENGINE.resetWaveformData()
            ENGINE.resetCorrelationData()
            ENGINE.resetTimeshiftData()
            ENGINE.resetRollingCorrelationData()
            ENGINE.resetRollingTimeshiftData()
            ENGINE.resetClusteringData()
        filetypes = [
            ("All supported files", "*.txt *.h5 *.rhd"),
            ("Spike2 event files", "*.txt"),
            ("pyBSA event files", "*.txt"),
            ("MCS h5 raw data files", "*.h5"),
            ("Intan RHD raw data files", "*.rhd")
            ]
        path = tkfd.askopenfilename(initialdir=".", filetypes=filetypes)
        import_parameters = {}
        reset_engine()
        datatype = ENGINE.loadFile(path, import_parameters)
        ''' Update messages & pre-processing frame status '''
        if datatype in engine.TIMESTAMP_DATATYPES:
            filehandling_status_strvar.set("Timestamp data loaded")
            filehandling_fileinfo_strvar.set(get_file_info_string())
            filehandling_status_label.config(fg=COLORCODE_SUCCESS)
            analysisctrl_run_button.configure(state="normal")
            enable_children(preproc_timestamps_labelframe)
            disable_children(preproc_rawdata_labelframe)
            update_preproc_timestamps_rms()
            channels = ENGINE.timestamps.keys()
            update_channels(channels)
            if datatype == engine.data_inout.SPIKE2EVENTS:
                msg = "Loaded Spike2 events file."
            if datatype == engine.data_inout.PYBSAEVENTS:
                msg = "Loaded pyBSA events file."
            message(msg)
            colprint.printokg(msg)
        elif datatype in engine.WAVEFORM_DATATYPES:
            filehandling_status_strvar.set("Raw data loaded")
            filehandling_fileinfo_strvar.set(get_file_info_string())
            filehandling_status_label.config(fg=COLORCODE_SUCCESS)
            analysisctrl_run_button.configure(state="normal")
            message("Loaded MCS h5 raw data file.")
            disable_children(preproc_timestamps_labelframe)
            enable_children(preproc_rawdata_labelframe)
            update_preproc_rawdata_rms()
            channels = ENGINE.waveforms.keys()
            update_channels(channels)
            if datatype == engine.data_inout.H5WAVEFORMS:
                msg = "Loaded MCS h5 raw data file."
            if datatype == engine.data_inout.RHDWAVEFORMS:
                msg = "Loaded Intan RHD raw data file."
            message(msg)
            colprint.printokg(msg)
        else:
            filehandling_status_strvar.set("No data loaded")
            filehandling_fileinfo_strvar.set("")
            filehandling_status_label.config(fg=COLORCODE_ERROR)
            analysisctrl_run_button.configure(state="disabled")
            disable_children(preproc_timestamps_labelframe)
            disable_children(preproc_rawdata_labelframe)
            update_channels([])
            msg = "Unrecognized data."
            message(msg)
            colprint.printerr(msg)

    def pbar(i, N, prefix="", done=""):
        message(progressbar.inlineCycles(i, N, prefix=prefix, done=done, stdout=False))

    def prompt_fs():
        return tksd.askfloat("Input", "What was the sampling frequency ? I can't tell.", minvalue=0.)

    def enable_children(parent):
        for child in parent.winfo_children():
            if child.winfo_class() not in ('Frame','Labelframe'):
                child.configure(state='normal')
            else:
                enable_children(child)

    def disable_children(parent):
        for child in parent.winfo_children():
            if child.winfo_class() not in ('Frame','Labelframe'):
                child.configure(state='disable')
            else:
                disable_children(child)

    def update_sourcedata_timerange():
        if sourcedata_timerange_checkbox_state.get():
            enable_children(sourcedata_timerange_configframe)
        else:
            disable_children(sourcedata_timerange_configframe)

    def update_preproc_timestamps_rms():
        if preproc_timestamps_rms_checkbox_state.get():
            enable_children(preproc_timestamps_rms_configframe)
        else:
            disable_children(preproc_timestamps_rms_configframe)

    def update_preproc_rawdata_rms():
        if preproc_rawdata_rms_checkbox_state.get():
            enable_children(preproc_rawdata_rms_configframe)
        else:
            disable_children(preproc_rawdata_rms_configframe)

    def update_channels(channels):
        sourcedata_channels_listbox.set_choices(sorted(channels))
        sourcedata_hubreference_listbox.set_choices(sorted(channels))


    plot_updates = []
    def update_all_plot_status():
        for pu in plot_updates:
            pu()

    """ Create all plot & export menu entries """
    def add_plot_entry(optionmenu, text, show_callback, status_check_reference):
        optionmenu.add_choice((text, show_callback))
        def update():
            state = ENGINE._isPlotReady(status_check_reference)
            state = 'normal' if state else 'disabled'
            optionmenu.change_state(text, state)
        plot_updates.append(update)

    def add_export_entry(optionmenu, text, export_callback, status_check_reference):
        extension = "xlsx" # Todo : Get from engine
        def gui_export():
            file_path = tkfd.asksaveasfilename(filetypes=[("Excel worksheets", "*.xlsx")])
            if file_path:
                if not file_path.endswith(".xlsx"):
                    file_path += ".xlsx"
                success = export_callback(destination=file_path)
                if success:
                    msg = "Export successful"
                    message(msg)
                    colprint.printokg(msg)
                else:
                    msg = "Export failed"
                    colprint.printerr(msg)
        optionmenu.add_choice((text, gui_export))
        def update():
            state = ENGINE._isExportReady(status_check_reference)
            state = 'normal' if state else 'disabled'
            optionmenu.change_state(text, state)
        plot_updates.append(update)

    """ Special exports """
    def add_local_export_entry(optionmenu, text, export_callback, status_check_reference):
        optionmenu.add_choice((text, export_callback))
        def update():
            state = ENGINE._isExportReady(status_check_reference)
            state = 'normal' if state else 'disabled'
            optionmenu.change_state(text, state)
        plot_updates.append(update)

    def export_dendrogram_to_electrode_selection():
        dialog = tk.Toplevel(root)
        if not ENGINE.clustering_data.clusters:
            colprint.printwar("No cluster found")
            return
        for i,cluster in enumerate(ENGINE.clustering_data.clusters):
            def callback(l):
                sourcedata_channels_listbox.set(l)
                print(f"Set channel filters to " + ";".join(l))
                dialog.destroy()
             # A little bit of weirdness here because without evaluating an expression in the lambda, the passed argument is only evaluated at the end of the for loop, hence preventing every button from having a separate callback function
            btn = tk.Button(dialog, text=f"Cluster #{i+1}", command=lambda x=[ch for ch in cluster]: callback(x)).grid(row=i, column=0)
            lab = tk.Label(dialog, text=";".join(cluster), justify=tk.LEFT).grid(row=i, column=1)


    add_plot_entry(analyses_widgets["CORRELATION"]["show_button"]       , "Correlation matrix"                   , lambda: ENGINE.drawCorrelation(0)       , engine.PLOTS["CORRELATIONMATRIX"     ])
    add_plot_entry(analyses_widgets["CORRELATION"]["show_button"]       , "Granger causality matrix"             , lambda: ENGINE.drawCorrelation(1)       , engine.PLOTS["GRANGERCAUSALITYMATRIX"])
    add_plot_entry(analyses_widgets["TIMESHIFT"]["show_button"]         , "Timeshift"                            , lambda: ENGINE.drawTimeshift(0)         , engine.PLOTS["TIMESHIFT"             ])
    add_plot_entry(analyses_widgets["ROLLINGCORRELATION"]["show_button"], "Rolling correlation (animation)"      , lambda: ENGINE.drawRollingCorrelation(0), engine.PLOTS["ROLLINGCORRELATION"])
    add_plot_entry(analyses_widgets["ROLLINGTIMESHIFT"]["show_button"]  , "Rolling timeshift (animation)"        , lambda: ENGINE.drawRollingTimeshift(0)  , engine.PLOTS["ROLLINGTIMESHIFT"])
    add_plot_entry(analyses_widgets["ROLLINGTIMESHIFT"]["show_button"]  , "Rolling timeshift spatial (animation)", lambda: ENGINE.drawRollingTimeshift(1)  , engine.PLOTS["ROLLINGTIMESHIFTSPATIAL"])
    add_plot_entry(analyses_widgets["ROLLINGTIMESHIFT"]["show_button"]  , "Rolling timeshift spatial"            , lambda: ENGINE.drawRollingTimeshift(2)  , engine.PLOTS["ROLLINGTIMESHIFTSPATIALSTATIC"])
    add_plot_entry(analyses_widgets["ROLLINGORDER"]["show_button"]      , "Rolling order stats : bar graph"      , lambda: ENGINE.drawRollingOrderStats(0) , engine.PLOTS["ROLLINGORDERBAR"])
    add_plot_entry(analyses_widgets["ROLLINGORDER"]["show_button"]      , "Rolling order stats : pie graph"      , lambda: ENGINE.drawRollingOrderStats(1) , engine.PLOTS["ROLLINGORDERPIE"])
    add_plot_entry(analyses_widgets["ROLLINGORDER"]["show_button"]      , "Rolling order spatial (animation)"    , lambda: ENGINE.drawRollingOrderStats(2) , engine.PLOTS["ROLLINGORDERSPATIAL"])
    add_plot_entry(analyses_widgets["CLUSTERING"]["show_button"]        , "Clustered events"                     , lambda: ENGINE.drawClustering(0)        , engine.PLOTS["CLUSTEREDEVENTS"       ])
    add_plot_entry(analyses_widgets["CLUSTERING"]["show_button"]        , "Dendrogram"                           , lambda: ENGINE.drawClustering(1)        , engine.PLOTS["DENDROGRAM"            ])

    add_export_entry(analyses_widgets["CORRELATION"]["export_button"]       , "Correlation matrix"      , lambda destination: ENGINE.exportCorrelation(which=0, destination=destination)       , engine.EXPORTS["CORRELATIONMATRIX"     ])
    add_export_entry(analyses_widgets["CORRELATION"]["export_button"]       , "Granger causality matrix", lambda destination: ENGINE.exportCorrelation(which=1, destination=destination)       , engine.EXPORTS["GRANGERCAUSALITYMATRIX"])
    add_export_entry(analyses_widgets["TIMESHIFT"]["export_button"]         , "Timeshift"               , lambda destination: ENGINE.exportTimeshift(which=0, destination=destination)         , engine.EXPORTS["TIMESHIFT"])
    add_export_entry(analyses_widgets["ORDER"]["export_button"]             , "Order"                   , lambda destination: ENGINE.exportOrder(which=0, destination=destination)             , engine.EXPORTS["ORDER"])
    add_export_entry(analyses_widgets["ROLLINGCORRELATION"]["export_button"], "Rolling correlation"     , lambda destination: ENGINE.exportRollingCorrelation(which=0, destination=destination), engine.EXPORTS["ROLLINGCORRELATION"])
    add_export_entry(analyses_widgets["ROLLINGTIMESHIFT"]["export_button"]  , "Rolling timeshift"       , lambda destination: ENGINE.exportRollingTimeshift(which=0, destination=destination)  , engine.EXPORTS["ROLLINGTIMESHIFT"])
    add_export_entry(analyses_widgets["ROLLINGORDER"]["export_button"]      , "Rolling order"           , lambda destination: ENGINE.exportRollingOrder(which=0, destination=destination)      , engine.EXPORTS["ROLLINGORDER"])
    add_export_entry(analyses_widgets["CLUSTERING"]["export_button"]        , "Clustered events"        , lambda destination: ENGINE.exportClustering(which=0, destination=destination)        , engine.EXPORTS["CLUSTERING"])

    add_local_export_entry(analyses_widgets["CLUSTERING"]["export_button"]  , "To channel selection"    , export_dendrogram_to_electrode_selection                                             , engine.EXPORTS["CLUSTERING"])

    # """ Create all export menu entries """
    # def add_export_entry(optionmenu, text, export_callback, status_check_reference):
    #     optionmenu.add_choice((text, export_callback))
    #     def update():
    #         state = ENGINE._isExportReady(status_check_reference)
    #         state = 'normal' if state else 'disabled'
    #         optionmenu.change_state(text, state)
    #     plot_updates.append(update)

    def import_params_from_engine():
        sourcedata_processingfs_entry_doublevar.set(ENGINE.parameters["processing_Fs"])
        sourcedata_rollingwindow_entry_doublevar.set(ENGINE.parameters["rolling_window_s"])
        preproc_timestamps_tolerance_entry_doublevar.set(ENGINE.parameters["evt_tolerance_s"])
        preproc_timestamps_rms_checkbox_state.set(ENGINE.parameters["RMS"]["enable"])
        preproc_timestamps_rms_entry_doublevar.set(ENGINE.parameters["RMS"]["window_s"])
        preproc_rawdata_rms_checkbox_state.set(ENGINE.parameters["RMS"]["enable"])
        preproc_rawdata_rms_entry_doublevar.set(ENGINE.parameters["RMS"]["window_s"])
        preproc_rawdata_filters_entry_HP_cutoff_doublevar.set(ENGINE.parameters["filters"]["args"]["hp"][0][0])
        preproc_rawdata_filters_entry_HP_order_intvar.set(    ENGINE.parameters["filters"]["args"]["hp"][0][1])
        preproc_rawdata_filters_entry_LP_cutoff_doublevar.set(ENGINE.parameters["filters"]["args"]["lp"][0][0])
        preproc_rawdata_filters_entry_LP_order_intvar.set(    ENGINE.parameters["filters"]["args"]["lp"][0][1])
        sourcedata_timerange_checkbox_state.set(0 if ENGINE.parameters["time_range_s"] is None else 1)
        sourcedata_timerange_entry1_doublevar.set(0 if ENGINE.parameters["time_range_s"] is None else ENGINE.parameters["time_range_s"][0])
        sourcedata_timerange_entry2_doublevar.set(0 if ENGINE.parameters["time_range_s"] is None else ENGINE.parameters["time_range_s"][1])

        if type(ENGINE.parameters["MEA_layout"]) is str:
            sourcedata_mealayout_dropdown_strvar.set(ENGINE.parameters["MEA_layout"])
            sourcedata_mealabeling_dropdown_strvar.set(ENGINE.parameters["MEA_layout"])
        else:
            colprint.printwar("Warning : could not import MEA layout from engine")
        # FIXME : this doesnt sync Channel filters

    def apply_params_to_engine():
        ENGINE.parameters["time_range_s"]       = [sourcedata_timerange_entry1_doublevar.get(), sourcedata_timerange_entry2_doublevar.get()] if sourcedata_timerange_checkbox_state.get() else None
        ENGINE.parameters["processing_Fs"]      = sourcedata_processingfs_entry_doublevar.get()
        ENGINE.parameters["channel_filters"]    = [k for k in sourcedata_channels_listbox.get() if sourcedata_channels_listbox.get()[k].get()]
        ENGINE.parameters["hub_reference"]      = sourcedata_hubreference_listbox.get() if sourcedata_hubreference_listbox.get() != "Auto" else None
        ENGINE.parameters["rolling_window_s"]   = sourcedata_rollingwindow_entry_doublevar.get()
        # Kind of a hack to circumvent MEAs that are not labelled correctly; that's annoying and it should never happen, but it does
        MEA_layout   = getattr(engine.MEAs, sourcedata_mealayout_dropdown_strvar.get()).clone()   # Get the actual layout
        MEA_labeling = getattr(engine.MEAs, sourcedata_mealabeling_dropdown_strvar.get()).clone() # Get the (mis)used labeling convention (hopefully it exists, otherwise I won't even bother)
        MEA_layout.relabel(MEA_labeling)                                                          # Relabel the layout, so we get the correct electrode placement AND the correct labels
        ENGINE.parameters["MEA_layout"] = MEA_layout                                              # All is well now
        if ENGINE.datatype in engine.TIMESTAMP_DATATYPES:
            ENGINE.parameters["RMS"]["enable"]   = preproc_timestamps_rms_checkbox_state.get()
            ENGINE.parameters["RMS"]["window_s"] = preproc_timestamps_rms_entry_doublevar.get()
            ENGINE.parameters["evt_tolerance_s"] = preproc_timestamps_tolerance_entry_doublevar.get()
        if ENGINE.datatype in engine.WAVEFORM_DATATYPES:
            ENGINE.parameters["RMS"]["enable"]   = preproc_rawdata_rms_checkbox_state.get()
            ENGINE.parameters["RMS"]["window_s"] = preproc_rawdata_rms_entry_doublevar.get()
            ENGINE.parameters["filters"] = {"family": "BPfilters", "args": {"hp": [[None,None]], "lp": [[None,None]], "filtertype": ""}}
            ENGINE.parameters["filters"]["args"]["filtertype"] = "bessel"
            ENGINE.parameters["filters"]["args"]["hp"][0][0] = preproc_rawdata_filters_entry_HP_cutoff_doublevar.get()
            ENGINE.parameters["filters"]["args"]["hp"][0][1] = preproc_rawdata_filters_entry_HP_order_intvar.get()
            ENGINE.parameters["filters"]["args"]["lp"][0][0] = preproc_rawdata_filters_entry_LP_cutoff_doublevar.get()
            ENGINE.parameters["filters"]["args"]["lp"][0][1] = preproc_rawdata_filters_entry_LP_order_intvar.get()

    @assets.alertonfail
    def export_parameters():
        file_path = tkfd.asksaveasfilename(filetypes=[("JSON file", "*.json")])
        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"
            # Due to the mea layout hack, MEA layouts are not a string anymore ...
            # Workaround : apply string, export, re-apply regular.
            apply_params_to_engine()                                                     # Apply parameters
            ENGINE.parameters["MEA_layout"] = sourcedata_mealayout_dropdown_strvar.get() # Fix Mea layout not being serializable
            ENGINE.exportParameters(file_path)                                           # Export
            apply_params_to_engine()                                                     # Re-apply parameters
            msg = "Export successful"
            message(msg)
            colprint.printokg(msg)

    @assets.alertonfail
    def import_parameters():
        file_path = tkfd.askopenfilename(initialdir=".", filetypes=[("JSON file", "*.json")])
        if file_path:
            ENGINE.importParameters(file_path)
            import_params_from_engine()
            update_sourcedata_timerange()
            update_preproc_timestamps_rms()
            update_preproc_rawdata_rms()
            msg = "Import successful"
            message(msg)
            colprint.printokg(msg)

    """ Overload command-line functions to a graphic alternative """
    # engine.processing.pbar = pbar
    engine.prompt_fs = prompt_fs

    """ Define run routine """
    @assets.alertonfail
    def run():
        ''' Configure '''
        apply_params_to_engine()
        ''' Run '''
        if ENGINE.timestamps_raw:
            ENGINE.preprocessTimestamps()
            ENGINE.bakeWaveforms()
        ENGINE.preprocessWaveforms()
        if analyses_widgets["CORRELATION"]["checkbox_state"].get():
            ENGINE.bakeCorrelation()
        if analyses_widgets["TIMESHIFT"]["checkbox_state"].get():
            ENGINE.bakeTimeshift()
        if analyses_widgets["ORDER"]["checkbox_state"].get():
            ENGINE.bakeOrder()
        if analyses_widgets["ACTIVATIONORDER"]["checkbox_state"].get():
            ENGINE.bakeActivationOrder()
        if analyses_widgets["CLUSTERING"]["checkbox_state"].get():
            ENGINE.bakeClustering()
        if analyses_widgets["ROLLINGCORRELATION"]["checkbox_state"].get():
            ENGINE.bakeRollingCorrelation()
        if analyses_widgets["ROLLINGTIMESHIFT"]["checkbox_state"].get():
            ENGINE.bakeRollingTimeshift()
        if analyses_widgets["ROLLINGORDER"]["checkbox_state"].get():
            ENGINE.bakeRollingOrder()
        update_all_plot_status()
        msg = "Successfully ran analysis"
        messagebox.showinfo(title="Success", message=msg)
        colprint.printokg(msg)

    """ Callbacks """
    filehandling_load_button["command"] = load_data
    sourcedata_timerange_checkbox["command"] = update_sourcedata_timerange
    preproc_timestamps_rms_checkbox["command"] = update_preproc_timestamps_rms
    preproc_rawdata_rms_checkbox["command"] = update_preproc_rawdata_rms
    analysisctrl_run_button["command"] = run
    analysisctrl_import_params_button["command"] = import_parameters
    analysisctrl_export_params_button["command"] = export_parameters
    sourcedata_mealayout_dropdown_strvar.trace('w', lambda *args: sourcedata_mealabeling_dropdown_strvar.set(sourcedata_mealayout_dropdown_strvar.get()))
    sourcedata_mealayout_dropdown_strvar


    """ Init gui """
    import_params_from_engine()
    message()
    update_sourcedata_timerange()
    update_preproc_timestamps_rms()
    update_preproc_rawdata_rms()
    update_all_plot_status()
    disable_children(preproc_timestamps_labelframe)
    disable_children(preproc_rawdata_labelframe)


    root.mainloop()
