#pragma once

namespace ne {

// M3: Unit system
// Base unit is meters. All physics calculations use meters internally.
// Scale factors allow simulation at different scales (ant to supernova)

// Unit conversion constants
namespace units {
    // Length conversions (all relative to meters)
    constexpr float METER = 1.0f;
    constexpr float CENTIMETER = 0.01f;
    constexpr float MILLIMETER = 0.001f;
    constexpr float KILOMETER = 1000.0f;
    
    // Mass conversions (all relative to kilograms)
    constexpr float KILOGRAM = 1.0f;
    constexpr float GRAM = 0.001f;
    constexpr float MILLIGRAM = 0.000001f;
    
    // Time conversions (all relative to seconds)
    constexpr float SECOND = 1.0f;
    constexpr float MILLISECOND = 0.001f;
    
    // Helper functions for unit conversions
    inline float to_meters(float value, float unit) { return value * unit; }
    inline float from_meters(float meters, float unit) { return meters / unit; }
}

// World scale presets
namespace scale {
    // Scale factors for different scenarios
    // Scale affects: sizes, distances, but NOT time or mass ratios
    constexpr float ANT = 0.001f;        // 1mm = 1 unit (ant-scale: mm)
    constexpr float HUMAN = 1.0f;        // 1m = 1 unit (human-scale: meters)
    constexpr float CITY = 1.0f;         // 1m = 1 unit (city-scale: meters)
    constexpr float PLANETARY = 1000.0f; // 1km = 1 unit (planetary-scale: km)
    constexpr float STELLAR = 1000000.0f; // 1Mm = 1 unit (stellar-scale: megameters)
}

} // namespace ne
