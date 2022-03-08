#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum

CLEAR_QUEUE_AFTER_EVERY_LOCATION: bool = True
"""If True, clear the priority queue after every repaired fault location"""

CHARACTERS: list[str] = [
    '0',  # Digits
    '=', '\\', '/', '\t', ';', ':', '.', ',', '^', '~', '`', '\'', '"', ')', '(', '[', ']', '{', '}', '\n', ' ',  # Special characters
    'A',  # Upper-Case characters
    'a',  # Lowercase characters. Add all remaining lowercase characters here to test the whole character class
    'n', 'u', 'l', 't', 'r', 'e', 'f', 'a', 's',  # JSON keyword characters (null, true, false
]
"""Characters to be inserted in insertion operations.
For bRepair, those classes are defined in https://projects.cispa.saarland/lukas.kirschner/bfuzzerrepairer/-/blob/main/project/src/main/java/bfuzzerrepairer/program/repairer/brepair/CharacterClass.java
"""

USE_CHARACTER_LIST: bool = True
"""If true, only attempt insertions from the given character list"""

ALLOW_MULTIPLE_CONSECUTIVE_WHITESPACES: bool = False
"""If True, allow inserting multiple consecutive whitespaces"""


class Status(enum.Enum):
    Complete = 0
    Incomplete = 1
    Incorrect = -1


class Repair:
    def __repr__(self):
        return repr((self.inputstr, self.boundary))

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
                      mask='_D%d' % self.boundary)

    def apply_insert(self):
        new_items = []
        if USE_CHARACTER_LIST:
            possible_chars = string.printable
        else:
            possible_chars = CHARACTERS
        for i in possible_chars:
            if i.isspace() and not ALLOW_MULTIPLE_CONSECUTIVE_WHITESPACES:
                if self.boundary > 0 and self.inputstr[self.boundary - 1].isspace():
                    continue  # Skip consecutive whitespace
            v = self.inputstr[:self.boundary] + i + self.inputstr[self.boundary:]
            new_items.append(Repair(v, self.boundary,
                                    mask='_I%d' % self.boundary
                                    ))
        return new_items

    def apply_modify(self):
        new_items = []
        for i in string.printable:
            v = self.inputstr[:self.boundary] + i + self.inputstr[self.boundary + 1:]
            new_items.append(Repair(v, self.boundary,
                                    mask='_M%d' % self.boundary
                                    ))
        return new_items

    def extend_item(self):
        assert self._status is None
        assert not self.extended
        # need to be done on the item becauese of invariant.
        new_val = 0
        while True:
            # assert boundary+new_val <= len(inputstr) <- inserts can overshoot
            if (self.boundary + new_val) > len(self.inputstr):
                assert len(self.inputstr) == (self.boundary + new_val - 1)
                self.boundary = self.boundary + new_val - 1
                self.extended = True
                return self
            s = Repair(self.inputstr, self.boundary + new_val)
            if s.is_incomplete():
                new_val += 1
                continue
            if s.is_incorrect():
                # the current new_val is bad, so go back to previous
                self.boundary = self.boundary + new_val - 1
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
        # return e_arr

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
    return right - 1


# at the boundary, it is always wrong.
# the incomplete substring is one behind boundary. i.e inputval[:boundary] 

MAX_NUM_PER_MASK = 1000


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
        if i.mask not in masks: masks[i.mask] = []
        masks[i.mask].append(i)

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
    global Threads, EDIT_DIST
    # First start with zero edit distance
    # priority, item where item is an array of elements 
    ThreadHash = {0: [Repair(inputval, boundary, extended=True)]}
    edit_dist = 0
    while True:
        EDIT_DIST = edit_dist
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
                    if CLEAR_QUEUE_AFTER_EVERY_LOCATION:
                        new_boundary = binary_search(i.full_input())
                        ThreadHash = {edit_dist + 1: [i, new_boundary]}
                        break  # inner loop
        if completed:
            return completed
        edit_dist += 1
    assert False


def repair(inputval):
    assert Repair(inputval, 0).is_incomplete()
    assert Repair(inputval, len(inputval)).is_incorrect()
    # first do binary search to find the boundary
    # not a requirement. Extend item will do as well.
    boundary = binary_search(inputval)
    assert Repair(inputval, boundary).is_incomplete()
    assert Repair(inputval, boundary + 1).is_incorrect()
    return find_fixes(inputval, boundary)


EDIT_DIST = 0


def logit(*v):
    print(EDIT_DIST, *v)
    return


TESTED = {}


def validate_json(input_str):
    if input_str in TESTED: return TESTED[input_str]
    TESTED[input_str] = _validate_json(input_str)
    return TESTED[input_str]


def _validate_json(input_str):
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


def main(inputval):
    fixes = repair(inputval)
    for fix in fixes:
        print('FIXED', repr(str(fix)))


# '{ "ABCD":[*"1,2,3,4,5,6"]*}'
# '{ "item": "Apple", "price": ***3.45 }'
# '[**]'
# '[**1]'
# '[*1*]'
# '{ "name": "Dave" "age": 42 }'
main(sys.argv[1])
