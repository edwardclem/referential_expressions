#!/usr/bin/env python2

import numpy as np
import matplotlib
from matplotlib.patches import Circle, Polygon
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.stats import multivariate_normal
from reference_algorithms import Command, Reference, World

import sys

# Object dimensions and commands from https://docs.google.com/document/d/1TbAKCrdEfgD6nCEjhlpJ4BpAJcmeSajsGQwb4HBsh7U/edit
keyboard = Reference("keyboard", np.array([[33.375, 13.5], [38.5, 13.5], [38, 24.625], [33, 24.375]]))
car = Reference("car", np.array([[9.5, 21.5], [10.625, 21.25], [11.625, 24], [10.375, 24.5]]))
bowl = Reference("bowl", (np.array([19.75, 10]), 2.5))

world = World([keyboard, car, bowl], 48, 36)

commands = {
	1 : Command("4 inches left of the car",                      4,   np.array([-1, 0]), car),
	2 : Command("1 foot left of the keyboard",                   12,  np.array([-1, 0]), keyboard),
	3 : Command("1 and a half feet right of the car",            18,  np.array([1, 0]),  car),
	4 : Command("4 inches in front of the pink bowl",            4,   np.array([0, -1]), bowl),
	5 : Command("5 and a half inches behind the keyboard",       5.5, np.array([0, 1]),  keyboard),
	6 : Command("2 inches left of the pink bowl",                2,   np.array([-1, 0]), bowl),
	7 : Command("1 and a half inches behind the car",            1.5, np.array([0, 1]),  car),
	8 : Command("2 feet behind the pink bowl",                   7,   np.array([1, 0]),  bowl),
	9 : Command("16 inches in front of the car",                 16,  np.array([0, -1]), car),
	10 : Command("2 feet behind the pink bowl",                  24,  np.array([0, 1]),  bowl),
	11 : Command("3 inches right of the keyboard",               3,   np.array([1, 0]),  keyboard),
	12 : Command("4 and a half inches in front of the keyboard", 4.5, np.array([0, -1]), keyboard)
}

"""
Get the data by doing:

	from data_vis import load_data
	data = load_data('point_data.csv')

then data is a dictionary with keys 1-12, referring to the points
"""
def load_data(filename):
	text = None
	with open(filename) as f:
		text = f.readline()

	text = text.split('\r')
	data = {}
	for line in text:
		line = line.split(',', 1)
		point_num = int(line[0])
		point_loc = [float(el) for el in line[1][2:-2].split(',')] # Parsing the tuple is annoying
		data[point_num] = data.get(point_num, []) + [point_loc]

	for i in range(1, 13):
		data[i] = np.array(data[i])

	return data

def get_means(data):
	return {pt : np.mean(data[pt], axis=0) for pt in data}

def get_covariances(data):
	return {pt : np.cov(data[pt].T) for pt in data}

"""
Get cheating normal distributions

Can use cheating_normals to get probability of data - 
	e.g. probs1 = cheating_normals[1].pdf(data[1])
"""
def get_cheating_distribution(data):
	means = get_means(data)
	covariances = get_covariances(data)
	cheating_normals = {pt : multivariate_normal(means[pt], covariances[pt]) for pt in data}
	return cheating_normals

def get_random_distribution(data):
	means = {pt : np.random.rand(2)*np.array(48, 36) for pt in data}
	random_normals = {pt : multivariate_normal(means[pt], np.array([1, 0], [0, 1])) for pt in data}
	return random_normals

def plot_distance_parallel(data):
	fig, ax = plt.subplots()
	covariances = get_covariances(data)
	variances_in_direction = [covariances[i][0, 0] if commands[i].direction[0] else covariances[i][1, 1] for i in range(1, 13)]
	distance = [commands[i].distance for i in range(1, 13)]
	#calculating line of best fit
	line_bestfit = np.polyfit(distance, variances_in_direction, 1)
	print "Linear fit results: slope= " + str(line_bestfit[0]) + " intercept = " + str(line_bestfit[1]) 
	#plotting line of best fit
	distance_range = np.linspace(0, 30)
	bestfit_points = distance_range*line_bestfit[0] + line_bestfit[1]
	plt.plot(distance_range, bestfit_points)
	plt.scatter(distance, variances_in_direction)
	ax.set_xlabel('Distance of Command (inches)')
	ax.set_ylabel('Variance in direction of command')
	plt.show()

def plot_distance_orthogonal(data):
	fig, ax = plt.subplots()
	covariances = get_covariances(data)
	variances_in_direction = [covariances[i][1, 1] if commands[i].direction[0] else covariances[i][0, 0] for i in range(1, 13)]
	distance = [commands[i].distance for i in range(1, 13)]
	plt.scatter(distance, variances_in_direction)
	ax.set_xlabel('Distance of Command (inches)')
	ax.set_ylabel('Variance orthogonal to direction of command')
	plt.show()

# i = command number
def estimated_position(i):
	ref = commands[i].reference
	center = ref.center
	direction = commands[i].direction
	vector = commands[i].distance*direction
	offset = ref.width/2.*direction if direction[0] else ref.height/2.*direction
	return center + offset + vector

def visualize(data, world, filename=None):
	fig, ax = plt.subplots()
	ax.set_xlim([0, world.xdim]) # Set x dim to 4 feet
	ax.set_ylim([0, world.ydim]) # Set y dim to 3 feet

	objects = PatchCollection([ref.patch for ref in world.references])
	objects.set_array(np.array([0, 0, 0, 1]))
	ax.add_collection(objects)

	colors = cm.rainbow(np.linspace(0, 1, 12))
	for i in range(1, 13):
		plt.scatter(data[i][:,0], data[i][:,1], c=colors[i-1], marker='+')
		estimated_pos = estimated_position(i)
		plt.scatter(estimated_pos[0], estimated_pos[1], c=np.array([0, 0, 0, 1]), marker='o')

	if filename:
		plt.savefig(filename, format='pdf')

	plt.show()

def visualize_distribution(points, distribution, world, filename=None):
	fig, ax = plt.subplots()
	ax.set_xlim([0, world.xdim]) # Set x dim to 4 feet
	ax.set_ylim([0, world.ydim]) # Set y dim to 3 feet

	x, y = np.mgrid[0:world.xdim:.1, 0:world.ydim:.1]
	pos = np.empty(x.shape + (2,))
	pos[:, :, 0] = x
	pos[:, :, 1] = y
	plt.contourf(x, y, distribution.pdf(pos))

	objects = PatchCollection([ref.patch for ref in world.references], cmap=matplotlib.cm.gray, alpha=1)
	objects.set_array(np.array([1, 1, 1]))
	ax.add_collection(objects)

	plt.scatter(points[:, 0], points[:, 1], c=np.array([1, 1, 1, 1]))

	if filename:
		plt.savefig(filename, format='pdf')

	plt.show()


if __name__ == '__main__':
	data = load_data('point_data.csv')
	if len(sys.argv) == 3 and sys.argv[1] == 'save':
		visualize(data, sys.argv[2])
	else:
		visualize(data)