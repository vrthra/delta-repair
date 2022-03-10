#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum
from pathlib import Path
import conformingjson
from conformingjson import Status

CHARACTERS = string.printable
"""Characters to be inserted in insertion operations.
"""

# the incomplete substring is one behind boundary. i.e inputval[:boundary] 

MAX_NUM_PER_MASK = 1

class Repair:
    def __repr__(self):
        s = repr(str(self))
        v = (self.inputstr, self.boundary, s)
        return repr(v)

    def __str__(self):
        return self.inputstr[:self.boundary]

    def __init__(self, inputstr, boundary, mask='', extended=False):
        self.inputstr, self.boundary = inputstr, boundary
        self.extended = extended
        self.mask = mask
        self._status = None

    def full_input(self) -> str:
        """Return the full input, ignoring the boundary"""
        return self.inputstr

    def test(self, mystr):
        return validate_json(mystr)

    def status(self):
        if self._status is not None: return self._status
        self._status = self.my_status()
        return self._status

    def my_status(self):
        my_str = self.inputstr[:self.boundary]
        if self.test(my_str)[0] == Status.Incorrect: return Status.Incorrect
        if self.test(my_str)[0] == Status.Incomplete: return Status.Incomplete
        # verify this is actually complete. For example, given [*1], [] is not
        # complete. It is likely incorrect. The other chance is 12*45 where
        # 123 is (it is not complete!) incomplete rather than incorrect. To
        # check this, we need to check the next index too.
        if self.boundary >= len(self.inputstr): return Status.Complete
        my_str = self.inputstr[:self.boundary + 1]
        if self.test(my_str)[0] == Status.Incorrect: return Status.Incorrect
        if self.test(my_str)[0] == Status.Incomplete: return Status.Incomplete

        # because if 123*5 is fixed to 12395 is complete, then 1239 is
        # incomplete
        return Status.Incomplete

    def is_incomplete(self):
        return self.status() == Status.Incomplete

    def is_incorrect(self):
        return self.status() == Status.Incorrect

    def is_complete(self):
        return self.status() == Status.Complete

    def apply_delete(self):
        return Repair(self.inputstr[:self.boundary] +
                      self.inputstr[self.boundary + 1:], self.boundary,
                      mask='%s_D%d' % (self.mask, self.boundary))

    def apply_insert(self):
        new_items = []
        for i in CHARACTERS:
            v = self.inputstr[:self.boundary] + i + self.inputstr[self.boundary:]
            new_items.append(Repair(v, self.boundary,
                                    # mask='_I%d%s' % (self.boundary, i)
                                    mask='%s_I%d' % (self.mask, self.boundary)
                                    ))
        return new_items

    def bsearch_extend_item(self):
        bs = binary_search(self.inputstr, left=self.boundary-1, check=check_is_incomplete)
        if bs >= len(self.inputstr):
            self.boundary = bs
            self.extended = True
            return self
        e = self.inputstr[bs] # error causing char.
        self.boundary = bs
        return self

    # there are many more invalid inserts than valid inserts. So searching the
    # whole file again is not useful.
    def lsearch_extend_item(self, nxt=1):
        # need to be done on the item becauese of invariant.
        while True:
            # assert boundary+nxt <= len(inputstr) <- inserts can overshoot
            if (self.boundary + nxt) > len(self.inputstr):
                assert len(self.inputstr) == (self.boundary + nxt - 1)
                self.boundary = self.boundary + nxt - 1
                self.extended = True
                return self
            s = Repair(self.inputstr, self.boundary + nxt)
            if s.is_incomplete():
                #return self.extend_deleted_item()
                nxt += 1
                continue
            if s.is_incorrect():
                # the current nxt is bad, so go back to previous
                self.boundary = self.boundary + nxt - 1
                self.extended = True
                return self
            if s.is_complete():
                self.boundary = self.boundary + nxt
                self.extended = True
                return self
            assert False
        assert False

    def extend_deleted_item(self):
        assert self._status is None
        assert not self.extended
        return self.bsearch_extend_item() #(nxt=0)

    def extend_inserted_item(self):
        assert self._status is None
        assert not self.extended
        return self.lsearch_extend_item(nxt=1)

    def repair_and_extend(self):
        e_arr = []
        item_d = self.apply_delete()
        ie = item_d.extend_deleted_item()
        e_arr.append(ie)
        # return e_arr

        # for insert only append if it resulted in a boundary increase
        new_items = self.apply_insert()
        # now extend these.
        for i in new_items:
            old_boundary = i.boundary
            ie = i.extend_inserted_item()

            if ie.boundary > old_boundary:
                e_arr.append(ie)
        return e_arr

# https://blog.tylerhou.io/posts/binary-search-with-confidence/
# check == is_green
def binary_search(array, left = 0, right = None, check=None):
    left, right = 0, len(array) - 1

    #if not check(array, left):
    #    return left
    assert check(array, left)

    if check(array, right):
        return len(array)
    # Main loop which narrows our search range.
    while left + 1 < right:
        middle = (left + right) // 2
        if check(array, middle):
            left = middle
        else:
            right = middle
    return left


# at the boundary, it is always wrong.

# We need to sample from inserts and modifiers to prevent them growing
# out of bounds. The idea is to collect all delete,insert,modification indexes
# and form a mask. i.e 3D_4I_5M means that at boundary 3, deletion happened,
# then, in the resulting string, at boundary4, insertion happenbed, and in the
# resuting, at boundary 5, modification happened. Then, we sample from the
# items with same mask. This needs to be done before extending. That is, each
# extend, we should test all possible character extensions on the sampled
# strings.

def sample_items_by_mask(items):
    # sample here. We only want a fixed number of items per mask.
    masks = {}
    for i in items:
        if i.mask not in masks: masks[(i.mask, i.boundary, i.inputstr[i.boundary - 1])] = []
        masks[(i.mask, i.boundary, i.inputstr[i.boundary - 1])].append(i)

    sampled = []
    for key in masks:
        if len(masks[key]) < MAX_NUM_PER_MASK:
            res = masks[key]
        else:
            res = random.sample(masks[key], MAX_NUM_PER_MASK)
        sampled.extend(res)
    return sampled


Threads = []


def find_fixes(inputval, boundary):
    global Threads
    # First start with zero edit distance
    # priority, item where item is an array of elements 
    ThreadHash = {0: [Repair(inputval, boundary, extended=True)]}
    edit_dist = 0
    while True:
        conformingjson.FLAG = edit_dist
        # fetch the first rank groups.
        current_items = ThreadHash[edit_dist]
        chosen_items = sample_items_by_mask(current_items)
        completed = []
        for item in chosen_items:
            # try repair and extending each item until we get incorrect.
            new_items = item.repair_and_extend()

            for i in new_items:
                if (edit_dist + 1) not in ThreadHash: ThreadHash[edit_dist + 1] = []
                ThreadHash[edit_dist + 1].append(i)
                if i.is_complete():
                    completed.append(i)
                    yield i
        if completed:
            break
        edit_dist += 1
    assert False


def check_is_incomplete(sval, i):
    s_ = Repair(sval, i)
    s = str(s_)
    return s_.is_incomplete()

def repair(inputval):
    assert check_is_incomplete(inputval, 0) # 1
    assert not check_is_incomplete(inputval, len(inputval))
    # first do binary search to find the boundary
    # not a requirement. Extend item will do as well.
    boundary = binary_search(inputval, check=check_is_incomplete)
    c = inputval[boundary] # this should be the error causing char.
    assert check_is_incomplete(inputval, boundary)
    assert not check_is_incomplete(inputval, boundary+1)
    return find_fixes(inputval, boundary)


TESTED = {}

def validate_json(input_str):
    if input_str in TESTED: return TESTED[input_str]
    TESTED[input_str] = conformingjson.validate_json(input_str)
    return TESTED[input_str]

def main(inputval):
    fixes = []
    for fix in repair(inputval):
        fixes.append(fix)
        break  # Return only the first fix
    for fix in fixes:
        print('FIXED', repr(str(fix)))
    print(f"Number of oracle runs required for fixing this input: {conformingjson.num_runs}")


# '{ "ABCD":[*"1,2,3,4,5,6"]*}'
# '{ "item": "Apple", "price": ***3.45 }'
# '[**]'
# '[**1]'
# '[*1*]'
# '{ "name": "Dave" "age": 42 }'
INPUT = None
try:
    f = Path(sys.argv[1])
    if not f.is_file():
        raise Exception()
    with f.open("r") as ff:
        INPUT: str = ff.read()
except UnicodeDecodeError as e:
    raise e  # We do not want to repair the file name itself
except Exception:
    INPUT: str = sys.argv[1]

TEST = False
if TEST:
    bsearch_tests = {
    '{"_":a{}}': 'a',
    '{ "ABCD":[*"1,2,3,4,5,6"]*}': '*',
    '{ "item": "Apple", "price": ***3.45 }': '*',
    '{ "item": "Apple", "price": **3.45 }': '*',
    '[*1, *2]': '*',
	'[**]': '*',
	'[**1]': '*',
	'[*1*]': '*',
    '{ "name": "Dave" "age": 42 }': '"',
    '{ "ABCD":[*"1,2,3,4,5,6"]*}': '*',
            }
    for k, t in bsearch_tests.items():
        bs = binary_search(k, check=check_is_incomplete)
        assert k[bs] == t, f"Test '{k}' failed - Reported {k[bs]} ({bs}), but expected {t}"

main(INPUT)
