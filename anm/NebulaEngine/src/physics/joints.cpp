#include "joints.h"
#include "../core/config.h"
#include <cmath>
#include <algorithm>

namespace ne {

void JointSystem::solve_hinge_joint(Registry& reg, const HingeJoint& joint, const Config& cfg) {
    if (!reg.has_alive(joint.e1) || !reg.has_alive(joint.e2)) return;
    
    const auto& t2 = reg.transform(joint.e2);
    const auto& m1 = reg.mass(joint.e1);
    const auto& m2 = reg.mass(joint.e2);
    
    // Calculate vector from anchor to e2
    Vec3 to_e2 = t2.pos - joint.anchor;
    float dist_sq = to_e2.x * to_e2.x + to_e2.y * to_e2.y + to_e2.z * to_e2.z;
    float dist = std::sqrt(dist_sq);
    
    if (dist < 1e-6f) return;
    
    // Keep distance from anchor constant (primary constraint)
    float rest_length = joint.rest_length;
    if (rest_length <= 0.0f) {
        rest_length = dist; // Auto-calculate from current distance
    }
    
    float error = dist - rest_length;
    if (std::abs(error) > 1e-5f) {
        Vec3 correction_dir = {to_e2.x / dist, to_e2.y / dist, to_e2.z / dist};
        
        // For hinge joint, pivot (e1) should stay at anchor, only move e2
        // Move e2 towards/away from anchor to maintain rest_length
        float stiffness = 1.0f;
        Vec3 correction_vec = correction_dir * (error * stiffness);
        
        auto& t2_mut = reg.transform(joint.e2);
        t2_mut.pos -= correction_vec; // Move e2 directly, don't move pivot
        
        // Recalculate after correction
        to_e2 = t2_mut.pos - joint.anchor;
        dist_sq = to_e2.x * to_e2.x + to_e2.y * to_e2.y + to_e2.z * to_e2.z;
        dist = std::sqrt(dist_sq);
    }
    
    // Optional: Apply angle constraint (simplified - just keep in plane)
    // For now, we'll skip angle constraint and let it swing freely
    // Angle constraint can be added later if needed
}

void JointSystem::solve_ball_socket_joint(Registry& reg, const BallSocketJoint& joint, const Config& cfg) {
    if (!reg.has_alive(joint.e1) || !reg.has_alive(joint.e2)) return;
    
    auto& t1 = reg.transform(joint.e1);
    auto& t2 = reg.transform(joint.e2);
    const auto& m1 = reg.mass(joint.e1);
    const auto& m2 = reg.mass(joint.e2);
    
    // Keep both entities at anchor position (or maintain rest_length)
    Vec3 to_e1 = t1.pos - joint.anchor;
    Vec3 to_e2 = t2.pos - joint.anchor;
    
    if (joint.rest_length > 0.0f) {
        // Distance constraint mode
        Vec3 diff = t2.pos - t1.pos;
        float dist_sq = diff.x * diff.x + diff.y * diff.y + diff.z * diff.z;
        float dist = std::sqrt(dist_sq);
        float error = dist - joint.rest_length;
        
        if (std::abs(error) < 1e-5f) return;
        
        Vec3 correction_dir = {diff.x / dist, diff.y / dist, diff.z / dist};
        float inv_mass1 = 1.0f / m1.m;
        float inv_mass2 = 1.0f / m2.m;
        float total_inv_mass = inv_mass1 + inv_mass2;
        
        float correction = error * 0.5f / total_inv_mass;
        Vec3 correction_vec = correction_dir * correction;
        
        t1.pos += correction_vec * inv_mass1;
        t2.pos -= correction_vec * inv_mass2;
    } else {
        // Keep both at anchor
        Vec3 correction1 = joint.anchor - t1.pos;
        Vec3 correction2 = joint.anchor - t2.pos;
        
        float inv_mass1 = 1.0f / m1.m;
        float inv_mass2 = 1.0f / m2.m;
        float total_inv_mass = inv_mass1 + inv_mass2;
        
        float stiffness = 0.5f;
        correction1 = correction1 * (stiffness / total_inv_mass);
        correction2 = correction2 * (stiffness / total_inv_mass);
        
        t1.pos += correction1 * inv_mass1;
        t2.pos += correction2 * inv_mass2;
    }
}

void JointSystem::solve_hinge_joints(Registry& reg, const std::vector<HingeJoint>& joints, const Config& cfg) {
    const int iterations = 5; // More iterations for stability
    for (int iter = 0; iter < iterations; ++iter) {
        for (const auto& joint : joints) {
            solve_hinge_joint(reg, joint, cfg);
        }
    }
}

void JointSystem::solve_ball_socket_joints(Registry& reg, const std::vector<BallSocketJoint>& joints, const Config& cfg) {
    const int iterations = 2;
    for (int iter = 0; iter < iterations; ++iter) {
        for (const auto& joint : joints) {
            solve_ball_socket_joint(reg, joint, cfg);
        }
    }
}

} // namespace ne
