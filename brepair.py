#!/usr/bin/env python3
import json
import sys
import string
import random
import enum
class Status(enum.Enum):
    Complete = 0
    Incomplete = 1
    Incorrect = -1

def new_char(seen): return random.choice([i for i in string.printable if i not in seen])

def logit(v): return

def generate(prev_str=''):
    seen = set()
    while True:
        char = new_char(seen)
        curr_str = prev_str + char
        rv, _n, _at = validate_json(curr_str)
        if rv == Status.Complete:
            return curr_str
        elif rv == Status.Incomplete:
            seen.clear()
            prev_str = curr_str
        elif rv == Status.Incorrect:
            seen.add(char)
        else:
            raise Exception(rv)
    return None

def validate_json(input_str):
    try:
        json.loads(input_str)
        return Status.Complete, -1, ''
    except Exception as e:
        msg = str(e)
        if msg.startswith('Expecting'):
            # Expecting value: line 1 column 4 (char 3)
            n = int(msg.rstrip(')').split()[-1])
            # If the error is 'outside' the string, it can still be valid
            if n >= len(input_str):
                return Status.Incomplete, n, ''
            else:
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Unterminated'):
            # Unterminated string starting at: line 1 column 1 (char 0)
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                return Status.Incomplete, n, ''
            else:
                return Status.Incomplete, n, input_str[n]
        elif msg.startswith('Extra data'):
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                return Status.Incorrect, n, ''
            else:
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Invalid '):
            idx = msg.find('(char ')
            eidx = msg.find(')')
            s = msg[idx + 6:eidx]
            n = int(s)
            return Status.Incorrect, n, input_str[n]
        else:
            raise e

def create_valid_strings(n):
    i = 0
    pstr = ''
    while True:
        created_string = generate(pstr)
        if created_string is not None:
            if random.randint(1,10) > 1:
                pstr = created_string
                continue
            #if len(created_string) < 4: continue
            print(repr(created_string), file=sys.stderr)
            print(created_string)
            i += 1
            if (i >= n):
                break

def binary_search(array, is_incomplete):
    left, right = 0, len(array) - 1
    # Main loop which narrows our search range.
    while left + 1 < right:
        middle = (left + right) // 2
        if is_incomplete(array[:middle]):
            left = middle
        else:
            right = middle
    return right

def search_for_boundary(inputval, test):
    return binary_search(inputval, lambda x: test(x)[0] == Status.Incomplete)

def repair(inputval, test):
    assert test('')[0] == Status.Incomplete
    assert test(inputval)[0] == Status.Incorrect
    # first do binary search to find the boundary
    boundary = search_for_boundary(inputval, test)
    assert test(inputval[:boundary-1])[0] == Status.Incomplete
    assert test(inputval[:boundary])[0] == Status.Incorrect


def main(inputval):
    fixes = repair(inputval, validate_json)
    for fix in fixes:
        print(repr(fix))

main(sys.argv[1])
