import numpy as np
import pandas as pd
from gurobipy import Model,GRB,LinExpr, quicksum
import time

r_out = pd.read_csv('r_out.csv', header=None)
r_ret = pd.read_csv('r_ret.csv', header=None)
r_all = pd.concat((r_out, r_ret))

dist = pd.read_excel('NewProject/ModelData/LargeDataSet/nodes_loc.xlsx', sheet_name='dist', header=None)
dem = pd.read_csv('NewProject/ModelData/LargeDataSet/demand.csv')
Retdem = pd.read_csv('NewProject/ModelData/LargeDataSet/demandReturn.csv')

def demand(dem, n):
    return dem['capacity'][n] * dem['freq'][n]

train_capacity = 377
n_trains = 5

startTimeSetUp = time.time()
model = Model()

#add variables
x = {}
for index, row in r_out.iterrows():
    for a in range(1, n_trains):
        for b in range(1, n_trains):
            for c in range(n_trains):
                x[1, index, a, b, c] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d, %d, %d]"%(1, index, a, b, c))
                x[0, index, a, b, c] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d, %d, %d]"%(0, index, a, b, c))
model.update()
print('Defined all variables', time.time() - startTimeSetUp)

#set objective function
obj = LinExpr()

for index, row in r_all.iterrows():
    for a in range(1, n_trains):
        for b in range(1, n_trains):
            for c in range(n_trains):
                if row[0] == 1:
                    n1, n2, n3 = row[1:4]
                    obj += x[1, index, a, b, c]*(dist[2][n1]*a + dist[n1][n2]*b + dist[n2][n3]*c)
                if row[0] == 0:
                    n1, n2, n3 = row[1:4]
                    obj += x[0, index, a, b, c]*(dist[n1][n2]*c + dist[n2][n3]*b + dist[n3][2]*a)

model.setObjective(obj,GRB.MINIMIZE)
print('Objective function set', time.time() - startTimeSetUp)

#set constraints
#Each leg in route needs enough trains to fulfill demand of remaining part of the leg
#for outgoing routes
for index, row in r_out.iterrows():
    n1, n2, n3 = row[1:4]
    model.addConstr(quicksum(x[1, index, a, b, c] for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, 1)

    if n2 != n3:
        model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n1)+demand(dem, n2)+demand(dem, n3))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n2)+demand(dem, n3))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n3))/train_capacity))

        model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.LESS_EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
        model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.LESS_EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

    if n2 == n3:
        model.addConstr(quicksum(x[1, index, a, b, 0]*a for a in range(1, n_trains) for b in range(1, n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n1)+demand(dem, n2))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, 0]*b for a in range(1, n_trains) for b in range(1, n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n2))/train_capacity))

        model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.LESS_EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

#for returning routes        
for index, row in r_ret.iterrows():
    n1, n2, n3 = row[1:4]
    model.addConstr(quicksum(x[0, index, a, b, c] for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, 1)
    
    #if the route goes out and returns via the same nodes
    if r_out.values.tolist()[index][2] != r_out.values.tolist()[index][3]:
        if [n3, n2, n1] == r_out.values.tolist()[index][1:4]:
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #if the route returns via different nodes
        else:
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

    else:
        #returns via same nodes
        if [n3, n2, n1] == r_out.values.tolist()[index][1:4]:
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #if the route returns via different nodes
        else:
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
           


model.update()        
print('Set all constraints', time.time() - startTimeSetUp)

model.optimize()

for index, row in r_ret.iterrows():
    for a in range(1, n_trains):
        for b in range(1, n_trains):
            for c in range(n_trains):
                if x[1, index, a, b, c].X > 0:
                    print([1, index, a,b,c])
                if x[0, index, a, b, c].X >0:
                    print([0, index, a,b,c])