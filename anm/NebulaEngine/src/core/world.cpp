#include "world.h"
#include "../physics/physics_system.h"
#include "../physics/collision_system.h"
#include "../physics/constraints.h"
#include "../physics/joints.h"
#include "../render/debug_draw.h"
#include "../astro/nbody.h"

namespace ne {

World::World(const Config& cfg)
: m_cfg(cfg), m_time(cfg.fixed_dt) {}

void World::init_demo() {
    // M1: Create spheres with collision shapes
    for (int i = 0; i < 10; ++i) {
        Entity e = m_reg.create();
        m_reg.add_transform(e, {{0.0f, 10.0f + (float)i * 1.2f, 0.0f}});
        m_reg.add_velocity(e,  {{0.5f, 0.0f, 0.0f}});
        m_reg.add_mass(e,      {1.0f});
        m_reg.add_force(e,     {{0.0f, 0.0f, 0.0f}});
        m_reg.add_sphere(e,    {0.5f}); // M1: Add sphere collision shape
    }
}

void World::tick(double real_dt) {
    const int steps = m_time.update(real_dt, m_cfg.max_steps_per_tick);
    for (int i = 0; i < steps; ++i) {
        // M7: Use n-body gravity if enabled, otherwise use simple gravity
        if (m_use_nbody) {
            NBodySystem::compute_gravitational_forces(m_reg, m_G);
        } else {
            PhysicsSystem::apply_gravity(m_reg, m_cfg);
        }
        PhysicsSystem::integrate(m_reg, (float)m_time.fixed_dt());
        
        // M2: Solve constraints and joints BEFORE collision (constraints are primary)
        if (!m_distance_constraints.empty()) {
            ConstraintSystem::solve_distance_constraints(m_reg, m_distance_constraints, m_cfg);
        }
        if (!m_hinge_joints.empty()) {
            JointSystem::solve_hinge_joints(m_reg, m_hinge_joints, m_cfg);
        }
        if (!m_ball_socket_joints.empty()) {
            JointSystem::solve_ball_socket_joints(m_reg, m_ball_socket_joints, m_cfg);
        }
        
        CollisionSystem::resolve_collisions(m_reg, m_cfg);  // M1: broadphase + narrowphase
        CollisionSystem::resolve_ground_plane(m_reg, m_cfg);
        
        // M2: Re-solve constraints after collision (to maintain constraints)
        if (!m_distance_constraints.empty()) {
            ConstraintSystem::solve_distance_constraints(m_reg, m_distance_constraints, m_cfg);
        }
        if (!m_hinge_joints.empty()) {
            JointSystem::solve_hinge_joints(m_reg, m_hinge_joints, m_cfg);
        }
        
        m_sim_time += m_time.fixed_dt();
    }
}

void World::render() {
    if (!m_renderer) return;
    
    m_renderer->begin_frame();
    
    // Render world state (read-only)
    m_renderer->render_world(m_reg, m_camera);
    
    // Debug drawing
    DebugDraw::draw_shapes(*m_renderer, m_reg);
    
    m_renderer->end_frame();
}

} // namespace ne