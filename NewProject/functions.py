# -*- coding: utf-8 -*-
"""
Created on Fri Dec  9 13:12:40 2022

@author: jaime
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default='browser'

def spherical_dist_rad(phi1, phi2, lambda1, lambda2, R=6367000):
    """
    Great circle distance in meters from coordinates in radians

    Parameters
    ----------
    phi1 : float
        Starting point latitude in radians north.
    phi2 : float
        End point latitude in radians north.
    lambda1 : float
        Starting point longitude in radians east.
    lambda2 : float
        End point longitude in radians east.
    R : float, optional
        Radius of the Earth in meters. The default is 6367000.

    Returns
    -------
    d : float
        Great circle distance in meters.

    """
    d = R * 2 * np.arcsin(np.sqrt(
        np.square(np.sin((phi2 - phi1) / 2))
        + np.cos(phi1) * np.cos(phi2) * np.square(np.sin((lambda2 - lambda1)
                                                         / 2))))
    
    return d

def retrieve_apts():
    
    df_apts = pd.read_csv('airports.csv')
    df = pd.read_csv('KLC_flightlist_20190901.csv')
    #df_apts.loc[df['iata'] == 'AMS']
    route_lst = []
    origin_lst = []
    destination_lst = []
    lat_lst1 = []
    lon_lst1 = []
    lat_lst2 =[]
    lon_lst2 =[]
    source_to_dest = []
    
    for flight_idx in range(len(df['callsign'])):
        origin_apt = df['origin_apt'][flight_idx]
        destination_apt = df['destination_apt'][flight_idx]
        
        origin = df_apts.loc[df_apts['iata'] == origin_apt]
        lat_o = origin['lat'].values[0]
        lon_o = origin['lon'].values[0]

        
        destination = df_apts.loc[df_apts['iata'] == destination_apt]

        lat_d = destination['lat'].values[0]
        lon_d = destination['lon'].values[0]
         
        
        route_dist = spherical_dist_rad(lat_o, lat_d, lon_o, lon_d, R=6367000)
        
        origin_lst.append(origin_apt)
        destination_lst.append(destination_apt)
        route_lst.append(route_dist)
        lat_lst1.append(lat_o)
        lon_lst1.append(lon_o)
        lat_lst2.append(lat_d)
        lon_lst2.append(lon_d)
        source_to_dest.append([lat_o, lat_d, lon_o, lon_d, origin_apt,destination_apt])
        
    
    d = {'origin': origin_lst, 'destination': destination_lst, 'route': route_lst, 'lat_origin':lat_lst1, 'lon_origin': lon_lst1, 'lat_destination':lat_lst2, 'lon_destination': lon_lst2}
    exp_df = pd.DataFrame(data=d)
    #exp_df.to_csv('routes.csv')
    
    
    
    #import pdb;pdb.set_trace()
    
    unique_lst = []
    pos_lat = []
    pos_lon = []
    
    
    for j in exp_df['origin'].unique():
        unique_lst.append(j)
    
    for i in exp_df['destination'].unique():
        if i not in unique_lst:
            unique_lst.append(i)
            
    
    for airport in unique_lst:
        apt = df_apts.loc[df_apts['iata'] == airport]
        lat = apt['lat'].values[0]
        lon = apt['lon'].values[0]
        
        pos_lat.append(lat)
        pos_lon.append(lon)
    
    #import pdb; pdb.set_trace()
    pos_lat1 = [x for _,x in sorted(zip(unique_lst,pos_lat))]
    pos_lon1 = [x for _,x in sorted(zip(unique_lst,pos_lon))]
    unique_lst.sort()
        
    #d2 = {'airport' : unique_lst, 'lat': pos_lat1, 'lon': pos_lon1}
    d2 = {'x': pos_lon1, 'y': pos_lat1}
    exp_df2 = pd.DataFrame(data=d2)
    exp_df2.to_csv('nodes_loc.csv')
    
    
    mat = np.zeros((len(unique_lst),len(unique_lst)))
    
    for apt1 in range(len(unique_lst)):
        for apt2 in range(len(unique_lst)):
            
            origin = df_apts.loc[df_apts['iata'] == unique_lst[apt1]]
            lat_o = origin['lat'].values[0]
            lon_o = origin['lon'].values[0]

            
            destination = df_apts.loc[df_apts['iata'] == unique_lst[apt2]]

            lat_d = destination['lat'].values[0]
            lon_d = destination['lon'].values[0]
             
            #import pdb; pdb.set_trace()
            route_dist = spherical_dist_rad(lat_o*np.pi/180, lat_d*np.pi/180, lon_o*np.pi/180, lon_d*np.pi/180, R=6367000)
            
            mat[apt1][apt2] = route_dist
    
    exp_df3 = pd.DataFrame(mat)
    exp_df3.to_csv('dist.csv')
    

    
    # Uncomment to Visualize
    
# =============================================================================
# 
#     
#     
#     fig = go.Figure()
#     lons =[]
#     lats =[]
#     dests = []
#     
#     # Loop through each flight entry
#     for slat, dlat, slon, dlon, origin, dest in source_to_dest:
#     
#         fig.add_trace(go.Scattergeo(
#                             lat=[slat, dlat],
#                             lon=[slon, dlon],
#                             mode='lines',
#                             line=dict(width=1, color= 'red')
#     
#                             ))
#         #lons.append(dlon)
#         #lats.append(dlat)
#         
#         if origin == 'AMS':
#             airport = dest
#             lons.append(dlon)
#             lats.append(dlat)
#         else:
#             airport = origin
#             lons.append(slon)
#             lats.append(slat)
#         dests.append(airport)
#         
#     
#     
#     fig.add_trace(
#         go.Scattergeo(
#                     lon = lons,
#                     lat = lats,
#                     hoverinfo = 'text',
#                     text = dests,
#                     mode = 'markers+text',
#                     textposition="top center",
#                     marker = dict(size = 1, color = 'rgb(0,0,0)', opacity = .5)))
#     
#     
#     fig.update_layout(title_text='Connection Map Depicting Flights for Airline Network',
#                       height=700, width=900,
#                       margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
#                       showlegend=False,
#                       geo=dict(showland=True, landcolor='white', countrycolor='lightgrey', bgcolor="lightgrey", resolution=50))
#     # =============================================================================
#     # 
#     # fig.add_trace(
#     #     go.Scattergeo(
#     #                 lon=airports_lon,
#     #                 lat=airports_lat,
#     #                 hoverinfo='text',
#     #                 text=airports,
#     #                 mode='markers+text',
#     #                 textposition="top center",
#     #                 marker=dict(size=3, color='rgb(0,0,0)', opacity=1)))
#     # =============================================================================
#     
#     fig.show()
#             
#         
# =============================================================================


def capacity():
    df = pd.read_csv('KLC_flightlist_20190901.csv')
    dup_flights = df.pivot_table(columns=['origin_apt','destination_apt', 'typecode'], aggfunc='size')
    dup_flights.to_csv('dup_flights.csv')
    
    
    