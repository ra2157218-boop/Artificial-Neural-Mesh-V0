#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"

namespace ne {

struct Config;

// M2: Joints system
// Hinge joint: allows rotation around one axis (for pendulum)
struct HingeJoint {
    Entity e1;  // Pivot point (fixed or heavy)
    Entity e2;  // Rotating entity
    Vec3 anchor;  // Local anchor point on e1 (world space)
    Vec3 axis;    // Rotation axis (normalized, world space)
    float rest_length = 0.0f;  // Rest length from anchor to e2 (0 = auto-calculate)
    float max_angle = 3.14159f;  // Max rotation angle (radians), PI = 180 degrees
};

// Ball-and-socket joint: allows rotation in all directions but keeps positions fixed
struct BallSocketJoint {
    Entity e1;
    Entity e2;
    Vec3 anchor;  // World space anchor point
    float rest_length = 0.0f;  // If > 0, acts like distance constraint
};

// M2: Joints solver
struct JointSystem {
    // Solve hinge joints
    static void solve_hinge_joints(Registry& reg, const std::vector<HingeJoint>& joints, const Config& cfg);
    
    // Solve ball-and-socket joints
    static void solve_ball_socket_joints(Registry& reg, const std::vector<BallSocketJoint>& joints, const Config& cfg);
    
private:
    static void solve_hinge_joint(Registry& reg, const HingeJoint& joint, const Config& cfg);
    static void solve_ball_socket_joint(Registry& reg, const BallSocketJoint& joint, const Config& cfg);
};

} // namespace ne
