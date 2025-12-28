#pragma once
#include "../ecs/registry.h"

namespace ne {

struct Config;

// M2: Constraints system
// Distance constraint: keeps two entities at a fixed distance
struct DistanceConstraint {
    Entity e1;
    Entity e2;
    float rest_length;  // Desired distance between entities
    float stiffness = 1.0f;  // How rigid (0 = loose, 1 = rigid)
};

// M2: Constraints solver
struct ConstraintSystem {
    // Solve distance constraints using position-based dynamics
    static void solve_distance_constraints(Registry& reg, const std::vector<DistanceConstraint>& constraints, const Config& cfg);
    
    // Solve a single distance constraint
    static void solve_distance_constraint(Registry& reg, const DistanceConstraint& constraint, const Config& cfg);
};

} // namespace ne
