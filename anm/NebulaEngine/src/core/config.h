#pragma once

namespace ne {

struct Config {
    double fixed_dt = 1.0 / 60.0;   // deterministic
    int    max_steps_per_tick = 8;  // spiral-of-death guard
    float  gravity = -9.81f;
    float  ground_y = 0.0f;
    float  restitution = 0.0f;      // 0 = no bounce
    float  friction = 0.5f;          // M2: friction coefficient (0 = no friction, 1 = full friction)
    
    // M3: World scaling
    float  world_scale = 1.0f;       // Scale factor for world (1.0 = human scale, 0.001 = ant scale)
    float  broadphase_cell_size = 2.0f; // Cell size for spatial partitioning (in world units)
};

} // namespace ne