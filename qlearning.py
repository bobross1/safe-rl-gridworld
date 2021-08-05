import numpy as np
import cv2
from PIL import Image
import pickle
import matplotlib.pyplot as plt
from matplotlib import style
import time
import random
import importlib
import os
from env import gridworld, layout_original, layout_nowalls
from helper import *
from agent import Agent


SIZE = 9
LAYOUT = layout_original
SHOW = True
EPISODES = 600000
SHIELD_ON = True
SHIELDED_FUTURE_Q = False
N_ACTIONS = 5 # N_ACTIONS must be 5 or 9 (including standing still)
MOVE_PENALTY = 1
ENEMY_PENALTY = 300
FOOD_REWARD = 25
WALL_PENALTY = -10

CHECK_SHIELD_OVERRIDE = False
SHIELD_OVERRIDE_PENALTY = -50

SHOW_EVERY = 2000
SAVE_INTERVAL = 10000

EPSILON_START=1.0
EPSILON_END=0.1 #0.02 # 0.1
EPSILON_DECAY=500000 #1000000

# LEARNING_RATE = 5e-4 #0.1
LEARNING_RATE_START = 0.3
LEARNING_RATE_END = 0.01
LEARNING_RATE_DECAY = 100000

DISCOUNT = 0.95

start_q_table = None # insert qtable filename if available/saved
SAVE_Q_TABLE =  True
SAVE_RESULTS = True
PLOT = True

# random.seed(34095)
# np.random.seed(34095)

# checks
assert N_ACTIONS == 5 or N_ACTIONS == 9, "N_ACTIONS can only be 5 or 9"

# import shield
if SHIELD_ON:
	try:
		mod_name = f"9x9_3_{str(N_ACTIONS - 1)}directions"
		Shield = importlib.import_module(mod_name).Shield
		shield = Shield()
	except ImportError as e:
		print("Could not find shield.")

# qlearning algo
q_table = generate_qtable(start_q_table, SIZE, N_ACTIONS)
episode_rewards = [0]
walls = gridworld(LAYOUT, SIZE).walls
for episode in range(EPISODES):
	if episode % SAVE_INTERVAL == 0 and episode > 1:
		save_results(q_table, episode_rewards, SHIELD_ON, SHIELDED_FUTURE_Q, EPISODES, N_ACTIONS, SAVE_RESULTS, SAVE_Q_TABLE)

	epsilon = np.interp(episode, [0, EPSILON_DECAY], [EPSILON_START, EPSILON_END])
	lr = np.interp(episode, [0, LEARNING_RATE_DECAY], [LEARNING_RATE_START, LEARNING_RATE_END])

	places_no_walls = no_walls(SIZE, walls)
	player = Agent(places_no_walls, walls, SHIELD_ON, SIZE, random_init=True)
	target = Agent(places_no_walls, walls, SHIELD_ON, SIZE, random_init=True)
	# enemy = Agent(places_no_walls, random_init=True)

	if episode % SHOW_EVERY == 0:
		print(f"Episode: {episode}, epsilon: {epsilon}, lr: {lr}, mean reward: {np.mean(episode_rewards[-SHOW_EVERY:])}")

	# steps in episode
	episode_reward = 0
	reward = 0
	for i in range(100):
		# obs = (player-target, player-enemy)
		obs = (player-target)

		rnd = np.random.random()
		if SHIELD_ON:
			action = safe_action(rnd, epsilon, obs, q_table, N_ACTIONS, player, walls, shield)
		else:
			action = random_action(rnd, epsilon, q_table, obs, N_ACTIONS)

		reward, done = check_reward(player, target, action, walls, FOOD_REWARD, WALL_PENALTY, N_ACTIONS)
		episode_reward += reward	

		# perforn action player (when N_ACTIONS is 5, action 8 should be used as standing still not 4)
		if action == 4 and N_ACTIONS == 5:
			player.action(8)
		else:
			player.action(action)
		
		# new_obs = (player-target, player-enemy)
		new_obs = (player-target)
		new_q = calc_new_q(SHIELDED_FUTURE_Q, q_table, obs, new_obs, action, lr, reward, DISCOUNT, player, walls)
		q_table[obs][action] = new_q

		# render visualisation
		if SHOW:
			env = gridworld(layout=layout_original, size=SIZE)
			env.render(player, target, step=i, reward=reward)

		# if target/wall/enemy is hit reset the game
		if done:
			break
		
	# save reward
	episode_rewards.append(episode_reward)

# plot directly
if PLOT:
	plot()
