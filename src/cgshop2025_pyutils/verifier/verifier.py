from typing import List

from pydantic import BaseModel

from cgshop2025_pyutils.data_schemas.instance import Cgshop2025Instance
from cgshop2025_pyutils.data_schemas.solution import Cgshop2025Solution
from cgshop2025_pyutils.geometry import Point, VerificationGeometryHelper, FieldNumber


class VerificationResult(BaseModel):
    num_obtuse_triangles: int
    num_steiner_points: int
    errors: List[str]


def verify(
    instance: Cgshop2025Instance, solution: Cgshop2025Solution
) -> VerificationResult:
    geom_helper = VerificationGeometryHelper()
    print("NEW CODE!")
    # Combine instance and solution points into one loop to simplify the logic
    all_points = [Point(x, y) for x, y in zip(instance.points_x, instance.points_y)]
    all_points.extend(
        Point(FieldNumber(x), FieldNumber(y))
        for x, y in zip(solution.steiner_points_x, solution.steiner_points_y)
    )

    # Add points to the geometry helper
    for point in all_points:
        geom_helper.add_point(point)

    # Add boundary segments to the geometry helper
    for i, j in zip(instance.region_boundary[:-1], instance.region_boundary[1:]):
        geom_helper.add_segment(i, j)
    if len(instance.region_boundary) > 2:
        geom_helper.add_segment(
            instance.region_boundary[-1], instance.region_boundary[0]
        )

    # Add constraint segments to the geometry helper
    for constraint in instance.additional_constraints:
        geom_helper.add_segment(constraint[0], constraint[1])
        assert len(constraint) == 2

    # Add segments to the geometry helper
    for edge in solution.edges:
        geom_helper.add_segment(edge[0], edge[1])

    # Initialize an error list to collect all issues found during verification
    errors = []

    # Check for non-triangular faces
    non_triang = geom_helper.search_for_non_triangular_faces()
    if non_triang:
        errors.append(f"Non-triangular face found at {non_triang}")

    # Check for bad edges (edges with the same face on both sides)
    bad_edges = geom_helper.search_for_bad_edges()
    if bad_edges:
        errors.append(f"Edges with the same face on both sides found at {bad_edges}")

    # Check for faces with holes
    holes = geom_helper.search_for_faces_with_holes()
    if holes:
        errors.append(f"Faces with holes found at {holes}")

    # Check for isolated points
    isolated_points = geom_helper.search_for_isolated_points()
    if isolated_points:
        errors.append(f"Isolated points found at {[str(p) for p in isolated_points]}")

    # Check the number of steiner points for correctness
    num_steiner_points = geom_helper.get_num_points() - len(instance.points_x)
    if num_steiner_points != len(solution.steiner_points_x):
        errors.append(
            f"Expected {num_steiner_points} Steiner points, but found {len(solution.steiner_points_x)}"
        )

    # If any errors were detected, return a result with those errors
    if errors:
        return VerificationResult(
            num_obtuse_triangles=-1, num_steiner_points=-1, errors=errors
        )

    # No errors, return the results of obtuse triangles and steiner points
    return VerificationResult(
        num_obtuse_triangles=geom_helper.count_obtuse_triangles(),
        num_steiner_points=num_steiner_points,
        errors=[],
    )
