import numpy as np


variance_scale = 0.43
variance_offset = -0.6

squared_weights = [0.0826, 1.9146, 0.1485, 0.3326]
squared_weights2 = [6.0255, 1.9138, 0.0696, 0.0354]
squared_weights3 = [0.1956, 0.0682, -0.0543, 0.1199]
non_squared_weights = [0.8521, 2.4242, 0.2660, 0.3044]
both_weights = [-0.0090, 1.9832, 0.9130, 0.0045, 0.2678, 0.2787]

sig_weights = [0.0855, 2.1579, 1, 0.1688, 0.3494]

class LoglinDistribution:
	# [0.0826, 1.9146, 0.1485, 0.3326]
	def __init__(self, command, direction, refpt, world, w=squared_weights2):
		self.command = command
		self.world = world
		self.features = all_features
		#these two features added for debugging, will be more explicit later
		self.refpt = refpt
		self.direction = direction

		x, y = np.mgrid[0:self.world.xdim:.1, 0:self.world.ydim:.1]

		self.feature_matrix = get_feature_matrix(x, y, self.command, self.direction, self.refpt, self.world, self.features)

		self.set_weights(w)

	def pdf(self, pts, normalize=True):
		xslice = [slice(None)]*(pts.ndim - 1) + [0]
		yslice = [slice(None)]*(pts.ndim - 1) + [1]
		x = pts[xslice]
		y = pts[yslice]
		ref_dists = get_ref_dists(x, y, self.world)

		features = np.array([w*f(x, y, self.command, self.direction, self.refpt, self.world, ref_dists) for f, w in zip(self.features, self.w)])
		vals = np.exp(np.sum(features, axis=0))

		if normalize:
			vals = vals/self.normalization*100
		return vals if vals.size > 1 else vals[0]

	def set_weights(self, w):
		self.w = np.array(w)
		self.normalization = np.sum(np.exp(self.feature_matrix*np.matrix(self.w).T))
		x, y = np.mgrid[0:self.world.xdim:.1, 0:self.world.ydim:.1]
		prob = self.pdf(np.dstack((x, y)), normalize=True)/100
		self.mean = np.array([np.sum(x*prob), np.sum(y*prob)])

class MultiPeakLoglin:

	#takes in a list of refpts directions, and probabilities, creates list of single-peaked
	def __init__(self, command, directions, refpts, probs, world):
		self.command = command
		self.world = world
		self.directions = directions
		self.refpts = refpts
		self.probs = probs

		self.distributions = [LoglinDistribution(command, direction, refpt, world) for direction, refpt in zip(self.directions, self.refpts)]

	def pdf(self, pts, normalize=False):

		print zip(self.distributions, self.probs)
		vals_stacked = np.array([distribution.pdf(pts)*prob for distribution, prob in zip(self.distributions, self.probs)])

		return np.sum(vals_stacked, axis=0)





def estimate_reference_pt(ref, direction):
	center = ref.center
	offset = ref.width/2.*direction if direction[0] else ref.height/2.*direction
	return center + offset

def estimate_pos(cmd):
	ref = cmd.reference
	direction = cmd.direction
	vector = cmd.distance*direction
	return estimate_reference_pt(ref, direction) + vector

#returns perpendicular unit vector in 2 dimensions
def get_normal_vec(vec):
	perp = np.array([-vec[1], vec[0]])
	return perp/np.linalg.norm(perp)

def get_ref_dists(x, y, world):
	ref_dists = {}
	for ref in world.references:
		directions = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])
		ref_pts = np.array([estimate_reference_pt(ref, direction) for direction in directions])
		possible_dists = np.dstack(np.sqrt((x - pt[0])**2 + (y - pt[1])**2) for pt in ref_pts)
		ref_dists[ref] = np.min(possible_dists, axis=2)
	return ref_dists

def feature_naive(x, y, cmd, world, ref_dists):
	variance_cmd_parallel = max(cmd.distance*variance_scale + variance_offset, 0.5)
	variance_cmd_ortho = 0.5
	mean = estimate_pos(cmd)
	if cmd.direction[0]:
		varx = variance_cmd_parallel
		vary = variance_cmd_ortho
	else:
		varx = variance_cmd_ortho
		vary = variance_cmd_parallel
	mean_dist = (x - mean[0])**2/varx + (y - mean[1])**2/vary
	return -mean_dist


#modified to allow for different direction vectors
def feature_parallel_squared(x, y, cmd, direction, refpt, world, ref_dists):
	mean = estimate_pos(cmd)
	if cmd.direction[0]:
		return -(x - mean[0])**2/cmd.distance**2
	else:
		return -(y - mean[1])**2/cmd.distance**2

	x_diff = x - refpt[0]
	y_diff = y - refpt[1]

	#just in case the direction isn't normalized
	direction_hat = direction/np.linalg.norm(direction)

	return -(x_diff*direction_hat[0] + y_diff*direction_hat[1])**2/cmd.distance**2

def feature_parallel(x, y, cmd, world, ref_dists):
	mean = estimate_pos(cmd)
	if cmd.direction[0]:
		return -np.abs(x - mean[0])
	else:
		return -np.abs(y - mean[1])

def feature_ortho_squared(x, y, cmd, direction, refpt, world, ref_dists):
	# mean = estimate_pos(cmd)
	# if cmd.direction[0]:
	# 	return -(y - mean[1])**2
	# else:
	# 	return -(x - mean[0])**2

	x_diff = x - refpt[0]
	y_diff = y - refpt[1]

	#just in case the direction isn't normalized
	direction_hat = direction/np.linalg.norm(direction)

	direction_perp = get_normal_vec(direction_hat)

	return -(x_diff*direction_perp[0] + y_diff*direction_perp[1])**2

def feature_ortho(x, y, cmd, world, ref_dists):
	mean = estimate_pos(cmd)
	if cmd.direction[0]:
		return -np.abs(y - mean[1])
	else:
		return -np.abs(x - mean[0])

def feature_sig_parallel_weak(x, y, cmd, world, ref_dists):
	refpt = estimate_reference_pt(cmd.reference, cmd.direction)
	if cmd.direction[0]:
		return -cmd.direction[0]*(x - refpt[0])
	else:
		return -cmd.direction[1]*(y - refpt[1])

def feature_objects(x, y, cmd, direction, refpt, world, ref_dists):
	min_ref_dists = np.min(np.dstack(ref_dists[ref] for ref in ref_dists), axis=2)
	ref_distance_diff = ref_dists[cmd.reference] - min_ref_dists
	return -(ref_distance_diff)

def feature_walls(x, y, cmd, direction, refpt, world, ref_dists):
	min_wall_dists = np.min(np.dstack((x, y, world.xdim - x, world.ydim - y)), axis=2)
	wall_distance_diff = ref_dists[cmd.reference] - min_wall_dists
	wall_distance_diff[wall_distance_diff < 0] = 0
	return -(wall_distance_diff)

def get_feature_matrix(x, y, cmd, direction, refpt, world, features):
	ref_dists = get_ref_dists(x, y, world)

	feature_vals = [f(x, y, cmd, direction, refpt, world, ref_dists) for f in features]

	f_matrix = np.matrix([el.flatten() for el in feature_vals])
	f_matrix = f_matrix.T
	return f_matrix

all_features = [
			feature_parallel_squared,
			feature_ortho_squared,
#			feature_parallel,
#			feature_ortho,
#			feature_sig_parallel_weak,
			feature_objects, 
			feature_walls
			]