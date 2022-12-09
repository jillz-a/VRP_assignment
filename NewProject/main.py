#Operations Optimization assignment
#Vehicle routing problem for train scheduling of all KLM City hopper flights
#By: Jaime Aalders, Mitchell de Keijzer, Jilles Andringa
import pandas as pd
from gurobipy import Model,GRB,LinExpr, quicksum
import time
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio


#import data
dist = pd.read_excel('nodes_loc.xlsx', sheet_name='dist', header=None) #distances between the nodes
pos = pd.read_excel('nodes_loc.xlsx', sheet_name='loc')



#Define constants

n_vehicles = 1 #number of trains

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


for k in range(n_vehicles):
    model.addConstr(quicksum(x[i,j,k] for i in range(1,n_nodes) for j in range(1,n_nodes) if i != j), GRB.LESS_EQUAL, n_nodes -2)

#Capacity contraints




#Time Window constraints




#(backhauls)





model.update()
model.write('model_formulation.lp')   
model.optimize()
endTime   = time.time()

#visualize

slat_lst = []
slon_lst = []
dlat_lst = []
dlon_lst = []
nr_flights = []

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        if n1 != n2:
            for k in range(n_vehicles):
                if x[n1,n2,k].X > 0:
                    #import pdb;pdb.set_trace()
                    nr_flights.append(k)
                    slat_lst.append(pos['y'][n1])
                    dlat_lst.append(pos['y'][n2])
                    slon_lst.append(pos['x'][n1])
                    dlon_lst.append(pos['x'][n2])


fig = go.Figure()
source_to_dest = zip(slat_lst, dlat_lst, slon_lst, dlon_lst, nr_flights)

# Loop through each flight entry
for slat, dlat, slon, dlon, num_flights in source_to_dest:

    fig.add_trace(go.Scattergeo(
                        lat=[slat, dlat],
                        lon=[slon, dlon],
                        mode='lines',
                        line=dict(width=num_flights + 1, color = 'red')
                        ))


fig.update_layout(title_text='Connection Map Depicting Flights for Airline Network',
                  height=700, width=900,
                  margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
                  showlegend=False,
                  geo=dict(showland=True, landcolor='white', countrycolor='grey', bgcolor="lightgrey", resolution=50))
Sapt_df = pd.read_csv('airportsUnique.csv')

airports = []
airports_lon = []
airports_lat =[]

for idx in range(len(Sapt_df['airport'])):
    airports.append(Sapt_df['airport'][idx])
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


# =============================================================================
# G = nx.DiGraph()
# 
# for node in range(n_nodes):
#     G.add_node(node, pos = (pos['x'][node], pos['y'][node]))
# 
# for n1 in range(n_nodes):
#     for n2 in range(n_nodes):
#         if n1 != n2:
#             for k in range(n_vehicles):
#                 if x[(n1,n2,k)].X == 1:
#                     G.add_edge(n1,n2, arrowstyle = "->")
# 
# pos=nx.get_node_attributes(G,'pos')
# nx.draw(G, pos, with_labels= True)
# 
# edges = [(n1,n2) for n1,n2 in G.edges]
# edge_labels = {}
# for i in range(len(edges)):
#     edge_labels[edges[i]] = i
# 
# nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
# 
# plt.show()
# =============================================================================



