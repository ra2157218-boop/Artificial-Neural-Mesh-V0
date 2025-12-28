#include "radiation.h"
#include <cmath>
#include <algorithm>

namespace ne {

Vec3 RadiationSystem::blackbody_color(float temperature) {
    // Simplified blackbody color approximation
    // Based on Planck's law approximation for visible spectrum
    
    if (temperature < 100.0f) {
        return {0.0f, 0.0f, 0.1f}; // Very cold - dark blue
    }
    
    // Normalize temperature to 0-1 range (roughly 1000K to 10000K)
    float t_norm = std::clamp((temperature - 1000.0f) / 9000.0f, 0.0f, 1.0f);
    
    // Approximate color based on temperature
    // Cool -> red, Medium -> white/yellow, Hot -> blue
    Vec3 color;
    
    if (t_norm < 0.33f) {
        // Red to orange
        float t_local = t_norm / 0.33f;
        color = {1.0f, 0.3f + 0.4f * t_local, 0.0f};
    } else if (t_norm < 0.66f) {
        // Orange to white
        float t_local = (t_norm - 0.33f) / 0.33f;
        color = {1.0f, 0.7f + 0.3f * t_local, 0.3f + 0.7f * t_local};
    } else {
        // White to blue
        float t_local = (t_norm - 0.66f) / 0.34f;
        color = {1.0f - 0.3f * t_local, 1.0f - 0.2f * t_local, 1.0f};
    }
    
    // Normalize
    float max_val = std::max({color.x, color.y, color.z});
    if (max_val > 1e-6f) {
        color = {color.x / max_val, color.y / max_val, color.z / max_val};
    }
    
    return color;
}

float RadiationSystem::compute_intensity(const Vec3& position,
                                          const std::vector<RadiationSource>& sources) {
    float total_intensity = 0.0f;
    
    for (const auto& source : sources) {
        float dx = position.x - source.position.x;
        float dy = position.y - source.position.y;
        float dz = position.z - source.position.z;
        float dist_sq = dx * dx + dy * dy + dz * dz;
        
        if (dist_sq < 1e-10f) {
            total_intensity += source.luminosity; // At source
            continue;
        }
        
        float dist = std::sqrt(dist_sq);
        // Inverse square law: I = L / (4πr²)
        float intensity = source.luminosity / (4.0f * 3.14159f * dist_sq);
        total_intensity += intensity;
    }
    
    return total_intensity;
}

Vec3 RadiationSystem::compute_radiation_pressure(const Vec3& position,
                                                   const std::vector<RadiationSource>& sources,
                                                   float cross_section) {
    Vec3 pressure = {0, 0, 0};
    
    for (const auto& source : sources) {
        Vec3 dir = {
            position.x - source.position.x,
            position.y - source.position.y,
            position.z - source.position.z
        };
        
        float dist_sq = dir.x * dir.x + dir.y * dir.y + dir.z * dir.z;
        if (dist_sq < 1e-10f) continue;
        
        float dist = std::sqrt(dist_sq);
        dir = {dir.x / dist, dir.y / dist, dir.z / dist};
        
        // Radiation pressure: P = I / c (simplified, c = speed of light)
        float intensity = source.luminosity / (4.0f * 3.14159f * dist_sq);
        float pressure_mag = intensity * cross_section / 3e8f; // c ≈ 3e8 m/s
        
        pressure.x += pressure_mag * dir.x;
        pressure.y += pressure_mag * dir.y;
        pressure.z += pressure_mag * dir.z;
    }
    
    return pressure;
}

float RadiationSystem::compute_absorption(float initial_intensity, float distance,
                                           float absorption_coeff) {
    // Exponential absorption: I = I₀ * e^(-αd)
    return initial_intensity * std::exp(-absorption_coeff * distance);
}

float RadiationSystem::stefan_boltzmann_luminosity(float temperature, float radius,
                                                     float sigma) {
    // L = 4πR²σT⁴
    float area = 4.0f * 3.14159f * radius * radius;
    float T4 = temperature * temperature * temperature * temperature;
    return area * sigma * T4;
}

float RadiationSystem::planck_approximation(float wavelength, float temperature) {
    // Simplified Planck's law: B(λ,T) ≈ (2hc²/λ⁵) * e^(-hc/(λkT))
    // Very simplified for our purposes
    const float h = 6.626e-34f; // Planck constant
    const float c = 3e8f;        // Speed of light
    const float k = 1.381e-23f; // Boltzmann constant
    
    if (wavelength < 1e-10f || temperature < 1e-10f) return 0.0f;
    
    float exponent = (h * c) / (wavelength * k * temperature);
    if (exponent > 50.0f) return 0.0f; // Avoid overflow
    
    float numerator = 2.0f * h * c * c;
    float denominator = wavelength * wavelength * wavelength * wavelength * wavelength;
    
    return (numerator / denominator) * std::exp(-exponent);
}

} // namespace ne
