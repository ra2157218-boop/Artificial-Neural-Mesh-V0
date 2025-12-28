#pragma once
#include "../core/types.h"
#include "../ecs/registry.h"
#include <vector>
#include <limits>
#include <random>

namespace ne {

// M6: Ray tracing system
struct Ray {
    Vec3 origin;
    Vec3 direction;
    
    Ray() = default;
    Ray(const Vec3& o, const Vec3& d) : origin(o), direction(d) {}
    
    Vec3 point_at(float t) const {
        return {origin.x + direction.x * t,
                origin.y + direction.y * t,
                origin.z + direction.z * t};
    }
};

struct RayHit {
    float t = std::numeric_limits<float>::max();
    Vec3 position;
    Vec3 normal;
    Entity entity = INVALID_ENTITY;
    bool hit = false;
    
    void reset() {
        t = std::numeric_limits<float>::max();
        hit = false;
        entity = INVALID_ENTITY;
    }
};

// M6: Bounding Volume Hierarchy (BVH) for ray tracing acceleration
struct RT_AABB {
    Vec3 min;
    Vec3 max;
    
    RT_AABB() : min({0,0,0}), max({0,0,0}) {}
    RT_AABB(const Vec3& min_, const Vec3& max_) : min(min_), max(max_) {}
    
    Vec3 center() const {
        return {(min.x + max.x) * 0.5f,
                (min.y + max.y) * 0.5f,
                (min.z + max.z) * 0.5f};
    }
    
    Vec3 extent() const {
        return {(max.x - min.x) * 0.5f,
                (max.y - min.y) * 0.5f,
                (max.z - min.z) * 0.5f};
    }
    
    bool intersect(const Ray& ray, float& t_min, float& t_max) const;
};

// M6: BVH Node
struct BVHNode {
    RT_AABB bounds;
    int left_child = -1;
    int right_child = -1;
    int first_primitive = -1;
    int primitive_count = 0;
    bool is_leaf() const { return primitive_count > 0; }
};

// M6: Primitive for ray tracing (sphere or AABB)
struct RTPrimitive {
    enum Type { SPHERE, AABB_BOX };
    Type type;
    Entity entity;
    Vec3 center;
    float radius; // For sphere
    Vec3 half_extents; // For AABB
    RT_AABB bounds;
    
    bool intersect(const Ray& ray, RayHit& hit) const;
    RT_AABB get_bounds() const { return bounds; }
};

// M6: BVH acceleration structure
class BVH {
public:
    BVH() = default;
    
    // Build BVH from primitives
    void build(const std::vector<RTPrimitive>& primitives);
    
    // Ray intersection with BVH
    bool intersect(const Ray& ray, RayHit& hit, const Registry& reg) const;
    
    // Clear BVH
    void clear() {
        m_nodes.clear();
        m_primitives.clear();
    }
    
private:
    std::vector<BVHNode> m_nodes;
    std::vector<RTPrimitive> m_primitives;
    
    // Build helpers
    int build_node(int start, int end);
    void split_primitives(int start, int end, int& split_index);
    RT_AABB compute_bounds(int start, int end) const;
};

// M6: Ray tracing material (extends PBR for ray tracing)
struct RTMaterial {
    Vec3 albedo = {0.8f, 0.8f, 0.8f};
    float metallic = 0.0f;
    float roughness = 0.5f;
    float emission = 0.0f; // Emission strength
    Vec3 emission_color = {1.0f, 1.0f, 1.0f};
    
    // Ray tracing specific
    float reflectivity = 0.0f; // How much light is reflected
    float transparency = 0.0f; // How transparent (0 = opaque, 1 = fully transparent)
    float ior = 1.0f; // Index of refraction
};

// M6: Ray tracer
class RayTracer {
public:
    RayTracer() = default;
    
    // Trace a ray through the scene
    Vec3 trace(const Ray& ray, const Registry& reg, const BVH& bvh, int depth = 0) const;
    
    // Set global illumination settings
    void set_gi_enabled(bool enabled) { m_gi_enabled = enabled; }
    void set_max_depth(int depth) { m_max_depth = depth; }
    void set_sky_color(const Vec3& color) { m_sky_color = color; }
    
private:
    bool m_gi_enabled = true;
    int m_max_depth = 4;
    Vec3 m_sky_color = {0.5f, 0.7f, 1.0f}; // Sky blue
    
    // Helper: sample material properties
    RTMaterial get_material(const Registry& reg, Entity e) const;
    
    // Helper: compute lighting at hit point
    Vec3 compute_lighting(const RayHit& hit, const Ray& ray, const Registry& reg, const BVH& bvh) const;
    
    // Helper: sample hemisphere for GI
    Vec3 sample_hemisphere(const Vec3& normal) const;
};

} // namespace ne
