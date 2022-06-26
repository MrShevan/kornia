# kornia.geometry.line module inspired by Eigen::geometry::ParametrizedLine
from typing import Optional, Union
from kornia.geometry.linalg import squared_norm

import torch
from kornia.core import Tensor, Module, Parameter, normalize

from kornia.testing import KORNIA_CHECK, KORNIA_CHECK_IS_TENSOR, KORNIA_CHECK_SHAPE

__all__ = ["ParametrizedLine", "fit_line",]

class ParametrizedLine(Module):
    """Class that describes a parametrize line.

    A parametrized line is defined by an origin point :math:`o` and a unit
    direction vector :math:`d` such that the line corresponds to the set

    .. math::

        l(t) = o + t * d
    """
    def __init__(self, origin: Tensor, direction: Tensor) -> None:
        """Initializes a parametrized line of direction and origin.

        Args:
            origin: the origin point of the line of any dimension.
            direction: the normalized vector direction of any dimension.

        Example:
            >>> o = tensor([0.0, 0.0])
            >>> d = tensor([1.0, 1.0])
            >>> l = ParametrizedLine(o, d)
        """
        super().__init__()
        self._origin = Parameter(origin)
        self._direction = Parameter(direction)

    def __str__(self) -> str:
        return f"Origin: {self.origin}\nDirection: {self.direction}"

    def __repr__(self) -> str:
        return str(self)

    @property
    def origin(self) -> Tensor:
        """Return the line origin point."""
        return self._origin

    @property
    def direction(self) -> Tensor:
        """Return the line direction vector."""
        return self._direction

    def dim(self) -> int:
        """Return the dimension in the line holds."""
        return len(self.direction)

    @classmethod
    def through(cls, p0, p1) -> "ParametrizedLine":
        """Constructs a parametrized line going from a point :math:`p0` to :math:`p1`.

        Args:
            p0: tensor with first point :math:`(B, D)`.
            p1: tensor with second point :math:`(B, D)`.

        Example:
            >>> p0 = tensor([0.0, 0.0])
            >>> p1 = tensor([1.0, 1.0])
            >>> l = ParametrizedLine.through(p0, p1)
        """
        return ParametrizedLine(p0, normalize((p1 - p0), p=2, dim=-1))

    @classmethod
    def from_hyperplane(cls, plane: "Hyperplane") -> "ParametrizedLine":
        raise NotImplementedError

    def point_at(self, t: Union[float, Tensor]) -> Tensor:
        """The point at :math:`t` along this line.

        Args:
            t: step along the line.

        Return:
            tensor with the point.

        Example:
            >>> p0 = tensor([0.0, 0.0])
            >>> p1 = tensor([1.0, 1.0])
            >>> l = ParametrizedLine.through(p0, p1)
            >>> p2 = l.point_at(0.1)
        """
        return self.origin + self.direction * t

    def projection(self, point: Tensor) -> Tensor:
        """Return the projection of a point onto the line.

        Args:
            point: the point to be projected.
        
        """
        return self.origin + (self.direction @ (point - self.origin)) * self.direction

    def squared_distance(self, point: Tensor) -> Tensor:
        """Return the squared distance of a point to its projection onte the line.
        
        Args:
            point: the point to calculate the distance onto the line.
        """
        diff: Tensor = point - self.origin
        return squared_norm(torch.inner(diff - self.direction, diff) * self.direction)
        #return squared_norm(((diff - self.direction) @ diff) * self.direction)

    def distance(self, point: Tensor) -> Tensor:
        """Return the distance of a point to its projections onto the line.
        
        Args:
            point: the point to calculate hte distance into the line.
        """
        return self.squared_distance(point).sqrt()


    # TODO(edgar) implement the following:
    # - intersection
    # - intersection_parameter
    # - intersection_point


def fit_line(points: Tensor, weights: Optional[Tensor] = None) -> Tensor:
    """Fit a line from a set of points.

    Args:
        points: tensor containing a batch of sets of n-dimensional points. The  expected
            shape of the tensor is :math:`(B,N,D)`.
        weights: weights to use to solve the equations system. The  expected
            shape of the tensor is :math:`(B,N)`.

    Return:
        A tensor containing the direction of the fited line of shape :math:`(B,D)`.

    Example:
        >>> points = torch.rand(2, 10, 3)
        >>> weights = torch.ones(2, 10)
        >>> direction = fit_line(points, weights)
        >>> direction.shape
        torch.Size([2,3])
    """
    KORNIA_CHECK_IS_TENSOR(points, "points must be a tensor")
    KORNIA_CHECK_SHAPE(points, ["B", "N", "D"])

    points_mean = points.mean(-2, True)
    A = points - points_mean

    if weights is not None:
        KORNIA_CHECK_IS_TENSOR(weights, "weights must be a tensor")
        KORNIA_CHECK_SHAPE(weights, ["B", "N"])
        KORNIA_CHECK(points.shape[:2] == weights.shape[:2])
        A = A.transpose(-2,-1) @ torch.diag_embed(weights) @ A
    else:
        A = A.transpose(-2,-1) @ A

    # NOTE: not optimal for 2d points, but for now works for other dimensions
    _, _, V = torch.linalg.svd(A)

    # the first left eigenvector is the direction on the fited line
    L = V[..., 0]
    return L  # Bx2
