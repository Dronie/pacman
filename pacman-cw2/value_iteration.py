import copy
from collections import deque

a = [[None, None, None, None, None, None],
     [None,    0,    0,    0,    1, None],
     [None,    0, None,    0,   -1, None],
     [None,    0,    0,    0,    0, None],
     [None, None, None, None, None, None]]

b = [[None, None, None, None, None, None],
     [None,    0,    0,    0,    1, None],
     [None,    0, None,    0,   -1, None],
     [None,    0,    0,    0,    0, None],
     [None, None, None, None, None, None]]    
    

for k in range(0, 19):
    print "Iteration", k+1
    for i in range(0, 5):
        for j in range(0, 5):
            
            if b[i][j] != None:
                
                neighbours = deque([a[i - 1][j],
                                   a[i][j + 1],
                                   a[i + 1][j],
                                   a[i][j - 1]])
                
                coefficients = deque([0.1,
                                      0.8,
                                      0.1,
                                      0])
    
                values = []
                
                for k in range(0, 4):
                    surp_coefficient = 0
                    if neighbours[k] == None:
                        if k == 1:
                            surp_coefficient += 0.8
                        else:
                            surp_coefficient += 0.1
                        neighbours[k] = a[i][j]
                
                for k in range(0, 4):
                    values.append(sum([neighbours[0] * coefficients[0],
                                      neighbours[1] * coefficients[1],
                                      neighbours[2] * coefficients[2],
                                      neighbours[3] * coefficients[3]]))
                    
                    coefficients.rotate(1)
                
                if [i, j] != [1, 4] and [i, j] != [2, 4]:
                    b[i][j] = -0.04 + (1 * min(values))
                    b[i][j] = float("{0:.3f}".format(b[i][j]))
                    print b[i][j], "= -0.04 + (1 *", min(values), ")"
    a = copy.deepcopy(b)
    

print(a)
print(b)
