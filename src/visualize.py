import math
import matplotlib.pyplot as plt
import matplotlib.collections as mc
import numpy as np
import argparse
import random
import sys

import detection

def load_dataset(stream):
    trajectories = []

    for line in stream:
        line = line.strip()

        # ignore empty lines
        if not line: continue

        # ignore comments
        if line[0] in ('#', '%'): continue

        parts = map(float, line.split())
        trajectories.append(np.array(parts).reshape(-1, 2))

    return trajectories


def parse_arguments():
    parser = argparse.ArgumentParser(add_help=False)
    parser.print_usage = parser.print_help

    p = parser.add_argument_group('General')
    p.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS,
            help='Show this help message and exit.')
    p.add_argument('--seed', type=int, default=0,
            help='Seed used for random number generation.')
    p.add_argument('file', help='Name of input file. If file is "-", read standard input.')

    p = parser.add_argument_group('Tracklet Extraction')
    p.add_argument('--window', '-w', type=int, default=10,
            help='Window size used during tracklet extraction. Larger ' + 
            'windows imply more smoothing of the input data.')

    p = parser.add_argument_group('Spatial Clustering')
    p.add_argument('--alpha', '-a', type=float, default=30,
            help='Normalization factor for position. Trackelts are ' + 
            'considered related if |p[i] - p[j]| < alpha.')
    p.add_argument('--beta', '-b', type=float, default=5,
            help='Normalization factor for velocity. Trackelts are ' + 
            'considered related if |v[i] - v[j]| < beta.')
    p.add_argument('--max-delta', type=float, default=1,
            help='Distance threshold for when cluster is considered ' + 
            'cluster center. Advised to keep default value.')
    p.add_argument('--min-rho', type=float, default=50,
            help='Density threshold for when cluster is considered noise.')

    p = parser.add_argument_group('Temporal Clustering')
    p.add_argument('--gamma', type=float, default=0.75,
            help='Temporal influence between motion patterns.')
    p.add_argument('--cut', type=float, default=0.35,
            help='Height at which to cut the dendrogram from temporal clustering.')

    return parser.parse_args()


def main():
    options = parse_arguments()

    random.seed(options.seed)
    np.random.seed(options.seed)

    if options.file == '-':
        dataset = load_dataset(sys.stdin)
    else:
        print 'opening: %s' % options.file

        with open(options.file, 'r') as handle:
            dataset = load_dataset(handle)

    print 'found %d trajectories, %d points' % (len(dataset), sum(map(len, dataset)))

    print 'build tracklets'
    ids, tracklets = detection.build_tracklets(dataset, options.window)
    normalize = [options.alpha] * 2 + [options.beta] * 2
    print 'generated %d tracklets' % len(tracklets)


    print 'perform quick shift'
    rho, delta, parent = detection.prepare_quick_shift(tracklets / normalize)
    labels, centers = detection.perform_quick_shift(rho, delta, parent,
            options.min_rho, options.max_delta)
    print 'labeled %d tracklets as noise' % np.sum(labels == -1)
    print 'found %d clusters' % len(centers)

    if len(centers) < 100:
        print 'perform hierarchical clustering'
        sim = detection.calculate_cohesion(ids, labels, options.gamma)
        labels, joins = detection.merge_cohesion(labels, sim, options.cut)
        print 'found %d patterns' % len(set(labels))
    else:
        print 'warning: too many clusters, adjust min_rho'
        joins = []

    xlim = [np.amin(tracklets.T[0]), np.amax(tracklets.T[0])]
    ylim = [np.amin(tracklets.T[1]), np.amax(tracklets.T[1])]

    axis = plt.subplot(231)
    plt.title('Input trajectories')
    plt.xlim(xlim); plt.ylim(ylim)
    axis.set_aspect('equal', 'datalim')
    axis.add_collection(mc.LineCollection(dataset, linewidth=.5))

    axis = plt.subplot(232)
    plt.title('Tracklets')
    indices = np.random.permutation(len(tracklets))[:2500]
    plt.quiver(
            tracklets[indices,0],
            tracklets[indices,1],
            tracklets[indices,2],
            tracklets[indices,3])
    plt.xlim(xlim); plt.ylim(ylim)
    axis.set_aspect('equal', 'datalim')

    axis = plt.subplot(233)
    plt.title('Density-delta plot')
    plt.hlines(options.max_delta, 0, 9999)
    plt.vlines(options.min_rho, 0, 9999)
    detection.plot_delta_rho(axis, rho, delta)

    axis = plt.subplot(234)
    plt.title('Cluster centers')
    plt.quiver(
            tracklets[centers,0],
            tracklets[centers,1],
            tracklets[centers,2],
            tracklets[centers,3])
    plt.xlim(xlim); plt.ylim(ylim)
    axis.set_aspect('equal', 'datalim')

    axis = plt.subplot(235)
    plt.title('Dendrogram')
    detection.plot_joins(axis, joins)
    plt.hlines(1-options.cut, 0, 999)

    axis = plt.subplot(236)
    plt.title('Final clusters')
    indices = np.random.permutation(len(tracklets))[:2500]

    cmap = plt.get_cmap('jet')
    colors = dict()
    colors[-1] = (0.5, 0.5, 0.5, 1)

    unique_labels = set(labels)
    unique_labels.discard(-1)
    
    for i,l in enumerate(unique_labels):
        colors[l] = cmap(i / float(len(unique_labels)))

    plt.quiver(
            tracklets[indices,0],
            tracklets[indices,1],
            tracklets[indices,2],
            tracklets[indices,3],
            color=[colors[l] for l in labels[indices]])
    plt.xlim(xlim); plt.ylim(ylim)
    axis.set_aspect('equal', 'datalim')

    plt.show()
    return 0


if __name__ == '__main__':
    sys.exit(main())
