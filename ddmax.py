import json
import sys

def test(s):
    print('test:', repr(s))
    if not s: return True
    try:
        json.loads(s)
        print('YES', s)
    except:
        return False
    return True

CX_S = None

# Fig 5: c'y contains the indexes of passing chars. Initially empty when n = 2
# c'y is subset of cx such that test(c'y) succeeds, and delta = cx-c'y is 1-minimal
def ddmax2(cprime_y, n):
    CX_minus_cprime_y = [i for i,s in enumerate(CX_S) if i not in cprime_y]
    # Fig 5: where delta = CX - c'y
    delta = CX_minus_cprime_y

    # Fig 5: recursion invariant for ddmax2 is test(cprime_y) and n <= len(delta)
    assert n <= len(delta)
    #TODO: if len(delta) < n: return cprime_y

    # Fig 5: For all delta_n[i] len(delta_n[i]) ~ (len(delta)/n) holds
    # split delta to n parts giving us delta_i == delta_n[i]
    # Fig 5: all delta_n[i] are pairwise disjoint
    delta_n = split_idxs(delta, n)
    # strs_n = [to_str(d) for d in delta_n]

    # Fig 5: if exist i such that test(cx-delta_i) holds, increase to complement
    passing_deltas = []
    for delta_i in delta_n:
        CX_minus_delta_i = [i for i,s in enumerate(CX_S) if i not in delta_i]
        s = to_str(CX_minus_delta_i)
        if test(s):
            passing_deltas.append((s, CX_minus_delta_i))

    if passing_deltas: # increase to complement
        #if \exist i \in {1..n} such that test(c_x - delta_i) holds
        CX_minus_delta_i = passing_deltas[0][1] # get the first such passing
        #pudb.set_trace()
        return ddmax2(CX_minus_delta_i, 2)

    #Fig 5: else, if exist i such that test(c'y union delta_i) holds, increase to subset
    passing_deltas = []
    for delta_i in delta_n:
        cprime_y_union_delta_i = cprime_y + delta_i # these are indexes
        delta_x_idxs = [i for i,s in enumerate(CX_S) if i in cprime_y_union_delta_i]
        s = to_str(delta_x_idxs)
        if test(s):
            passing_deltas.append((s, delta_x_idxs))
    if passing_deltas: # increase to subset
        # if \exist i \in {1 ... n}. test(cprime_y\union delta_i) holds
        delta_x_idxs = passing_deltas[0][1] # get the first such passing
        #pudb.set_trace()
        return ddmax2(delta_x_idxs, max(n-1, 2))

    #Fig 5: else, if n < len(delta), increase granularity
    #note: CX_minus_cprime_y = CX_S - cprime_y
    if n < len(CX_minus_cprime_y):
        # Fig 5: ddmax2(c'y, min(|cx|, 2n))  <-- this is buggy
        #return ddmax2(cprime_y, min(len(CX_S), 2*n)) # XXX: LIKELY BUGGY but from Fig 5.
        return ddmax2(cprime_y, min(len(CX_minus_cprime_y), 2*n)) # THIS WILL WORK: 
    #else:
    return cprime_y

def to_str(idxs):
    return ''.join([CX_S[i] for i in idxs])

# Choose one of the two:
#round down
def split_idxs(lst,n, round_down=True):
    stride = len(lst)//n
    rem =  len(lst) - (stride * n)
    if not rem:
        return  [lst[i*stride:(i*stride+stride)] for i in range(0,n)]
    if round_down:
        return [lst[i*stride:(i*stride+stride)] for i in range(0,n-1)] + [lst[stride*(n-1):]]
    else:
        stride += 1
        return  [lst[i*stride:(i*stride+stride)] for i in range(0,n)]


def ddmax(cx):
    global CX_S
    CX_S = list(cx)
    empty_idxs = []
    # From Fig 5.
    # ddmax(CX_S) = ddmax2(empty_idxs, 2) where
    sol_idxs = ddmax2(empty_idxs, 2)
    return ''.join([s for i,s in enumerate(CX_S) if i in sol_idxs] )

inputstr = '{ "item": "Apple", "price": ***3.45 }'
#inputstr = '[*1, *2]'

if __name__ == "__main__":
    #s = sys.argv[1] # inputstr
    s = inputstr
    assert not test(s)
    solution = ddmax(s)
    print('SOLUTION:', solution)
    
# python3 -m pudb ddmax.py '{1:$+1}'  
# python3 -m pudb ddmax.py '{123:$+1}'
