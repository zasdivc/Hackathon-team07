"""

Assumptions:

"""

import time
import math
from ortools.sat.python import cp_model


NUM_OF_FOOD_HUB = 10
NUM_OF_FARM = 10
FOOD_HUB_MAX_CAPACITY = 500
QUANTITY_PER_RIDE = 100
TOTAL_BUDGET = 10_000
DEBUG = True
MAX_VALUE = 9_999

TOTAL_BUDGET_AFTER_REFACTOR = TOTAL_BUDGET  # * QUANTITY_PER_RIDE

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

print("Solving food hub logistics!")

# def happinessStepFunction(averageFood):
#     """
#     Here we use a step function to define people's
#     happiness. The idea is we encourage the model
#     to prioritize result-fairness (everyone get at
#     least 1 food.) And discourage the model to
#     concentrate food distribution to a convenient area.

#     Note: The values here are adjustable for tunning.
#     """


def getDistance(foodHubId, farmId):
    # TODO: may shall call from api.
    return distData[(foodHubId, farmId)]


def getSingleTripCost(foodHubId, farmId):
    cost = getDistance(foodHubId, farmId)
    return cost


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

# print out the solution if any.
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for i in range(NUM_OF_FOOD_HUB):
        for j in range(NUM_OF_FARM):
            local_value = solver.Value(X[i, j])
            if local_value != 0:
                print(f"X[{i}, {j}] = {local_value}")
                local_distance = getSingleTripCost(i, j)
                print(f"correlated distance={local_distance}," +
                      f"and cost={local_distance * local_value}")

    totalHappiness = sum([solver.Value(Happiness[i])
                         for i in range(NUM_OF_FOOD_HUB)])
    print(f"Total happiness = {totalHappiness}, Budget = {TOTAL_BUDGET}")
else:
    print("Unable to solve with the given setting.")
