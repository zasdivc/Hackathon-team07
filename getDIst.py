from typing import List
import googlemaps
import csv
import os

def getDist() -> List:
    sources = []
    destinations = []
    path = os.getcwd() + '\Hackthon\Partners.csv'
    with open(path,'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        sources = [row[4] for row in reader]
    path = os.getcwd() + '\Hackthon\Food Hub.csv'
    with open(path,'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i > 0:
                destinations.append(row[0])
    # only for test purpose
    # sources.append('V5X 0H3')
    # destinations.append('410 West Georgia')
    gmaps = googlemaps.Client(key='put your api-key here :-)') 
    matrix = gmaps.distance_matrix(sources, destinations)
    dist_matrix = []
    for i, source in enumerate(sources):
        for j, destination in enumerate(destinations):
            cur_row = []
            cur_row.append(source)
            cur_row.append(destination)
            distance = matrix['rows'][i]['elements'][j]['distance']['value']
            cur_row.append(distance)
            if distance > 500000:
                print(source + " " + destination + " " + str(distance))
            dist_matrix.append(cur_row)
    with open('distance.csv','w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(dist_matrix)
            
    # print(matrix)

getDist()

            
