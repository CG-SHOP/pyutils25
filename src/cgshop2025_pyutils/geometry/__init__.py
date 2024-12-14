"""
This module provides geometric utilities based on CGAL for computational geometry tasks. It includes classes for manipulating points, segments, polygons, and tools for geometric verification and triangulation, leveraging CGAL's exact arithmetic.

#### `FieldNumber`
Represents an exact number (rational or floating-point) for precise arithmetic operations.

- `FieldNumber(value: int | float | str)`: Initialize with an integer, float, or string.
- `exact() -> str`: Returns the exact representation of the number as a string.
- Supports `+`, `-`, `*`, `/` arithmetic and comparison operators (`<`, `>`, `==`, `!=`).

#### `Point`
Represents a 2D point with exact coordinates.

- `Point(x: FieldNumber, y: FieldNumber)`: Initialize a point with two `FieldNumber` coordinates.
- `x() -> FieldNumber`: Returns the x-coordinate.
- `y() -> FieldNumber`: Returns the y-coordinate.
- `scale(factor: FieldNumber) -> Point`: Returns a new point scaled by the given factor.
- Supports `+`, `-` operators for point arithmetic.

#### `Segment`
Represents a 2D segment between two `Point` objects.

- `Segment(source: Point, target: Point)`: Initialize a segment with source and target points.
- `source() -> Point`: Returns the source point of the segment.
- `target() -> Point`: Returns the target point of the segment.
- `squared_length() -> FieldNumber`: Returns the squared length of the segment.
- `does_intersect(other: Segment) -> bool`: Checks if the segment intersects with another segment.

#### `Polygon`
Represents a simple polygon.

- `Polygon(points: List[Point])`: Initialize a polygon with a list of points.
- `is_simple() -> bool`: Checks if the polygon is simple (no self-intersections).
- `contains(point: Point) -> bool`: Checks if the polygon contains the given point.
- `on_boundary(point: Point) -> bool`: Checks if the point is on the polygon boundary.
- `area() -> FieldNumber`: Returns the area of the polygon.

#### `VerificationGeometryHelper`
Verifies geometric structures, detecting non-triangular faces, bad edges, and isolated points.

- `VerificationGeometryHelper()`: Initialize the geometry helper.
- `add_point(point: Point) -> int`: Adds a point to the geometry and returns its index.
- `add_segment(index1: int, index2: int)`: Adds a segment between two points by their indices.
- `get_num_points() -> int`: Returns the number of points in the geometry.
- `search_for_non_triangular_faces() -> Optional[Point]`: Searches for any non-triangular faces.
- `search_for_bad_edges() -> Optional[Segment]`: Searches for edges with the same face on both sides.
- `search_for_isolated_points() -> List[Point]`: Returns a list of isolated points.
- `count_obtuse_triangles() -> int`: Counts the number of obtuse triangles in the geometry.

#### `ConstrainedTriangulation`
Handles 2D constrained Delaunay triangulation.

- `ConstrainedTriangulation()`: Initialize the triangulation.
- `add_point(point: Point) -> int`: Adds a point and returns its index.
- `add_boundary(indices: List[int])`: Adds a polygon boundary defined by the point indices.
- `add_segment(index1: int, index2: int)`: Adds a segment between two points by their indices.
- `get_triangulation_edges() -> List[Tuple[int, int]]`: Returns a list of edges as tuples of point indices.

#### `compute_convex_hull`
Computes the convex hull of a set of points.

- `compute_convex_hull(points: List[Point]) -> List[int]`: Returns the indices of points on the convex hull.

#### `intersection_point`
Finds the intersection point of two segments, if they intersect.

- `intersection_point(seg1: Segment, seg2: Segment) -> Optional[Point]`: Returns the intersection point or `None`.

#### `points_contain_duplicates`
Check the list of exact points for duplicate points.
"""

from ._bindings import (
    ConstrainedTriangulation,
    FieldNumber,
    Point,
    Polygon,
    Segment,
    VerificationGeometryHelper,
    compute_convex_hull,
    intersection_point,
    points_contain_duplicates,
    squared_distance,
)

__all__ = [
    "FieldNumber",
    "Point",
    "Segment",
    "Polygon",
    "compute_convex_hull",
    "squared_distance",
    "VerificationGeometryHelper",
    "ConstrainedTriangulation",
    "intersection_point",
    "points_contain_duplicates",
]
