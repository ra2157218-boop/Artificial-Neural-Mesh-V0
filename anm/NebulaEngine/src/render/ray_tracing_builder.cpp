#include "ray_tracing_builder.h"

namespace ne {

RT_AABB RayTracingBuilder::compute_entity_bounds(const Registry& reg, Entity e) {
    const auto& t = reg.transform(e);
    
    if (reg.has_sphere(e)) {
        const auto& sphere = reg.sphere(e);
        Vec3 min = {t.pos.x - sphere.radius, t.pos.y - sphere.radius, t.pos.z - sphere.radius};
        Vec3 max = {t.pos.x + sphere.radius, t.pos.y + sphere.radius, t.pos.z + sphere.radius};
        return RT_AABB(min, max);
    } else if (reg.has_aabb(e)) {
        const auto& aabb = reg.aabb(e);
        Vec3 min = {t.pos.x - aabb.half_extents.x,
                   t.pos.y - aabb.half_extents.y,
                   t.pos.z - aabb.half_extents.z};
        Vec3 max = {t.pos.x + aabb.half_extents.x,
                   t.pos.y + aabb.half_extents.y,
                   t.pos.z + aabb.half_extents.z};
        return RT_AABB(min, max);
    }
    
    // Default: point bounds
    return RT_AABB(t.pos, t.pos);
}

std::vector<RTPrimitive> RayTracingBuilder::extract_primitives(const Registry& reg) {
    std::vector<RTPrimitive> primitives;
    const auto& alive = reg.alive();
    
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        const auto& t = reg.transform(e);
        RTPrimitive prim;
        prim.entity = e;
        prim.center = t.pos;
        
        if (reg.has_sphere(e)) {
            const auto& sphere = reg.sphere(e);
            prim.type = RTPrimitive::SPHERE;
            prim.radius = sphere.radius;
            prim.bounds = compute_entity_bounds(reg, e);
            primitives.push_back(prim);
        } else         if (reg.has_aabb(e)) {
            const auto& aabb = reg.aabb(e);
            prim.type = RTPrimitive::AABB_BOX;
            prim.half_extents = aabb.half_extents;
            prim.bounds = compute_entity_bounds(reg, e);
            primitives.push_back(prim);
        }
    }
    
    return primitives;
}

BVH RayTracingBuilder::build_bvh(const Registry& reg) {
    auto primitives = extract_primitives(reg);
    BVH bvh;
    bvh.build(primitives);
    return bvh;
}

} // namespace ne
