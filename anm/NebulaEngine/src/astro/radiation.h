#pragma once
#include "../ecs/registry.h"
#include "../core/types.h"
#include <vector>

namespace ne {

// M7: Radiation models
// Light emission, absorption, and scattering

struct RadiationSource {
    Vec3 position;
    float luminosity;      // Total power output (Watts)
    float temperature;     // Blackbody temperature (Kelvin)
    Vec3 color;            // RGB color (normalized)
};

struct RadiationField {
    Vec3 position;
    float intensity;       // Radiation intensity at this point
    Vec3 direction;         // Direction of radiation
    float wavelength;      // Wavelength (for spectral calculations)
};

class RadiationSystem {
public:
    // Compute blackbody radiation color from temperature
    // Uses Planck's law approximation
    static Vec3 blackbody_color(float temperature);
    
    // Compute radiation intensity at a point from sources
    static float compute_intensity(const Vec3& position, 
                                    const std::vector<RadiationSource>& sources);
    
    // Apply radiation pressure (for stellar winds, etc.)
    static Vec3 compute_radiation_pressure(const Vec3& position,
                                            const std::vector<RadiationSource>& sources,
                                            float cross_section = 1.0f);
    
    // Compute absorption (simplified - exponential decay)
    static float compute_absorption(float initial_intensity, float distance, 
                                     float absorption_coeff = 0.1f);
    
    // Stefan-Boltzmann law: P = σ * T^4 * A
    static float stefan_boltzmann_luminosity(float temperature, float radius, 
                                               float sigma = 5.670374419e-8f);
    
private:
    // Planck's law approximation (simplified)
    static float planck_approximation(float wavelength, float temperature);
};

} // namespace ne
