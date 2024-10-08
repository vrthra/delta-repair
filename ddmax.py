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
CX_I = None

def minus(first, second):
    return [i for i in first if i not in second]

def union(first, second):
    return list(sorted(first + second))

def intersect(first, second):
    return [i for i in first if i in second]

def increase_to_complement(delta_n):
    # Fig 5: if exist i such that test(cx-delta_i) holds, increase to complement
    for delta_i in delta_n:
        CX_minus_delta_i = minus(CX_I, delta_i)
        s = to_str(CX_minus_delta_i)
        print('increase_to_complement:', repr(s))
        if test(s):
            return CX_minus_delta_i
    return None

def increase_to_subset(delta_n, cprime_y):
    for delta_i in delta_n:
        # c'y union delta_i
        cprime_y_union_delta_i = union(cprime_y, delta_i) # these are indexes
        s = to_str(cprime_y_union_delta_i)
        print('increase_to_subset:', repr(s))
        if test(s):
            return cprime_y_union_delta_i
    return None

def increase_grannularity(n, CX_minus_cprime_y):
    print('increase_grannularity: %d < %d: %s' %( n, len(CX_minus_cprime_y), n < len(CX_minus_cprime_y)))
    return n < len(CX_minus_cprime_y)

# Fig 5: c'y contains the indexes of passing chars. Initially empty when n = 2
# c'y is subset of cx such that test(c'y) succeeds, and delta = cx-c'y is 1-minimal
def ddmax2(cprime_y, n):
    print('ddmax2: %s %d' %(repr(to_str(cprime_y)), n))

    # Base case where the number of excluded bytes from the input has a size of
    # 1, i.e. cannot be minimized further
    print('base: %d == 1?' % len(minus(CX_I, cprime_y)))
    if len(minus(CX_I, cprime_y)) == 1: # NOT in Fig 5.
        return cprime_y

    CX_minus_cprime_y = minus(CX_I, cprime_y)
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

    CX_minus_delta_i =  increase_to_complement(delta_n)
    if CX_minus_delta_i:
        #if \exist i \in {1..n} such that test(c_x - delta_i) holds
        return ddmax2(CX_minus_delta_i, 2)

    cprime_y_union_delta_i = increase_to_subset(delta_n, cprime_y)
    if cprime_y_union_delta_i: # increase to subset
        # if \exist i \in {1 ... n}. test(cprime_y_union delta_i) holds
        return ddmax2(cprime_y_union_delta_i, max(n-1, 2))


    #Fig 5: else, if n < len(delta), increase granularity
    if increase_grannularity(n, CX_minus_cprime_y):
        # Fig 5: ddmax2(c'y, min(|cx|, 2n))  <-- this is buggy
        return ddmax2(cprime_y, min(len(minus(CX_I,cprime_y)), 2*n)) # XXX: BUGGY but from Fig 5.

    # Fig5: otherwise done
    return cprime_y

def to_str(idxs):
    return ''.join([CX_S[i] for i in idxs])

# Choose one of the two:
#round down
def split_idxs(lst,n, round_down=False):
    stride = len(lst)//n
    rem =  len(lst) - (stride * n)
    if not rem:
        v = []
        for i in range(0,n):
            v.append(lst[i*stride:(i*stride+stride)])
        return v
    if round_down:
        v = []
        for i in range(0,n-1):
            v.append(lst[i*stride:(i*stride+stride)])
        v.append(lst[stride*(n-1):])
        return v
    else:
        stride += 1
        v = []
        for i in range(0,n):
            v.append(lst[i*stride:(i*stride+stride)])
        return v


def ddmax(cx):
    global CX_S, CX_I
    CX_S = list(cx)
    CX_I = list(range(len(cx)))
    empty_idxs = []
    # From Fig 5.
    # ddmax(CX_S) = ddmax2(empty_idxs, 2) where
    sol_idxs = ddmax2(empty_idxs, 2)
    return ''.join([s for i,s in enumerate(CX_S) if i in sol_idxs] )

inputstr = '{ "item": "Apple", "price": ***3.45 }'
#inputstr = '{ "product": "Apple", "price": **3.45 }'
#inputstr = '[*1, *2]'

#inputstr = '{ "name": "Dave" "age": 42 }'
#inputstr = '{"ABCD":[*"1,2,3,4,5,6"]*}'

if __name__ == "__main__":
    if len(sys.argv) > 1:
        s = sys.argv[1] # inputstr
    else:
        s = inputstr
    assert not test(s)
    solution = ddmax(s)
    print('SOLUTION:', repr(solution))

# python3 -m pudb ddmax.py '{1:$+1}'  
# python3 -m pudb ddmax.py '{123:$+1}'
