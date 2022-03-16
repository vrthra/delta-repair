#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum
from pathlib import Path
import conformingjson as conformingparser
from status import Status

MAX_SIMULTANIOUS_CORRECTIONS = 2 # set it to a positive number to restrict the queue.

LAST_INSERT_ONLY = True

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

    def set_boundary(self, b):
        assert b >= 0
        self.boundary = b

    def __str__(self):
        return self.inputstr[:self.boundary]

    def __init__(self, inputstr, boundary, mask='', extended=False):
        assert boundary >= 0
        self.inputstr, self.boundary = inputstr, boundary
        self.extended = extended
        self.mask = mask
        self._status = None

    def test(self, mystr):
        return validate(mystr)

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
                      mask='%s_D%d' % (self.mask, self.boundary)).extend_deleted_item()

    def insert_at(self, k, i, suffix):
        v = self.inputstr[:k] + i + self.inputstr[k:self.boundary] + suffix
        new_item = Repair(v, k, mask='%s_I%d' % (self.mask, k))
        ie = new_item.extend_inserted_item()
        if ie.boundary > k:
           return ie
        return None

    # one of the problems with deletion is that we do not know exactly where the
    # character was deleted from, eventhough the parser can be conforming. For
    # example, given an original string "[1,2,3]", where the corruption happened
    # at the first character, we will only get the failure at the last
    # character. Hence to be accurate, what we shouuld do is to try insert all
    # characters everywhere, and see if it helps. This is ofcourse not a very
    # easy task. So we control this behavior with a switch.
    def insert_char(self, i):
        suffix = self.inputstr[self.boundary:]
        return_lst = []
        if LAST_INSERT_ONLY:
            v = self.insert_at(self.boundary, i, suffix)
            if v is not None: return_lst.append(v)
        else:
            # the repair could be any where from 0 to self.boundary (inclusive).
            # So we try all
            for k in range(self.boundary):
                v = self.insert_at(k,i, suffix)
                if v is not None: return_lst.append(v)
        return return_lst

    def apply_insert(self):
        new_items = []
        for i in CHARACTERS:
            items = self.insert_char(i)
            if items:
                new_items.extend(items)
        return new_items

    def bsearch_extend_item(self):
        bs = binary_search(self.inputstr, left=self.boundary, check=check_is_incomplete)
        assert bs >= 0
        if bs >= len(self.inputstr):
            self.set_boundary(bs)
            self.extended = True
            return self
        # e = self.inputstr[bs] # error causing char.
        self.set_boundary(bs)
        return self

    # there are many more invalid inserts than valid inserts. So searching the
    # whole file again is not useful.
    def lsearch_extend_item(self, nxt=1):
        # need to be done on the item becauese of invariant.
        while True:
            # assert boundary+nxt <= len(inputstr) <- inserts can overshoot
            if (self.boundary + nxt) > len(self.inputstr):
                assert len(self.inputstr) == (self.boundary + nxt - 1)
                self.set_boundary (self.boundary + nxt - 1)
                self.extended = True
                return self
            s = Repair(self.inputstr, self.boundary + nxt)
            if s.is_incomplete():
                #return self.extend_deleted_item()
                nxt += 1
                continue
            if s.is_incorrect():
                # the current nxt is bad, so go back to previous
                self.set_boundary(self.boundary + nxt - 1)
                self.extended = True
                return self
            if s.is_complete():
                self.set_boundary(self.boundary + nxt)
                self.extended = True
                return self
            assert False
        assert False

    def extend_deleted_item(self):
        assert self._status is None
        assert not self.extended
        return self.bsearch_extend_item()
        #return self.lsearch_extend_item(nxt=0)

    def extend_inserted_item(self):
        assert self._status is None
        assert not self.extended
        return self.lsearch_extend_item(nxt=1)
        #return self.bsearch_extend_item()

    def repair_and_extend(self):
        e_arr = []
        item_d = self.apply_delete()
        e_arr.append(item_d)

        # for insert only append if it resulted in a boundary increase
        new_items = self.apply_insert()
        e_arr.extend(new_items)
        return e_arr

# https://blog.tylerhou.io/posts/binary-search-with-confidence/
# check == is_green
def binary_search(array, left = 0, right = None, check=None):
    if not array: return left
    left, right = 0, len(array) - 1

    #if not check(array, left):
    #    return left
    assert check(array, left)

    if check(array, right):
        return len(array)-1
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
        key = (i.mask, i.boundary, i.inputstr[i.boundary-1:i.boundary])
        if i.mask not in masks: masks[key] = []
        masks[key].append(i)

    sampled = []
    for key in masks:
        if len(masks[key]) < MAX_NUM_PER_MASK:
            res = masks[key]
        else:
            res = random.sample(masks[key], MAX_NUM_PER_MASK)
        sampled.extend(res)
    return filter_best(sampled)

def filter_best(items):
    if MAX_SIMULTANIOUS_CORRECTIONS < 0: return items
    boundaries = sorted({i.boundary for i in items}, reverse=True)
    return [i for i in items if i.boundary in  boundaries[:MAX_SIMULTANIOUS_CORRECTIONS]]

Threads = []


def find_fixes(inputval, boundary):
    global Threads
    # First start with zero edit distance
    # priority, item where item is an array of elements
    next_items = [Repair(inputval, boundary, extended=True)]
    edit_dist = 0
    while True:
        conformingparser.FLAG = edit_dist
        # fetch the first rank groups.
        current_items = next_items
        next_items = []
        chosen_items = sample_items_by_mask(current_items)
        completed = []
        for item in chosen_items:
            # try repair and extending each item until we get incorrect.
            new_items = item.repair_and_extend()

            for i in new_items:
                next_items.append(i)
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
    # assert not check_is_incomplete(inputval, len(inputval))
    # first do binary search to find the boundary
    # not a requirement. Extend item will do as well.
    boundary = binary_search(inputval, check=check_is_incomplete)
    c = inputval[boundary] # this should be the error causing char.
    assert check_is_incomplete(inputval, boundary)
    # assert not check_is_incomplete(inputval, boundary+1)
    return find_fixes(inputval, boundary)


TESTED = {}

def validate(input_str):
    if input_str in TESTED: return TESTED[input_str]
    TESTED[input_str] = conformingparser.validate(input_str)
    return TESTED[input_str]

def main(inputval):
    fixes = []
    for fix in repair(inputval):
        fixes.append(fix)
        break  # Return only the first fix
    for fix in fixes:
        print('FIXED', repr(str(fix)))
    print(f"Number of oracle runs required for fixing this input: {conformingparser.num_runs}")


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

INPUT = None
if __name__ == '__main__':
    try:
        f = Path(sys.argv[1])
        if f.is_file():
            with f.open("r") as ff:
                 INPUT = ff.read()
        else:
            INPUT = sys.argv[1]
        main(INPUT)
    except UnicodeDecodeError as e:
        raise e
