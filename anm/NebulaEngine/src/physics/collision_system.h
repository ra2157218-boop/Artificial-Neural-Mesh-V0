#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"

namespace ne {

struct Config;

// M1: Collision detection and resolution
struct CollisionSystem {
    static void resolve_ground_plane(Registry& reg, const Config& cfg);
    
    // M1: Resolve collisions between entities
    static void resolve_collisions(Registry& reg, const Config& cfg);
    
private:
    // Narrowphase: sphere-sphere collision
    static void resolve_sphere_sphere(Registry& reg, Entity e1, Entity e2, const Config& cfg);
    
    // Narrowphase: sphere-AABB collision
    static void resolve_sphere_aabb(Registry& reg, Entity sphere_e, Entity aabb_e, const Config& cfg);
    
    // Helper: calculate distance squared between two points
    static float distance_sq(const Vec3& a, const Vec3& b);
    
    // Helper: normalize vector
    static Vec3 normalize(const Vec3& v);
};

}