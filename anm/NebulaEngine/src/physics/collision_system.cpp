#include "collision_system.h"
#include "broadphase.h"
#include "../core/config.h"
#include <cmath>
#include <algorithm>

namespace ne {

void CollisionSystem::resolve_ground_plane(Registry& reg, const Config& cfg) {
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    const auto& alive = reg.alive();

    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;

        auto& t = transforms[e];
        if (t.pos.y < cfg.ground_y) {
            t.pos.y = cfg.ground_y;

            // kill downward velocity and apply restitution
            auto& v = velocities[e].v;
            if (v.y < 0.0f) {
                v.y *= -cfg.restitution;  // bounce if restitution > 0
            }
        }
    }
}

float CollisionSystem::distance_sq(const Vec3& a, const Vec3& b) {
    Vec3 diff = a - b;
    return diff.x * diff.x + diff.y * diff.y + diff.z * diff.z;
}

Vec3 CollisionSystem::normalize(const Vec3& v) {
    float len_sq = v.x * v.x + v.y * v.y + v.z * v.z;
    if (len_sq < 1e-8f) return {0, 0, 0};
    float len = std::sqrt(len_sq);
    return {v.x / len, v.y / len, v.z / len};
}

void CollisionSystem::resolve_sphere_sphere(Registry& reg, Entity e1, Entity e2, const Config& cfg) {
    const auto& t1 = reg.transform(e1);
    const auto& t2 = reg.transform(e2);
    const auto& s1 = reg.sphere(e1);
    const auto& s2 = reg.sphere(e2);
    auto& v1 = reg.velocity(e1);
    auto& v2 = reg.velocity(e2);
    const auto& m1 = reg.mass(e1);
    const auto& m2 = reg.mass(e2);
    
    Vec3 diff = t1.pos - t2.pos;
    float dist_sq = distance_sq(t1.pos, t2.pos);
    float min_dist = s1.radius + s2.radius;
    float min_dist_sq = min_dist * min_dist;
    
    if (dist_sq >= min_dist_sq) return; // Not colliding
    
    // Collision detected - resolve penetration
    float dist = std::sqrt(dist_sq);
    if (dist < 1e-6f) {
        // Overlapping exactly - separate along Y axis
        diff = {0, 1, 0};
        dist = min_dist;
    }
    
    Vec3 normal = normalize(diff);
    
    // Separate spheres
    float penetration = min_dist - dist;
    float inv_mass1 = 1.0f / m1.m;
    float inv_mass2 = 1.0f / m2.m;
    float total_inv_mass = inv_mass1 + inv_mass2;
    
    Vec3 separation = normal * (penetration / total_inv_mass);
    auto& t1_mut = reg.transform(e1);
    auto& t2_mut = reg.transform(e2);
    t1_mut.pos += separation * inv_mass1;
    t2_mut.pos -= separation * inv_mass2;
    
    // Resolve collision impulse (conservation of momentum)
    Vec3 rel_vel = v1.v - v2.v;
    float vel_along_normal = rel_vel.x * normal.x + rel_vel.y * normal.y + rel_vel.z * normal.z;
    
    // Don't resolve if velocities are separating
    if (vel_along_normal > 0) return;
    
    // Calculate normal impulse scalar
    float restitution = cfg.restitution;
    float j = -(1.0f + restitution) * vel_along_normal;
    j /= total_inv_mass;
    
    Vec3 normal_impulse = normal * j;
    v1.v += normal_impulse * inv_mass1;
    v2.v -= normal_impulse * inv_mass2;
    
    // M2: Apply friction (tangential impulse)
    if (cfg.friction > 0.0f) {
        Vec3 tangent = rel_vel - normal * vel_along_normal;
        float tangent_len_sq = tangent.x * tangent.x + tangent.y * tangent.y + tangent.z * tangent.z;
        
        if (tangent_len_sq > 1e-6f) {
            Vec3 tangent_dir = normalize(tangent);
            float vel_along_tangent = rel_vel.x * tangent_dir.x + rel_vel.y * tangent_dir.y + rel_vel.z * tangent_dir.z;
            
            // Coulomb friction: j_t = -min(μ * j_n, |v_t|)
            float j_t = -std::min(cfg.friction * std::abs(j), std::abs(vel_along_tangent));
            j_t /= total_inv_mass;
            
            Vec3 friction_impulse = tangent_dir * j_t;
            v1.v += friction_impulse * inv_mass1;
            v2.v -= friction_impulse * inv_mass2;
        }
    }
}

void CollisionSystem::resolve_sphere_aabb(Registry& reg, Entity sphere_e, Entity aabb_e, const Config& cfg) {
    const auto& sphere_t = reg.transform(sphere_e);
    const auto& aabb_t = reg.transform(aabb_e);
    const auto& sphere = reg.sphere(sphere_e);
    const auto& aabb = reg.aabb(aabb_e);
    auto& sphere_v = reg.velocity(sphere_e);
    auto& aabb_v = reg.velocity(aabb_e);
    const auto& sphere_m = reg.mass(sphere_e);
    const auto& aabb_m = reg.mass(aabb_e);
    
    // Find closest point on AABB to sphere center
    Vec3 closest;
    closest.x = std::max(aabb_t.pos.x - aabb.half_extents.x, 
                        std::min(sphere_t.pos.x, aabb_t.pos.x + aabb.half_extents.x));
    closest.y = std::max(aabb_t.pos.y - aabb.half_extents.y,
                        std::min(sphere_t.pos.y, aabb_t.pos.y + aabb.half_extents.y));
    closest.z = std::max(aabb_t.pos.z - aabb.half_extents.z,
                        std::min(sphere_t.pos.z, aabb_t.pos.z + aabb.half_extents.z));
    
    // Check if closest point is inside sphere
    float dist_sq = distance_sq(sphere_t.pos, closest);
    if (dist_sq >= sphere.radius * sphere.radius) return; // Not colliding
    
    // Collision detected
    float dist = std::sqrt(dist_sq);
    Vec3 normal;
    
    if (dist < 1e-6f) {
        // Sphere center inside AABB - find closest face
        Vec3 diff = sphere_t.pos - aabb_t.pos;
        float min_dist = std::abs(diff.x) - aabb.half_extents.x;
        float min_axis = 0;
        
        float dist_y = std::abs(diff.y) - aabb.half_extents.y;
        if (dist_y < min_dist) { min_dist = dist_y; min_axis = 1; }
        
        float dist_z = std::abs(diff.z) - aabb.half_extents.z;
        if (dist_z < min_dist) { min_dist = dist_z; min_axis = 2; }
        
        normal = {0, 0, 0};
        if (min_axis == 0) normal.x = (diff.x > 0) ? 1.0f : -1.0f;
        else if (min_axis == 1) normal.y = (diff.y > 0) ? 1.0f : -1.0f;
        else normal.z = (diff.z > 0) ? 1.0f : -1.0f;
        dist = sphere.radius;
    } else {
        normal = normalize(sphere_t.pos - closest);
    }
    
    // Separate sphere from AABB
    float penetration = sphere.radius - dist;
    float inv_mass1 = 1.0f / sphere_m.m;
    float inv_mass2 = 1.0f / aabb_m.m;
    float total_inv_mass = inv_mass1 + inv_mass2;
    
    Vec3 separation = normal * (penetration / total_inv_mass);
    auto& sphere_t_mut = reg.transform(sphere_e);
    auto& aabb_t_mut = reg.transform(aabb_e);
    sphere_t_mut.pos += separation * inv_mass1;
    aabb_t_mut.pos -= separation * inv_mass2;
    
    // Resolve collision impulse
    Vec3 rel_vel = sphere_v.v - aabb_v.v;
    float vel_along_normal = rel_vel.x * normal.x + rel_vel.y * normal.y + rel_vel.z * normal.z;
    
    if (vel_along_normal > 0) return;
    
    float restitution = cfg.restitution;
    float j = -(1.0f + restitution) * vel_along_normal;
    j /= total_inv_mass;
    
    Vec3 normal_impulse = normal * j;
    sphere_v.v += normal_impulse * inv_mass1;
    aabb_v.v -= normal_impulse * inv_mass2;
    
    // M2: Apply friction (tangential impulse)
    if (cfg.friction > 0.0f) {
        Vec3 tangent = rel_vel - normal * vel_along_normal;
        float tangent_len_sq = tangent.x * tangent.x + tangent.y * tangent.y + tangent.z * tangent.z;
        
        if (tangent_len_sq > 1e-6f) {
            Vec3 tangent_dir = normalize(tangent);
            float vel_along_tangent = rel_vel.x * tangent_dir.x + rel_vel.y * tangent_dir.y + rel_vel.z * tangent_dir.z;
            
            float j_t = -std::min(cfg.friction * std::abs(j), std::abs(vel_along_tangent));
            j_t /= total_inv_mass;
            
            Vec3 friction_impulse = tangent_dir * j_t;
            sphere_v.v += friction_impulse * inv_mass1;
            aabb_v.v -= friction_impulse * inv_mass2;
        }
    }
}

void CollisionSystem::resolve_collisions(Registry& reg, const Config& cfg) {
    // Use broadphase to find potential collision pairs
    // M3: Use adaptive cell size based on world scale
    float cell_size = cfg.broadphase_cell_size;
    auto pairs = Broadphase::find_pairs(reg, cell_size);
    
    for (const auto& [e1, e2] : pairs) {
        if (!reg.has_alive(e1) || !reg.has_alive(e2)) continue;
        
        bool e1_sphere = reg.has_sphere(e1);
        bool e1_aabb = reg.has_aabb(e1);
        bool e2_sphere = reg.has_sphere(e2);
        bool e2_aabb = reg.has_aabb(e2);
        
        // Sphere-sphere
        if (e1_sphere && e2_sphere) {
            resolve_sphere_sphere(reg, e1, e2, cfg);
        }
        // Sphere-AABB (order matters for function signature)
        else if (e1_sphere && e2_aabb) {
            resolve_sphere_aabb(reg, e1, e2, cfg);
        }
        else if (e1_aabb && e2_sphere) {
            resolve_sphere_aabb(reg, e2, e1, cfg);
        }
        // AABB-AABB: skip for M1 (can add later)
    }
}

}