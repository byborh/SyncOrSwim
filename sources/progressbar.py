import sys
import time as timemodule

TIMEMEM   = None
UPDATEMEM = None

def inline(x, X, N=50, prefix="", suffix = "", done = "Done", stdout=True, time=True, autoupdate=0):
    """
    Base progress bar function.
    Finishes when x == X.
    ---
    x      : Current advancement
    X      : Final advancement
    N      : Bar length
    prefix : bar prefix
    suffix : bar suffix
    """
    global TIMEMEM
    global UPDATEMEM
    if x > X:
        x = X
    if TIMEMEM is None:
        TIMEMEM = timemodule.time()
    if UPDATEMEM is None:
        UPDATEMEM = timemodule.time()
    k = int(N * (x/X)) if X > 0 else N
    bar = "#" * k + " " * (N - k)
    count = f"({x+1}/{X+1})"
    text = f"\r{prefix} |{bar}| {count} {suffix}"
    if time or autoupdate :
        T = timemodule.time()
    if x >= X:
        if time:
            dt = T - TIMEMEM
            text += f" - {done} in {dt:.3f} s\n"
            TIMEMEM = None
        else:
            text += f" - {done}\n"
    if stdout:
        update = (x >= X) # Force update if progress is 100%
        if autoupdate:
            dt = T - UPDATEMEM
            if dt > autoupdate:
                update |= True
                UPDATEMEM = T
            else:
                update |= False
        else:
            update |= True
        if update :
            sys.stdout.write(text)
    return text

def inlineCycles(i, I, *args, **kwargs):
    """
    Progress bar to keep track of a given number of cycles (eg. for loop).
    i starts at 0
    Finishes when i+1 == I
    ---
    i      : Current cycle (starting at 0)
    I      : Total number of cycles
    N      : Bar length
    prefix : bar prefix
    suffix : bar suffix
    """
    inline(i, I-1, *args, **kwargs)
