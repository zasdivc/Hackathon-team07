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

print("hummm")


# def happinessStepFunction(averageFood):
#     """
#     Here we use a step function to define people's
#     happiness. The idea is we encourage the model
#     to prioritize result-fairness (everyone get at
#     least 1 food.) And discourage the model to
#     concentrate food distribution to a convenient area.

#     Note: The values here are adjustable for tunning.
#     """
#     floorAverageFood = math.floor(averageFood)
#     if floorAverageFood <= 0:
#         raise Exception("average food shall not be negative")
#     elif floorAverageFood == 1:
#         return 5
#     elif floorAverageFood == 2:
#         return 7
#     else:
#         return 8


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

# define an intermediate variable for the division relationship:
# average food per population at certain food-hub i =
# sum(X[i,j]) / population[i].

# TotalFood = {}
# for i in range(NUM_OF_FOOD_HUB):
#     TotalFood[i] = Model.NewIntVar(
#         0, MAX_VALUE, 'TotalFood[%d]' % i)
#     Model.Add(TotalFood[i] == sum([X[i, j] for j in range(NUM_OF_FARM)]))

# LocalPopulation = {}
# for i in range(NUM_OF_FOOD_HUB):
#     LocalPopulation[i] = Model.NewIntVar(
#         0, MAX_VALUE, 'LocalPopulation[%d]' % i)
#     Model.Add(LocalPopulation[i] == populationData[i])

# AverageFood = {}
# for i in range(NUM_OF_FOOD_HUB):
#     AverageFood[i] = Model.NewIntVar(
#         0, MAX_VALUE, 'AverageFood[%d]' % i)
# Model.AddDivisionEquality(AverageFood, TotalFood, LocalPopulation)
HappinessStepHelper1 = {}
# HappinessStepHelper2 = {}
# HappinessStepHelper3 = {}

for i in range(NUM_OF_FOOD_HUB):
    HappinessStepHelper1[i] = Model.NewBoolVar(f'stepRegion1_{i}')
    # HappinessStepHelper2[i] = Model.NewBoolVar(f'stepRegion2_{i}')
    # HappinessStepHelper3[i] = Model.NewBoolVar(f'stepRegion3_{i}')

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

    # step function
    Model.Add(AverageFood[i] >= 1).OnlyEnforceIf(HappinessStepHelper1[i])
    Model.Add(AverageFood[i] < 1).OnlyEnforceIf(HappinessStepHelper1[i].Not())
    # Model.Add(AverageFood[i] >= 1).OnlyEnforceIf(HappinessStepHelper2[i].Not())
    # Model.Add(AverageFood[i] >= 1).OnlyEnforceIf(HappinessStepHelper3[i].Not())


# change happiness into a variable to make model work
Happiness = {}
for i in range(NUM_OF_FOOD_HUB):
    Happiness[i] = Model.NewIntVar(0, 8, f'Happiness[{i}]]')

# include third constrain - step function for happiness.
for i in range(NUM_OF_FOOD_HUB):
    Model.Add(Happiness[i] == 5).OnlyEnforceIf(HappinessStepHelper1[i])
    Model.Add(Happiness[i] == 0).OnlyEnforceIf(HappinessStepHelper1[i].Not())

    # Model.Add(Happiness[i] == 0).OnlyEnforceIf((AverageFood[i] < 1))
    # Model.Add(Happiness[i] == 5).OnlyEnforceIf(1 <= AverageFood[i] < 2)
    # Model.Add(Happiness[i] == 7).OnlyEnforceIf(2 <= AverageFood[i] < 3)
    # Model.Add(Happiness[i] == 8).OnlyEnforceIf(AverageFood[i] >= 3)

# include first constrain: food hub has a capacity limit.
for i in range(NUM_OF_FOOD_HUB):
    Model.Add(sum([X[i, j] for j in range(NUM_OF_FARM)])
              <= FOOD_HUB_MAX_CAPACITY)

# include second constrain: total cost below total budge
# cost_relation = Model.NewIntVar(1, MAX_VALUE, "cost_relation")
total_cost_function = 0
for i in range(NUM_OF_FOOD_HUB):
    for j in range(NUM_OF_FARM):
        total_cost_function += getSingleTripCost(i, j) * X[i, j]
# Model.AddDivisionEquality(
#     cost_relation, total_cost_function, QUANTITY_PER_RIDE)
Model.Add(total_cost_function <= TOTAL_BUDGET_AFTER_REFACTOR)

objectFunction = sum([Happiness[i] for i in range(NUM_OF_FOOD_HUB)])
Model.Maximize(objectFunction)

solver = cp_model.CpSolver()
status = solver.Solve(Model)


if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for i in range(NUM_OF_FOOD_HUB):
        for j in range(NUM_OF_FARM):
            local_value = solver.Value(X[i, j])
            if local_value != 0:
                local_distance = getSingleTripCost(i, j)
                print(f"X[{i}, {j}] = {local_value}")
                print(f"correlated distance={local_distance}," +
                      f"and cost={local_distance * local_value}")

    totalHappiness = sum([solver.Value(Happiness[i])
                         for i in range(NUM_OF_FOOD_HUB)])
    print(f"Total happiness = {totalHappiness}, Budget = {TOTAL_BUDGET}")
else:
    print("Unable to solve with the given setting.")
