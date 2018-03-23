import matplotlib.pyplot as plt
import numpy as np
import random
import scipy.spatial

from collections import defaultdict

def collect_edges(pos, d_max, d_hop=None):
    """
    Let two nodes be connected if their Euclidian distance is less
    than ``d_max``. This function returns all pairs of nodes that
    are directly or indirectly (at most one hop) connected.

    :param pos: Physical locations of nodes.
    :param d_max: "Detection" radius of nodes.
    :param d_hop: Average distance per hop.
    :returns: List of ``(i, j, d)`` tuples indicating that
    nodes ``i`` and ``j`` are connected. Value of ``d``
    is ``d_hop`` or ``2*d_hop``, depending on wether
    ``i`` and ``j`` are 1-hop or 2-hop neighbors.
    """

    n = len(pos)
    tree = scipy.spatial.cKDTree(np.array(pos))
    direct_edges = tree.query_pairs(d_max)
    final_edges = []

    adj = [[] for _ in range(n)]
    
    if d_hop is None:
        d_hop = 0.666 * d_max

    for a,b in direct_edges:
        adj[a].append(b)
        adj[b].append(a)

    for a in range(n):
        final_edges.append((a, a, 0))

        hop1 = set(adj[a])
        hop2 = set()

        for b in adj[a]:
            hop2.update(adj[b])

        for b in hop1:
            if a < b:
                final_edges.append((a, b, d_hop))

        for b in hop2 - hop1:
            if a < b:
                final_edges.append((a, b, 2 * d_hop))

    return final_edges


def embed_rounds(max_iter, rate, pos, edges, is_anchor):
    """
    Execute stochastic proximity embedding (SPE) algorithm. The algorithm
    attempts to position nodes such that their distances matches the
    inputs from ``edges``.

    :param max_iter: Number of rounds to perform.
    :param rate: Parameter lambda for SPE algorithm.
    :param pos: Initial positions of nodes.
    :param edges: Edges generated by ``collect_edges``.
    :param is_anchor: List of booleans where ``is_anchor[i]``
    is an anchor node and thus cannot be moved.
    """
    n = len(pos)
    pos = np.array(pos)
    indices = []

    if len(edges) == 0:
        return pos

    for it in range(max_iter):
        if not indices:
            indices = list(np.random.permutation(len(edges)))

        a,b,w = edges[indices.pop()]

        delta = (pos[a] - pos[b]) + np.random.normal(size=2)*0.1
        real_dist = np.linalg.norm(delta)
        pref_dist = w

        if real_dist == 0: continue

        scale = rate ** (it / float(max_iter))
        delta = scale * (pref_dist - real_dist) / real_dist * delta

        if not is_anchor[a]: pos[a] += .5 * delta
        if not is_anchor[b]: pos[b] -= .5 * delta

    return pos


def embed_trajectories(trajectories, anchors, max_rounds, rate, d_max, d_hop=None):
    """
    Takes a list of trajectories and executes the SPE algorithm for each 
    timestep. Each timestep consists of calling ``collect_edges`` to collect
    edges and calling ``embed_rounds`` to perform the embedding.

    :param trajectories: List of trajectories. Each trajectory must be list of
    ``(x, y, t)`` tuples indicating position ``(x, y)`` at timestep ``t``.
    :param anchors: Positions of anchor nodes.
    :param max_rounds: Parameter for ``embed_rounds``.
    :param rate: Parameter for ``embed_rounds``.
    :param d_max: Parameter for ``collect_edges``.
    :param d_hop: Parameter for ``collect_edges``.
    :returns: List of trajectories after embedding.
    """

    n = len(trajectories)
    result = [[] for _ in range(n)]
    per_timestep = defaultdict(lambda: [])
    last_pos = dict()

    for i, trajectory in enumerate(trajectories):
        for x,y,t in trajectory:
            per_timestep[t].append((x, y, i))

    for t in sorted(per_timestep.keys()):
        real_pos = []
        embed_pos = []
        is_anchor = []

        for x,y,i in per_timestep[t]:

            # new node, set embed pos. to real pos.
            if i not in last_pos:
                last_pos[i] = (x, y)

            real_pos.append((x, y))
            embed_pos.append(last_pos[i])
            is_anchor.append(False)

        for x,y in anchors:
            real_pos.append((x, y))
            embed_pos.append((x, y))
            is_anchor.append(True)

        edges = collect_edges(
                real_pos,
                d_max,
                d_hop)

        embed_pos = embed_rounds(
                max_rounds,
                rate,
                embed_pos,
                edges,
                is_anchor)
        
        for (x, y), (_, _, i) in zip(embed_pos, per_timestep[t]):
            last_pos[i] = (x, y)
            result[i].append((x, y, t))

    return result