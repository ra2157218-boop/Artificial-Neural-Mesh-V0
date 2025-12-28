#pragma once
#include "../ecs/registry.h"

namespace ne {

struct Config;

struct PhysicsSystem {
    static void apply_gravity(Registry& reg, const Config& cfg);
    static void integrate(Registry& reg, float dt);
    static void apply_damping(Registry& reg, float damping);
};

}