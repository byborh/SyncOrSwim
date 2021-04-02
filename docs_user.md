# Docs - SyncOrSwim

## Installation

This might look like dev docs, but if you're a user, at some point you will need to install the software and the right environment to run it ...

### If you don't already have the SyncOrSwim archive

You can clone the public git repository with :

```
git clone --recurse-submodules --branch master https://git.renater.fr/anonscm/git/pypanephy/SyncOrSwim.git
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

(1) : to use the included `run.cmd` shortcut, the virtual environment path should be `path/to/syncorswim/venv`, but you are free to do as you please

All should be set

### Bonus round : updating

If you have git, you can run `git pull --recurse-submodules` to update the software (or run `update.cmd`)
