#include "physics_system.h"
#include "../core/config.h"
#include <cmath>

namespace ne {

void PhysicsSystem::apply_gravity(Registry& reg, const Config& cfg) {
    auto& masses = reg.masses();
    auto& forces = reg.forces();
    const auto& alive = reg.alive();

    for (Entity e : alive) {
        if (reg.has_alive(e)) {
            forces[e].f.y += masses[e].m * cfg.gravity;
        }
    }
}

void PhysicsSystem::apply_damping(Registry& reg, float damping) {
    auto& velocities = reg.velocities();
    const auto& alive = reg.alive();

    for (Entity e : alive) {
        if (reg.has_alive(e)) {
            velocities[e].v.x *= (1.0f - damping);
            velocities[e].v.y *= (1.0f - damping);
            // Z component removed (2D)
        }
    }
}

void PhysicsSystem::integrate(Registry& reg, float dt) {
    auto& transforms = reg.transforms();
    auto& velocities = reg.velocities();
    auto& forces     = reg.forces();
    auto& masses     = reg.masses();
    const auto& alive = reg.alive();

    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;

        auto& v = velocities[e].v;
        auto& f = forces[e].f;
        float invMass = 1.0f / masses[e].m;

        v.x += f.x * invMass * dt;
        v.y += f.y * invMass * dt;
        // Z component removed (2D)

        transforms[e].pos.x += v.x * dt;
        transforms[e].pos.y += v.y * dt;
        // Z component removed (2D)

        // clear forces (2D)
        f = {0,0,0};  // z component ignored in 2D
    }
}

} // namespace ne
