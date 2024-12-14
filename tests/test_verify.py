import copy
import random
import uuid

from cgshop2025_pyutils import VerificationResult, verify
from cgshop2025_pyutils.data_schemas.instance import Cgshop2025Instance
from cgshop2025_pyutils.data_schemas.solution import Cgshop2025Solution
from cgshop2025_pyutils.geometry import Point, compute_convex_hull
from cgshop2025_pyutils.naive_algorithm import DelaunayBasedSolver


def test_verify():
    instance = Cgshop2025Instance(
        instance_uid="example",
        num_points=8,
        points_x=[0, 1, 2, 3, 4, 1, 3, 1],
        points_y=[0, 3, 2, 6, 2, 1, 2, 2],
        region_boundary=[0, 1, 2, 3, 4][::-1],
        num_constraints=1,
        additional_constraints=[[5, 6]],
    )

    solver = DelaunayBasedSolver(instance)
    solution = solver.solve()
    result = verify(instance, solution)
    assert not result.errors
    assert result.num_obtuse_triangles == 5
    assert result.num_steiner_points == 0


SEEDS = [
    3059623771,
    912801942,
    2417586875,
    4024461812,
    3551918909,
    3475446657,
    2075485937,
    3679785335,
]


def test_negative_steiner_points():
    solution = Cgshop2025Solution(
        instance_uid="test_id",
        steiner_points_x=[-1, "-1", "-1/2"],
        steiner_points_y=[-1, "-1", "2/-1"],
        edges=[[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
    )


def generate_random_point_sets(seed, num_sets=10, num_points=500):
    rng = random.Random(seed)
    for _ in range(num_sets):
        yield {
            (
                int(round(rng.uniform(0, 100000000))),
                int(round(rng.uniform(0, 100000000))),
            )
            for _ in range(num_points)
        }


def instance_from_point_set(plist, instance_uid):
    chull_indices: list[int] = compute_convex_hull(plist)
    return Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=len(plist),
        num_constraints=0,
        region_boundary=chull_indices,
        additional_constraints=[],
        points_x=[p[0] for p in plist],
        points_y=[p[1] for p in plist],
    )


def generate_random_instances(seed, num_instances=10, num_points=500):
    for ps in generate_random_point_sets(seed, num_instances, num_points):
        plist = [Point(x, y) for x, y in ps]
        yield instance_from_point_set(plist, f"random_{seed}_{uuid.uuid4()}")


def break_solution_delete_edge(
    instance: Cgshop2025Instance, solution: Cgshop2025Solution
):
    k = len(instance.region_boundary)
    boundary = {
        (instance.region_boundary[i % k], instance.region_boundary[(i + 1) % k])
        for i in range(k)
    }
    boundary.update({(b, a) for a, b in boundary})
    while True:
        i = random.randint(0, len(solution.edges) - 1)
        e = tuple(solution.edges[i])
        if e not in boundary:
            del solution.edges[i]
            return


def verifier_on_random_instance(instance: Cgshop2025Instance):
    solution = DelaunayBasedSolver(instance).solve()
    result: VerificationResult = verify(instance, solution)
    assert result.errors == []
    assert result.num_steiner_points == 0

    broken_solution1 = copy.deepcopy(solution)
    break_solution_delete_edge(instance, broken_solution1)
    result: VerificationResult = verify(instance, broken_solution1)
    assert result.errors != []


def test_verify_random_instances():
    for seed in SEEDS:
        for instance in generate_random_instances(seed):
            verifier_on_random_instance(instance)


def test_verify_correct_solution_extra_points():
    points = [(192, 512), (384, 512), (320, 560), (272, 576), (192, 576)]
    instance = instance_from_point_set(
        [Point(x, y) for x, y in points], "two_extra_points"
    )
    solution = Cgshop2025Solution(
        instance_uid=instance.instance_uid,
        steiner_points_x=["272/1", 320],
        steiner_points_y=[512, "1024/2"],
        edges=[
            [0, 5],
            [5, 6],
            [6, 1],
            [1, 2],
            [2, 3],
            [3, 4],
            [4, 0],
            [5, 3],
            [5, 2],
            [2, 6],
            [5, 4],
        ],
        meta={"constructed_by": "the hand"},
    )
    result = verify(instance, solution)
    assert not result.errors
    assert result.num_steiner_points == 2
    assert result.num_obtuse_triangles == 0


def test_verify_point_outside():
    # Test Case 1 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - point outside of the container => should be counted, irrelevant
    # - edge crossing through a steiner point => should be split, irrelevant
    # expected: pass in both modes
    instance_uid = "Steiner point outside region_boundary / convex hull ([5,5])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2, 5],
        steiner_points_y=[2, 5],
        edges=[
            [0, 1],
            [1, 2],
            [2, 3],
            [3, 0],
            [2, 5],
            [3, 5],
            [1, 5],
            [0, 2],
            [4, 3],
            [1, 4],
        ],
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 2
    assert result.num_steiner_points == 2


def test_verify_missing_edge_and_point():
    # Test Case 2 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - point outside of the container => should be counted, irrelevant
    # - missing boundary edge => auto-added anyways, irrelevant
    # - missing boundary edge intersects with another edge => auto-add steiner point
    # expected: pass in relaxed mode, error in strict mode
    instance_uid = "Steiner point outside region_boundary / convex hull ([6,2]) \nand missing boundary edge ([1,2])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2, 6],
        steiner_points_y=[2, 2],
        edges=[[0, 1], [2, 3], [3, 0], [2, 4], [3, 4], [1, 4], [0, 2], [2, 5], [4, 5]],
        meta={},
    )
    strict_result = verify(instance, solution, strict=True)
    assert strict_result.errors

    relaxed_result = verify(instance, solution, strict=False)
    assert not relaxed_result.errors
    assert relaxed_result.num_obtuse_triangles == 0
    assert relaxed_result.num_steiner_points == 3


def test_verify_intersecting_edges_missing_point():
    # Test Case 4 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - intersecting triangulation edges => auto-add steiner point
    # expected: pass in relaxed mode, error in strict mode
    instance_uid = "Intersecting edges ([0,2], [1,3])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[],
        steiner_points_y=[],
        edges=[[0, 1], [2, 3], [3, 0], [0, 2], [1, 2], [1, 3]],
        meta={},
    )
    strict_result = verify(instance, solution, strict=True)
    assert strict_result.errors

    relaxed_result = verify(instance, solution, strict=False)
    assert not relaxed_result.errors
    assert relaxed_result.num_obtuse_triangles == 0
    assert relaxed_result.num_steiner_points == 1


def test_verify_intersecting_edges_multiple_missing_point():
    # Test Case 5 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - several crossing triangulation edges => auto-add steiner points
    # - point on instance boundary => split edge, irrelevant
    # expected: pass in relaxed mode, error in strict mode
    instance_uid = "Intersecting edges ([0,2], [1,3], [1,4], [0,4])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2, 2],
        steiner_points_y=[4, 2],
        edges=[[0, 1], [2, 3], [3, 0], [0, 2], [1, 2], [1, 3], [1, 4], [0, 4], [4, 5]],
        meta={},
    )
    strict_result = verify(instance, solution, strict=True)
    assert strict_result.errors

    relaxed_result = verify(instance, solution, strict=False)
    assert not relaxed_result.errors
    assert relaxed_result.num_obtuse_triangles == 4
    assert relaxed_result.num_steiner_points == 4


def test_verify_parallel_edges():
    # Test Case 6 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - point on instance boundary => split edge, irrelevant
    # - boundary both split and not split => irrelevant
    # expected: pass in both modes
    instance_uid = "Edge both split ([13,18], [18,2])\nand not split ([13,2])\n=> 0 obtuse triangles"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=15,
        points_x=[0, 6, 3, 1, 5, 2, 4, 1, 5, 3, 2, 4, 6, 0, 3],
        points_y=[0, 0, 6, 3, 2, 1, 4, 5, 5, 3, 4, 1, 3, 5, 0],
        region_boundary=[0, 14, 1, 12, 8, 2, 13],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2, 6, 0, "9/10", 4],
        steiner_points_y=[0, 2, 3, "53/10", 0],
        edges=[
            [2, 8],
            [16, 12],
            [13, 3],
            [3, 7],
            [7, 13],
            [5, 0],
            [0, 15],
            [15, 5],
            [1, 19],
            [3, 9],
            [9, 10],
            [10, 3],
            [4, 1],
            [1, 16],
            [16, 4],
            [14, 15],
            [9, 4],
            [4, 6],
            [6, 9],
            [5, 3],
            [3, 0],
            [6, 10],
            [5, 11],
            [11, 9],
            [9, 5],
            [13, 2],
            [3, 17],
            [17, 0],
            [2, 6],
            [6, 8],
            [4, 12],
            [12, 6],
            [2, 10],
            [2, 7],
            [7, 10],
            [11, 1],
            [4, 11],
            [8, 12],
            [7, 18],
            [13, 18],
            [19, 14],
            [5, 14],
            [14, 11],
            [13, 17],
            [18, 2],
            [11, 19],
        ],
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 0
    assert result.num_steiner_points == 5


def test_verify_implied_point_exists():
    # Test Case 7 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - unconnected steiner point => add anyways, irrelevant*
    # - edges intersecting in precisely that point => auto-split, irrelevant
    # expected: pass in both modes
    instance_uid = "Steiner point ([2,2]) without edge"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2],
        steiner_points_y=[2],
        edges=[[0, 1], [2, 3], [3, 0], [0, 2], [1, 2], [1, 3]],
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 0
    assert result.num_steiner_points == 1


def test_verify_same_edge():
    # Test Case 8 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - edge [0,1] twice and adds [1,0] => irrelevant
    # - intersecting edges at same position as steiner point
    # expected: pass in both modes
    instance_uid = "Steiner point ([2,2]) without edge"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=4,
        points_x=[0, 4, 4, 0],
        points_y=[0, 0, 4, 4],
        region_boundary=[0, 1, 2, 3],
        num_constraints=0,
        additional_constraints=[],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[2],
        steiner_points_y=[2],
        edges=[[0, 1], [2, 3], [3, 0], [0, 2], [1, 2], [1, 3]],
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 0
    assert result.num_steiner_points == 1


def test_verify_missing_boundary_edge():
    # Test Case 9 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - missing a boundary edge => auto-added anyways, irrelevant
    # expected: pass in both modes
    instance_uid = "Boundary edge missing ([2,3])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=8,
        points_x=[0, 5, 6, 3, 0, 3, 2, 4],
        points_y=[0, 0, 4, 8, 5, 3, 6, 5],
        region_boundary=[0, 1, 2, 3, 4],
        num_constraints=2,
        additional_constraints=[[0, 5], [5, 6]],
    )
    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[4, 2],
        steiner_points_y=[6, 7],
        edges=[
            [4, 9],
            [4, 6],
            [5, 7],
            [0, 5],
            [2, 5],
            [2, 8],
            [6, 8],
            [4, 5],
            [3, 9],
            [5, 6],
            [3, 6],
            [0, 1],
            [1, 2],
            [0, 4],
            [2, 7],
            [1, 5],
            [6, 7],
            [3, 8],
            [6, 9],
            [7, 8],
        ],
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 4
    assert result.num_steiner_points == 2


def test_verify_missing_additional_constraint():
    # Test Case 10 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - missing a boundary edge => auto-added anyways, irrelevant
    # - said edge intersects another edge => auto-add steiner point
    # expected: pass in relaxed mode, error in strict mode
    instance_uid = "Missing additional constraint ([0,3])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=5,
        points_x=[192, 384, 320, 272, 192],
        points_y=[512, 512, 560, 576, 576],
        region_boundary=[0, 1, 2, 3, 4],
        num_constraints=1,
        additional_constraints=[[0, 3]],
    )
    solution = Cgshop2025Solution(
        instance_uid=instance_uid,
        steiner_points_x=[288],
        steiner_points_y=[512],
        edges=[[2, 1], [2, 5], [5, 1], [4, 5], [3, 4], [4, 0], [0, 5], [5, 3], [3, 2]],
        meta={},
    )
    strict_result = verify(instance, solution, strict=True)
    assert strict_result.errors

    relaxed_result = verify(instance, solution, strict=False)
    assert not relaxed_result.errors
    assert relaxed_result.num_obtuse_triangles == 2
    assert relaxed_result.num_steiner_points == 2


def test_verify_edge_outside_boundary():
    # Test Case 11 kindly pointed out by Efi Malesiou from NKUA, Greece.
    # special characteristics:
    # - non-convex boundary => irrelevant
    # - external not required edge connecting boundary points => irrelevant
    # expected: pass in both modes
    instance_uid = "Edge outside region_boundary ([2,3])"
    instance = Cgshop2025Instance(
        instance_uid=instance_uid,
        num_points=5,
        points_x=[0, 4, 4, 0, 2],
        points_y=[0, 0, 4, 4, 2],
        region_boundary=[0, 1, 2, 4, 3],
        num_constraints=0,
        additional_constraints=[],
    )

    solution = Cgshop2025Solution(
        content_type="CG_SHOP_2025_Solution",
        instance_uid=instance_uid,
        steiner_points_x=[],
        steiner_points_y=[],
        edges=[[0, 1], [1, 2], [2, 4], [4, 3], [3, 0], [0, 4], [1, 4], [2, 3]],  # [2,3]
        meta={},
    )
    result = verify(instance, solution, strict=True)
    assert not result.errors
    assert result.num_obtuse_triangles == 0
    assert result.num_steiner_points == 0
