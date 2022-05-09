#Operations Optimization assignment
#Vehicle routing problem applied to baggage transportation from and to aircraft
#By: Jaime Aalders, Mitchell de Keijzer, Jilles Andringa
import pandas as pd
from gurobipy import Model,GRB,LinExpr, quicksum
import time
import networkx as nx
import matplotlib.pyplot as plt


#import data
dist = pd.read_excel('nodes_loc.xlsx', sheet_name='dist', header=None) #distances between the nodes
pos = pd.read_excel('nodes_loc.xlsx', sheet_name='loc')

#Define constants

n_vehicles = 1 #number of bagage vehicles

#Define lists

n_nodes = len(dist[0]) #number of nodes including central node 0


startTimeSetUp = time.time()
model = Model()


#################
### DEFINE VARIABLES ###
#################

x = {}

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        if n1 != n2:
            for k in range(n_vehicles):
                x[n1,n2,k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k))

model.update()
#################
### DEFINE OBJECTIVE FUNCTION ###
#################


obj = LinExpr()

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        if n1 != n2:
            for k in range(n_vehicles):
                obj += x[n1,n2,k] * dist[n1][n2]
            

model.setObjective(obj,GRB.MINIMIZE)
 

###################
### DEFINE CONSTRAINTS ###
###################

           
#Each vehicle must leave the depot

for k in range(n_vehicles):
    model.addConstr(quicksum(x[0,n2,k] for n2 in range(1,n_nodes)), GRB.EQUAL, 1)


#Each vehicle must return to the depot

for k in range(n_vehicles):
    model.addConstr(quicksum(x[n1,0,k] for n1 in range(1,n_nodes)), GRB.EQUAL, 1)




#Each customer must be visited by a vehicle


for n2 in range(n_nodes):
    model.addConstr(quicksum(x[n1,n2,k] for k in range(n_vehicles) for n1 in range(n_nodes) if n1 != n2), GRB.EQUAL, 1)



#If a vehicle visits a customer, then the same vehicle must leave that customer
for k in range(n_vehicles):
    for n1 in range(n_nodes):
            model.addConstr(quicksum(x[n1,n2,k] for n2 in range(n_nodes) if n2 != n1), GRB.EQUAL, quicksum(x[n2,n1,k] for n2 in range(n_nodes) if n2 != n1))

#Subtour elimination


#for k in range(n_vehicles):
#    model.addConstr(quicksum(x[i,j,k] for i in range(1,n_nodes) for j in range(1,n_nodes) if i != j), GRB.LESS_EQUAL, 1)

#Capacity contraints




#Time Window constraints




#(backhauls)





model.update()
model.write('model_formulation.lp')   
model.optimize()
endTime   = time.time()

#visualize
G = nx.DiGraph()

for node in range(n_nodes):
    G.add_node(node, pos = (pos['x'][node], pos['y'][node]))

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        if n1 != n2:
            for k in range(n_vehicles):
                if x[(n1,n2,k)].X == 1:
                    G.add_edge(n1,n2, arrowstyle = "->")

pos=nx.get_node_attributes(G,'pos')
nx.draw(G, pos, with_labels= True)

edges = [(n1,n2) for n1,n2 in G.edges]
edge_labels = {}
for i in range(len(edges)):
    edge_labels[edges[i]] = i

nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

plt.show()