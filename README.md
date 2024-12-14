# CG:SHOP - Official pyutils25 for the 2025 Challenge on Non-Obtuse Triangulation

Utilities for verifying solutions of the CG:SHOP 2025 Competition. Feel free to
use the code, but it is optimized for _exact_ verification not for sampling or
other purposes.

## Installation

You can install the utilities via pip:

```bash
pip install cgshop2025-pyutils
```

Alternatively, you can install this package via source:

```bash
pip install --verbose .
```

You can also install it without the need to clone the repository:

```bash
pip install --verbose git+https://github.com/CG-SHOP/pyutils25
```

During the installation, CGAL and other dependencies will be downloaded and
compiled. This can take a while but should happen mostly automatic. You need to
have a C++ compiler (and the Python development environment) installed. Most
systems will come with all dependencies preinstalled. Otherwise, you can for
example install them on Ubuntu with the following command

```bash
sudo apt install build-essential python3-dev
```

You can test the installation with

```bash
pytest -s tests
```

> Please check for updates of the utils frequently as we are still working on
> them.

## Usage

You can use the utilities to verify solutions of the CG:SHOP 2025 Competition.

1. **Instance Database**: Utilize the instance database to iterate over all
   instances in the benchmark effortlessly.
2. **Naive Solver**: Compute a solution for each instance using the naive
   solver, which performs a constrained Delaunay triangulation without using
   Steiner points.
3. **ZipWriter**: Use the ZipWriter to create a valid submission file easily.
4. **SolutionChecker**: Verify the validity of the solution using the
   SolutionChecker.

```python
from pathlib import Path

from cgshop2025_pyutils import (
    DelaunayBasedSolver,
    InstanceDatabase,
    ZipSolutionIterator,
    ZipWriter,
    verify,
)

# Load the instances from the example_instances folder. Instead of referring to the folder,
# you can also give a path to a zip file.
idb = InstanceDatabase("example_instances/")

# If the solution zip file already exists, delete it
if Path("example_solutions.zip").exists():
    Path("example_solutions.zip").unlink()

# Compute solutions for all instances using the provided (naive) solver
solutions = []
for instance in idb:
    solver = DelaunayBasedSolver(instance)
    solution = solver.solve()
    solutions.append(solution)

# Write the solutions to a new zip file
with ZipWriter("example_solutions.zip") as zw:
    for solution in solutions:
        zw.add_solution(solution)

# Verify the solutions
for solution in ZipSolutionIterator("example_solutions.zip"):
    instance = idb[solution.instance_uid]
    result = verify(instance, solution)
    print(f"{solution.instance_uid}: {result}")
    assert not result.errors, "Expect no errors."
```

## Additional Features

The utils also expose a number of additional features that may be useful for
developing your own solvers, as you will need to use exact arithmetic as
provided by CGAL. However, if you want to use Python, we recommend to actually
just fork this repository and adapt/extend the provided code to your needs.
Check out the test cases (in `./tests/`) for some examples. We may provide some
further utilities in the near future, but for now, you can use the following
classes:

#### `FieldNumber`

Represents an exact number (rational or floating-point) for precise arithmetic
operations. If you are not sure about exact arithmetic, this single class will
save you a lot of time. Just use it for all your arithmetic operations and you
will be fine. For extracting the exact representation of the number, use the
`exact()` method, which returns a string that is an exact representation and
accepted by our verifier.

- `FieldNumber(value: int | float | str)`: Initialize with an integer, float, or
  string.
- `exact() -> str`: Returns the exact representation of the number as a string.
- Supports `+`, `-`, `*`, `/` arithmetic and comparison operators (`<`, `>`,
  `==`, `!=`).

#### `Point`

Represents a 2D point with exact coordinates.

- `Point(x: FieldNumber, y: FieldNumber)`: Initialize a point with two
  `FieldNumber` coordinates.
- `x() -> FieldNumber`: Returns the x-coordinate.
- `y() -> FieldNumber`: Returns the y-coordinate.
- `scale(factor: FieldNumber) -> Point`: Returns a new point scaled by the given
  factor.
- Supports `+`, `-` operators for point arithmetic.

#### `Segment`

Represents a 2D segment between two `Point` objects.

- `Segment(source: Point, target: Point)`: Initialize a segment with source and
  target points.
- `source() -> Point`: Returns the source point of the segment.
- `target() -> Point`: Returns the target point of the segment.
- `squared_length() -> FieldNumber`: Returns the squared length of the segment.
- `does_intersect(other: Segment) -> bool`: Checks if the segment intersects
  with another segment.

#### `Polygon`

Represents a simple polygon.

- `Polygon(points: List[Point])`: Initialize a polygon with a list of points.
- `is_simple() -> bool`: Checks if the polygon is simple (no
  self-intersections).
- `contains(point: Point) -> bool`: Checks if the polygon contains the given
  point.
- `on_boundary(point: Point) -> bool`: Checks if the point is on the polygon
  boundary.
- `area() -> FieldNumber`: Returns the area of the polygon.

#### `VerificationGeometryHelper`

Verifies geometric structures, detecting non-triangular faces, bad edges, and
isolated points.

- `VerificationGeometryHelper()`: Initialize the geometry helper.
- `add_point(point: Point) -> int`: Adds a point to the geometry and returns its
  index.
- `add_segment(index1: int, index2: int)`: Adds a segment between two points by
  their indices.
- `get_num_points() -> int`: Returns the number of points in the geometry.
- `search_for_non_triangular_faces() -> Optional[Point]`: Searches for any
  non-triangular faces.
- `search_for_bad_edges() -> Optional[Segment]`: Searches for edges with the
  same face on both sides.
- `search_for_isolated_points() -> List[Point]`: Returns a list of isolated
  points.
- `count_obtuse_triangles() -> int`: Counts the number of obtuse triangles in
  the geometry.

#### `ConstrainedTriangulation`

Handles 2D constrained Delaunay triangulation.

- `ConstrainedTriangulation()`: Initialize the triangulation.
- `add_point(point: Point) -> int`: Adds a point and returns its index.
- `add_boundary(indices: List[int])`: Adds a polygon boundary defined by the
  point indices.
- `add_segment(index1: int, index2: int)`: Adds a segment between two points by
  their indices.
- `get_triangulation_edges() -> List[Tuple[int, int]]`: Returns a list of edges
  as tuples of point indices.

#### `compute_convex_hull`

Computes the convex hull of a set of points.

- `compute_convex_hull(points: List[Point]) -> List[int]`: Returns the indices
  of points on the convex hull.

#### `intersection_point`

Finds the intersection point of two segments, if they intersect.

- `intersection_point(seg1: Segment, seg2: Segment) -> Optional[Point]`: Returns
  the intersection point or `None`.

## License

Our code is licensed under the MIT License. However, the code depends on CGAL,
which can have implications for non-academic users. Please check the CGAL
license for more information.

## Reporting Issues

If you encounter any issues, please report them in the issue tracker. We will
try to fix them as soon as possible.

## Changelog

- `0.0.9`: Better bounds checking for segment endpoint indices in `verify`
- `0.0.8`: Adding file information to exceptions of `ZipSolutionIterator`
- `0.0.7`: Fix for only accepting `.solution.json` (there was a `,` missing)
- `0.0.6`: Fix for CGAL 6
- `0.0.5`: Improved error messages for isolated points. Only accepting
  `.solution.json` as solution file extension.
- `0.0.4`: Fixed bug with negative numbers in FieldNumber with string input
- `0.0.3`: Allows negative Steiner points and ensure coordinates are converted
  to FieldNumber before Point construction
