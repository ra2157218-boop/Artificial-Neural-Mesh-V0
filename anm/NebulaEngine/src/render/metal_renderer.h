#pragma once
#include "renderer.h"
#include <memory>

// Forward declarations for Objective-C types
#ifdef __OBJC__
@class MTKView;
@class MTKDevice;
@class MTLRenderPipelineState;
@class MTLCommandQueue;
@class MTLBuffer;
@class MTLRenderCommandEncoder;
#else
struct MTKView;
struct MTKDevice;
struct MTLRenderPipelineState;
struct MTLCommandQueue;
struct MTLBuffer;
struct MTLRenderCommandEncoder;
#endif

namespace ne {

// M5: Metal renderer implementation
// Concrete implementation of IRenderer using Metal on macOS/iOS
class MetalRenderer : public IRenderer {
public:
    MetalRenderer();
    ~MetalRenderer();
    
    // Initialize Metal device and setup
    bool init(void* view); // MTKView* passed as void* to avoid ObjC in header
    
    // IRenderer interface
    void begin_frame() override;
    void end_frame() override;
    void render_world(const Registry& reg, const Camera& camera) override;
    void draw_line(const DebugLine& line) override;
    void draw_sphere(const DebugSphere& sphere) override;
    void draw_contact(const DebugContact& contact) override;
    
    // M5: PBR material properties
    struct PBRMaterial {
        Vec3 albedo = {0.8f, 0.8f, 0.8f};
        float metallic = 0.0f;
        float roughness = 0.5f;
        float ao = 1.0f;
    };
    
    void set_material(const PBRMaterial& material) { m_material = material; }
    
private:
    // Metal objects (opaque pointers to avoid ObjC in header)
    void* m_device = nullptr;           // MTKDevice*
    void* m_commandQueue = nullptr;     // MTLCommandQueue*
    void* m_view = nullptr;             // MTKView*
    void* m_pipelineState = nullptr;    // MTLRenderPipelineState*
    
    // Frame state
    bool m_frameStarted = false;
    PBRMaterial m_material;
    
    // Helper methods
    bool create_pipeline();
    void setup_view(void* view);
};

} // namespace ne
