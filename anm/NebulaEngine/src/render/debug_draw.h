#pragma once
#include "renderer.h"
#include "../ecs/registry.h"
#include "../physics/collision_system.h"
#include <vector>

namespace ne {

// M4: Debug drawing system
// Collects debug information and draws it via renderer
struct DebugDraw {
    // Trajectory tracking (stores recent positions)
    struct Trajectory {
        Entity entity;
        std::vector<Vec3> positions;
        Vec3 color = {0.0f, 1.0f, 0.0f}; // Green
        size_t max_points = 100;
    };
    
    // Contact information
    struct ContactInfo {
        Vec3 position;
        Vec3 normal;
        float magnitude;
    };
    
    // Draw trajectories for entities
    static void draw_trajectories(IRenderer& renderer, const Registry& reg, 
                                  const std::vector<Trajectory>& trajectories);
    
    // Draw collision shapes (spheres, AABBs)
    static void draw_shapes(IRenderer& renderer, const Registry& reg);
    
    // Draw contacts
    static void draw_contacts(IRenderer& renderer, const std::vector<ContactInfo>& contacts);
    
    // Update trajectory for an entity
    static void update_trajectory(Trajectory& traj, const Registry& reg, Entity e);
    
private:
    // Helper to draw a single trajectory
    static void draw_trajectory(IRenderer& renderer, const Trajectory& traj);
};

} // namespace ne
