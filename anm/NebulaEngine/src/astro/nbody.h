#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"
#include <vector>

namespace ne {

// M7: N-body gravitational physics
// Computes gravitational forces between all bodies

class NBodySystem {
public:
    // Compute gravitational forces for all entities with mass
    // Uses Newton's law of universal gravitation: F = G * m1 * m2 / r^2
    static void compute_gravitational_forces(Registry& reg, float G = 6.67430e-11f);
    
    // Compute force between two bodies
    static Vec3 compute_pair_force(const Vec3& pos1, float mass1,
                                     const Vec3& pos2, float mass2,
                                     float G = 6.67430e-11f);
    
    // Apply gravitational forces to entities
    static void apply_forces(Registry& reg);
    
private:
    // Helper: distance squared between two points
    static float distance_sq(const Vec3& a, const Vec3& b);
    
    // Minimum distance to avoid singularity (softening parameter)
    static constexpr float EPSILON = 1.0e-3f;
};

} // namespace ne
