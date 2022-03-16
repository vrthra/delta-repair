from status import Status
from subprocess import run
import tempfile
TESTED = {}
FLAG = ''
EXE = './sexp'

num_runs: int = 0

def logit(*v):
    print(FLAG, *v)
    return

def validate(input_str):
    global num_runs
    num_runs += 1
    with tempfile.NamedTemporaryFile(mode='w+t') as temp:
        temp.write(input_str)
        temp.flush()
        p = run([EXE, temp.name])
        logit('*', repr(input_str))
        if p.returncode == 0:
            return Status.Complete, 0, ''
        if p.returncode == 1:
            return Status.Incorrect, 1, ''
        else:
            return Status.Incomplete, -1, ''
