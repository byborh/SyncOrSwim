# Docs - SyncOrSwim

## Installation

Prerequisites : You will need a Python 3 installation and a git installation :
  * https://www.python.org/downloads/
  * https://git-scm.com/downloads

### Getting the SyncOrSwim archive

You can clone the public git repository with :

```
git clone --recurse-submodules --branch master https://git.renater.fr/anonscm/git/syncorswim-pub/syncorswim-pub.git
```

### When you have the whole archive

#### For Windows users

If you have the whole archive, you should have all the necessary sources. All you have left to do is set up a python environment. Steps :

1. Install Python 3.7
2. Create venv (1):
  * `path/to/python.exe -m virtualenv path/to/syncorswim/venv`
2. Install dependencies :
  * In SyncOrSwim directory, double-click `install_requirements.cmd`

All should be set

#### For (advanced) Windows users

If you have the whole archive, you should have all the necessary sources. All you have left to do is set up a python environment. Steps :

1. Install Python 3.7
2. Create venv (1):
  * `path/to/python.exe -m venv path/to/venv`
3. Activate venv :
  * `path/to/venv/Scripts/activate`
4. Install dependencies :
  * `pip install -r requirements.txt`

(1) : to use the included `run.cmd` shortcut, the virtual environment path should be `path/to/syncorswim/venv`, but you are free to do as you please

All should be set

#### For linux users

If you have the whole archive, you should have all the necessary sources. All you have left to do is set up a python environment. Steps :

1. cd to SyncOrSwim directory
2. Create venv:
  * `python3 -m venv path/to/venv`
3. Activate virtualenv :
  * `source path/to/venv/bin/activate`
4. Install dependencies :
  * `pip install -r requirements.txt`

All should be set

## Updating

  * Windows users : run `update.cmd`
  * Linux/advanced users : From SyncOrSwim directory, run `git pull --recurse-submodules`

## Running SyncOrSwim

### Windows users

You can double-click `run.cmd`, which will do everything for you.

### Linux users / advanced users

1. Activate venv
  * (Linux) `source path/to/venv/bin/activate`
  * (Windows) `path/to/venv/Scripts/activate`
2. Launch the gui :
  * `python path/to/sources/gui.py`