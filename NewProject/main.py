#Operations Optimization assignment
#Vehicle routing problem for train scheduling of all KLM Cityhopper flights
#By: Jaime Aalders, Mitchell de Keijzer, Jilles Andringa
import pandas as pd
from gurobipy import Model,GRB,LinExpr, quicksum
import time
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import random
pio.renderers.default = 'browser'


#import data
dist = pd.read_excel('ModelData/nodes_loc.xlsx', sheet_name='dist', header=None) #distances between the nodes
pos = pd.read_excel('ModelData/nodes_loc.xlsx', sheet_name='loc')
dem = pd.read_csv('ModelData/demand.csv')
Retdem = pd.read_csv('ModelData/demandReturn.csv')

#Define constants

n_vehicles = 50 #number of trains
train_capacity = 377 #377 # based of thalys

#With this number a route should at most consit of 4 stops

#Define lists

n_nodes = len(dist) #number of nodes including central node 0


startTimeSetUp = time.time()
model = Model()


#################
### DEFINE VARIABLES ###
#################

x = {}
for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        for n3 in range(n_nodes):
            for k in range(n_vehicles):
                if n1 != 2 and n2 != 2 and n3 !=2: #n1 != n2 and n2 != n3 and n3 != n1 and
                    
                        x[1,n1,n2,n3, k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k)) #Is route from hub  via n1, n2, and n3 ie. Outgoing flights
                        x[0,n3,n2,n1, k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k)) #Is route to hub back to hub via n1, n2, and n3 ie. Returning flights
                        
                        #Important to note that there is not the same amount of flights leaving and returning to AMS
                    
                        #Could consider that instead of serving 3 nodes 4 nodes are used as this would be the theoretical maximum amount of nodes which could be served by a full train of 377 seats serving 4 nodes of 88 demand

model.update()

print('Defined all variables', time.time() - startTimeSetUp)
#################
### DEFINE OBJECTIVE FUNCTION ###
#################


obj = LinExpr()

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        for n3 in range(n_nodes):
            if  n1 != 2 and n2 != 2 and n3 !=2: #n1 != n2 and n2 != n3 and n3 != n1:
                for k in range(n_vehicles):
                    obj += x[1,n1,n2,n3,k] * (dist[2][n1] + dist[n1][n2] + dist[n2][n3])
                    obj += x[0,n3,n2,n1,k] * (dist[n3][n2] + dist[n2][n1] + dist[n1][2])

model.setObjective(obj,GRB.MINIMIZE)

print('Objective function set', time.time() - startTimeSetUp)

###################
### DEFINE CONSTRAINTS ###
###################

#Amsterdam hub is node number 2
           



for k in range(n_vehicles):
    #Each vehicle can only be used once for the outgoing legs. Return is implicity done in combination with the vehicle contunuity constraint
    model.addConstr(quicksum(x[1,n1,n2,n3,k] for n2 in range(n_nodes) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2 ), GRB.LESS_EQUAL, 1)

    #Capacity contraints for returning flights
    model.addConstr(quicksum((Retdem['capacity'][n1] * Retdem['freq'][n1]+ Retdem['capacity'][n2] * Retdem['freq'][n2] + Retdem['freq'][n3]*dem['capacity'][n3]) * x[0,n3,n2,n1,k] for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2), GRB.LESS_EQUAL, train_capacity )
    
    #Capacity contraints for outgoing flights
    model.addConstr(quicksum((dem['capacity'][n1] * dem['freq'][n1]+ dem['capacity'][n2] * dem['freq'][n2] + dem['freq'][n3]*dem['capacity'][n3]) * x[1,n1,n2,n3,k] for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2), GRB.LESS_EQUAL, train_capacity )
    



for n2 in range(n_nodes):
    if n2 != 2:
        #Each customer must be visited by a vehicle on the outgoing phase
        model.addConstr(quicksum(x[1,n1,n2,n3, k]for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[1,n2,n1,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if  n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[1,n1,n3,n2, k]  for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if  n1 != 2 and n2 != 2 and n3 !=2), GRB.GREATER_EQUAL, 1, name = "Visit Customer Once")
        
        #Each customer must be visited by a vehicle on the returning phase
        model.addConstr(quicksum(x[0,n1,n2,n3, k]  for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[0,n2,n1,n3, k]  for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if  n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[0,n1,n3,n2, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if  n1 != 2 and n2 != 2 and n3 !=2), GRB.GREATER_EQUAL, 1, name = "Visit Customer Once")
  
        


#Vehile arriving at node 3 from an outgoing leg is also used for a returning leg



for n3 in range(n_nodes):
    for k in range(n_vehicles):
        if n3 != 2:
            model.addConstr(quicksum(x[1,n1,n2,n3, k]  for n1 in range(n_nodes) for n2 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2), GRB.EQUAL, quicksum(x[0,n3,n2,n1, k]  for n1 in range(n_nodes) for n2 in range(n_nodes) if n1 != 2 and n2 != 2 and n3 !=2), name = "Enter Node Leave Node")
    
print('Set all constraints', time.time() - startTimeSetUp)


#Geographical constraints for trains towards Scandinavia and the UK


UK_nodes = [14,31,25,36,28,29,9,13] # Entry through node 28 or 29 from 10


Scan_nodes = [4,16,41,40,38,37,42,21,45, 12] #Entry through node 12 from 24


#Geographical constraints for Scandinavian nodes on the ougoing segment



model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in range(n_nodes) for n3 in Scan_nodes if n1 != 12 and n2 not in Scan_nodes and n2 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in Scan_nodes for n3 in range(n_nodes) if n1 != 12  and n3 not in Scan_nodes and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 12 and n2 not in Scan_nodes and n3 not in Scan_nodes and n2 != 2 and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in Scan_nodes for n3 in Scan_nodes if n1 != 12),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in Scan_nodes for n3 in range(n_nodes) if n1 not in Scan_nodes and n1 != 2 and n2 != 12 and n3 != 2 and n3 not in Scan_nodes),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in Scan_nodes if n1 not in Scan_nodes and n1 != 2 and n2 not in Scan_nodes and n2 != 2 and n3 != 12),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in Scan_nodes for n3 in Scan_nodes if n1 not in Scan_nodes and n1 != 2 and n2 != 12),GRB.EQUAL, 0, name =  "Entry Node")


model.addConstr(quicksum(x[1,12,n2,n3, k] for k in range(n_vehicles) for n2 in Scan_nodes for n3 in range(n_nodes) if n2 != 12 and n3 not in Scan_nodes and n3 !=2 ),GRB.EQUAL, 0, name =  "Entry Node")






#Geographical constraints for UK nodes on the ougoing segment



model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in range(n_nodes) for n3 in UK_nodes if n1 != 29 and n2 not in UK_nodes and n2 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in UK_nodes for n3 in range(n_nodes) if n1 != 29 and n3 not in UK_nodes and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 29 and n2 not in UK_nodes and n3 not in UK_nodes and n2 != 2 and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in UK_nodes for n3 in UK_nodes if n1 != 29),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in UK_nodes for n3 in range(n_nodes) if n1 not in UK_nodes and n1 != 2 and n2 != 29 and n3 != 2 and n3 not in UK_nodes),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in UK_nodes if n1 not in UK_nodes and n1 != 2 and n2 not in UK_nodes and n2 != 2 and n3 != 29),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[1,n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in UK_nodes for n3 in UK_nodes if n1 not in UK_nodes and n1 != 2 and n2 != 29 ),GRB.EQUAL, 0, name =  "Entry Node")


model.addConstr(quicksum(x[1,29,n2,n3, k] for k in range(n_vehicles) for n2 in UK_nodes for n3 in range(n_nodes) if n3 not in UK_nodes and n3 !=2 ),GRB.EQUAL, 0, name =  "Entry Node")




#Geographical constraints for Scandinavian nodes on the returning segment



model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in range(n_nodes) for n3 in Scan_nodes if n1 != 12 and n2 not in Scan_nodes and n2 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in Scan_nodes for n3 in range(n_nodes) if n1 != 12  and n3 not in Scan_nodes and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 12 and n2 not in Scan_nodes and n3 not in Scan_nodes and n2 != 2 and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in Scan_nodes for n2 in Scan_nodes for n3 in Scan_nodes if n1 != 12),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in Scan_nodes for n3 in range(n_nodes) if n1 not in Scan_nodes and n1 != 2 and n2 != 12 and n3 != 2 and n3 not in Scan_nodes),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in Scan_nodes if n1 not in Scan_nodes and n1 != 2 and n2 not in Scan_nodes and n2 != 2 and n3 != 12),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in Scan_nodes for n3 in Scan_nodes if n1 not in Scan_nodes and n1 != 2 and n2 != 12),GRB.EQUAL, 0, name =  "Entry Node")


model.addConstr(quicksum(x[0,n3,n2,12, k] for k in range(n_vehicles) for n2 in Scan_nodes for n3 in range(n_nodes) if n2 != 12 and n3 not in Scan_nodes and n3 !=2 ),GRB.EQUAL, 0, name =  "Entry Node")






#Geographical constraints for UK nodes on the returning segment



model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in range(n_nodes) for n3 in UK_nodes if n1 != 29 and n2 not in UK_nodes and n2 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in UK_nodes for n3 in range(n_nodes) if n1 != 29 and n3 not in UK_nodes and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != 29 and n2 not in UK_nodes and n3 not in UK_nodes and n2 != 2 and n3 != 2),GRB.EQUAL, 0, name =  "Entry Node")
model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in UK_nodes for n2 in UK_nodes for n3 in UK_nodes if n1 != 29),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in UK_nodes for n3 in range(n_nodes) if n1 not in UK_nodes and n1 != 2 and n2 != 29 and n3 != 2 and n3 not in UK_nodes),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in UK_nodes if n1 not in UK_nodes and n1 != 2 and n2 not in UK_nodes and n2 != 2 and n3 != 29),GRB.EQUAL, 0, name =  "Entry Node")

model.addConstr(quicksum(x[0,n3,n2,n1, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n2 in UK_nodes for n3 in UK_nodes if n1 not in UK_nodes and n1 != 2 and n2 != 29 ),GRB.EQUAL, 0, name =  "Entry Node")


model.addConstr(quicksum(x[0,n1,n2,29, k] for k in range(n_vehicles) for n2 in UK_nodes for n3 in range(n_nodes) if n3 not in UK_nodes and n3 !=2 ),GRB.EQUAL, 0, name =  "Entry Node")



model.update()
#model.write('model_formulation.lp')   
model.setParam('TimeLimit', 10* 60)
model.optimize()
endTime   = time.time()

#visualize
#%%
slat_lst = []
slon_lst = []
dlat_lst = []
dlon_lst = []
nr_flights = []

Sapt_df = pd.read_csv('ModelData/airportsUnique.csv')

color_lst = []

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        for n3 in range(n_nodes):
            if  n1 != 2 and n2 != 2 and n3 !=2: # and n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2:
                for k in range(n_vehicles):
                    if x[1,n1,n2, n3,k].X > 0:
                        print('Outgoing',Sapt_df['airport'][n1],Sapt_df['airport'][n2], Sapt_df['airport'][n3],k)
                        #import pdb;pdb.set_trace()
                        nr_flights.append(k)
                        color_lst.append('red')
                        slat_lst.append(pos['y'][2])
                        dlat_lst.append(pos['y'][n1])
                        nr_flights.append(k)
                        color_lst.append('red')
                        slat_lst.append(pos['y'][n1])
                        dlat_lst.append(pos['y'][n2])   
                        nr_flights.append(k)
                        color_lst.append('red')
                        slat_lst.append(pos['y'][n2])
                        dlat_lst.append(pos['y'][n3])

                        
                        slon_lst.append(pos['x'][2])
                        dlon_lst.append(pos['x'][n1])
                        slon_lst.append(pos['x'][n1])
                        dlon_lst.append(pos['x'][n2])
                        slon_lst.append(pos['x'][n2])
                        dlon_lst.append(pos['x'][n3])


                    if x[0,n3,n2, n1,k].X > 0:
                        print('Return', Sapt_df['airport'][n3],Sapt_df['airport'][n2], Sapt_df['airport'][n1],k)
                        #import pdb;pdb.set_trace()
                        nr_flights.append(k)
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n3])
                        dlat_lst.append(pos['y'][n2])
                        nr_flights.append(k)
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n2])
                        dlat_lst.append(pos['y'][n1])   
                        nr_flights.append(k)
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n1])
                        dlat_lst.append(pos['y'][2])

                        
                        slon_lst.append(pos['x'][n3])
                        dlon_lst.append(pos['x'][n2])
                        slon_lst.append(pos['x'][n2])
                        dlon_lst.append(pos['x'][n1])
                        slon_lst.append(pos['x'][n1])
                        dlon_lst.append(pos['x'][2])


# =============================================================================
# 
# for c in model.getConstrs():
#   if c.Slack > 1e-6:
#     print('Constraint %s is active at solution point' % (c.ConstrName))
# 
# =============================================================================
fig = go.Figure()
source_to_dest = zip(slat_lst, dlat_lst, slon_lst, dlon_lst, nr_flights, color_lst)

#get_colors = lambda n: ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(n)]
    

#color_lst = get_colors(n_vehicles)
# Loop through each flight entry
for slat, dlat, slon, dlon, num_flights, color in source_to_dest:

    fig.add_trace(go.Scattergeo(
                        lat=[slat, dlat],
                        lon=[slon, dlon],
                        mode='lines',
                        line=dict(width= 1, color = color)#_lst[num_flights])
                        ))


fig.update_layout(title_text='Connection Map Depicting Flights for Airline Network',
                  height=700, width=900,
                  margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
                  showlegend=False,
                  geo=dict(showland=True, landcolor='white', countrycolor='grey', bgcolor="lightgrey", resolution=50))


airports = []
airports_lon = []
airports_lat =[]

for idx in range(len(Sapt_df['airport'])):
    airports.append(Sapt_df['airport'][idx])#+ '(nr.'+ str(idx) + ')')
    airports_lon.append(Sapt_df['lon'][idx])
    airports_lat.append(Sapt_df['lat'][idx])
fig.add_trace(
    go.Scattergeo(
                lon=airports_lon,
                lat=airports_lat,
                hoverinfo='text',
                text=airports,
                mode='markers+text',
                textposition="top center",
                marker=dict(size=3, color='rgb(0,0,0)', opacity=1)))

fig.show()


