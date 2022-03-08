#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum

# TODO: We need to sample from inserts and modifiers to prevent them growing
# out of bounds. The idea is to collect all delete,insert,modification indexes
# and form a mask. i.e 3D_4I_5M means that at boundary 3, deletion happened,
# then, in the resulting string, at boundary4, insertion happenbed, and in the
# resuting, at boundary 5, modification happened. Then, we sample from the
# items with same mask. This needs to be done before extending. That is, each
# extend, we should test all possible character extensions on the sampled
# strings.

class Status(enum.Enum):
    Complete = 0
    Incomplete = 1
    Incorrect = -1

class Repair:
    def __repr__(self):
        return repr((self.inputstr, self.boundary))

    def __str__(self):
        return self.inputstr[:self.boundary]

    def __init__(self, inputstr, boundary, extended=False):
        self.inputstr, self.boundary = inputstr, boundary
        self.extended = extended

    def test(self):
        return validate_json(self.inputstr[:self.boundary])

    def is_incomplete(self):
        return self.test()[0] == Status.Incomplete

    def is_incorrect(self):
        return self.test()[0] == Status.Incorrect

    def is_complete(self):
        return self.test()[0] == Status.Complete

    def apply_delete(self):
        return Repair(self.inputstr[:self.boundary] +
                self.inputstr[self.boundary+1:], self.boundary)

    def apply_insert(self):
        new_items = []
        for i in string.printable:
            v = self.inputstr[:self.boundary] + i + self.inputstr[self.boundary:]
            new_items.append(Repair(v, self.boundary))
        return new_items

    def apply_modify(self):
        new_items = []
        for i in string.printable:
            v = self.inputstr[:self.boundary] + i + self.inputstr[self.boundary+1:]
            new_items.append(Repair(v, self.boundary))
        return new_items

    def extend_item(self):
        assert not self.extended
        # need to be done on the item becauese of invariant.
        new_val = 0
        while True:
            #assert boundary+new_val <= len(inputstr) <- inserts can overshoot
            if (self.boundary+new_val) > len(self.inputstr):
                assert len(self.inputstr) == (self.boundary + new_val -1)
                self.boundary = self.boundary + new_val-1
                self.extended = True
                return self
            s = Repair(self.inputstr, self.boundary+new_val)
            if s.is_incomplete():
                new_val += 1
                continue
            if s.is_incorrect():
                # the current new_val is bad, so go back to previous
                self.boundary = self.boundary + new_val-1
                self.extended = True
                return self
            if s.is_complete():
                self.boundary = self.boundary + new_val
                self.extended = True
                return self
            assert False
        assert False


    def repair_and_extend(self):
        e_arr = []
        item_d = self.apply_delete()
        ie = item_d.extend_item()
        e_arr.append(ie)
        #return e_arr

        # for insert and modify, only apepnd if it resulted in a boundary
        # increase
        items_i = self.apply_insert()
        items_m = self.apply_modify()

        new_items = items_i + items_m
        # now extend these.
        for i in new_items:
            old_boundary = i.boundary
            ie = i.extend_item()
            if ie.boundary > old_boundary:
                e_arr.append(ie)
        return e_arr

def binary_search(array):
    left, right = 0, len(array) - 1
    # Main loop which narrows our search range.
    while left + 1 < right:
        middle = (left + right) // 2
        if Repair(array, middle).is_incomplete():
            left = middle
        else:
            right = middle
    return right-1

# at the boundary, it is always wrong.
# the incomplete substring is one behind boundary. i.e inputval[:boundary] 

Threads = []

def find_fixes(inputval, boundary):
    global Threads
    # First start with zero edit distance
    # priority, item where item is an array of elements 
    ThreadHash = {0: [Repair(inputval, boundary, extended=True)]}
    edit_dist = 0
    while True:
        # fetch the first rank groups.
        current_items = ThreadHash[edit_dist]
        for item in current_items:
            # try repair and extending each item until we get incorrect.
            new_items = item.repair_and_extend()

            completed = []
            for i in new_items:
                if (edit_dist+1) not in ThreadHash: ThreadHash[edit_dist+1] = []
                ThreadHash[edit_dist+1].append(i)
                if i.is_complete():
                    completed.append(i)
            if completed:
                return completed
        edit_dist += 1
    assert False

def repair(inputval, test):
    assert Repair(inputval, 0).is_incomplete()
    assert Repair(inputval, len(inputval)).is_incorrect()
    # first do binary search to find the boundary
    # not a requirement. Extend item will do as well.
    boundary = binary_search(inputval)
    assert Repair(inputval,boundary).is_incomplete()
    assert Repair(inputval,boundary+1).is_incorrect()
    return find_fixes(inputval, boundary)

def logit(*v):
    print(*v)
    return

def validate_json(input_str):
    try:
        json.loads(input_str)
        logit('*', input_str)
        return Status.Complete, -1, ''
    except Exception as e:
        msg = str(e)
        if msg.startswith('Expecting'):
            # Expecting value: line 1 column 4 (char 3)
            n = int(msg.rstrip(')').split()[-1])
            # If the error is 'outside' the string, it can still be valid
            if n >= len(input_str):
                logit('+', input_str)
                return Status.Incomplete, n, ''
            elif len(input_str) > 1 and input_str[-1] == '.' and input_str[-2].isdigit():
                # JSON returns incorrect for [3. rather than incomplete.
                return Status.Incomplete, n, ''
            else:
                logit('X', input_str)
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Unterminated'):
            # Unterminated string starting at: line 1 column 1 (char 0)
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                logit('+', input_str)
                return Status.Incomplete, n, ''
            else:
                logit('+', input_str)
                return Status.Incomplete, n, input_str[n]
        elif msg.startswith('Extra data'):
            n = int(msg.rstrip(')').split()[-1])
            if n >= len(input_str):
                logit('X', input_str)
                return Status.Incorrect, n, ''
            else:
                logit('X', input_str)
                return Status.Incorrect, n, input_str[n]
        elif msg.startswith('Invalid '):
            idx = msg.find('(char ')
            eidx = msg.find(')')
            s = msg[idx + 6:eidx]
            n = int(s)
            logit('X', input_str)
            return Status.Incorrect, n, input_str[n]
        else:
            raise e


def main(inputval):
    fixes = repair(inputval, validate_json)
    for fix in fixes:
        print('FIXED', repr(str(fix)))

# '{ "ABCD":[*"1,2,3,4,5,6"]*}'
# '{ "item": "Apple", "price": ***3.45 }'
# '[**]'
# '[**1]'
# '{ "name": "Dave" "age": 42 }'
main(sys.argv[1])
