import numpy as np
import pandas as pd
from gurobipy import Model,GRB,LinExpr, quicksum
import time
import plotly.graph_objects as go

r_out = pd.read_csv('r_out.csv', header=None)
r_ret = pd.read_csv('r_ret.csv', header=None)
r_all = pd.concat((r_out, r_ret))

dist = pd.read_excel('NewProject/ModelData/LargeDataSet/nodes_loc.xlsx', sheet_name='dist', header=None)
dem = pd.read_csv('NewProject/ModelData/LargeDataSet/demand.csv')
Retdem = pd.read_csv('NewProject/ModelData/LargeDataSet/demandReturn.csv')
pos = pd.read_excel('NewProject/ModelData/LargeDataSet/nodes_loc.xlsx', sheet_name='loc')

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
    #only one decision variable per route
    model.addConstr(quicksum(x[1, index, a, b, c] for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, 1)

    if n2 != n3:
        #trains out equals trains in
        model.addConstr(quicksum(x[0, index, a, b, c]*(a+b+c) for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*(a+b+c) for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #demand constraint
        model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n1)+demand(dem, n2)+demand(dem, n3))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n2)+demand(dem, n3))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n3))/train_capacity))

        #train continuity
        model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.LESS_EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
        model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.LESS_EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

    if n2 == n3:
        #trains out equals trains in
        model.addConstr(quicksum(x[0, index, a, b, c]*(a+b+b) for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*(a+b+b) for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #demand
        model.addConstr(quicksum(x[1, index, a, b, 0]*a for a in range(1, n_trains) for b in range(1, n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n1)+demand(dem, n2))/train_capacity))
        model.addConstr(quicksum(x[1, index, a, b, 0]*b for a in range(1, n_trains) for b in range(1, n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(dem, n2))/train_capacity))

        #continuity
        model.addConstr(quicksum(x[1, index, a, b, 0]*b for a in range(1, n_trains) for b in range(1, n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, 0]*a for a in range(1, n_trains) for b in range(1, n_trains)))

#for returning routes        
for index, row in r_ret.iterrows():
    n1, n2, n3 = row[1:4]
    #only 1 decision variable per route
    model.addConstr(quicksum(x[0, index, a, b, c] for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, 1)
    
    #if the route goes out and returns via the same nodes
    if r_out.values.tolist()[index][2] != r_out.values.tolist()[index][3]:
        if [n3, n2, n1] == r_out.values.tolist()[index][1:4]:
            #demand
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            #continuity
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #if the route returns via different nodes
        else:
            #demand
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            #continuity
            model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

    else:
        #returns via same nodes
        if [n3, n2, n1] == r_out.values.tolist()[index][1:4]:
            #demand
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            #continuity
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.EQUAL, quicksum(x[1, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))

        #if the route returns via different nodes
        else:
            #demand
            model.addConstr(quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))
            model.addConstr(quicksum(x[0, index, a, b, c]*c for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, np.ceil((demand(Retdem, n1)+demand(Retdem, n2)+demand(Retdem, n3))/train_capacity))

            #continuity
            model.addConstr(quicksum(x[1, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
            model.addConstr(quicksum(x[1, index, a, b, c]*b for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)), GRB.GREATER_EQUAL, quicksum(x[0, index, a, b, c]*a for a in range(1, n_trains) for b in range(1, n_trains) for c in range(n_trains)))
           


model.update()        
print('Set all constraints', time.time() - startTimeSetUp)

model.optimize()

sum_out = 0
sum_ret = 0
for index, row in r_ret.iterrows():
    for a in range(1, n_trains):
        for b in range(1, n_trains):
            for c in range(n_trains):
                if x[1, index, a, b, c].X > 0:
                    print([1, index, a,b,c])
                    if c != 0:
                        sum_out += a+b+c
                    else:
                        sum_out += a+b+b
                if x[0, index, a, b, c].X >0:
                    print([0, index, a,b,c])
                    if c != 0:
                        sum_ret += a+b+c
                    else:
                        sum_ret += a+b+b

print('Total trains = ', sum_out - sum_ret)

slat_lst = []
slon_lst = []
dlat_lst = []
dlon_lst = []
nr_trains = []

Sapt_df = pd.read_csv('NewProject/ModelData/LargeDataSet/airportsUnique.csv')

color_lst = []



for index, row in r_all.iterrows():
    n1, n2, n3 = row[1:4]
    for a in range(1, n_trains):
        for b in range(1, n_trains):
            for c in range(n_trains):
                if  n1 != 2 and n2 != 2 and n3 !=2: # and n1 != n2 and n2 != n3 and n3 != n1 and n1 != 2:
                    
                    if row[0] == 1 and x[1,index,a, b, c].X > 0:
                        print('Outgoing',Sapt_df['airport'][n1],Sapt_df['airport'][n2], Sapt_df['airport'][n3])
                        print([1, index, a,b,c])
                        #import pdb;pdb.set_trace()
                       
                        color_lst.append('red')
                        slat_lst.append(pos['y'][2])
                        dlat_lst.append(pos['y'][n1])
                        nr_trains.append(a)
                        
                        color_lst.append('red')
                        slat_lst.append(pos['y'][n1])
                        dlat_lst.append(pos['y'][n2])
                        nr_trains.append(b)   
                        
                        color_lst.append('red')
                        slat_lst.append(pos['y'][n2])
                        dlat_lst.append(pos['y'][n3])
                        nr_trains.append(c)

                        
                        slon_lst.append(pos['x'][2])
                        dlon_lst.append(pos['x'][n1])
                        slon_lst.append(pos['x'][n1])
                        dlon_lst.append(pos['x'][n2])
                        slon_lst.append(pos['x'][n2])
                        dlon_lst.append(pos['x'][n3])


                    if row[0] == 0 and x[0,index, a, b, c].X > 0:
                        print('Return', Sapt_df['airport'][n1],Sapt_df['airport'][n2], Sapt_df['airport'][n3])
                        print([0, index, a,b,c])
                        #import pdb;pdb.set_trace()
                        
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n1])
                        dlat_lst.append(pos['y'][n2])
                        nr_trains.append(a)
                        
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n2])
                        dlat_lst.append(pos['y'][n3])
                        nr_trains.append(b)   
                        
                        color_lst.append('blue')
                        slat_lst.append(pos['y'][n3])
                        dlat_lst.append(pos['y'][2])
                        nr_trains.append(c)

                        
                        slon_lst.append(pos['x'][n1])
                        dlon_lst.append(pos['x'][n2])
                        slon_lst.append(pos['x'][n2])
                        dlon_lst.append(pos['x'][n3])
                        slon_lst.append(pos['x'][n3])
                        dlon_lst.append(pos['x'][2])



# =============================================================================
# 
# for c in model.getConstrs():
#   if c.Slack > 1e-6:
#     print('Constraint %s is active at solution point' % (c.ConstrName))
# 
# =============================================================================
fig = go.Figure()
source_to_dest = zip(slat_lst, dlat_lst, slon_lst, dlon_lst, color_lst, nr_trains)

#get_colors = lambda n: ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(n)]
    

#color_lst = get_colors(n_vehicles)
# Loop through each flight entry
for slat, dlat, slon, dlon, color, ntrains in source_to_dest:
    if color == 'red':
        textpos = 'top center'
        dash = 'dash'
    if color == 'blue':
        textpos = 'bottom center'
        dash = 'dashdot'

    fig.add_trace(go.Scattergeo(
                        lat=[slat, dlat],
                        lon=[slon, dlon],
                        mode='lines',
                        # textposition=["middle center"],
                        # hoverinfo = 'text',
                        # text= ntrains,
                        line=dict(width= 1, color = color)
                        ))
    fig.update_traces(line_dash=dash)

    fig.add_trace(go.Scattergeo(
                        lat=[(slat + dlat)/2],
                        lon=[(slon + dlon)/2],
                        mode='markers+text',
                        textposition=[textpos],
                        hoverinfo = 'text',
                        text= ntrains,
                        line=dict(width= 0, color = color)
                        ))
    


fig.update_layout(title_text='Connection Map Depicting Flights for Airline Network',
                #   height=1000, width=1200,
                autosize=True,
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