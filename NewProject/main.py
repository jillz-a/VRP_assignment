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

n_vehicles = 15 #number of trains
train_capacity = 350 # based of thalys

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

        if n1 != n2:
                for k in range(n_vehicles):

                    x[n1,n2,k] = model.addVar(vtype=GRB.BINARY, name= "x[%d, %d, %d]"%(n1,n2,k)) #OLD
                    

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

#Amsterdam hub is node number 2
           
#Each vehicle must leave the depot


#Each vehicle which leaves depot must return to the depot

for k in range(n_vehicles):
    model.addConstr(quicksum(x[n1,2,k] for n1 in range(n_nodes) if n1 != 2), GRB.EQUAL, 1, name = "N enter Depot")#quicksum(x[3,n1,k] for n1 in range(n_nodes) if n1 != 3), name = "Hub Leave Depot")


for k in range(n_vehicles):
    model.addConstr(quicksum(x[2,n1,k] for n1 in range(n_nodes) if n1 != 2), GRB.EQUAL, 1, name = "N leave Depot")#quicksum(x[3,n1,k] for n1 in range(n_nodes) if n1 != 3), name = "Hub Leave Depot")


#Remove case where vehicule only goes up and down
    
    
for k in range(n_vehicles):
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j:
                model.addConstr(x[i,j,k] + x[j,i,k], GRB.LESS_EQUAL, 1, name = "No up and down")
            for l in range(n_nodes):
                if i != j and j != l and l != i and i != 2 and j!= 2 and l != 2:
                    model.addConstr(x[2,i,k] + x[i,j,k] + x[j,l,k] + x[l,2,k], GRB.EQUAL, 4, name = "Three customers")



#Each customer must be visited by a vehicle


for n2 in range(n_nodes):
    if n2 != 2:
        model.addConstr(quicksum(x[n1,n2,k] for k in range(n_vehicles) for n1 in range(n_nodes) if n1 != n2), GRB.GREATER_EQUAL, 1, name = "Visit Customer Once")



#If a vehicle visits a customer, then the same vehicle must leave that customer
for k in range(n_vehicles):
    for n1 in range(n_nodes):
        model.addConstr(quicksum(x[n2,n1,k] for n2 in range(n_nodes) if n2 != n1), GRB.EQUAL, quicksum(x[n1,n2,k] for n2 in range(n_nodes) if n2 != n1), name = "Same Vehicule Leaves Customer")



#Capacity contraints

#Function does not work but was tried to set constraint considerin origin
# =============================================================================
# for idx in range(len(dem['origin_apt'])):
#     destination = dem['destination_apt'][idx]
#     origin = dem['origin_apt'][idx]
#     demand = dem['freq'][idx] * dem['capacity'][idx]
#     #import pdb ; pdb.set_trace()
#     model.addConstr(quicksum(x[origin, destination,k] for k in range(n_vehicles))* train_capacity, GRB.GREATER_EQUAL, demand, name = 'Capacity')
# 
# 
# =============================================================================

for k in range(n_vehicles):
    #import pdb ; pdb.set_trace()
    model.addConstr(quicksum(dem['destination_apt'][n2] * x[n1,n2,k] for n1 in range(n_nodes) for n2 in range(n_nodes) if n2 != 2 and n1 != n2), GRB.LESS_EQUAL, train_capacity )

#Subtour elimination -> ADD lazy constraints based on found subtours in optimal solution. Best to do this once capacity constraints has been added


#Elimination of scandinavian subtour

# =============================================================================
# 
# Nodes_ScSbT = [37, 42, 38, 40, 4, 16, 41]
# 
# for k in range(n_vehicles):
#     model.addConstr(quicksum( x[n1,n2,k] for n1 in Nodes_ScSbT for n2 in Nodes_ScSbT if n1 != n2 ), GRB.EQUAL, len(Nodes_ScSbT)-1)
# 
# =============================================================================
#Bellow Function does not work
# =============================================================================
# 
# for k in range(n_vehicles):
#     model.addConstr(quicksum(x[i,j,k] for i in range(1,n_nodes) for j in range(1,n_nodes) if i != j), GRB.LESS_EQUAL, n_nodes -2, name = "Subtour Elimination")
# 
# 
# =============================================================================










#Time Window constraints




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

