# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

from pacman import Directions
from game import Agent
import api
import random
import game
import util

# libraries I am using: (all are part of python 2.7 standard)
import copy
import math
from collections import deque

# class that handles all environement related information
class Environment(Agent):
    def __init__(self):
        # initializing important variables
        self.all_food_locations = []
        self.closest_food = []
        self.capsule_locations = []
        self.ghost_locations = []
        self.ghost_prev_locations = []
        self.wall_locations = []
        self.open_locations = []
        self.maze_shape = [0, 0]

    # find where the remaining food currently is
    def updateFoodLocations(self, state):
        self.all_food_locations = api.food(state)
    
    # find where the remaining capsules currently are
    def updateCapsuleLocations(self, state):
        self.capsule_locations = api.capsules(state)
    
    # find where the ghosts currently are
    def updateGhostLocations(self, state):
        self.ghost_locations = api.ghosts(state)
    
    # store the size of the current maze (excluding borders)
    def getMazeShape(self, state):
        if self.maze_shape == [0, 0]:
            for i in self.open_locations:
                if i[0] >= self.maze_shape[0]:
                    self.maze_shape[0] = i[0]
                if i[1] >= self.maze_shape[1]:
                    self.maze_shape[1] = i[1]

    # find all locations that pacman can move to
    def getEmptyLocations(self, state):
        self.wall_locations = api.walls(state)

        if self.open_locations == []:
            # for every point in the maze: if that point is not present in the
            # wall locations list then add it to the open locations list

            for i in range(0, self.wall_locations[len(self.wall_locations) - 1][0]): # uses the value of the last element in the wall
                for j in range(0, self.wall_locations[len(self.wall_locations) - 1][1]): # locations list to determine the size of the maze
                    if (i, j) not in self.wall_locations:
                        self.open_locations.append((i, j))
    
    # find the location of the closest piece of food
    def getClosestFood(self, state):
        dists = []
        # store the manhattan distances between pacman and all of the food currently in the maze
        for i in self.all_food_locations:
            dists.append(util.manhattanDistance(api.whereAmI(state), i))

        # and set that with the smallest value to the closest food currently
        self.closest_food = min(dists)
        
        # since the list that stores the distances and the food locations are 1-1, you simply find the index
        # of the minimum value in the distance list and will correspond to the correct food location in the
        # food location list
        closest_index = 0
        for i in dists:
            if i == self.closest_food:
                closest_index = dists.index(self.closest_food)
        
        self.closest_food = self.all_food_locations[closest_index]

            
                

    
# class to handle all value iteration information and instructions
class ValueIterator(Agent):
    def __init__(self):
        # initializing important variables
        self.value_matrix_b = []
        self.value_matrix_a = []
        self.nxt_loc = []
        self.gamma = 0.5
        self.reward = -0.1

    # function to predict the next location of a ghost (used to help steer pacman away from ghosts):
    # next = ((previous - present) * -1) + present
    # where previous and present are 2-tuples or 2 element lists : (x, y)
    def getNextGhostLocation(self, previous, present):
        return [((math.floor(previous[0]) - math.floor(present[0])) * -1) + math.floor(present[0]),
                ((math.floor(previous[1]) - math.floor(present[1])) * -1) + math.floor(present[1])]

    # my value matricies are 1-1 a representation of the current maze but rotated 90 degrees clockwise
    # e.g
    # if real map is:              the value matricies represent it as such:
    #                          (NOT TO SCALE)
    #  ##################                              ##################
    #  #                #                              #                #
    #  #    ########    #                              #    ########    #
    #  #    #           #                              #    #      #    #
    #  #    ########    #                              #    #      #    #
    #  #                #                              #                #
    #  ##################                              ##################
    #  

    # get the intial set up of the value matrix (i.e. get iteration 0)
    def getInitialValueMatrix(self, state, maze_shape, wall_locations,
                              closest_food, ghost_locations, ghost_prev_locations,
                              capsule_locations):
        
        # uses the maze_shape variable to construct the matrix
        for i in range(0, maze_shape[0] + 2):
            self.value_matrix_a.append([])
            for j in range(0, maze_shape[1] + 2):
                self.value_matrix_a[i].append(0)

                # place wall values in matrix
                if (i, j) in wall_locations:
                    self.value_matrix_a[i][j] = None
                # place closest food value in matrix
                if (i, j) == closest_food:
                    self.value_matrix_a[i][j] = 1
                # place ghost values in matrix
                if (i, j) in ghost_locations:
                    self.value_matrix_a[i][j] = -1
                # place capsule values in matrix
                if(i, j) in capsule_locations:
                    self.value_matrix_a[i][j] = 1
        
        # uses the getNextLocation() function to predict the positions of ghost in s' 
        # and place a value in that location of the value matrix
        # (the int() and math.ceil() are to ensure that these values are compatible
        # with list indices)
        self.nxt_loc = []
        if ghost_prev_locations != []:
            # for each ghost, predict it's next location and place it in the matrix
            # ensuring that walls are not overwritten
            for i in range(0, len(ghost_prev_locations)):
                self.nxt_loc = self.getNextGhostLocation(ghost_prev_locations[i], ghost_locations[i])
                if( int(self.nxt_loc[0]) <= maze_shape[1] and int(self.nxt_loc[1]) <= maze_shape[0] 
                   and self.value_matrix_a[int(math.ceil(self.nxt_loc[0]))][int(math.ceil(self.nxt_loc[1]))] != None ):

                    self.value_matrix_a[int(math.ceil(self.nxt_loc[0]))][int(math.ceil(self.nxt_loc[1]))] = -1
                    
        
    # value iteration function
    def iterateValues(self, maze_shape, wall_locations, closest_food, ghost_locations, capsule_locations, iterations):
        self.value_matrix_b = copy.deepcopy(self.value_matrix_a)
        # for k iterations
        for k in range(0 , iterations):     
            # for every value in the value matrix
            for i in range(0, maze_shape[0] + 2):
                for j in range(0, maze_shape[1] + 2):

                    # if the current value isn't a wall
                    if self.value_matrix_b[i][j] != None:
                        # define the current value's neighbours
                        neighbours = [self.value_matrix_a[i - 1][j], # left
                                      self.value_matrix_a[i][j + 1], # up
                                      self.value_matrix_a[i + 1][j], # right
                                      self.value_matrix_a[i][j - 1]] # down
                        
                        # store the coefficients in a deque
                        coefficients = deque([0.1,
                                              0.8,
                                              0.1,
                                              0])

                        values = []

                        # if there are walls in the neighbourhood, adjust the coefficients accordingly
                        for m in range(0, 4):
                            surp_coefficient = 0
                            if neighbours[m] == None:
                                if k == 1:
                                    surp_coefficient += 0.8
                                else:
                                    surp_coefficient += 0.1

                                neighbours[m] = self.value_matrix_a[i][j]

                        # store probabilisic utilities for each s' (P(s'|s,a) * U(s'))
                        for k in range(0, 4):
                            values.append(sum([neighbours[0] * coefficients[0],
                                               neighbours[1] * coefficients[1],
                                               neighbours[2] * coefficients[2],
                                               neighbours[3] * coefficients[3]]))
                    
                            coefficients.rotate(1)
                        
                        # find utility of current value
                        if( (i, j) not in wall_locations and (i, j) != closest_food 
                           and (i, j) not in ghost_locations and (i, j) not in capsule_locations
                           and [i, j] != self.nxt_loc ):

                            # U(s) = R(s) + gamma * max(P(s'|s,a) * U(s'))
                            self.value_matrix_b[i][j] = self.reward + (self.gamma * max(values))


            self.value_matrix_a = copy.deepcopy(self.value_matrix_b)
        
# actual MDPAgent class
class MDPAgent(Agent):

    # initialize environment and value iterator classes
    def __init__(self):
        self.env = Environment()
        self.vi = ValueIterator()
    
    # initialize object locations and initial state of value matrix
    def registerInitialState(self, state):
        self.env.updateFoodLocations(state)
        self.env.getClosestFood(state)
        self.env.updateCapsuleLocations(state)
        self.env.getEmptyLocations(state)
        self.env.getMazeShape(state)
        self.env.updateGhostLocations(state)

        self.vi.getInitialValueMatrix(state, self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.ghost_prev_locations, self.env.capsule_locations)
        
    # reset all values at end of game
    def final(self, state):
        self.env.all_food_locations = []
        self.env.closest_food = []
        self.env.capsule_locations = []
        self.env.ghost_locations = []
        self.env.ghost_prev_locations = []
        self.env.wall_locations = []
        self.env.open_locations = []
        self.env.maze_shape = [0, 0]

        self.vi.value_matrix_b = []
        self.vi.value_matrix_a = []
    
    # get the next direction to take (max value of pacman's current neighbours)
    def getNextDirection(self, state, value_matrix_b, pacman_location):
        i = pacman_location[0]
        j = pacman_location[1]
        
        neighbours = {'left': self.vi.value_matrix_b[i - 1][j],
                      'right': self.vi.value_matrix_b[i + 1][j],
                      'down': self.vi.value_matrix_b[i][j - 1],
                      'up': self.vi.value_matrix_b[i][j + 1]}
        
        if max(neighbours, key=neighbours.get) == 'left':
            return Directions.WEST
            
        elif max(neighbours, key=neighbours.get) == 'right':
            return Directions.EAST
            
        elif max(neighbours, key=neighbours.get) == 'down':
            return Directions.SOUTH
            
        elif max(neighbours, key=neighbours.get) == 'up':
            return Directions.NORTH
            
    def getAction(self, state):
        # reset the value matrix
        self.vi.value_matrix_b = []
        self.vi.value_matrix_a = []

        # update the locations of objects
        self.env.updateFoodLocations(state)
        self.env.getClosestFood(state)
        self.env.updateCapsuleLocations(state)
        self.env.getEmptyLocations(state)
        self.env.getMazeShape(state)
        self.env.updateGhostLocations(state)

        # update initial value matrix
        self.vi.getInitialValueMatrix(state, self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.ghost_prev_locations, self.env.capsule_locations)

        # iterate value matrix
        self.vi.iterateValues(self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.capsule_locations, 20)

        # set ghost previous locations (for predicting ghost s')
        self.env.ghost_prev_locations = api.ghosts(state)

        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        # make the move
        return api.makeMove(self.getNextDirection(state, self.vi.value_matrix_b, api.whereAmI(state)), legal)
