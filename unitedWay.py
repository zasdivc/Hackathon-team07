"""
This is the main function serves the submission for the UnitedWay hackerson,
where we aim to provide a partial solution/contribution to the problem 1.

Problem 1 background:
A focus of the United Way British Columbia's Food Hubs is building long term 
partnerships in community for sustainable solutions to address food insecurity. 
That is strengthening connections between food producers, logistic providers, 
distributors and community agencies to provide food that is appropriate to 
the community, regularly available, and of high quality. 

Problem 1 description: 
Our current food hub locations are primarily a result of our community partner 
agencies and the assessed need in the community we serve. We need a way to 
location our new food hubs across the province to include considerations of 
where food producers and distributors are, proximity to major transportation 
routes, and nearby community partners.​

============Our Solution============
Here we frame this problem 1 as a constraint optimization problem (COP), and use
google or-tools to find a viable solution.

In short, we try to find the best logistics to maximize happiness with a limited
budget. (i.e. logistics in the sense of which food hub shall buy food from which farm)

Our main purpose here is to show a powerful prototype that can potentially create
a huge amount of benefit by dramatically increase efficiency.


To frame this problem as a math model, we made the following assumptions:
1 - Stepped Happiness:
    we measure the happiness of local community by how many food they received 
    on average (per family). And we use a step function to regular the behavior,
    such that from 0 unit food to 1 unit food, there's a huge increase (+5), 
    from 1 unit food to 2 unit food, there's a very moderate increase (+2), 
    and from 2 unit food to more, there's a minimum increase (+1) and the 
    happiness is caped by 8 ( = 0 + 5 + 2 + 1).

2 - Farm's unlimited supply:
    we assume the production of any farm is far greater than what we could buy
    thus we don't constraint the farm supply here (if needed: we could add it on.)

3 - Hub's limited capacity:
    we assume each hub has a limited amount of food storage capacity, and this 
    value can not be infinite. (if needed: we can include hub maintainance as
    part of the cost)

4 - Cost only by travel:
    here we only calculated total cost based on transportation cost, that is the 
    cost to move X amount of food from farm A to hub B.

    And we assume the cost to be a function of distance multiply quantity (per unit 
    food).

Example of solution and interpretation:
    Finished the program in 0.016767024993896484 seconds.

    hub0=Richmond shall buy from farm8=L5R3L1
    with amount = X[0, 8] = 8942
    correlated distance=917

    hub1=Vancouver shall buy from farm9=V7L1C4
    with amount = X[1, 9] = 39556
    correlated distance=11

    hub2=Surrey BC shall buy from farm3=V3M1J2
    with amount = X[2, 3] = 38418
    correlated distance=7

    hub3=Coquitlam shall buy from farm7=V3C2Z8
    with amount = X[3, 7] = 14457
    correlated distance=6

    hub4=Burnaby shall buy from farm9=V7L1C4
    with amount = X[4, 9] = 25574
    correlated distance=14

    hub5=Abbotsford shall buy from farm5=V2R1A5
    with amount = X[5, 5] = 21442
    correlated distance=31

    hub6=North Vancouver shall buy from farm9=V7L1C4
    with amount = X[6, 9] = 38174
    correlated distance=1

    hub7=Langley shall buy from farm3=V3M1J2
    with amount = X[7, 3] = 4203
    correlated distance=6

    hub8=Delta shall buy from farm7=V3C2Z8
    with amount = X[8, 7] = 5136
    correlated distance=744

    hub9=Chilliwack shall buy from farm6=V3A1C3
    with amount = X[9, 6] = 8514
    correlated distance=1

    Total cost =  69532.13
    Total happiness = 69, with total budget = 70000
"""

import time
import os
from ortools.sat.python import cp_model


NUM_OF_FOOD_HUB = 10
NUM_OF_FARM = 10
FOOD_HUB_MAX_CAPACITY = 50_000
QUANTITY_PER_RIDE = 100
TOTAL_BUDGET = 70_000
DEBUG = False
MAX_VALUE = 999_999
FACTOR = 2  # amount of food unit per km per dollar

TOTAL_BUDGET_AFTER_REFACTOR = TOTAL_BUDGET * QUANTITY_PER_RIDE * FACTOR

populationData = {}
distData = {}

if DEBUG:
    import random
    random.seed(10)
    populationData = {i: random.randint(50, 100)
                      for i in range(NUM_OF_FOOD_HUB)}

    for i in range(NUM_OF_FOOD_HUB):
        for j in range(i, NUM_OF_FARM):
            fakeDistance = random.randint(10, 100)
            distData[(i, j)] = fakeDistance
            distData[(j, i)] = fakeDistance

else:
    import pandas as pd
    # populating real distance data from csv.
    dataFilePath = os.path.join(os.getcwd(), "distance.csv")
    distance_df = pd.read_csv(dataFilePath, header=None)
    distance_df.columns = ["farm_zip_code",
                           "census", "meter_distance", "km_distance"]

    farmList = distance_df['farm_zip_code'].unique()
    farmToIndexMapping = {farmList[i]: i for i in range(len(farmList))}
    indexToFarmMapping = {i: farmList[i] for i in range(len(farmList))}

    censusList = distance_df['census'].unique()
    censusToIndexMapping = {censusList[j]: j for j in range(len(censusList))}
    indexToCensusMapping = {j: censusList[j] for j in range(len(censusList))}

    distData = {}
    for index, row in distance_df.iterrows():
        farm_zip_code = row["farm_zip_code"]
        census_name = row["census"]
        km_distance = row["km_distance"]

        farmIndex = farmToIndexMapping[farm_zip_code]
        censusIndex = censusToIndexMapping[census_name]

        distData[(farmIndex, censusIndex)] = km_distance
        distData[(censusIndex, farmIndex)] = km_distance

    # populating real population data from csv
    populationFilePath = os.path.join(
        os.getcwd(), "Food Hub Target Population New.csv")
    populating_df = pd.read_csv(populationFilePath, index_col=None)
    populating_df = populating_df[["census_name", "population"]]

    populationData = {}

    for index, row in populating_df.iterrows():
        census_name = row["census_name"]
        population = row['population']

        # print(f"census_name = {census_name}, population = {population}")
        censusIndex = censusToIndexMapping[census_name]
        populationData[censusIndex] = int(population)

print("Solving food hub logistics!")


def getDistance(foodHubId, farmId):
    # TODO: may shall call from api.
    return distData[(foodHubId, farmId)]


def getSingleTripCost(foodHubId, farmId):
    cost = getDistance(foodHubId, farmId)
    return cost


start = time.time()

# init model, use CpModel for COP
Model = cp_model.CpModel()

# define binary variables X_i,j where i indicate which foodhub,
# and j indicate which farm, and the value of X_i,j indicate
# how many amount of food (by unit) shall food hub i get from
# farm j.
X = {}
for i in range(NUM_OF_FOOD_HUB):
    for j in range(NUM_OF_FARM):
        X[i, j] = Model.NewIntVar(
            0, FOOD_HUB_MAX_CAPACITY * 2, 'X[%d, %d]' % (i, j))

# define happiness variable, it will be populated by a step function
# based on the average food each family received by that food-hub
# i.e. happiness[1] = 5 if on average, the food-hub-1 can distribute
# at least 1 unit of food to each associated family in the region.
Happiness = {}
for i in range(NUM_OF_FOOD_HUB):
    Happiness[i] = Model.NewIntVar(0, 8, f'Happiness[{i}]]')

# Here we define 4 step helper functions to make the happiness step
# function work.
HappinessStepHelper0 = {}
HappinessStepHelper1 = {}
HappinessStepHelper2 = {}
HappinessStepHelper3 = {}

for i in range(NUM_OF_FOOD_HUB):
    HappinessStepHelper0[i] = Model.NewBoolVar(f'stepHelper0_{i}')
    HappinessStepHelper1[i] = Model.NewBoolVar(f'stepHelper1_{i}')
    HappinessStepHelper2[i] = Model.NewBoolVar(f'stepHelper2_{i}')
    HappinessStepHelper3[i] = Model.NewBoolVar(f'stepHelper3_{i}')

# Define three intermediate variables to calculate the average food received
# per family at each food-hub i
TotalFood = {}
LocalPopulation = {}
AverageFood = {}

for i in range(NUM_OF_FOOD_HUB):
    TotalFood[i] = Model.NewIntVar(
        0, MAX_VALUE, f'TotalFood[{i}]')
    Model.Add(TotalFood[i] == sum([X[i, j] for j in range(NUM_OF_FARM)]))
    LocalPopulation[i] = Model.NewIntVar(
        1, MAX_VALUE, f'LocalPopulation[{i}]')
    Model.Add(LocalPopulation[i] == populationData[i])
    AverageFood[i] = Model.NewIntVar(
        0, MAX_VALUE, f'AverageFood[{i}]]')
    Model.AddDivisionEquality(AverageFood[i], TotalFood[i], LocalPopulation[i])

    # step function,
    # HappinessStepHelper1[i] iff average[i] \in coorelated region
    # if average food = 0, set HappinessStepHelper0 = true
    Model.Add(AverageFood[i] == 0).OnlyEnforceIf(HappinessStepHelper0[i])
    # if HappinessStepHelper0 = true, set Happiness = 0
    Model.Add(Happiness[i] == 0).OnlyEnforceIf(HappinessStepHelper0[i])

    # if average food = 1, set HappinessStepHelper1 = true
    Model.Add(AverageFood[i] == 1).OnlyEnforceIf(HappinessStepHelper1[i])
    # if HappinessStepHelper1 = true, set Happiness = 5
    Model.Add(Happiness[i] == 5).OnlyEnforceIf(HappinessStepHelper1[i])

    Model.Add(AverageFood[i] == 2).OnlyEnforceIf(HappinessStepHelper2[i])
    Model.Add(Happiness[i] == 7).OnlyEnforceIf(HappinessStepHelper2[i])

    Model.Add(AverageFood[i] >= 3).OnlyEnforceIf(HappinessStepHelper3[i])
    Model.Add(Happiness[i] == 8).OnlyEnforceIf(HappinessStepHelper3[i])

    # one and only one of that step case shall be true.
    Model.Add(HappinessStepHelper0[i] + HappinessStepHelper1[i] +
              HappinessStepHelper2[i] + HappinessStepHelper3[i] == 1)

# include constraint: each food hub has a capacity limit.
for i in range(NUM_OF_FOOD_HUB):
    Model.Add(sum([X[i, j] for j in range(NUM_OF_FARM)])
              <= FOOD_HUB_MAX_CAPACITY)

# include constraint: total cost has to be lower than the total budge
# notice here we refactor the unit convetion via a new constant
# "TOTAL_BUDGET_AFTER_REFACTOR". The major reason being or-tools
# can not handle division well. Thus it is better to modify them into
# multiply relationships.
total_cost_function = 0
for i in range(NUM_OF_FOOD_HUB):
    for j in range(NUM_OF_FARM):
        total_cost_function += getSingleTripCost(i, j) * X[i, j]
Model.Add(total_cost_function <= TOTAL_BUDGET_AFTER_REFACTOR)

# define objective function to optimize, here our goal is to maximize
# the overall happiness (aka get more food delivered to people in need)
# given the budget and all other natural constraints.
objectFunction = sum([Happiness[i] for i in range(NUM_OF_FOOD_HUB)])
Model.Maximize(objectFunction)

# define a solver
solver = cp_model.CpSolver()
status = solver.Solve(Model)

end = time.time()

print(f"Finished the program in {end - start} seconds.\n")
# print out the solution if any.
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for i in range(NUM_OF_FOOD_HUB):
        for j in range(NUM_OF_FARM):
            local_value = solver.Value(X[i, j])
            if local_value != 0:
                local_distance = getSingleTripCost(i, j)
                print(
                    f"hub{i}={indexToCensusMapping[i]} shall buy from farm{j}={indexToFarmMapping[j]}")
                print(f"with amount = X[{i}, {j}] = {local_value}")
                print(f"correlated distance={local_distance}\n")
                # print(f"and cost={local_distance * local_value}\n")

    totalHappiness = sum([solver.Value(Happiness[i])
                         for i in range(NUM_OF_FOOD_HUB)])
    print("Total cost = ", solver.Value(
        total_cost_function)/QUANTITY_PER_RIDE/FACTOR)
    print(
        f"Total happiness = {totalHappiness}, with total budget = {TOTAL_BUDGET}")
else:
    print("Unable to solve with the given setting.")
