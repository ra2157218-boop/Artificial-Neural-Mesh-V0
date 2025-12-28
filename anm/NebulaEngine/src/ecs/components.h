#pragma once
#include <cmath>

namespace ne {

// 2D Vector for ANM (Astrophysical N-body Merger)
struct Vec2 {
    float x = 0, y = 0;
    Vec2 operator+(const Vec2& o) const { return {x+o.x, y+o.y}; }
    Vec2 operator-(const Vec2& o) const { return {x-o.x, y-o.y}; }
    Vec2 operator*(float s) const { return {x*s, y*s}; }
    Vec2& operator+=(const Vec2& o) { x+=o.x; y+=o.y; return *this; }
    Vec2& operator-=(const Vec2& o) { x-=o.x; y-=o.y; return *this; }
    float length() const { return std::sqrt(x*x + y*y); }
    Vec2 normalized() const { float len = length(); return len > 0 ? Vec2{x/len, y/len} : Vec2{0,0}; }
};

// Alias for compatibility (Vec3 -> Vec2 for 2D)
// Vec3 now uses only x,y components (z ignored in 2D)
struct Vec3 {
    float x = 0, y = 0, z = 0;  // z kept for compatibility but ignored
    Vec3 operator+(const Vec3& o) const { return {x+o.x, y+o.y, 0}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x, y-o.y, 0}; }
    Vec3 operator*(float s) const { return {x*s, y*s, 0}; }
    Vec3& operator+=(const Vec3& o) { x+=o.x; y+=o.y; z=0; return *this; }
    Vec3& operator-=(const Vec3& o) { x-=o.x; y-=o.y; z=0; return *this; }
    // Implicit conversion from Vec2
    Vec3(const Vec2& v) : x(v.x), y(v.y), z(0) {}
    Vec3() : x(0), y(0), z(0) {}
};

struct Transform { Vec2 pos; };
struct Velocity  { Vec2 v;   };
struct Mass      { float m = 1.0f; };
struct Force     { Vec2 f;   };

// M1: Collision shapes (2D)
struct Circle {
    float radius = 0.5f;
};

// Alias for compatibility
using Sphere = Circle;  // Sphere is now Circle in 2D

struct AABB {
    Vec2 half_extents = {0.5f, 0.5f}; // half-width, half-height (2D)
};

} // namespace ne