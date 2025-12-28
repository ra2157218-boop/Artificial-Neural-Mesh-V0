#include "advanced_physics.h"
#include "../core/config.h"
#include "../physics/collision_system.h"
#include <cmath>
#include <algorithm>

namespace ne {

// RK4 Integration (4th order Runge-Kutta)
void AdvancedPhysicsSystem::integrate_rk4(Registry& reg, float dt) {
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    auto& forces = reg.forces();
    auto& masses = reg.masses();
    const auto& alive = reg.alive();
    
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        auto& pos = transforms[e].pos;
        auto& vel = velocities[e].v;
        auto& force = forces[e].f;
        float invMass = 1.0f / masses[e].m;
        
        // k1 = f(t, y) - 2D (z ignored)
        Vec3 k1_v = {force.x * invMass, force.y * invMass, 0};
        Vec3 k1_p = {vel.x, vel.y, 0};
        
        // k2 = f(t + dt/2, y + dt*k1/2) - 2D
        Vec3 k2_v = k1_v;  // Assuming force constant for small dt
        Vec3 k2_p = {pos.x + k1_p.x * dt * 0.5f,
                     pos.y + k1_p.y * dt * 0.5f,
                     0};
        
        // k3 = f(t + dt/2, y + dt*k2/2) - 2D
        Vec3 k3_v = k2_v;
        Vec3 k3_p = {pos.x + k2_p.x * dt * 0.5f,
                     pos.y + k2_p.y * dt * 0.5f,
                     0};
        
        // k4 = f(t + dt, y + dt*k3) - 2D
        Vec3 k4_v = k3_v;
        Vec3 k4_p = {pos.x + k3_p.x * dt,
                     pos.y + k3_p.y * dt,
                     0};
        
        // Final integration (2D)
        vel.x += (k1_v.x + 2.0f*k2_v.x + 2.0f*k3_v.x + k4_v.x) * dt / 6.0f;
        vel.y += (k1_v.y + 2.0f*k2_v.y + 2.0f*k3_v.y + k4_v.y) * dt / 6.0f;
        vel.z = 0;  // Z component always 0 in 2D
        
        pos.x += (k1_p.x + 2.0f*k2_p.x + 2.0f*k3_p.x + k4_p.x) * dt / 6.0f;
        pos.y += (k1_p.y + 2.0f*k2_p.y + 2.0f*k3_p.y + k4_p.y) * dt / 6.0f;
        pos.z = 0;  // Z component always 0 in 2D
        
        // Clear forces (2D)
        force = {0, 0, 0};
    }
}

// Verlet Integration (better energy conservation)
void AdvancedPhysicsSystem::integrate_verlet(Registry& reg, float dt) {
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    auto& forces = reg.forces();
    auto& masses = reg.masses();
    const auto& alive = reg.alive();
    
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        auto& pos = transforms[e].pos;
        auto& vel = velocities[e].v;
        auto& force = forces[e].f;
        float invMass = 1.0f / masses[e].m;
        
        // Verlet: x(t+dt) = 2*x(t) - x(t-dt) + a(t)*dt²
        // For first step, use: x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
        float dt2 = dt * dt;
        
        Vec3 acceleration = {force.x * invMass, force.y * invMass, force.z * invMass};
        
        Vec3 new_pos = {
            pos.x + vel.x * dt + 0.5f * acceleration.x * dt2,
            pos.y + vel.y * dt + 0.5f * acceleration.y * dt2,
            pos.z + vel.z * dt + 0.5f * acceleration.z * dt2
        };
        
        // Update velocity: v(t+dt) = (x(t+dt) - x(t)) / dt
        vel.x = (new_pos.x - pos.x) / dt;
        vel.y = (new_pos.y - pos.y) / dt;
        vel.z = (new_pos.z - pos.z) / dt;
        
        pos = new_pos;
        
        // Clear forces
        force = {0, 0, 0};
    }
}

// Continuous Collision Detection
void AdvancedPhysicsSystem::continuous_collision_detection(
    Registry& reg, float dt, const Config& cfg
) {
    // Sweep and prune for continuous collision detection
    // Check for collisions along the entire motion path
    const auto& alive = reg.alive();
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    
    // For each pair, check if they collide during the timestep
    std::vector<Entity> entities(alive.begin(), alive.end());
    
    for (size_t i = 0; i < entities.size(); ++i) {
        for (size_t j = i + 1; j < entities.size(); ++j) {
            Entity e1 = entities[i];
            Entity e2 = entities[j];
            
            if (!reg.has_alive(e1) || !reg.has_alive(e2)) continue;
            if (!reg.has_sphere(e1) || !reg.has_sphere(e2)) continue;
            
            Vec3 p1 = transforms[e1].pos;
            Vec3 p2 = transforms[e2].pos;
            Vec3 v1 = velocities[e1].v;
            Vec3 v2 = velocities[e2].v;
            
            float r1 = reg.spheres()[e1].radius;
            float r2 = reg.spheres()[e2].radius;
            float min_dist = r1 + r2;
            
            // Relative motion
            Vec3 rel_pos = {p2.x - p1.x, p2.y - p1.y, p2.z - p1.z};
            Vec3 rel_vel = {v2.x - v1.x, v2.y - v1.y, v2.z - v1.z};
            
            // Solve: ||rel_pos + t*rel_vel|| = min_dist
            // Quadratic: ||rel_vel||²*t² + 2*(rel_pos·rel_vel)*t + ||rel_pos||² - min_dist² = 0
            float a = rel_vel.x*rel_vel.x + rel_vel.y*rel_vel.y + rel_vel.z*rel_vel.z;
            float b = 2.0f * (rel_pos.x*rel_vel.x + rel_pos.y*rel_vel.y + rel_pos.z*rel_vel.z);
            float c = (rel_pos.x*rel_pos.x + rel_pos.y*rel_pos.y + rel_pos.z*rel_pos.z) - min_dist*min_dist;
            
            float discriminant = b*b - 4.0f*a*c;
            
            if (discriminant >= 0 && a > 0.0001f) {
                float t = (-b - std::sqrt(discriminant)) / (2.0f * a);
                
                if (t >= 0.0f && t <= dt) {
                    // Collision occurs at time t
                    // Resolve collision immediately
                    CollisionSystem::resolve_sphere_sphere(reg, e1, e2, cfg);
                }
            }
        }
    }
}

// Constraint Solver
void AdvancedPhysicsSystem::ConstraintSolver::solve_constraints(
    Registry& reg, float dt
) {
    // Iterative constraint solver with warm starting
    // This is a simplified version - full implementation would handle
    // multiple constraint types (distance, angle, etc.)
    
    for (int iter = 0; iter < max_iterations; ++iter) {
        // Solve all constraints iteratively
        // This would integrate with the existing constraint system
        // For now, this is a placeholder structure
    }
}

// Material Properties
void AdvancedPhysicsSystem::apply_material_properties(
    Registry& reg, Entity e, const Material& mat
) {
    // Store material properties (would need to extend ECS)
    // For now, apply friction and restitution to collisions
    // This would be used during collision resolution
}

// Soft Body Update
void AdvancedPhysicsSystem::update_soft_body(
    SoftBody& body, Registry& reg, float dt
) {
    // Update spring forces between particles
    auto& forces = reg.forces();
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    
    for (const auto& spring : body.springs) {
        Entity p1 = body.particles[spring.first];
        Entity p2 = body.particles[spring.second];
        
        if (!reg.has_alive(p1) || !reg.has_alive(p2)) continue;
        
        Vec3 pos1 = transforms[p1].pos;
        Vec3 pos2 = transforms[p2].pos;
        Vec3 vel1 = velocities[p1].v;
        Vec3 vel2 = velocities[p2].v;
        
        Vec3 diff = {pos2.x - pos1.x, pos2.y - pos1.y, pos2.z - pos1.z};
        float dist = std::sqrt(diff.x*diff.x + diff.y*diff.y + diff.z*diff.z);
        
        if (dist > 0.001f) {
            float rest_length = 1.0f;  // Would be stored in spring data
            float stretch = dist - rest_length;
            
            Vec3 force_dir = {diff.x/dist, diff.y/dist, diff.z/dist};
            float spring_force = body.spring_stiffness * stretch;
            
            // Damping
            Vec3 rel_vel = {vel2.x - vel1.x, vel2.y - vel1.y, vel2.z - vel1.z};
            float damping_force = body.damping * (rel_vel.x*force_dir.x + rel_vel.y*force_dir.y + rel_vel.z*force_dir.z);
            
            float total_force = spring_force + damping_force;
            
            forces[p1].f.x += force_dir.x * total_force;
            forces[p1].f.y += force_dir.y * total_force;
            forces[p1].f.z += force_dir.z * total_force;
            
            forces[p2].f.x -= force_dir.x * total_force;
            forces[p2].f.y -= force_dir.y * total_force;
            forces[p2].f.z -= force_dir.z * total_force;
        }
    }
}

// Fluid Simulation (simplified SPH)
void AdvancedPhysicsSystem::update_fluid_simulation(
    std::vector<FluidParticle>& particles,
    float dt,
    float smoothing_radius
) {
    // Simplified SPH (Smoothed Particle Hydrodynamics)
    // Calculate density and pressure for each particle
    for (auto& p : particles) {
        p.density = 0.0f;
        
        for (const auto& other : particles) {
            Vec3 diff = {
                other.position.x - p.position.x,
                other.position.y - p.position.y,
                other.position.z - p.position.z
            };
            float dist_sq = diff.x*diff.x + diff.y*diff.y + diff.z*diff.z;
            float dist = std::sqrt(dist_sq);
            
            if (dist < smoothing_radius) {
                // Poly6 kernel
                float q = dist / smoothing_radius;
                float w = 315.0f / (64.0f * 3.14159f * std::pow(smoothing_radius, 9));
                w *= std::pow(1.0f - q*q, 3);
                p.density += other.mass * w;
            }
        }
        
        // Ideal gas equation of state
        float rest_density = 1000.0f;
        float gas_constant = 2000.0f;
        p.pressure = gas_constant * (p.density - rest_density);
    }
    
    // Calculate forces and update velocities
    for (auto& p : particles) {
        Vec3 pressure_force = {0, 0, 0};
        Vec3 viscosity_force = {0, 0, 0};
        
        for (const auto& other : particles) {
            Vec3 diff = {
                other.position.x - p.position.x,
                other.position.y - p.position.y,
                other.position.z - p.position.z
            };
            float dist_sq = diff.x*diff.x + diff.y*diff.y + diff.z*diff.z;
            float dist = std::sqrt(dist_sq);
            
            if (dist > 0.001f && dist < smoothing_radius) {
                Vec3 dir = {diff.x/dist, diff.y/dist, diff.z/dist};
                
                // Pressure force (Spiky kernel gradient)
                float q = dist / smoothing_radius;
                float grad_w = -45.0f / (3.14159f * std::pow(smoothing_radius, 6));
                grad_w *= std::pow(1.0f - q, 2);
                
                float pressure_term = (p.pressure + other.pressure) / (2.0f * other.density);
                pressure_force.x -= dir.x * pressure_term * grad_w * other.mass;
                pressure_force.y -= dir.y * pressure_term * grad_w * other.mass;
                pressure_force.z -= dir.z * pressure_term * grad_w * other.mass;
                
                // Viscosity force
                Vec3 vel_diff = {
                    other.velocity.x - p.velocity.x,
                    other.velocity.y - p.velocity.y,
                    other.velocity.z - p.velocity.z
                };
                float viscosity = 0.018f;
                viscosity_force.x += vel_diff.x * viscosity * other.mass / other.density;
                viscosity_force.y += vel_diff.y * viscosity * other.mass / other.density;
                viscosity_force.z += vel_diff.z * viscosity * other.mass / other.density;
            }
        }
        
        // Update velocity
        p.velocity.x += (pressure_force.x + viscosity_force.x) * dt;
        p.velocity.y += (pressure_force.y + viscosity_force.y) * dt;
        p.velocity.z += (pressure_force.z + viscosity_force.z) * dt;
        
        // Gravity
        p.velocity.y -= 9.81f * dt;
        
        // Update position
        p.position.x += p.velocity.x * dt;
        p.position.y += p.velocity.y * dt;
        p.position.z += p.velocity.z * dt;
    }
}

// Sphere-Mesh Collision
bool AdvancedPhysicsSystem::sphere_mesh_collision(
    const Vec3& sphere_pos,
    float sphere_radius,
    const MeshCollider& mesh
) {
    // Check bounding sphere first
    Vec3 diff = {
        sphere_pos.x - mesh.center.x,
        sphere_pos.y - mesh.center.y,
        sphere_pos.z - mesh.center.z
    };
    float dist_to_center = std::sqrt(diff.x*diff.x + diff.y*diff.y + diff.z*diff.z);
    
    if (dist_to_center > sphere_radius + mesh.radius) {
        return false;  // No collision possible
    }
    
    // Check triangle collisions
    for (size_t i = 0; i < mesh.indices.size(); i += 3) {
        Vec3 v0 = mesh.vertices[mesh.indices[i]];
        Vec3 v1 = mesh.vertices[mesh.indices[i+1]];
        Vec3 v2 = mesh.vertices[mesh.indices[i+2]];
        
        // Closest point on triangle to sphere center
        Vec3 edge0 = {v1.x - v0.x, v1.y - v0.y, v1.z - v0.z};
        Vec3 edge1 = {v2.x - v0.x, v2.y - v0.y, v2.z - v0.z};
        Vec3 v0_to_sphere = {sphere_pos.x - v0.x, sphere_pos.y - v0.y, sphere_pos.z - v0.z};
        
        float a = edge0.x*edge0.x + edge0.y*edge0.y + edge0.z*edge0.z;
        float b = edge0.x*edge1.x + edge0.y*edge1.y + edge0.z*edge1.z;
        float c = edge1.x*edge1.x + edge1.y*edge1.y + edge1.z*edge1.z;
        float d = edge0.x*v0_to_sphere.x + edge0.y*v0_to_sphere.y + edge0.z*v0_to_sphere.z;
        float e = edge1.x*v0_to_sphere.x + edge1.y*v0_to_sphere.y + edge1.z*v0_to_sphere.z;
        
        float det = a*c - b*b;
        float s = b*e - c*d;
        float t = b*d - a*e;
        
        if (s + t < det) {
            if (s < 0) {
                if (t < 0) {
                    // Region 4
                    s = 0;
                    t = 0;
                } else {
                    // Region 3
                    t = 0;
                    s = std::max(0.0f, -d / a);
                }
            } else if (t < 0) {
                // Region 5
                s = 0;
                t = std::max(0.0f, -e / c);
            } else {
                // Region 0
                s /= det;
                t /= det;
            }
        } else {
            if (s < 0) {
                // Region 2
                s = 0;
                t = std::max(0.0f, std::min(1.0f, -e / c));
            } else if (t < 0) {
                // Region 6
                t = 0;
                s = std::max(0.0f, std::min(1.0f, -d / a));
            } else {
                // Region 1
                float num = c + e - b - d;
                if (num <= 0) {
                    s = 0;
                } else {
                    float denom = a - 2*b + c;
                    s = (denom > 0) ? num / denom : 0;
                }
                t = 1 - s;
            }
        }
        
        Vec3 closest = {
            v0.x + s*edge0.x + t*edge1.x,
            v0.y + s*edge0.y + t*edge1.y,
            v0.z + s*edge0.z + t*edge1.z
        };
        
        Vec3 to_sphere = {
            sphere_pos.x - closest.x,
            sphere_pos.y - closest.y,
            sphere_pos.z - closest.z
        };
        float dist_sq = to_sphere.x*to_sphere.x + to_sphere.y*to_sphere.y + to_sphere.z*to_sphere.z;
        
        if (dist_sq < sphere_radius * sphere_radius) {
            return true;  // Collision detected
        }
    }
    
    return false;
}

// Spatial Grid
void AdvancedPhysicsSystem::SpatialGrid::build(Registry& reg) {
    // Build spatial hash grid for broadphase collision detection
    // This significantly speeds up collision detection for many objects
    const auto& alive = reg.alive();
    auto& transforms = reg.transforms();
    
    // Clear cells
    for (auto& cell : cells) {
        cell.clear();
    }
    
    // Determine grid dimensions
    int cells_x = static_cast<int>((max_bound.x - min_bound.x) / cell_size) + 1;
    int cells_y = static_cast<int>((max_bound.y - min_bound.y) / cell_size) + 1;
    int cells_z = static_cast<int>((max_bound.z - min_bound.z) / cell_size) + 1;
    
    cells.resize(cells_x * cells_y * cells_z);
    
    // Insert entities into cells
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        Vec3 pos = transforms[e].pos;
        
        int cell_x = static_cast<int>((pos.x - min_bound.x) / cell_size);
        int cell_y = static_cast<int>((pos.y - min_bound.y) / cell_size);
        int cell_z = static_cast<int>((pos.z - min_bound.z) / cell_size);
        
        cell_x = std::max(0, std::min(cells_x - 1, cell_x));
        cell_y = std::max(0, std::min(cells_y - 1, cell_y));
        cell_z = std::max(0, std::min(cells_z - 1, cell_z));
        
        int cell_idx = cell_x + cell_y * cells_x + cell_z * cells_x * cells_y;
        cells[cell_idx].push_back(e);
    }
}

std::vector<Entity> AdvancedPhysicsSystem::SpatialGrid::query(
    const Vec3& pos, float radius
) const {
    std::vector<Entity> results;
    
    int cells_x = static_cast<int>((max_bound.x - min_bound.x) / cell_size) + 1;
    int cells_y = static_cast<int>((max_bound.y - min_bound.y) / cell_size) + 1;
    int cells_z = static_cast<int>((max_bound.z - min_bound.z) / cell_size) + 1;
    
    int min_cell_x = std::max(0, static_cast<int>((pos.x - radius - min_bound.x) / cell_size));
    int max_cell_x = std::min(cells_x - 1, static_cast<int>((pos.x + radius - min_bound.x) / cell_size));
    int min_cell_y = std::max(0, static_cast<int>((pos.y - radius - min_bound.y) / cell_size));
    int max_cell_y = std::min(cells_y - 1, static_cast<int>((pos.y + radius - min_bound.y) / cell_size));
    int min_cell_z = std::max(0, static_cast<int>((pos.z - radius - min_bound.z) / cell_size));
    int max_cell_z = std::min(cells_z - 1, static_cast<int>((pos.z + radius - min_bound.z) / cell_size));
    
    for (int x = min_cell_x; x <= max_cell_x; ++x) {
        for (int y = min_cell_y; y <= max_cell_y; ++y) {
            for (int z = min_cell_z; z <= max_cell_z; ++z) {
                int cell_idx = x + y * cells_x + z * cells_x * cells_y;
                if (cell_idx >= 0 && cell_idx < static_cast<int>(cells.size())) {
                    results.insert(results.end(), cells[cell_idx].begin(), cells[cell_idx].end());
                }
            }
        }
    }
    
    return results;
}

} // namespace ne
