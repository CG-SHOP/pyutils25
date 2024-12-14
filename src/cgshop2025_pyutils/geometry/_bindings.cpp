// pybind11
#include <pybind11/operators.h> // To define operator overloading
#include <pybind11/pybind11.h>  // Basic pybind11 functionality
#include <pybind11/stl.h>       // Automatic conversion of vectors

// cgal
#include <CGAL/Arr_naive_point_location.h>
#include <CGAL/Arr_segment_traits_2.h>
#include <CGAL/Arrangement_2.h>
#include <CGAL/Boolean_set_operations_2.h>
#include <CGAL/Constrained_Delaunay_triangulation_2.h>
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Point_2.h>
#include <CGAL/Polygon_2.h>
#include <CGAL/Polygon_with_holes_2.h>
#include <CGAL/Rotational_sweep_visibility_2.h>
#include <CGAL/Triangular_expansion_visibility_2.h>
#include <CGAL/Triangulation_vertex_base_with_info_2.h>
#include <CGAL/convex_hull_2.h>
#include <CGAL/create_straight_skeleton_2.h>

// fmt
#include <exception>
#include <fmt/core.h>
#include <unordered_map>

// for duplicate check
#include <map>

// Define CGAL types for easy readability and maintenance
using Kernel = CGAL::Epeck; // Exact Predicates Exact Constructions Kernel
using Point = CGAL::Point_2<Kernel>;
using Polygon2WithHoles = CGAL::Polygon_with_holes_2<Kernel>;
using Polygon2 = CGAL::Polygon_2<Kernel>;
using Segment2 = Kernel::Segment_2;
using Traits_2 = CGAL::Arr_segment_traits_2<Kernel>;
using Arrangement_2 = CGAL::Arrangement_2<Traits_2>;
using Halfedge_const_handle = Arrangement_2::Halfedge_const_handle;
using Face_handle = Arrangement_2::Face_handle;
using PointLocation = CGAL::Arr_naive_point_location<Arrangement_2>;
using Rational = CGAL::Gmpq;

// Compute convex hull and return the indices of the points on the hull
std::vector<int64_t> compute_convex_hull(const std::vector<Point> &points) {
  // Compute convex hull
  std::vector<Point> hull;
  CGAL::convex_hull_2(points.begin(), points.end(), std::back_inserter(hull));

  // Find the indices of the points in the original vector
  std::vector<int64_t> result;
  for (const auto &p : hull) {
    auto it = std::find(points.begin(), points.end(), p);
    if (it != points.end()) {
      result.push_back(std::distance(points.begin(), it));
    } else {
      throw std::runtime_error(
          "Point on hull not found in original points list.");
    }
  }
  return result;
}

// Helper class to manage geometry and verify solutions using CGAL's
// arrangements
class VerificationGeometryHelper {
public:
  VerificationGeometryHelper()
      : arrangement_(), point_location_(arrangement_) {}

  // Add a point to the arrangement and return its index
  int add_point(const Point &p) {
    CGAL::insert_point(arrangement_, p, point_location_);
    points_.push_back(p);
    return static_cast<int>(points_.size() - 1);
  }

  // Add a segment between two points in the arrangement
  void add_segment(const int i, const int j) {
    const Point &p1 = points_[i];
    const Point &p2 = points_[j];
    Segment2 s(p1, p2);
    CGAL::insert(arrangement_, s, point_location_);
  }

  // Get the number of points in the arrangement
  int get_num_points() const {
    return static_cast<int>(arrangement_.number_of_vertices());
  }

  // Search for any bounded face that is not triangular
  std::optional<Point> search_for_non_triangular_faces() const {
    for (auto it = arrangement_.faces_begin(); it != arrangement_.faces_end();
         ++it) {
      if (it->is_unbounded())
        continue;

      // Count the number of edges in the outer boundary
      int num_edges = 0;
      Halfedge_const_handle e = it->outer_ccb();
      do {
        num_edges++;
        e = e->next();
      } while (e != it->outer_ccb());

      // If the face is not a triangle, return a point inside the face
      if (num_edges != 3) {
        return e->source()->point();
      }
    }
    return std::nullopt;
  }

  // Search for faces with holes and return a point in such a face
  std::optional<Point> search_for_faces_with_holes() const {
    for (auto it = arrangement_.faces_begin(); it != arrangement_.faces_end();
         ++it) {
      if (!it->is_unbounded() && it->number_of_holes() > 0) {
        return it->outer_ccb()->source()->point();
      }
    }
    return std::nullopt;
  }

  // Count obtuse triangles in bounded faces
  int count_obtuse_triangles() const {
    int count = 0;
    for (auto it = arrangement_.faces_begin(); it != arrangement_.faces_end();
         ++it) {
      if (it->is_unbounded())
        continue;

      // Get the three vertices of the face
      auto e = it->outer_ccb();
      Point p1 = e->source()->point();
      Point p2 = e->target()->point();
      e = e->next();
      Point p3 = e->target()->point();

      // Compute all three dot products to check for obtuse angles
      std::array<Point, 3> points = {p1, p2, p3};
      for (int i = 0; i < 3; i++) {
        auto v1 = points[(i + 1) % 3] - points[i];
        auto v2 = points[(i + 2) % 3] - points[i];
        if (CGAL::scalar_product(v1, v2) < 0) {
          count++;
          break;
        }
      }
    }
    return count;
  }

  // Get points that are isolated (not connected by any edge)
  std::vector<Point> search_for_isolated_points() const {
    std::vector<Point> isolated_points;
    for (auto it = arrangement_.vertices_begin();
         it != arrangement_.vertices_end(); ++it) {
      if (it->is_isolated()) {
        isolated_points.push_back(it->point());
      }
    }
    return isolated_points;
  }

  // Search for segments that have the same face on both sides
  std::optional<Segment2> search_for_bad_edges() const {
    for (auto it = arrangement_.edges_begin(); it != arrangement_.edges_end();
         ++it) {
      if (it->face() == it->twin()->face()) {
        return it->curve();
      }
    }
    return std::nullopt;
  }

protected:
  std::vector<Point> points_;    // Store the points in the arrangement
  Arrangement_2 arrangement_;    // The CGAL arrangement of segments and points
  PointLocation point_location_; // A point location utility for fast querying
};

// Define CGAL types for constrained triangulation
using Vb = CGAL::Triangulation_vertex_base_2<Kernel>;
using Fb = CGAL::Constrained_triangulation_face_base_2<Kernel>;
using Tds = CGAL::Triangulation_data_structure_2<Vb, Fb>;
using CDT = CGAL::Constrained_Delaunay_triangulation_2<
    Kernel, Tds, CGAL::No_constraint_intersection_tag>;

class ConstrainedTriangulation {
public:
  ConstrainedTriangulation() : cdt_() {}

  // Add a point to the triangulation and return its index
  int add_point(const Point &p) {
    auto index = points_.size();
    auto v = cdt_.insert(p);
    points_.push_back(v);
    point_to_index_[v] = index;
    return static_cast<int>(index);
  }

  // Add a boundary made of points and verify if it is valid
  void add_boundary(const std::vector<int> &boundary) {
    std::vector<Point> vertices;
    vertices.reserve(boundary.size());
    for (auto i : boundary) {
      vertices.push_back(points_[i]->point());
    }
    cdt_.insert_constraint(vertices.begin(), vertices.end(), true);
    boundary_ = Polygon2(vertices.begin(), vertices.end());

    // Ensure the boundary is a simple, counter-clockwise polygon
    if (!boundary_->is_simple()) {
      throw std::runtime_error("Boundary must be a simple polygon.");
    }
    if (boundary_->is_clockwise_oriented()) {
      throw std::runtime_error("Boundary must be counter-clockwise oriented.");
    }
  }

  // Add a segment between two points in the triangulation
  void add_segment(const int i, const int j) {
    auto p1 = points_[i];
    auto p2 = points_[j];
    cdt_.insert_constraint(p1, p2);
  }

  // Get the edges of the triangulation, ignoring those outside the boundary
  std::vector<std::tuple<int, int>> get_triangulation_edges() const {
    std::vector<std::tuple<int, int>> edges;
    for (auto e = cdt_.finite_edges_begin(); e != cdt_.finite_edges_end();
         ++e) {
      auto v1 = e->first->vertex((e->second + 1) % 3);
      auto v2 = e->first->vertex((e->second + 2) % 3);
      auto middle = CGAL::midpoint(v1->point(), v2->point());

      // Ignore edges outside the boundary
      if (boundary_.has_value() && boundary_->has_on_unbounded_side(middle)) {
        continue;
      }
      auto i = point_to_index_.at(v1);
      auto j = point_to_index_.at(v2);
      edges.emplace_back(i, j);
    }
    return edges;
  }

protected:
  std::optional<Polygon2> boundary_; // Store the boundary polygon
  std::vector<CDT::Vertex_handle>
      points_; // Store the points in the triangulation
  std::unordered_map<CDT::Vertex_handle, int>
      point_to_index_; // Map points to their indices
  CDT cdt_;            // The constrained Delaunay triangulation
};

// Function to convert Kernel::FT to rational string
std::string to_rational_string(const Kernel::FT &x) {
  auto exact_value = CGAL::exact(x);
  std::string exact_str = exact_value.str();
  return exact_str;
}

// Exact conversion of a long to CGAL's Field Type (FT)
auto to_exact(std::int64_t x) {
  double lo32 = x & 0xffff'ffff;
  double hi32 = static_cast<double>(x >> 32) * 4294967296.0;
  return Kernel::FT(hi32) + Kernel::FT(lo32);
}

std::optional<Point> intersection_point(const Segment2 &s1,
                                        const Segment2 &s2) {
  auto result = CGAL::intersection(s1, s2);
  if (result) {
    if (const Point *p = std::get_if<Point>(&*result)) {
      return *p;
    }
  }
  return std::nullopt;
}

// Convert string to exact number (Kernel::FT), handling rational numbers
Kernel::FT str_to_exact(std::string number) {
  number.erase(0, number.find_first_not_of('0'));
  if (number.empty())
    number += '0';
  if (number[0] == '-') {
    return -str_to_exact(number.substr(1));
  }
  if (std::count(number.begin(), number.end(), '/') == 1) { // rational numbers
    auto point_pos = number.find('/');
    auto numerator = str_to_exact(number.substr(0, point_pos));
    auto denominator = str_to_exact(number.substr(point_pos + 1));
    return numerator / denominator;
  }
  constexpr size_t max_len = 14;
  if (number.length() <= max_len) {
    return to_exact(std::int64_t(std::stoll(number)));
  }
  auto small_part = str_to_exact(number.substr(number.length() - max_len));
  auto large_part = std::pow(10, max_len) *
                    str_to_exact(number.substr(0, number.length() - max_len));
  return large_part + small_part;
}

std::string point_to_string(const Point &p) {
  return fmt::format("({}, {})", CGAL::to_double(p.x()),
                     CGAL::to_double(p.y()));
}

std::optional<std::pair<int, int>>
points_contain_duplicates(const std::vector<Point> &points) {
  std::map<Point, std::size_t> unique_points;
  std::size_t index = 0;
  for (const auto &p : points) {
    auto result = unique_points.try_emplace(p, index);
    if (!result.second) {
      return std::pair<int, int>{int(result.first->second), int(index)};
    }
    ++index;
  }
  return std::nullopt;
}

// Pybind11 module definitions
PYBIND11_MODULE(_bindings, m) {
  namespace py = pybind11;
  m.doc() = "Example of PyBind11 and CGAL."; // Optional module docstring

  // Exact numbers
  py::class_<Kernel::FT>(m, "FieldNumber",
                         "A container for exact numbers in CGAL.")
      .def(py::init<long>())
      .def(py::init<double>())
      .def(py::init(&str_to_exact))
      .def(py::self / Kernel::FT())
      .def(py::self + Kernel::FT())
      .def(py::self - Kernel::FT())
      .def(py::self * Kernel::FT())
      .def(py::self == Kernel::FT())
      .def(py::self < Kernel::FT())
      .def(py::self > Kernel::FT())
      .def(py::self <= Kernel::FT())
      .def(py::self >= Kernel::FT())
      .def("__float__",
           [](const Kernel::FT &ft) { return CGAL::to_double(ft); })
      .def("__str__",
           [](const Kernel::FT &x) {
             return std::to_string(CGAL::to_double(x));
           })
      .def("exact", &to_rational_string);

  // Points
  py::class_<Point>(m, "Point", "A 2-dimensional point.")
      .def(py::init<long, long>())
      .def(py::init<double, double>())
      .def(py::init<Kernel::FT, Kernel::FT>())
      .def("__add__",
           [](const Point &p1, const Point &p2) {
             // Addition is not defined in CGAL for points (?!)
             return Point(p1.x() + p2.x(), p1.y() + p2.y());
           })
      .def("__sub__",
           [](const Point &p1, const Point &p2) {
             return Point(p1.x() - p2.x(), p1.y() - p2.y());
           })
      .def(py::self == Point())
      .def(py::self != Point())
      .def("scale",
           [](const Point &p, const Kernel::FT &s) {
             return Point(p.x() * s, p.y() * s);
           })
      .def("x", [](const Point &p) { return p.x(); })
      .def("y", [](const Point &p) { return p.y(); })
      .def("__len__", [](const Point &self) { return 2; })
      .def("__getitem__",
           [](const Point &self, int i) {
             if (i == 0) {
               return self.x();
             } else if (i == 1) {
               return self.y();
             }
             throw std::out_of_range("Only 0=x and 1=y.");
           })
      .def(py::self == Point())
      .def("__str__", &point_to_string);

  // Segments
  py::class_<Segment2>(m, "Segment", "A 2-dimensional segment.")
      .def(py::init<Point, Point>())
      .def("source", &Segment2::source)
      .def("target", &Segment2::target)
      .def("squared_length", &Segment2::squared_length)
      .def("does_intersect",
           [](const Segment2 &self, const Segment2 &s2) {
             return CGAL::do_intersect(self, s2);
           })
      .def("does_intersect",
           [](const Segment2 &self, const Point &p) {
             return CGAL::do_intersect(self, p);
           })
      .def("__str__", [](const Segment2 &self) {
        return fmt::format("[{}, {}]", point_to_string(self.source()),
                           point_to_string(self.target()));
      });

  // Polygons
  py::class_<Polygon2>(m, "Polygon", "A simple polygon in CGAL.")
      .def(py::init<>())
      .def(py::init([](const std::vector<Point> &vertices) {
        return std::make_unique<Polygon2>(vertices.begin(), vertices.end());
      }))
      .def("boundary",
           [](const Polygon2 &poly) {
             std::vector<Point> points;
             std::copy(poly.begin(), poly.end(), std::back_inserter(points));
             return points;
           })
      .def("is_simple", &Polygon2::is_simple)
      .def("contains",
           [](const Polygon2 &self, const Point &p) {
             return self.bounded_side(p) != CGAL::ON_UNBOUNDED_SIDE;
           })
      .def("contains",
           [](const Polygon2 &self, const Segment2 &s) {
             bool both_points_inside =
                 self.bounded_side(s.source()) != CGAL::ON_UNBOUNDED_SIDE &&
                 self.bounded_side(s.target()) != CGAL::ON_UNBOUNDED_SIDE;
             if (!both_points_inside) {
               return false;
             }
             for (auto it = self.edges_begin(); it != self.edges_end(); ++it) {
               if (CGAL::do_intersect(*it, s)) {
                 return false;
               }
             }
             return true;
           })
      .def("on_boundary",
           [](const Polygon2 &self, const Point &p) {
             return self.bounded_side(p) == CGAL::ON_BOUNDARY;
           })
      .def("area", [](const Polygon2 &poly) { return poly.area(); });

  // Convex hull
  m.def("compute_convex_hull", &compute_convex_hull,
        "Compute the convex hull of a set of points.");

  // Squared distance functions
  m.def("squared_distance", [](const Point &p1, const Point &p2) {
    return CGAL::squared_distance(p1, p2);
  });
  m.def("squared_distance", [](const Segment2 &s, const Point &p) {
    return CGAL::squared_distance(s, p);
  });
  m.def("squared_distance", [](const Point &p, const Segment2 &s) {
    return CGAL::squared_distance(p, s);
  });
  m.def("squared_distance", [](const Segment2 &s1, const Segment2 &s2) {
    return CGAL::squared_distance(s1, s2);
  });
  m.def("intersection_point", &intersection_point,
        "Compute the intersection point of two segments.");

  // VerificationGeometryHelper bindings
  py::class_<VerificationGeometryHelper>(
      m, "VerificationGeometryHelper",
      "An exact solution verifier using arrangements.")
      .def(py::init<>())
      .def("add_point", &VerificationGeometryHelper::add_point)
      .def("add_segment", &VerificationGeometryHelper::add_segment)
      .def("search_for_isolated_points",
           &VerificationGeometryHelper::search_for_isolated_points)
      .def("search_for_bad_edges",
           &VerificationGeometryHelper::search_for_bad_edges)
      .def("get_num_points", &VerificationGeometryHelper::get_num_points)
      .def("search_for_non_triangular_faces",
           &VerificationGeometryHelper::search_for_non_triangular_faces)
      .def("search_for_faces_with_holes",
           &VerificationGeometryHelper::search_for_faces_with_holes)
      .def("count_obtuse_triangles",
           &VerificationGeometryHelper::count_obtuse_triangles);

  // ConstrainedTriangulation bindings
  py::class_<ConstrainedTriangulation>(m, "ConstrainedTriangulation",
                                       "A constrained triangulation.")
      .def(py::init<>())
      .def("add_point", &ConstrainedTriangulation::add_point)
      .def("add_segment", &ConstrainedTriangulation::add_segment)
      .def("get_triangulation_edges",
           &ConstrainedTriangulation::get_triangulation_edges)
      .def("add_boundary", &ConstrainedTriangulation::add_boundary);

  // Duplicate check
  m.def("points_contain_duplicates", &points_contain_duplicates,
        "Check if a list of points contains duplicates.");
}
