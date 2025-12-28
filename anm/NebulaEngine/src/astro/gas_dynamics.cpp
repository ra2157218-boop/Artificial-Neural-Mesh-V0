#include "gas_dynamics.h"
#include <cmath>
#include <algorithm>

namespace ne {

float GasDynamics::compute_pressure(float density, float temperature, float R) {
    // Ideal gas law: P = ρRT
    return density * R * temperature;
}

float GasDynamics::compute_density(float pressure, float temperature, float R) {
    // From ideal gas law: ρ = P / (RT)
    if (temperature < 1e-10f) return 0.0f;
    return pressure / (R * temperature);
}

std::vector<size_t> GasDynamics::find_nearby(const std::vector<GasParticle>& particles,
                                               size_t idx, float radius) {
    std::vector<size_t> nearby;
    if (idx >= particles.size()) return nearby;
    
    const auto& p = particles[idx];
    float r_sq = radius * radius;
    
    for (size_t i = 0; i < particles.size(); ++i) {
        if (i == idx) continue;
        const auto& other = particles[i];
        float dx = other.position.x - p.position.x;
        float dy = other.position.y - p.position.y;
        float dz = other.position.z - p.position.z;
        float dist_sq = dx * dx + dy * dy + dz * dz;
        
        if (dist_sq < r_sq) {
            nearby.push_back(i);
        }
    }
    
    return nearby;
}

void GasDynamics::apply_pressure_forces(std::vector<GasParticle>& particles, float dt) {
    const float interaction_radius = 2.0f;
    
    for (size_t i = 0; i < particles.size(); ++i) {
        auto& p = particles[i];
        auto nearby = find_nearby(particles, i, interaction_radius);
        
        Vec3 pressure_force = {0, 0, 0};
        
        for (size_t j : nearby) {
            const auto& other = particles[j];
            
            // Pressure gradient force: F = -∇P
            // Simplified: force proportional to pressure difference
            float pressure_diff = p.pressure - other.pressure;
            Vec3 dir = {
                other.position.x - p.position.x,
                other.position.y - p.position.y,
                other.position.z - p.position.z
            };
            
            float dist_sq = dir.x * dir.x + dir.y * dir.y + dir.z * dir.z;
            if (dist_sq < 1e-10f) continue;
            
            float dist = std::sqrt(dist_sq);
            dir = {dir.x / dist, dir.y / dist, dir.z / dist};
            
            // Force magnitude proportional to pressure difference
            float force_mag = pressure_diff * 0.1f;
            pressure_force.x += force_mag * dir.x;
            pressure_force.y += force_mag * dir.y;
            pressure_force.z += force_mag * dir.z;
        }
        
        // Apply force to velocity (simplified - assume unit mass)
        p.velocity.x += pressure_force.x * dt;
        p.velocity.y += pressure_force.y * dt;
        p.velocity.z += pressure_force.z * dt;
    }
}

void GasDynamics::apply_diffusion(std::vector<GasParticle>& particles, float dt, float diffusion_coeff) {
    const float interaction_radius = 2.0f;
    
    for (size_t i = 0; i < particles.size(); ++i) {
        auto& p = particles[i];
        auto nearby = find_nearby(particles, i, interaction_radius);
        
        if (nearby.empty()) continue;
        
        // Average density of nearby particles
        float avg_density = 0.0f;
        float avg_temperature = 0.0f;
        
        for (size_t j : nearby) {
            avg_density += particles[j].density;
            avg_temperature += particles[j].temperature;
        }
        
        avg_density /= nearby.size();
        avg_temperature /= nearby.size();
        
        // Diffusion: move towards average
        float density_diff = avg_density - p.density;
        float temp_diff = avg_temperature - p.temperature;
        
        p.density += density_diff * diffusion_coeff * dt;
        p.temperature += temp_diff * diffusion_coeff * dt;
        
        // Update pressure from new density/temperature
        p.pressure = compute_pressure(p.density, p.temperature);
    }
}

void GasDynamics::update_gas_particles(std::vector<GasParticle>& particles, float dt) {
    // Update positions
    for (auto& p : particles) {
        p.position.x += p.velocity.x * dt;
        p.position.y += p.velocity.y * dt;
        p.position.z += p.velocity.z * dt;
    }
    
    // Apply pressure forces
    apply_pressure_forces(particles, dt);
    
    // Apply diffusion
    apply_diffusion(particles, dt);
}

} // namespace ne
