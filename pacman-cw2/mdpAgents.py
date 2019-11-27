# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
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

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

# extra libraries I am using:
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
    def update_food_locations(self, state):
        self.all_food_locations = api.food(state)
    
    # find where the remaining capsules currently are
    def update_capsule_locations(self, state):
        self.capsule_locations = api.capsules(state)
    
    # find where the ghosts currently are
    def update_ghost_locations(self, state):
        self.ghost_locations = api.ghosts(state)
    
    # store the size of the current maze (excluding borders)
    def get_maze_shape(self, state):
        if self.maze_shape == [0, 0]:
            for i in self.open_locations:
                if i[0] >= self.maze_shape[0]:
                    self.maze_shape[0] = i[0]
                if i[1] >= self.maze_shape[1]:
                    self.maze_shape[1] = i[1]

    # find all locations that pacman can move to
    def get_empty_locations(self, state):
        self.wall_locations = api.walls(state)

        if self.open_locations == []:
            for i in range(0, self.wall_locations[len(self.wall_locations) - 1][0]):
                for j in range(0, self.wall_locations[len(self.wall_locations) - 1][1]):
                    if (i, j) not in self.wall_locations:
                        self.open_locations.append((i, j))
    
    # find the location of the closest piece of food
    def get_closest_food(self, state):
        dists = []
        for i in self.all_food_locations:
            dists.append(util.manhattanDistance(api.whereAmI(state), i))
        self.closest_food = min(dists)
        
        closest_index = 0
        for i in dists:
            if i == self.closest_food:
                closest_index = dists.index(self.closest_food)
        
        self.closest_food = self.all_food_locations[closest_index]

            
                

    
# class to handle all value iteration information and instructions
class ValueIterator(Agent):
    def __init__(self):
        self.value_matrix = []
        self.value_table = []
        self.gamma = 0.9
        self.reward = -0.04

    # function to predict the next location of a ghost (used to help steer pacman away from ghosts):
    # next = ((previous - present) * -1) + present
    # where previous and present are 2-tuples or 2 element lists : (x, y)
    def get_ghost_next_location(self, previous, present):
        return [((math.floor(previous[0]) - math.floor(present[0])) * -1) + math.floor(present[0]), ((math.floor(previous[1]) - math.floor(present[1])) * -1) + math.floor(present[1])]

    # value table is a 1-1 representation of the current maze but rotated 90 degrees clockwise
    def ammend_value_table(self, state, maze_shape, wall_locations, closest_food, ghost_locations, ghost_prev_locations, capsule_locations):
        for i in range(0, maze_shape[0] + 2):
            self.value_table.append([])
            for j in range(0, maze_shape[1] + 2):
                self.value_table[i].append(0)
                if (i, j) in wall_locations:
                    self.value_table[i][j] = None
                if (i, j) == closest_food:
                    self.value_table[i][j] = 1
                if (i, j) in ghost_locations:
                    self.value_table[i][j] = -1
                if(i, j) in capsule_locations:
                    self.value_table[i][j] = 1
        
        nxt_loc = []
        if ghost_prev_locations != []:
            for i in range(0, len(ghost_locations)):
                nxt_loc = self.get_ghost_next_location(ghost_prev_locations[i], ghost_locations[i])
                if int(nxt_loc[0]) <= maze_shape[1] and int(nxt_loc[1]) <= maze_shape[0] and self.value_table[int(math.ceil(nxt_loc[0]))][int(math.ceil(nxt_loc[1]))] != None:
                    self.value_table[int(math.ceil(nxt_loc[0]))][int(math.ceil(nxt_loc[1]))] = -1
                    
        
                
    def iterate_value_matrix(self, maze_shape, wall_locations, closest_food, ghost_locations, capsule_locations, iterations):
        self.value_matrix = copy.deepcopy(self.value_table)
        for k in range(0 , iterations):     
            for i in range(0, maze_shape[0] + 2):
                for j in range(0, maze_shape[1] + 2):
                    if self.value_matrix[i][j] != None:
                        neighbours = [self.value_table[i - 1][j], # left
                                      self.value_table[i][j + 1], # up
                                      self.value_table[i + 1][j], # right
                                      self.value_table[i][j - 1]] # down
                        
                        coefficients = deque([0.1,
                                              0.8,
                                              0.1,
                                              0])

                        values = []

                        for m in range(0, 4):
                            surp_coefficient = 0
                            if neighbours[m] == None:
                                if k == 1:
                                    surp_coefficient += 0.8
                                else:
                                    surp_coefficient += 0.1

                                neighbours[m] = self.value_table[i][j]

                        for k in range(0, 4):
                            values.append(sum([neighbours[0] * coefficients[0],
                                               neighbours[1] * coefficients[1],
                                               neighbours[2] * coefficients[2],
                                               neighbours[3] * coefficients[3]]))
                    
                            coefficients.rotate(1)
                        
                        if (i, j) not in wall_locations and (i, j) != closest_food and (i, j) not in ghost_locations and (i, j) not in capsule_locations:
                            self.value_matrix[i][j] = self.reward + (self.gamma * max(values))
            self.value_table = copy.deepcopy(self.value_matrix)
        

class MDPAgent(Agent):


    def __init__(self):
        self.env = Environment()
        self.vi = ValueIterator()

    def registerInitialState(self, state):
        self.env.update_food_locations(state)
        self.env.get_closest_food(state)
        self.env.update_capsule_locations(state)
        self.env.get_empty_locations(state)
        self.env.get_maze_shape(state)
        self.env.update_ghost_locations(state)

        self.vi.ammend_value_table(state, self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.ghost_prev_locations, self.env.capsule_locations)


    def final(self, state):
        self.env.all_food_locations = []
        self.env.closest_food = []
        self.env.capsule_locations = []
        self.env.ghost_locations = []
        self.env.ghost_prev_locations = []
        self.env.wall_locations = []
        self.env.open_locations = []
        self.env.maze_shape = [0, 0]

        self.vi.value_matrix = []
        self.vi.value_table = []
        self.vi.gamma = 0.99
        self.vi.reward = -0.04
    
    def get_next_direction(self, state, value_matrix, pacman_location):
        i = pacman_location[0]
        j = pacman_location[1]
        
        neighbours = {'left': self.vi.value_matrix[i - 1][j], # left
                      'right': self.vi.value_matrix[i + 1][j], # right
                      'down': self.vi.value_matrix[i][j - 1], # down
                      'up': self.vi.value_matrix[i][j + 1]} # up
        
        if max(neighbours, key=neighbours.get) == 'left':
            return Directions.WEST
            
        elif max(neighbours, key=neighbours.get) == 'right':
            return Directions.EAST
            
        elif max(neighbours, key=neighbours.get) == 'down':
            return Directions.SOUTH
            
        elif max(neighbours, key=neighbours.get) == 'up':
            return Directions.NORTH
            

    def getAction(self, state):
        self.vi.value_matrix = []
        self.vi.value_table = []

        self.env.update_food_locations(state)
        self.env.get_closest_food(state)
        self.env.update_capsule_locations(state)
        self.env.get_empty_locations(state)
        self.env.get_maze_shape(state)
        self.env.update_ghost_locations(state)

        self.vi.ammend_value_table(state, self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.ghost_prev_locations, self.env.capsule_locations)


        self.vi.iterate_value_matrix(self.env.maze_shape, self.env.wall_locations, 
                                    self.env.closest_food, self.env.ghost_locations,
                                    self.env.capsule_locations, 20)
        
        self.env.ghost_prev_locations = api.ghosts(state)

        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        return api.makeMove(self.get_next_direction(state, self.vi.value_matrix, api.whereAmI(state)), legal)
