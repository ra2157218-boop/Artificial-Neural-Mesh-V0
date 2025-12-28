#include "ray_tracing.h"
#include "../ecs/registry.h"
#include <algorithm>
#include <cmath>
#include <random>

namespace ne {

// RT_AABB-Ray intersection (slab method)
bool RT_AABB::intersect(const Ray& ray, float& t_min, float& t_max) const {
    float t0 = (min.x - ray.origin.x) / ray.direction.x;
    float t1 = (max.x - ray.origin.x) / ray.direction.x;
    if (ray.direction.x < 0.0f) std::swap(t0, t1);
    t_min = std::max(t_min, t0);
    t_max = std::min(t_max, t1);
    
    if (t_max < t_min) return false;
    
    t0 = (min.y - ray.origin.y) / ray.direction.y;
    t1 = (max.y - ray.origin.y) / ray.direction.y;
    if (ray.direction.y < 0.0f) std::swap(t0, t1);
    t_min = std::max(t_min, t0);
    t_max = std::min(t_max, t1);
    
    if (t_max < t_min) return false;
    
    t0 = (min.z - ray.origin.z) / ray.direction.z;
    t1 = (max.z - ray.origin.z) / ray.direction.z;
    if (ray.direction.z < 0.0f) std::swap(t0, t1);
    t_min = std::max(t_min, t0);
    t_max = std::min(t_max, t1);
    
    return t_max >= t_min;
}

// Sphere-Ray intersection
static bool intersect_sphere(const Vec3& center, float radius, const Ray& ray, RayHit& hit) {
    Vec3 oc = ray.origin - center;
    float a = ray.direction.x * ray.direction.x + ray.direction.y * ray.direction.y + ray.direction.z * ray.direction.z;
    float b = 2.0f * (oc.x * ray.direction.x + oc.y * ray.direction.y + oc.z * ray.direction.z);
    float c = oc.x * oc.x + oc.y * oc.y + oc.z * oc.z - radius * radius;
    float discriminant = b * b - 4.0f * a * c;
    
    if (discriminant < 0.0f) return false;
    
    float sqrt_disc = std::sqrt(discriminant);
    float t = (-b - sqrt_disc) / (2.0f * a);
    if (t < 0.0f) t = (-b + sqrt_disc) / (2.0f * a);
    if (t < 0.0f || t >= hit.t) return false;
    
    hit.t = t;
    hit.position = ray.point_at(t);
    Vec3 normal = hit.position - center;
    float len = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);
    if (len > 1e-6f) {
        hit.normal = {normal.x / len, normal.y / len, normal.z / len};
    }
    hit.hit = true;
    return true;
}

bool RTPrimitive::intersect(const Ray& ray, RayHit& hit) const {
    if (type == SPHERE) {
        return intersect_sphere(center, radius, ray, hit);
    } else {
        // AABB_BOX intersection
        float t_min = 0.0f;
        float t_max = hit.t;
        if (bounds.intersect(ray, t_min, t_max)) {
            if (t_min > 0.0f && t_min < hit.t) {
                hit.t = t_min;
                hit.position = ray.point_at(t_min);
                // Compute normal (simplified - find closest face)
                Vec3 local_pos = hit.position - center;
                Vec3 abs_pos = {std::abs(local_pos.x), std::abs(local_pos.y), std::abs(local_pos.z)};
                if (abs_pos.x > abs_pos.y && abs_pos.x > abs_pos.z) {
                    hit.normal = {local_pos.x > 0 ? 1.0f : -1.0f, 0, 0};
                } else if (abs_pos.y > abs_pos.z) {
                    hit.normal = {0, local_pos.y > 0 ? 1.0f : -1.0f, 0};
                } else {
                    hit.normal = {0, 0, local_pos.z > 0 ? 1.0f : -1.0f};
                }
                hit.hit = true;
                return true;
            }
        }
        return false;
    }
}

RT_AABB BVH::compute_bounds(int start, int end) const {
    if (start >= end) return RT_AABB();
    
    Vec3 min_val = m_primitives[start].bounds.min;
    Vec3 max_val = m_primitives[start].bounds.max;
    
    for (int i = start + 1; i < end; ++i) {
        const auto& b = m_primitives[i].bounds;
        min_val.x = std::min(min_val.x, b.min.x);
        min_val.y = std::min(min_val.y, b.min.y);
        min_val.z = std::min(min_val.z, b.min.z);
        max_val.x = std::max(max_val.x, b.max.x);
        max_val.y = std::max(max_val.y, b.max.y);
        max_val.z = std::max(max_val.z, b.max.z);
    }
    
    return RT_AABB(min_val, max_val);
}

void BVH::split_primitives(int start, int end, int& split_index) {
    // Simple split: find longest axis and split in middle
    RT_AABB bounds = compute_bounds(start, end);
    Vec3 extent = bounds.extent();
    
    int axis = 0;
    if (extent.y > extent.x && extent.y > extent.z) axis = 1;
    else if (extent.z > extent.x) axis = 2;
    
    Vec3 center = bounds.center();
    float split_pos = (axis == 0) ? center.x : (axis == 1) ? center.y : center.z;
    
    split_index = start;
    for (int i = start; i < end; ++i) {
        Vec3 prim_center = m_primitives[i].get_bounds().center();
        float prim_pos = (axis == 0) ? prim_center.x : (axis == 1) ? prim_center.y : prim_center.z;
        
        if (prim_pos < split_pos) {
            std::swap(m_primitives[i], m_primitives[split_index]);
            split_index++;
        }
    }
    
    // Ensure we have at least one primitive on each side
    if (split_index == start || split_index == end) {
        split_index = start + (end - start) / 2;
    }
}

int BVH::build_node(int start, int end) {
    if (start >= end) return -1;
    
    BVHNode node;
    node.bounds = compute_bounds(start, end);
    node.first_primitive = start;
    node.primitive_count = end - start;
    
    // Leaf node if few primitives
    if (node.primitive_count <= 2) {
        int node_index = static_cast<int>(m_nodes.size());
        m_nodes.push_back(node);
        return node_index;
    }
    
    // Split and recurse
    int split_index;
    split_primitives(start, end, split_index);
    
    node.primitive_count = 0; // Internal node
    int node_index = static_cast<int>(m_nodes.size());
    m_nodes.push_back(node);
    
    m_nodes[node_index].left_child = build_node(start, split_index);
    m_nodes[node_index].right_child = build_node(split_index, end);
    
    return node_index;
}

void BVH::build(const std::vector<RTPrimitive>& primitives) {
    m_primitives = primitives;
    m_nodes.clear();
    
    if (m_primitives.empty()) return;
    
    build_node(0, static_cast<int>(m_primitives.size()));
}

bool BVH::intersect(const Ray& ray, RayHit& hit, const Registry& reg) const {
    if (m_nodes.empty()) return false;
    
    // Stack-based traversal
    struct StackEntry {
        int node_index;
        float t_min, t_max;
    };
    
    StackEntry stack[64];
    int stack_ptr = 0;
    
    float t_min = 0.0f;
    float t_max = hit.t;
    
    if (!m_nodes[0].bounds.intersect(ray, t_min, t_max)) {
        return false;
    }
    
    stack[stack_ptr++] = {0, t_min, t_max};
    
    bool found_hit = false;
    
    while (stack_ptr > 0) {
        StackEntry entry = stack[--stack_ptr];
        const BVHNode& node = m_nodes[entry.node_index];
        
        if (node.is_leaf()) {
            // Test all primitives in leaf
            for (int i = 0; i < node.primitive_count; ++i) {
                const RTPrimitive& prim = m_primitives[node.first_primitive + i];
                RayHit test_hit = hit;
                if (prim.intersect(ray, test_hit)) {
                    if (test_hit.t < hit.t) {
                        hit = test_hit;
                        hit.entity = prim.entity;
                        found_hit = true;
                    }
                }
            }
        } else {
            // Test children
            float left_t_min = entry.t_min, left_t_max = entry.t_max;
            float right_t_min = entry.t_min, right_t_max = entry.t_max;
            
            bool left_hit = false, right_hit = false;
            
            if (node.left_child >= 0) {
                left_hit = m_nodes[node.left_child].bounds.intersect(ray, left_t_min, left_t_max);
            }
            if (node.right_child >= 0) {
                right_hit = m_nodes[node.right_child].bounds.intersect(ray, right_t_min, right_t_max);
            }
            
            // Push closer child first (for early termination)
            if (left_hit && right_hit) {
                if (left_t_min < right_t_min) {
                    stack[stack_ptr++] = {node.right_child, right_t_min, right_t_max};
                    stack[stack_ptr++] = {node.left_child, left_t_min, left_t_max};
                } else {
                    stack[stack_ptr++] = {node.left_child, left_t_min, left_t_max};
                    stack[stack_ptr++] = {node.right_child, right_t_min, right_t_max};
                }
            } else if (left_hit) {
                stack[stack_ptr++] = {node.left_child, left_t_min, left_t_max};
            } else if (right_hit) {
                stack[stack_ptr++] = {node.right_child, right_t_min, right_t_max};
            }
        }
    }
    
    return found_hit;
}

RTMaterial RayTracer::get_material(const Registry& reg, Entity e) const {
    RTMaterial mat;
    // Default material - in full implementation, would read from component
    return mat;
}

Vec3 RayTracer::sample_hemisphere(const Vec3& normal) const {
    // Simple cosine-weighted hemisphere sampling
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    
    float u1 = dis(gen);
    float u2 = dis(gen);
    
    float r = std::sqrt(u1);
    float theta = 2.0f * 3.14159f * u2;
    
    Vec3 sample;
    sample.x = r * std::cos(theta);
    sample.y = r * std::sin(theta);
    sample.z = std::sqrt(1.0f - u1);
    
    // Transform to normal space (simplified - assume normal is +Z)
    // In full implementation, would use proper basis
    return sample;
}

Vec3 RayTracer::compute_lighting(const RayHit& hit, const Ray& ray, const Registry& reg, const BVH& bvh) const {
    RTMaterial mat = get_material(reg, hit.entity);
    
    Vec3 color = {0, 0, 0};
    
    // Direct lighting (simplified - single directional light)
    Vec3 light_dir = {0.5f, 1.0f, 0.3f};
    float len = std::sqrt(light_dir.x * light_dir.x + light_dir.y * light_dir.y + light_dir.z * light_dir.z);
    light_dir = {light_dir.x / len, light_dir.y / len, light_dir.z / len};
    
    float NdotL = hit.normal.x * light_dir.x + hit.normal.y * light_dir.y + hit.normal.z * light_dir.z;
    if (NdotL > 0.0f) {
        // Check shadow
        Ray shadow_ray;
        shadow_ray.origin = hit.position;
        shadow_ray.direction = light_dir;
        RayHit shadow_hit;
        shadow_hit.t = 1000.0f;
        
        bool in_shadow = bvh.intersect(shadow_ray, shadow_hit, reg);
        
        if (!in_shadow) {
            float light_intensity = 1.0f;
            color.x += mat.albedo.x * light_intensity * NdotL;
            color.y += mat.albedo.y * light_intensity * NdotL;
            color.z += mat.albedo.z * light_intensity * NdotL;
        }
    }
    
    // Emission
    if (mat.emission > 0.0f) {
        color.x += mat.emission_color.x * mat.emission;
        color.y += mat.emission_color.y * mat.emission;
        color.z += mat.emission_color.z * mat.emission;
    }
    
    return color;
}

Vec3 RayTracer::trace(const Ray& ray, const Registry& reg, const BVH& bvh, int depth) const {
    if (depth >= m_max_depth) {
        return m_sky_color; // Return sky color at max depth
    }
    
    RayHit hit;
    hit.t = 10000.0f;
    
    if (!bvh.intersect(ray, hit, reg)) {
        return m_sky_color; // Hit sky
    }
    
    RTMaterial mat = get_material(reg, hit.entity);
    
    // Compute direct lighting
    Vec3 color = compute_lighting(hit, ray, reg, bvh);
    
    // Global illumination (simplified)
    if (m_gi_enabled && depth < m_max_depth - 1) {
        Vec3 gi_sample = sample_hemisphere(hit.normal);
        Ray gi_ray;
        gi_ray.origin = hit.position;
        gi_ray.direction = gi_sample;
        Vec3 gi_color = trace(gi_ray, reg, bvh, depth + 1);
        
        // Add GI contribution (simplified)
        color.x += gi_color.x * 0.3f * mat.albedo.x;
        color.y += gi_color.y * 0.3f * mat.albedo.y;
        color.z += gi_color.z * 0.3f * mat.albedo.z;
    }
    
    // Reflection
    if (mat.reflectivity > 0.0f && depth < m_max_depth - 1) {
        Vec3 reflect_dir;
        float dot = ray.direction.x * hit.normal.x + ray.direction.y * hit.normal.y + ray.direction.z * hit.normal.z;
        reflect_dir.x = ray.direction.x - 2.0f * dot * hit.normal.x;
        reflect_dir.y = ray.direction.y - 2.0f * dot * hit.normal.y;
        reflect_dir.z = ray.direction.z - 2.0f * dot * hit.normal.z;
        
        Ray reflect_ray;
        reflect_ray.origin = hit.position;
        reflect_ray.direction = reflect_dir;
        Vec3 reflect_color = trace(reflect_ray, reg, bvh, depth + 1);
        
        color.x += reflect_color.x * mat.reflectivity;
        color.y += reflect_color.y * mat.reflectivity;
        color.z += reflect_color.z * mat.reflectivity;
    }
    
    return color;
}

} // namespace ne
