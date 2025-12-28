#include "nbody.h"
#include "../ecs/components.h"
#include <cmath>

namespace ne {

float NBodySystem::distance_sq(const Vec3& a, const Vec3& b) {
    float dx = a.x - b.x;
    float dy = a.y - b.y;
    float dz = a.z - b.z;
    return dx * dx + dy * dy + dz * dz;
}

Vec3 NBodySystem::compute_pair_force(const Vec3& pos1, float mass1,
                                      const Vec3& pos2, float mass2,
                                      float G) {
    Vec3 r_vec = pos2 - pos1;
    float r_sq = distance_sq(pos1, pos2);
    
    // Add softening to avoid singularity
    r_sq += EPSILON * EPSILON;
    
    float r = std::sqrt(r_sq);
    if (r < 1e-10f) return {0, 0, 0}; // Too close, skip
    
    // F = G * m1 * m2 / r^2 * (r_vec / r)
    float force_magnitude = G * mass1 * mass2 / r_sq;
    Vec3 force = {
        force_magnitude * r_vec.x / r,
        force_magnitude * r_vec.y / r,
        force_magnitude * r_vec.z / r
    };
    
    return force;
}

void NBodySystem::compute_gravitational_forces(Registry& reg, float G) {
    const auto& alive = reg.alive();
    
    // Reset all forces
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        reg.force(e) = {{0.0f, 0.0f, 0.0f}};
    }
    
    // Compute pairwise gravitational forces
    for (size_t i = 0; i < alive.size(); ++i) {
        Entity e1 = alive[i];
        if (!reg.has_alive(e1)) continue;
        
        const auto& m1 = reg.mass(e1);
        if (m1.m <= 0.0f) continue; // Skip entities without valid mass
        
        const auto& t1 = reg.transform(e1);
        
        for (size_t j = i + 1; j < alive.size(); ++j) {
            Entity e2 = alive[j];
            if (!reg.has_alive(e2)) continue;
            
            const auto& m2 = reg.mass(e2);
            if (m2.m <= 0.0f) continue; // Skip entities without valid mass
            
            const auto& t2 = reg.transform(e2);
            
            // Compute force pair
            Vec3 force = compute_pair_force(t1.pos, m1.m, t2.pos, m2.m, G);
            
            // Apply Newton's third law: equal and opposite
            auto& f1 = reg.force(e1);
            auto& f2 = reg.force(e2);
            
            f1.f.x += force.x;
            f1.f.y += force.y;
            f1.f.z += force.z;
            
            f2.f.x -= force.x;
            f2.f.y -= force.y;
            f2.f.z -= force.z;
        }
    }
}

void NBodySystem::apply_forces(Registry& reg) {
    compute_gravitational_forces(reg);
}

} // namespace ne
