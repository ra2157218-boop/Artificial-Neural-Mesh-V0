#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"
#include <vector>

namespace ne {

struct Config;

// Advanced physics system - RE Engine / Unreal Engine level
struct AdvancedPhysicsSystem {
    // Advanced time integration methods
    static void integrate_rk4(Registry& reg, float dt);  // 4th order Runge-Kutta
    static void integrate_verlet(Registry& reg, float dt);  // Verlet integration
    
    // Continuous collision detection (prevents tunneling)
    static void continuous_collision_detection(Registry& reg, float dt, const Config& cfg);
    
    // Advanced constraint solver (iterative with warm starting)
    struct ConstraintSolver {
        int max_iterations = 10;
        float tolerance = 0.001f;
        bool warm_start = true;
        
        void solve_constraints(Registry& reg, float dt);
    };
    
    // Advanced material properties
    struct Material {
        float density = 1.0f;        // kg/m³
        float friction = 0.5f;       // Friction coefficient
        float restitution = 0.3f;    // Bounciness (0-1)
        float young_modulus = 1e6f;  // Elastic modulus (Pa)
        float poisson_ratio = 0.3f;   // Poisson's ratio
    };
    
    // Apply advanced material properties
    static void apply_material_properties(Registry& reg, Entity e, const Material& mat);
    
    // Soft body dynamics (basic implementation)
    struct SoftBody {
        std::vector<Entity> particles;
        std::vector<std::pair<int, int>> springs;  // Particle indices
        float spring_stiffness = 1000.0f;
        float damping = 0.1f;
    };
    
    static void update_soft_body(SoftBody& body, Registry& reg, float dt);
    
    // Fluid dynamics (basic SPH-like)
    struct FluidParticle {
        Vec3 position;
        Vec3 velocity;
        float density = 1000.0f;  // kg/m³ (water)
        float pressure = 0.0f;
        float mass = 0.01f;  // kg
    };
    
    static void update_fluid_simulation(
        std::vector<FluidParticle>& particles,
        float dt,
        float smoothing_radius = 0.1f
    );
    
    // Advanced collision shapes
    struct MeshCollider {
        std::vector<Vec3> vertices;
        std::vector<int> indices;  // Triangle indices
        Vec3 center;
        float radius;  // Bounding sphere radius
    };
    
    static bool sphere_mesh_collision(
        const Vec3& sphere_pos,
        float sphere_radius,
        const MeshCollider& mesh
    );
    
    // Spatial acceleration structures
    struct SpatialGrid {
        float cell_size;
        Vec3 min_bound;
        Vec3 max_bound;
        std::vector<std::vector<Entity>> cells;
        
        void build(Registry& reg);
        std::vector<Entity> query(const Vec3& pos, float radius) const;
    };
};

} // namespace ne
