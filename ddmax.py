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

cx_s = None

def ddmax2(cy_i, n):
    # delta is cx - c'y
    cx_cy_i = [i for i,s in enumerate(cx_s) if i not in cy_i]
    delta = cx_cy_i
    if len(delta) < n: return cy_i

    # split delta to n parts
    delta_n = split_idxs(delta, n)
    strs_n = [to_str(d, cx_s) for d in delta_n]
    passing_deltas = []
    for delta_i in delta_n:
        # test c_x - delta_i
        delta_x_idxs = [i for i,s in enumerate(cx_s) if i not in delta_i]
        s = to_str(delta_x_idxs, cx_s)
        if test(s):
            passing_deltas.append(delta_x_idxs)
    if passing_deltas: # increase to complement
        #if \exist i \in {1..n} such that test(c_x - delta_i) holds
        delta_x_idxs = passing_deltas[0]
        #pudb.set_trace()
        return ddmax2(delta_x_idxs, 2)

    #else:
    passing_deltas = []
    for delta_i in delta_n:
        c_union_delta_i = cy_i + delta_i
        delta_x_idxs = [i for i,s in enumerate(cx_s) if i in c_union_delta_i]
        s = to_str(delta_x_idxs, cx_s)
        if test(s):
            passing_deltas.append(delta_x_idxs)
    if passing_deltas: # increase to subset
        # if \exist i \in {1 ... n}. test(cy_i\union delta_i) holds
        delta_x_idxs = passing_deltas[0]
        #pudb.set_trace()
        return ddmax2(delta_x_idxs, max(n-1, 2))

    #else:
    #cx_cy_i = cx_s - cy_i
    if n < len(cx_cy_i):
        return ddmax2(cy_i, min(len(cx_s), 2*n))
    #else:
    return cy_i

def to_str(idxs, s):
    return ''.join([s[i] for i in idxs])

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
    global cx_s
    cx_s = list(cx)
    empty_idxs = []
    # From Fig 5.
    # ddmax(cx_s) = ddmax2(empty_idxs, 2) where
    sol_idxs = ddmax2(empty_idxs, 2)
    return ''.join([s for i,s in enumerate(cx_s) if i in sol_idxs] )

inputstr = '{ "item": "Apple", "price": ***3.45 }'
#inputstr = '[*1, *2]'

if __name__ == "__main__":
    s = sys.argv[1] # inputstr
    s = inputstr
    assert not test(s)
    solution = ddmax(s)
    print('SOLUTION:', solution)
    
# python3 -m pudb ddmax.py '{1:$+1}'  
# python3 -m pudb ddmax.py '{123:$+1}'
