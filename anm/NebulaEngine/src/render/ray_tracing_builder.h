#pragma once
#include "ray_tracing.h"
#include "../ecs/registry.h"

namespace ne {

// M6: Helper to build BVH from Registry
class RayTracingBuilder {
public:
    // Build BVH from registry entities
    static BVH build_bvh(const Registry& reg);
    
    // Convert registry entities to ray tracing primitives
    static std::vector<RTPrimitive> extract_primitives(const Registry& reg);
    
private:
    static RT_AABB compute_entity_bounds(const Registry& reg, Entity e);
};

} // namespace ne
