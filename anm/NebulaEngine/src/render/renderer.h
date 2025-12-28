#pragma once
#include "../ecs/registry.h"
#include "camera.h"
#include "../core/types.h"
#include <vector>

namespace ne {

// M4: Debug draw primitives
struct DebugLine {
    Vec3 start;
    Vec3 end;
    Vec3 color = {1.0f, 1.0f, 1.0f}; // White by default
};

struct DebugSphere {
    Vec3 center;
    float radius;
    Vec3 color = {1.0f, 1.0f, 1.0f};
};

struct DebugContact {
    Vec3 position;
    Vec3 normal;
    float magnitude;
};

// M4: Abstract renderer interface
// Rendering reads world state only (no modification of physics)
class IRenderer {
public:
    virtual ~IRenderer() = default;
    
    // Frame lifecycle
    virtual void begin_frame() = 0;
    virtual void end_frame() = 0;
    
    // Render world state (read-only)
    virtual void render_world(const Registry& reg, const Camera& camera) = 0;
    
    // Debug drawing
    virtual void draw_line(const DebugLine& line) = 0;
    virtual void draw_sphere(const DebugSphere& sphere) = 0;
    virtual void draw_contact(const DebugContact& contact) = 0;
    
    // Batch debug drawing (for efficiency)
    virtual void draw_lines(const std::vector<DebugLine>& lines) {
        for (const auto& line : lines) {
            draw_line(line);
        }
    }
    
    virtual void draw_spheres(const std::vector<DebugSphere>& spheres) {
        for (const auto& sphere : spheres) {
            draw_sphere(sphere);
        }
    }
    
    virtual void draw_contacts(const std::vector<DebugContact>& contacts) {
        for (const auto& contact : contacts) {
            draw_contact(contact);
        }
    }
    
    // M6: Ray tracing support
    virtual bool supports_ray_tracing() const { return false; }
    virtual void enable_ray_tracing(bool enable) {}
    virtual bool ray_tracing_enabled() const { return false; }
};

// M4: Null renderer (for headless/testing)
class NullRenderer : public IRenderer {
public:
    void begin_frame() override {}
    void end_frame() override {}
    void render_world(const Registry& reg, const Camera& camera) override {}
    void draw_line(const DebugLine& line) override {}
    void draw_sphere(const DebugSphere& sphere) override {}
    void draw_contact(const DebugContact& contact) override {}
};

// M6: Hybrid renderer (supports both raster and ray tracing)
class HybridRenderer : public IRenderer {
public:
    HybridRenderer() = default;
    
    void begin_frame() override {}
    void end_frame() override {}
    void render_world(const Registry& reg, const Camera& camera) override {}
    void draw_line(const DebugLine& line) override {}
    void draw_sphere(const DebugSphere& sphere) override {}
    void draw_contact(const DebugContact& contact) override {}
    
    // M6: Ray tracing support
    bool supports_ray_tracing() const override { return true; }
    void enable_ray_tracing(bool enable) override { m_rt_enabled = enable; }
    bool ray_tracing_enabled() const override { return m_rt_enabled; }
    
private:
    bool m_rt_enabled = false;
};

} // namespace ne
