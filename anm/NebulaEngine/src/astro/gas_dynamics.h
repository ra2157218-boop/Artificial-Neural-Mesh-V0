#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"
#include <vector>

namespace ne {

// M7: Gas dynamics models
// Simplified fluid/gas simulation for stellar atmospheres, nebulas, etc.

struct GasParticle {
    Vec3 position;
    Vec3 velocity;
    float density;
    float temperature;
    float pressure;
};

class GasDynamics {
public:
    // Update gas particles based on pressure, temperature, and density
    static void update_gas_particles(std::vector<GasParticle>& particles, float dt);
    
    // Compute pressure from ideal gas law: P = ρRT
    static float compute_pressure(float density, float temperature, float R = 8.314f);
    
    // Compute density from pressure and temperature
    static float compute_density(float pressure, float temperature, float R = 8.314f);
    
    // Apply pressure forces to nearby particles
    static void apply_pressure_forces(std::vector<GasParticle>& particles, float dt);
    
    // Simple diffusion model
    static void apply_diffusion(std::vector<GasParticle>& particles, float dt, float diffusion_coeff = 0.1f);
    
private:
    // Find nearby particles within radius
    static std::vector<size_t> find_nearby(const std::vector<GasParticle>& particles, 
                                            size_t idx, float radius);
};

} // namespace ne
