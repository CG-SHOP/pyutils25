import pytest

from cgshop2025_pyutils.geometry import (
    ConstrainedTriangulation,
    FieldNumber,
    Point,
    Polygon,
    Segment,
    VerificationGeometryHelper,
    compute_convex_hull,
    intersection_point,
)


def test_number():
    assert FieldNumber("1/2") == FieldNumber(1) / FieldNumber(2)
    assert FieldNumber("1") == FieldNumber(1)
    assert FieldNumber(FieldNumber(1 / 2).exact()) == FieldNumber(1) / FieldNumber(2)
    assert FieldNumber(1 / 2).exact() == "1/2"
    assert FieldNumber("-1/2") == FieldNumber(-1) / FieldNumber(2)
    assert FieldNumber(" - 1 / 2  ") == FieldNumber(-1) / FieldNumber(2)
    assert FieldNumber("-1").exact() == "-1"
    assert FieldNumber("0000/1") == FieldNumber(0)
    long_num = "1" + 10_000_000 * "0"
    long_den = "2" + 10_000_000 * "0"
    long_str = long_num + " / " + long_den
    assert FieldNumber("1/2") == FieldNumber(long_str)


def test_invalid_numbers():
    with pytest.raises(RuntimeError):
        FieldNumber("1/00000")
    with pytest.raises(RuntimeError):
        FieldNumber("--0")
    with pytest.raises(RuntimeError):
        FieldNumber("1/--1")
    with pytest.raises(RuntimeError):
        FieldNumber("123 lala")
    with pytest.raises(RuntimeError):
        FieldNumber("123 🤷")
    with pytest.raises(RuntimeError):
        FieldNumber("0/0")


# Test the basic functionality of Point class
def test_point_creation():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    assert p1.x() == FieldNumber(0)
    assert p1.y() == FieldNumber(0)
    assert p2.x() == FieldNumber(1)
    assert p2.y() == FieldNumber(1)
    assert str(p1) == "(0, 0)"
    assert str(p2) == "(1, 1)"
    assert p1 != p2


def test_negative_strings():
    for i in range(100):
        _number = FieldNumber(f"-{10**i}")
        assert _number == FieldNumber(-1) * FieldNumber(f"{10**i}")


def test_point_operations():
    p = Point(1, 1)
    assert p + p == Point(2, 2)
    assert p.scale(FieldNumber(2)) == Point(2, 2)
    assert p - p == Point(0, 0)


# Test the creation and operation of segments
def test_segment_creation():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    segment = Segment(p1, p2)
    assert segment.source() == p1
    assert segment.target() == p2
    assert segment.squared_length() == FieldNumber(2)


# Test computing the convex hull
def test_compute_convex_hull():
    points = [Point(0, 0), Point(1, 1), Point(1, 0), Point(0, 1)]
    hull_indices = compute_convex_hull(points)

    # The convex hull should contain the four corners in some order
    assert set(hull_indices) == {0, 1, 2, 3}


# Test the VerificationGeometryHelper class
def test_verification_geometry_helper():
    helper = VerificationGeometryHelper()

    # Add points to the helper
    idx1 = helper.add_point(Point(0, 0))
    idx2 = helper.add_point(Point(1, 1))
    idx3 = helper.add_point(Point(1, 0))

    # Check the number of points
    assert helper.get_num_points() == 3

    # Add a segment between two points
    helper.add_segment(idx1, idx2)
    helper.add_segment(idx2, idx3)
    assert helper.search_for_bad_edges() is not None, "Triangle isn't closed yet"
    helper.add_segment(idx3, idx1)

    # Ensure no bad edges (same face on both sides)
    assert helper.search_for_bad_edges() is None

    # Ensure no isolated points after adding segments
    isolated_points = helper.search_for_isolated_points()
    assert len(isolated_points) == 0


def test_intersection_point():
    seg1 = Segment(Point(0, 0), Point(1, 1))
    seg2 = Segment(Point(0, 1), Point(1, 0))

    assert seg1.does_intersect(seg2)

    intersection = intersection_point(seg1, seg2)
    assert intersection is not None
    assert intersection.x() == FieldNumber(0.5)
    assert intersection.y() == FieldNumber(0.5)


# Test finding non-triangular faces
def test_non_triangular_faces():
    helper = VerificationGeometryHelper()

    # Add points and segments that form a square
    idx1 = helper.add_point(Point(0, 0))
    idx2 = helper.add_point(Point(1, 0))
    idx3 = helper.add_point(Point(1, 1))
    idx4 = helper.add_point(Point(0, 1))

    helper.add_segment(idx1, idx2)
    helper.add_segment(idx2, idx3)
    helper.add_segment(idx3, idx4)
    helper.add_segment(idx4, idx1)

    # There should be one non-triangular face (the square)
    assert helper.search_for_non_triangular_faces() is not None


# Test the ConstrainedTriangulation class
def test_constrained_triangulation():
    triangulation = ConstrainedTriangulation()

    # Add points to the triangulation
    idx1 = triangulation.add_point(Point(0, 0))
    idx2 = triangulation.add_point(Point(1, 0))
    idx3 = triangulation.add_point(Point(0, 1))

    # Add boundary and segments
    triangulation.add_boundary([idx1, idx2, idx3])

    # Ensure that the triangulation edges contain the right segments
    edges = triangulation.get_triangulation_edges()
    assert len(edges) > 0  # At least 1 triangle edge should exist


# Test the FieldNumber class and its arithmetic
def test_field_number_operations():
    num1 = FieldNumber(1)
    num2 = FieldNumber(2)

    assert float(num1) == 1.0
    assert float(num2) == 2.0

    assert num1 + num2 == FieldNumber(3)
    assert num2 - num1 == FieldNumber(1)
    assert num1 * num2 == FieldNumber(2)
    assert num2 / num1 == FieldNumber(2)

    assert num1 < num2
    assert num2 > num1


# Test Polygon operations
def test_polygon_operations():
    points = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
    polygon = Polygon(points)

    assert polygon.is_simple()
    assert polygon.area() > FieldNumber(0)
    assert polygon.contains(Point(0.5, 0.5))
    assert not polygon.contains(Point(2, 2))

    # Verify points on the boundary
    assert polygon.on_boundary(Point(0, 0))
    assert not polygon.on_boundary(Point(0.5, 0.5))
