#Operations Optimization assignment
#Vehicle routing problem applied to baggage transportation from and to aircraft
#By: Jaime Aalders, Mitchell de Keijzer, Jilles Andringa

import numpy as np
import pandas as pd
from gurobipy import Model,GRB,LinExpr
import time




#Define constants

n_nodes = 10
n_vehicles = 10



#Define indices list
n = list(range(n_nodes))
k = list(range(n_vehicles))

startTimeSetUp = time.time()
model = Model()


#################
### DEFINE VARIABLES ###
#################

x ={}


model.update()
#################
### DEFINE OBJECTIVE FUNCTION ###
#################


obj        = LinExpr() 
            

model.setObjective(obj,GRB.MINIMIZE)
model.update()
model.write('model_formulation.lp')    

###################
### DEFINE CONSTRAINTS ###
###################

           
#Each vehicle must leave the depot





#Each vehicle must return to the depot







#Each customer must be visited by a vehicle




#If a vehicle visits a custome, then the same vehicle must leave that customer




#Capacity contraints





#Time Window constraints




#(backhauls)






model.optimize()
endTime   = time.time()