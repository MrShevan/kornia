from asyncio import base_tasks

import pytest
import torch
from torch.autograd import gradcheck

import kornia.testing as utils  # test utils
from kornia.geometry.line import ParametrizedLine, fit_line
from kornia.testing import assert_close


class TestParametrizedLine:
    def test_smoke(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0], device=device, dtype=dtype)
        d0 = torch.tensor([1.0, 0.0], device=device, dtype=dtype)
        l0 = ParametrizedLine(p0, d0)
        assert_close(l0.origin, p0)
        assert_close(l0.direction, d0)
        assert_close(l0.dim(), 2)

    def test_through(self, device, dtype):
        p0 = torch.tensor([-1.0, -1.0], device=device, dtype=dtype)
        p1 = torch.tensor([1.0, 1.0], device=device, dtype=dtype)
        l1 = ParametrizedLine.through(p0, p1)
        direction_expected = torch.tensor(
            [0.7071, 0.7071], device=device, dtype=dtype)
        assert_close(l1.origin, p0)
        assert_close(l1.direction, direction_expected)

    def test_point_at(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0], device=device, dtype=dtype)
        p1 = torch.tensor([1.0, 0.0], device=device, dtype=dtype)
        l1 = ParametrizedLine.through(p0, p1)
        assert_close(l1.point_at(0.0),
            torch.tensor([0.0, 0.0], device=device, dtype=dtype))
        assert_close(l1.point_at(0.5),
            torch.tensor([0.5, 0.0], device=device, dtype=dtype))
        assert_close(l1.point_at(1.0),
            torch.tensor([1.0, 0.0], device=device, dtype=dtype))

    def test_projection1(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0], device=device, dtype=dtype)
        p1 = torch.tensor([1.0, 0.0], device=device, dtype=dtype)
        p2 = torch.tensor([0.5, 0.5], device=device, dtype=dtype)
        p3_expected = torch.tensor([0.5, 0.0], device=device, dtype=dtype)
        l1 = ParametrizedLine.through(p0, p1)
        p3 = l1.projection(p2)
        assert_close(p3, p3_expected)

    def test_projection2(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0], device=device, dtype=dtype)
        p1 = torch.tensor([0.0, 1.0], device=device, dtype=dtype)
        p2 = torch.tensor([0.5, 0.5], device=device, dtype=dtype)
        p3_expected = torch.tensor([0.0, 0.5], device=device, dtype=dtype)
        l1 = ParametrizedLine.through(p0, p1)
        p3 = l1.projection(p2)
        assert_close(p3, p3_expected)

    def test_gradcheck(self, device):
        #pts = torch.rand(2, 3, 2, device=device, requires_grad=True, dtype=torch.float64)
        #lines = torch.rand(2, 3, 3, device=device, requires_grad=True, dtype=torch.float64)
        #assert gradcheck(kgl.point_line_distance, (pts, lines), raise_exception=True)
        pass

class TestFitLine:
    @pytest.mark.parametrize("B", (1, 2))
    @pytest.mark.parametrize("D", (2, 3, 4))
    def test_smoke(self, device, dtype, B, D):
        N: int = 10  # num points
        points = torch.ones(B, N, D, device=device, dtype=dtype)
        dir_est = fit_line(points)
        assert dir_est.shape == (B, D)

    def test_fit_line2(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0], device=device, dtype=dtype)
        p1 = torch.tensor([1.0, 1.0], device=device, dtype=dtype)

        l1 = ParametrizedLine.through(p0, p1)
        num_points: int = 10

        pts = []
        for t in torch.linspace(-10, 10, num_points):
            p2 = l1.point_at(t)
            pts.append(p2)
        pts = torch.stack(pts)

        dir_est = fit_line(pts)
        dir_exp = torch.tensor([0.7071, 0.7071], device=device, dtype=dtype)
        # NOTE: result differs with the sign between cpu/cuda
        assert_close(dir_est.dot(dir_exp), 0.)

    @pytest.mark.skip(reason="investigate for another solution")
    def test_fit_line3(self, device, dtype):
        p0 = torch.tensor([0.0, 0.0, 0.0], device=device, dtype=dtype)
        p1 = torch.tensor([1.0, 1.0, 1.0], device=device, dtype=dtype)

        l1 = ParametrizedLine.through(p0, p1)
        num_points: int = 10

        pts = []
        for t in torch.linspace(-10, 10, num_points):
            p2 = l1.point_at(t)
            pts.append(p2)
        pts = torch.stack(pts)

        dir_est = fit_line(pts[None])
        dir_exp = torch.tensor([0.7071, 0.7071, 0.7071], device=device, dtype=dtype)
        # NOTE: result differs with the sign between cpu/cuda
        assert_close(dir_est.dot(dir_exp), 0.)

    def test_gradcheck(self, device):
        pts = torch.rand(2, 3, 2, device=device, dtype=torch.float64)
        weights = torch.ones(2, 3, device=device, dtype=torch.float64, requires_grad=True)
        assert gradcheck(fit_line, (pts, weights), raise_exception=True)
