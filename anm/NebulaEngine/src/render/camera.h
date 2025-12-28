#pragma once
#include "../core/types.h"
#include <cmath>

namespace ne {

// M4: Camera system
struct Camera {
    Vec3 position = {0.0f, 5.0f, 10.0f};
    Vec3 target = {0.0f, 0.0f, 0.0f};
    Vec3 up = {0.0f, 1.0f, 0.0f};
    
    float fov = 60.0f;        // Field of view in degrees
    float near_plane = 0.1f;
    float far_plane = 1000.0f;
    
    // View matrix calculation (for renderers)
    // Returns forward direction
    Vec3 forward() const {
        Vec3 dir = target - position;
        float len_sq = dir.x * dir.x + dir.y * dir.y + dir.z * dir.z;
        if (len_sq < 1e-8f) return {0, 0, -1};
        float len = std::sqrt(len_sq);
        return {dir.x / len, dir.y / len, dir.z / len};
    }
    
    // Right direction
    Vec3 right() const {
        Vec3 fwd = forward();
        Vec3 right_dir;
        // Cross product: right = forward × up
        right_dir.x = fwd.y * up.z - fwd.z * up.y;
        right_dir.y = fwd.z * up.x - fwd.x * up.z;
        right_dir.z = fwd.x * up.y - fwd.y * up.x;
        float len_sq = right_dir.x * right_dir.x + right_dir.y * right_dir.y + right_dir.z * right_dir.z;
        if (len_sq < 1e-8f) return {1, 0, 0};
        float len = std::sqrt(len_sq);
        return {right_dir.x / len, right_dir.y / len, right_dir.z / len};
    }
};

} // namespace ne
