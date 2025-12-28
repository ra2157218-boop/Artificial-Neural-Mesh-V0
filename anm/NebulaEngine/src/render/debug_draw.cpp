#include "debug_draw.h"
#include <cmath>

namespace ne {

void DebugDraw::update_trajectory(Trajectory& traj, const Registry& reg, Entity e) {
    if (!reg.has_alive(e)) return;
    
    const auto& t = reg.transform(e);
    traj.positions.push_back(t.pos);
    
    // Limit trajectory length
    if (traj.positions.size() > traj.max_points) {
        traj.positions.erase(traj.positions.begin());
    }
}

void DebugDraw::draw_trajectory(IRenderer& renderer, const Trajectory& traj) {
    if (traj.positions.size() < 2) return;
    
    // Draw lines connecting trajectory points
    for (size_t i = 1; i < traj.positions.size(); ++i) {
        DebugLine line;
        line.start = traj.positions[i - 1];
        line.end = traj.positions[i];
        line.color = traj.color;
        renderer.draw_line(line);
    }
}

void DebugDraw::draw_trajectories(IRenderer& renderer, const Registry& reg,
                                  const std::vector<Trajectory>& trajectories) {
    for (const auto& traj : trajectories) {
        if (reg.has_alive(traj.entity)) {
            draw_trajectory(renderer, traj);
        }
    }
}

void DebugDraw::draw_shapes(IRenderer& renderer, const Registry& reg) {
    const auto& alive = reg.alive();
    
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        const auto& t = reg.transform(e);
        
        // Draw sphere if entity has sphere component
        if (reg.has_sphere(e)) {
            const auto& sphere = reg.sphere(e);
            DebugSphere dbg_sphere;
            dbg_sphere.center = t.pos;
            dbg_sphere.radius = sphere.radius;
            dbg_sphere.color = {0.8f, 0.8f, 1.0f}; // Light blue
            renderer.draw_sphere(dbg_sphere);
        }
        
        // Draw AABB if entity has AABB component
        if (reg.has_aabb(e)) {
            const auto& aabb = reg.aabb(e);
            // Draw AABB as wireframe (8 corners connected)
            Vec3 min = {t.pos.x - aabb.half_extents.x,
                       t.pos.y - aabb.half_extents.y,
                       t.pos.z - aabb.half_extents.z};
            Vec3 max = {t.pos.x + aabb.half_extents.x,
                       t.pos.y + aabb.half_extents.y,
                       t.pos.z + aabb.half_extents.z};
            
            Vec3 color = {1.0f, 0.8f, 0.8f}; // Light red
            
            // Draw 12 edges of the AABB
            Vec3 corners[8] = {
                {min.x, min.y, min.z}, {max.x, min.y, min.z},
                {max.x, max.y, min.z}, {min.x, max.y, min.z},
                {min.x, min.y, max.z}, {max.x, min.y, max.z},
                {max.x, max.y, max.z}, {min.x, max.y, max.z}
            };
            
            // Bottom face
            renderer.draw_line({corners[0], corners[1], color});
            renderer.draw_line({corners[1], corners[2], color});
            renderer.draw_line({corners[2], corners[3], color});
            renderer.draw_line({corners[3], corners[0], color});
            
            // Top face
            renderer.draw_line({corners[4], corners[5], color});
            renderer.draw_line({corners[5], corners[6], color});
            renderer.draw_line({corners[6], corners[7], color});
            renderer.draw_line({corners[7], corners[4], color});
            
            // Vertical edges
            renderer.draw_line({corners[0], corners[4], color});
            renderer.draw_line({corners[1], corners[5], color});
            renderer.draw_line({corners[2], corners[6], color});
            renderer.draw_line({corners[3], corners[7], color});
        }
    }
}

void DebugDraw::draw_contacts(IRenderer& renderer, const std::vector<ContactInfo>& contacts) {
    for (const auto& contact : contacts) {
        DebugContact dbg_contact;
        dbg_contact.position = contact.position;
        dbg_contact.normal = contact.normal;
        dbg_contact.magnitude = contact.magnitude;
        renderer.draw_contact(dbg_contact);
    }
}

} // namespace ne
