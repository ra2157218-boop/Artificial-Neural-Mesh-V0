#pragma once
#include "config.h"
#include "time_system.h"
#include "../ecs/registry.h"
#include "../physics/constraints.h"
#include "../physics/joints.h"
#include "../render/renderer.h"
#include "../render/camera.h"
#include <vector>
#include <memory>

// Forward declarations
namespace ne {
    namespace astro {
        class NBodySystem;
    }
}

namespace ne {

class World {
public:
    explicit World(const Config& cfg);

    void init_demo();
    void tick(double real_dt);

    const Registry& registry() const { return m_reg; }
    Registry& registry() { return m_reg; }
    
    // M2: Constraints and joints management
    void add_distance_constraint(const DistanceConstraint& constraint) {
        m_distance_constraints.push_back(constraint);
    }
    
    void add_hinge_joint(const HingeJoint& joint) {
        m_hinge_joints.push_back(joint);
    }
    
    void add_ball_socket_joint(const BallSocketJoint& joint) {
        m_ball_socket_joints.push_back(joint);
    }
    
    void clear_constraints() {
        m_distance_constraints.clear();
        m_hinge_joints.clear();
        m_ball_socket_joints.clear();
    }
    
    // M4: Rendering
    void set_renderer(IRenderer* renderer) { m_renderer = renderer; }
    void set_camera(const Camera& camera) { m_camera = camera; }
    const Camera& camera() const { return m_camera; }
    Camera& camera() { return m_camera; }
    
    // Render current frame (call after tick)
    void render();
    
    // M7: Astro module integration
    void enable_nbody(bool enabled) { m_use_nbody = enabled; }
    void set_gravitational_constant(float G) { m_G = G; }

private:
    Config m_cfg;
    TimeSystem m_time;
    Registry m_reg;
    double m_sim_time = 0.0;
    
    // M2: Constraints and joints
    std::vector<DistanceConstraint> m_distance_constraints;
    std::vector<HingeJoint> m_hinge_joints;
    std::vector<BallSocketJoint> m_ball_socket_joints;
    
    // M4: Rendering
    IRenderer* m_renderer = nullptr;
    Camera m_camera;
    
    // M7: Astro module
    bool m_use_nbody = false;
    float m_G = 6.67430e-11f; // Gravitational constant
};

} // namespace ne