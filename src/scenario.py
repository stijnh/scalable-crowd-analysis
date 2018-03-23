import numpy as np
import math
import random
from bisect import bisect


class Path:
    def __init__(self, points=[]):
        self.points = []
        self.distances = []
        self.length = 0

        for p in points:
            self.add_point(*p)

    def reverse(self):
        path = Path()
        for p in self.points[::-1]:
            path.add_point(p[0], p[1])
        return path

    def add_point(self, x, y):
        if len(self.points) > 0:
            prev = self.points[-1]
            d = self.distances[-1]
            dist = d + math.hypot(x - prev[0], y - prev[1])
        else:
            dist = 0

        self.points.append((x, y))
        self.distances.append(dist)
        self.length = self.distances[-1]

    def at(self, d):
        i = bisect(self.distances, d)

        if i == 0:
            return self.points[0]
        if i == len(self.points):
            return self.points[-1]
            
        t = (d - self.distances[i - 1]) / (self.distances[i] - self.distances[i - 1])
        x1, y1 = self.points[i - 1]
        x2, y2 = self.points[i]

        return (
            (1 - t) * x1 + t * x2,
            (1 - t) * y1 + t * y2)

def create_path(*points):
    return Path(points)


def create_hline(width, y=0):
    return create_path(
            (0.5 * width, y),
            (-0.5 * width, y))


def create_corner(width):
    return create_path(
            (0, 0.5 * width),
            (0, 0),
            (0.5 * width, 0))


def create_sinus(width, amplitude):
    points = []

    for t in np.linspace(-1, 1):
        x = t * width * 0.5
        y = amplitude * np.sin(t * math.pi)
        points.append((x, y))

    return create_path(*points)


def simulate_path(path, t_max, offset_max, speed_avg, speed_sigma):
    d = 0
    dataset = []

    for t in range(int(t_max)):
        if t == 0 or d > path.length:
            if t == 0:
                d = random.uniform(0, path.length)
            else:
                d = 0

            dataset.append([])
            speed = random.gauss(speed_avg, speed_sigma)
            offset = np.array([-999, -999])

            while np.linalg.norm(offset) > offset_max:
                offset = np.random.uniform(-1, 1, size=2) * offset_max

        x, y = path.at(d) + offset
        dataset[-1].append((x, y, t))
        d += speed

    return dataset
