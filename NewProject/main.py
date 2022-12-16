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
dist = pd.read_excel('nodes_loc.xlsx', sheet_name='dist', header=None) #distances between the nodes
pos = pd.read_excel('nodes_loc.xlsx', sheet_name='loc')
dem = pd.read_csv('demand.csv')


#Define constants

n_vehicles = 35 #number of trains
train_capacity = 500 #377 # based of thalys

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
            if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2:
                for k in range(n_vehicles):
                    x[n1,n2,n3, k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k)) #Is route from hub back to hub via n1, n2, and n3
                

# =============================================================================
# for n1 in range(n_nodes):
#     for n2 in range(n_nodes):
# 
#         if n1 != n2:
#                 for k in range(n_vehicles):
#                     
#                     #x[n1,n2,k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k)) #OLD
#                     
# 
# =============================================================================
model.update()
#################
### DEFINE OBJECTIVE FUNCTION ###
#################


obj = LinExpr()

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        for n3 in range(n_nodes):
            if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2:
                for k in range(n_vehicles):
                    obj += x[n1,n2,n3,k] * (dist[2][n1] + dist[n1][n2] + dist[n2][n3])
                

model.setObjective(obj,GRB.MINIMIZE)
 

###################
### DEFINE CONSTRAINTS ###
###################

#Amsterdam hub is node number 2
           
#
#Each vehicle can only be used once

for k in range(n_vehicles):
    model.addConstr(quicksum(x[n1,n2,n3,k] for n2 in range(n_nodes) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2 ), GRB.LESS_EQUAL, 1)

#Each customer must be visited by a vehicle


for n2 in range(n_nodes):
    if n2 != 2:
        model.addConstr(quicksum(x[n1,n2,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[n2,n1,n3, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2)
                        + quicksum(x[n1,n3,n2, k] for k in range(n_vehicles) for n1 in range(n_nodes) for n3 in range(n_nodes) if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2), GRB.GREATER_EQUAL, 1, name = "Visit Customer Once")


#Capacity contraints



for k in range(n_vehicles):
        model.addConstr(quicksum((dem['capacity'][n1] * dem['freq'][n1]+ dem['capacity'][n2] * dem['freq'][n2] + dem['freq'][n3]*dem['capacity'][n3]) * x[n1,n2,n3,k] for n1 in range(n_nodes) for n2 in range(n_nodes) for n3 in range(n_nodes) if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2), GRB.LESS_EQUAL, train_capacity )










#(backhauls)





model.update()
model.write('model_formulation.lp')   
model.setParam('TimeLimit', 1* 60)
model.optimize()
endTime   = time.time()

#visualize

slat_lst = []
slon_lst = []
dlat_lst = []
dlon_lst = []
nr_flights = []

Sapt_df = pd.read_csv('airportsUnique.csv')

for n1 in range(n_nodes):
    for n2 in range(n_nodes):
        for n3 in range(n_nodes):
            if n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2 and n2 != 2 and n3 !=2:
                for k in range(n_vehicles):
                    if x[n1,n2, n3,k].X > 0:
                        print(Sapt_df['airport'][n1],Sapt_df['airport'][n2], Sapt_df['airport'][n3],k,x[n1,n2,n3,k].X)
                        #import pdb;pdb.set_trace()
                        nr_flights.append(k)
                        slat_lst.append(pos['y'][2])
                        dlat_lst.append(pos['y'][n1])
                        nr_flights.append(k)
                        slat_lst.append(pos['y'][n1])
                        dlat_lst.append(pos['y'][n2])   
                        nr_flights.append(k)
                        slat_lst.append(pos['y'][n2])
                        dlat_lst.append(pos['y'][n3])
                        #slat_lst.append(pos['y'][n3])
                        #dlat_lst.append(pos['y'][2])
                        
                        
                        slon_lst.append(pos['x'][2])
                        dlon_lst.append(pos['x'][n1])
                        slon_lst.append(pos['x'][n1])
                        dlon_lst.append(pos['x'][n2])
                        slon_lst.append(pos['x'][n2])
                        dlon_lst.append(pos['x'][n3])
                        #slon_lst.append(pos['x'][n3])
                        #dlon_lst.append(pos['x'][2])


# =============================================================================
# 
# for c in model.getConstrs():
#   if c.Slack > 1e-6:
#     print('Constraint %s is active at solution point' % (c.ConstrName))
# 
# =============================================================================
fig = go.Figure()
source_to_dest = zip(slat_lst, dlat_lst, slon_lst, dlon_lst, nr_flights)

get_colors = lambda n: ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(n)]
    

color_lst = get_colors(n_vehicles)
# Loop through each flight entry
for slat, dlat, slon, dlon, num_flights in source_to_dest:

    fig.add_trace(go.Scattergeo(
                        lat=[slat, dlat],
                        lon=[slon, dlon],
                        mode='lines',
                        line=dict(width= 1, color = color_lst[num_flights])
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

