import json
TESTED = {}
FLAG = ''

import enum

class Status(enum.Enum):
    Complete = 0
    Incomplete = 1
    Incorrect = -1

num_runs: int = 0

def logit(*v):
    print(FLAG, *v)
    return

# check if jstr fits in this context.
def it_fits(input_str):
    try:
        json.loads(input_str)
        logit('*', repr(input_str))
        return True
    except Exception as e:
        msg = str(e)
        if msg.startswith('Expecting'):
            # Expecting value: line 1 column 4 (char 3)
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                logit('+', repr(input_str))
                return True
        return False


def validate_json(input_str):
    global num_runs
    num_runs += 1
    try:
        json.loads(input_str)
        logit('*', repr(input_str))
        return Status.Complete, -1, ''
    except Exception as e:
        msg = str(e)
        if msg.startswith('Expecting'):
            # Expecting value: line 1 column 4 (char 3)
            n = int(msg.rstrip(')').split()[-1])
            # If the error is 'outside' the string, it can still be valid
            if n >= len(input_str):
                logit('+', repr(input_str))
                return Status.Incomplete, n, ''
            elif len(input_str) > 1 and input_str[-1] == '.' and input_str[-2].isdigit():
                # JSON returns incorrect for [3. rather than incomplete.
                return Status.Incomplete, n, ''
            else:
                logit('X', repr(input_str))
                remaining = input_str[n:]
                if remaining in ['t', 'tr', 'tru']:
                    # check if it fits first.
                    if it_fits(input_str[:n] + 'true'):
                        return Status.Incomplete, n, input_str[n]
                    return Status.Incorrect, n, input_str[n]
                if remaining in ['f', 'fa', 'fal', 'fals']:
                    if it_fits(input_str[:n] + 'false'):
                        return Status.Incomplete, n, input_str[n]
                    return Status.Incorrect, n, input_str[n]
                if remaining in ['n', 'nu', 'nul']:
                    if it_fits(input_str[:n] + 'null'):
                        return Status.Incomplete, n, input_str[n]
                    return Status.Incorrect, n, input_str[n]
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Unterminated'):
            # Unterminated string starting at: line 1 column 1 (char 0)
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                logit('+', repr(input_str))
                return Status.Incomplete, n, ''
            else:
                logit('+', repr(input_str))
                return Status.Incomplete, n, input_str[n]
        elif msg.startswith('Extra data'):
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                logit('X', repr(input_str))
                return Status.Incorrect, n, ''
            else:
                logit('X', repr(input_str))
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Invalid '):
            idx = msg.find('(char ')
            eidx = msg.find(')')
            s = msg[idx + 6:eidx]
            n = int(s)
            logit('X', repr(input_str))
            return Status.Incorrect, n, input_str[n]
        else:
            raise e
