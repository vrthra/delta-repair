#!/usr/bin/env python3
import json
import heapq
import sys
import string
import random
import enum
from pathlib import Path

CHARACTERS = string.printable
"""Characters to be inserted in insertion operations.
"""

# the incomplete substring is one behind boundary. i.e inputval[:boundary] 

MAX_NUM_PER_MASK = 1


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

        # for insert only append if it resulted in a boundary increase
        new_items = self.apply_insert()
        # now extend these.
        for i in new_items:
            old_boundary = i.boundary
            ie = i.extend_item()
            if ie.boundary > old_boundary:
                e_arr.append(ie)
        return e_arr


def binary_search(array, left=0, right=None):
    if Repair(array, len(array)).is_incomplete():
        return len(array) - 1
    left, right = 0, len(array) - 1
    # Main loop which narrows our search range.
    while right - left > 1:
        middle = (left + right) // 2
        if Repair(array, middle).is_incomplete():
            left = middle
        else:
            right = middle
    assert right - left == 1
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
                    yield i
        if completed:
            break
        edit_dist += 1
    assert False


def repair(inputval):
    assert Repair(inputval, 0).is_incomplete()
    assert Repair(inputval, len(inputval)).status() in [Status.Incomplete, Status.Incorrect]
    # first do binary search to find the boundary
    # not a requirement. Extend item will do as well.
    boundary = binary_search(inputval)
    assert Repair(inputval, boundary).is_incomplete()
    assert boundary + 1 >= len(inputval) or Repair(inputval, boundary + 1).is_incorrect()
    return find_fixes(inputval, boundary)


EDIT_DIST = 0


def logit(*v):
    print(EDIT_DIST, *v)
    return


TESTED = {}

num_runs: int = 0


def validate_json(input_str):
    if input_str in TESTED: return TESTED[input_str]
    TESTED[input_str] = _validate_json(input_str)
    return TESTED[input_str]


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


def _validate_json(input_str):
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


def main(inputval):
    global num_runs
    for fix in repair(inputval):
        print('FIXED', repr(str(fix)))
        break # Return only the first fix
    print(f"Number of oracle runs required for fixing this input: {num_runs}")


# '{ "ABCD":[*"1,2,3,4,5,6"]*}'
# '{ "item": "Apple", "price": ***3.45 }'
# '[**]'
# '[**1]'
# '[*1*]'
# '{ "name": "Dave" "age": 42 }'
try:
    f = Path(sys.argv[1])
    if not f.is_file():
        raise Exception()
    with f.open("r") as ff:
        inp: str = ff.read()
except UnicodeDecodeError as e:
    raise e  # We do not want to repair the file name itself
except Exception:
    inp: str = sys.argv[1]
main(inp)
