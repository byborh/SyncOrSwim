# import colorama
# colorama.init()
import os
if os.name == 'nt': # Init ANSI escape sequences in Windows cmd
    from ctypes import windll
    windll.kernel32.SetConsoleMode(windll.kernel32.GetStdHandle(-11), 0x0007)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format(string, which):
    return which + string + bcolors.ENDC

def printspe(string, which, *args, **kwargs):
    print(which + string + bcolors.ENDC, *args, **kwargs)

def printerr(string, *args, **kwargs):
    printspe(string, bcolors.FAIL, *args, **kwargs)

def printwar(string, *args, **kwargs):
    printspe(string, bcolors.WARNING, *args, **kwargs)

def printokg(string, *args, **kwargs):
    printspe(string, bcolors.OKGREEN, *args, **kwargs)

def printokb(string, *args, **kwargs):
    printspe(string, bcolors.OKBLUE, *args, **kwargs)

def printokc(string, *args, **kwargs):
    printspe(string, bcolors.OKCYAN, *args, **kwargs)

if __name__ == "__main__":
    print(bcolors.WARNING + "test warning" + bcolors.ENDC)
