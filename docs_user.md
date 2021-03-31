# Docs - SPcorrelation2020

## Installation

This might look like dev docs, but if you're a user, at some point you will need to install the software and the right environment to run it ...

### If you don't already have the SPcorrelation2020 archive

**FIXME** : repo not live yet

You can clone the public git repository with :

```
FIXME
git clone --recurse-submodules path/to/project.git
```

### If you have the whole archive

If you have the whole archive, you should have all the necessary sources. All you have left to do is set up a python environment. Steps :

1. Install Python 3.7
2. Install virtualenv :
  * `path/to/python.exe -m pip install --upgrade pip`
  * `path/to/python.exe -m pip install virtualenv`
3. Create virtualenv (1):
  * `path/to/python.exe -m virtualenv path/to/venv`
4. Activate virtualenv :
  * `path/to/venv/Scripts/activate`
5. Install dependencies :
  * `pip install -r requirements.txt`

(1) : to use the included `run.cmd` shortcut, the virtual environment path should be `path/to/SPcorrelation2020/venv`, but you are free to do as you please

All should be set
