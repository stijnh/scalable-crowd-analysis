import math
import matplotlib.pyplot as plt
import numpy as np
import argparse
import random
import sys

import proximity
import scenario

def generate_trajectories(options):
    name = options.scenario.lower()
    width = 250
    paths = []

    if name in 'lane':
        path = scenario.create_hline(width)
        paths = [path, path.reverse()]

    elif name == 'sinus':
        path = scenario.create_sinus(width, options.sinus_amplitude)
        paths = [path, path.reverse()]

    elif name == 'parallel':
        dist = options.parallel_distance

        if dist < 0:
            raise Exception('distance must be positive')

        paths = [
            scenario.create_hline(width, -0.5 * dist),
            scenario.create_hline(width, 0.5 * dist)]

    elif name == 'crossing':
        angle = options.crossing_angle / 180.0 * math.pi

        if angle < 0 or angle > math.pi:
            raise Exception('angle not allowed, must be in [0, 180]')

        paths = [
            scenario.create_path(
                (-0.5 * width, 0),
                (+0.5 * width, 0)),
            scenario.create_path(
                (-0.5 * width * math.cos(angle), -0.5 * width * math.sin(angle)),
                (+0.5 * width * math.cos(angle), +0.5 * width * math.sin(angle)))
        ]

    elif name == 'divergent':
        paths = [
            scenario.create_hline(width),
            scenario.create_corner(width)]
    else:
        print 'unknown scenario "%s"' % name
        sys.exit(1)

    dataset = []
    anchors = []

    for path in paths:
        for _ in range(options.num_nodes):
            dataset += scenario.simulate_path(
                    path,
                    options.timesteps,
                    5,    # offset,
                    1.3,  # average velocity
                    0.3)  # stddev velocity

        # spawn anchor every 25 meter
        for d in np.linspace(0, path.length, options.anchor_radius):
            anchors += [path.at(d)]

    return anchors, dataset


def embed_trajectories(anchors, trajectories, options):
    if options.skip_embedding:
        print '# skipping embedding phase'
        return trajectories

    return proximity.embed_trajectories(
            trajectories,
            anchors,
            500,  # number of rounds
            0.05, # lambda
            options.detection_radius) # detection radius


def parse_arguments():
    info='''
    Simulates N nodes following two distinct paths in the specified scenario.
    Valid scenarios are: lane (two opssing lane), sinus (two opposing sinusoidal paths),
    parallel (two parallel lanes some distance apart), crossing (two parallel lanes 
    intersecting at some angle), and divergent (one lane splitting into two lanes).
    After simulation, the nodes are embedding into 2D space using a fast embedding
    algorithm. The resulting trajectories after the embedding are written to output.
    '''

    parser = argparse.ArgumentParser(add_help=False, description=info)
    parser.print_usage = parser.print_help

    parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS,
            help='Show this help message and exit.')
    parser.add_argument('--output', '-o', default='-',
            help='Optional output file. Output is written to stdout if no file is provided.')
    parser.add_argument('scenario',
            help='Scenario to simulate. Choices: %s' % 
            ', '.join(['lane', 'sinus', 'parallel', 'crossing', 'divergent']))

    parser.add_argument('--skip-embedding', action='store_true',
            help='Omit the embedding phase. Simulated trajectories are directly written to output.')
    parser.add_argument('--seed', type=int, default=0,
            help='Seed to use for random number generator.')

    parser.add_argument('-n', '--num-nodes', type=int, default=25,
            help='Number of simulated nodes assigned to each path. Default is 25')
    parser.add_argument('-t', '--timesteps', type=int, default=1500,
            help='Number of timesteps to run the simulation. Default is 1500.')

    parser.add_argument('--sinus-amplitude', type=float, default=50,
            help='Only applies to SINUS scenario. Amplitude to use for sinusoidal paths.')
    parser.add_argument('--parallel-distance', type=float, default=10,
            help='Only applies to PARALLEL scenario. Distance between parallel lanes.')
    parser.add_argument('--crossing-angle', type=float, default=45,
            help='Only applies to CROSSING scenario. Angle in degrees (NOT radians) between crossing lanes.')

    parser.add_argument('--anchor-radius', type=float, default=25,
            help='Distance between anchor nodes.')
    parser.add_argument('--detection-radius', type=float, default=25,
            help='Detection radius for mobile nodes.')


    return parser.parse_args()


def main():
    options = parse_arguments()

    random.seed(options.seed)
    np.random.seed(options.seed)

    print '# generating trajectories: %s' % options.scenario
    anchors, dataset = generate_trajectories(options)

    print '# perform embedding'
    dataset = embed_trajectories(anchors, dataset, options)

    if options.output == '-':
        handle = sys.stdout
    else:
        handle = open(options.output)

    for trajectory in dataset:
        for point in trajectory:
            print point[0], point[1],
        print


if __name__ == '__main__':
    sys.exit(main())
