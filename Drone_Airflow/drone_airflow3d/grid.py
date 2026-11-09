from dataclasses import dataclass
import numpy as np


def plane(axis, index):
    s = [slice(None)] * 3
    s[axis] = index
    return tuple(s)


@dataclass
class Grid:
    shape: tuple
    bounds: tuple

    def __post_init__(self):
        self.shape = tuple(int(n) for n in self.shape)
        self.bounds = np.asarray(self.bounds, float)
        if len(self.shape) != 3 or min(self.shape) < 3:
            raise ValueError('Three grid dimensions >= 3 are required.')
        if self.bounds.shape != (3, 2) or not np.isfinite(self.bounds).all():
            raise ValueError('bounds must be three finite [lower, upper] pairs.')
        self.h = (self.bounds[:, 1] - self.bounds[:, 0]) / self.shape
        if min(self.h) <= 0:
            raise ValueError('Bounds must increase.')
        self.volume = float(np.prod(self.h))
        self.axes = tuple(self.bounds[a, 0] + (np.arange(n)+.5)*self.h[a]
                          for a, n in enumerate(self.shape))

    def coordinates(self, component=None):
        axes = list(self.axes)
        if component is not None:
            a = component
            axes[a] = self.bounds[a, 0] + np.arange(self.shape[a]+1)*self.h[a]
        return np.meshgrid(*axes, indexing='ij')

    def faces(self):
        result = []
        for a in range(3):
            shape = list(self.shape); shape[a] += 1
            result.append(np.zeros(shape))
        return result

    def to_faces(self, q, a):
        """Linear centre-to-face interpolation; constant extrapolation outside."""
        pad = [(0, 0)]*3; pad[a] = (1, 1)
        z = np.pad(q, pad, mode='edge')
        return .5*(z[plane(a, slice(None, -1))]+z[plane(a, slice(1, None))])


def cell_velocity(vel):
    return [.5*(v[plane(a, slice(None, -1))]+v[plane(a, slice(1, None))])
            for a, v in enumerate(vel)]


def divergence(grid, vel):
    return sum(np.diff(v, axis=a)/grid.h[a] for a, v in enumerate(vel))

