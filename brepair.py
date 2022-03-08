#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum

class Status(enum.Enum):
    Complete = 0
    Incomplete = 1
    Incorrect = -1

def logit(v): return

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

def extend_item(item, is_incomplete, is_incorrect, is_complete):
    inputval, boundary = item 
    new_val = 0
    while True:
        s = inputval[0:boundary+new_val]
        assert boundary+new_val < len(input_val)
        if is_incomplete(s):
            new_val += 1
            continue
        if is_incorrect(s):
            return (inputval, boundary + new_val)
        if is_complete(s):
            return (inputval, boundary + new_val)
        assert False
    assert False


def apply_delete(inputval, boundary):
    return inputval[:boundary] + inputval[boundary+1:]

def apply_insert(inputval, boundary):
    new_items = []
    for i in string.printable:
        v = inputval[:boundary] + i + inputval[boundary:]
        new_items.append(v)
    return new_items

def apply_modify(inputval, boundary):
    new_items = []
    for i in string.printable:
        v = inputval[:boundary] + i + inputval[boundary+1:]
        new_items.append(v)
    return new_items

def repair_and_extend(item, is_incomplete, is_incorrect, is_complete):
    item_d = apply_delete(*item)
    items_i = apply_insert(*item)
    items_m = apply_modify(*item)

    new_items = [item_d] + items_i, items_m
    # now extend these.
    e_arr = []
    for i in new_items:
        ie = extend_item(i, is_incomplete, is_incorrect, is_complete)
        e_arr.append(ie)
    return e_arr

Threads = []

def find_fixes(inputval, boundary, is_incomplete, is_incorrect, is_complete):
    global Threads
    # First start with zero edit distance
    # priority, item where item is an array of elements 
    heapq.heappush(Threads, (0, [(inputval, boundary)]))
    while Threads:
        # fetch the first rank groups.
        edit_dist, current_items = heapq.heappop(Threads)
        for item in current_items:
            # try repair and extending each item until we get incorrect.
            new_items = repair_and_extend(item,
                    is_incomplete,
                    is_incorrect,
                    is_complete)
            for i in new_items:
                heapq.heappush(Threads, (edit_dist+1, i))
                if is_complete(i):
                    return i
        break

def repair(inputval, test):
    is_incomplete = lambda x: test(x)[0] == Status.Incomplete
    is_incorrect = lambda x: test(x)[0] == Status.Incorrect
    is_complete = lambda x: test(x)[0] == Status.Complete
    assert is_incomplete('')
    assert is_incorrect(inputval)
    # first do binary search to find the boundary
    boundary = binary_search(inputval, is_incomplete)
    assert is_incomplete(inputval[:boundary-1])
    assert is_incorrect(inputval[:boundary])
    return find_fixes(inputval, boundary,
            is_incomplete,
            is_incorrect,
            is_complete)

def main(inputval):
    fixes = repair(inputval, validate_json)
    for fix in fixes:
        print(repr(fix))

main(sys.argv[1])
