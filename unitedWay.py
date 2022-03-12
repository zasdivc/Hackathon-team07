"""

Assumptions:

"""

import time
import math
from ortools.sat.python import cp_model


NUM_OF_FOOD_HUB = 10
NUM_OF_FARM = 10
FOOD_HUB_MAX_CAPACITY = 500
QUANTITY_PER_RIDE = 1
TOTAL_BUDGET = 1_000
DEBUG = True

populationData = {}
distData = {}

if DEBUG:
    import random
    random.seed(10)
    populationData = {i: random.randint(500, 1000)
                      for i in range(NUM_OF_FOOD_HUB)}

    for i in range(NUM_OF_FOOD_HUB):
        for j in range(i, NUM_OF_FARM):
            fakeDistance = random.randint(10, 100)
            distData[(i, j)] = fakeDistance
            distData[(j, i)] = fakeDistance

print("hummm")


def happinessStepFunction(averageFood):
    """
    Here we use a step function to define people's
    happiness. The idea is we encourage the model
    to prioritize result-fairness (everyone get at 
    least 1 food.) And discourage the model to 
    concentrate food distribution to a convenient area.

    Note: The values here are adjustable for tunning.
    """
    floorAverageFood = math.floor(averageFood)
    if floorAverageFood <= 0:
        raise Exception("average food shall not be negative")
    elif floorAverageFood == 1:
        return 5
    elif floorAverageFood == 2:
        return 7
    else:
        return 8


def getHappiness(foodHubId):
    foodHubTotalFoodQuantity = 0
    for j in range(NUM_OF_FARM):
        foodHubTotalFoodQuantity += X[foodHubId, j]

    averageFood = foodHubTotalFoodQuantity/populationData[foodHubId]
    happiness = happinessStepFunction(averageFood) * populationData[foodHubId]
    return happiness


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
            0, FOOD_HUB_MAX_CAPACITY, 'X[%d, %d]' % (i, j))

# include first constrain: food hub has a capacity limit.
for i in range(NUM_OF_FOOD_HUB):
    Model.Add(sum([X[i, j] for j in range(NUM_OF_FARM)])
              <= FOOD_HUB_MAX_CAPACITY)

# include second constrain: total cost below total budge
total_cost_function = 0
for i in range(NUM_OF_FOOD_HUB):
    for j in range(NUM_OF_FARM):
        total_cost_function += getSingleTripCost(
            i, j) * (X[i, j] * (1/QUANTITY_PER_RIDE))
Model.Add(total_cost_function <= TOTAL_BUDGET)

objectFunction = sum(getHappiness(i) for i in range(NUM_OF_FOOD_HUB))
Model.Maxmize(objectFunction)

solver = cp_model.CpSolver()
status = solver.Solve(Model)


if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for i in range(NUM_OF_FOOD_HUB):
        for j in range(NUM_OF_FARM):
            print(f"X[{i}, {j}] = {solver.Value(X[i, j])}")
else:
    print("Unable to solve with the given setting.")
