#include "constraints.h"
#include "../core/config.h"
#include <cmath>

namespace ne {

void ConstraintSystem::solve_distance_constraint(Registry& reg, const DistanceConstraint& constraint, const Config& cfg) {
    if (!reg.has_alive(constraint.e1) || !reg.has_alive(constraint.e2)) return;
    
    auto& t1 = reg.transform(constraint.e1);
    auto& t2 = reg.transform(constraint.e2);
    const auto& m1 = reg.mass(constraint.e1);
    const auto& m2 = reg.mass(constraint.e2);
    
    Vec3 diff = t1.pos - t2.pos;
    float dist_sq = diff.x * diff.x + diff.y * diff.y + diff.z * diff.z;
    
    if (dist_sq < 1e-8f) {
        // Entities are at same position - separate slightly
        diff = {0, 0.01f, 0};
        dist_sq = 0.0001f;
    }
    
    float dist = std::sqrt(dist_sq);
    float error = dist - constraint.rest_length;
    
    if (std::abs(error) < 1e-5f) return; // Already satisfied
    
    // Calculate correction direction
    Vec3 correction_dir = {diff.x / dist, diff.y / dist, diff.z / dist};
    
    // Mass-weighted correction
    float inv_mass1 = 1.0f / m1.m;
    float inv_mass2 = 1.0f / m2.m;
    float total_inv_mass = inv_mass1 + inv_mass2;
    
    // Apply correction based on stiffness
    float correction = error * constraint.stiffness / total_inv_mass;
    Vec3 correction_vec = correction_dir * correction;
    
    t1.pos -= correction_vec * inv_mass1;
    t2.pos += correction_vec * inv_mass2;
}

void ConstraintSystem::solve_distance_constraints(Registry& reg, const std::vector<DistanceConstraint>& constraints, const Config& cfg) {
    // Iterate constraints multiple times for stability (Gauss-Seidel style)
    const int iterations = 3;
    for (int iter = 0; iter < iterations; ++iter) {
        for (const auto& constraint : constraints) {
            solve_distance_constraint(reg, constraint, cfg);
        }
    }
}

} // namespace ne
