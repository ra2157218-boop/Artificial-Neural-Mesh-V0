// M5: Metal renderer implementation (Objective-C++)
#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>
#import <CoreFoundation/CoreFoundation.h>
#include "metal_renderer.h"
#include "../ecs/registry.h"
#include "camera.h"
#include <vector>
#include <cmath>

// Metal shader source (embedded)
static const char* shader_source = R"(
#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float3 position [[attribute(0)]];
    float3 normal [[attribute(1)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 worldPos;
    float3 normal;
};

struct Uniforms {
    float4x4 viewMatrix;
    float4x4 projMatrix;
    float3 cameraPos;
};

// Simple vertex shader
vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                              constant Uniforms& uniforms [[buffer(0)]]) {
    VertexOut out;
    float4 worldPos = float4(in.position, 1.0);
    out.worldPos = worldPos.xyz;
    out.position = uniforms.projMatrix * uniforms.viewMatrix * worldPos;
    out.normal = in.normal;
    return out;
}

// Simple PBR fragment shader
fragment float4 fragment_main(VertexOut in [[stage_in]],
                               constant float3& albedo [[buffer(1)]],
                               constant float& metallic [[buffer(2)]],
                               constant float& roughness [[buffer(3)]]) {
    // Simple lighting (directional light)
    float3 lightDir = normalize(float3(1.0, 1.0, 1.0));
    float3 normal = normalize(in.normal);
    float NdotL = max(dot(normal, lightDir), 0.0);
    
    // Simple PBR approximation
    float3 diffuse = albedo * NdotL;
    float3 ambient = albedo * 0.1;
    float3 color = diffuse + ambient;
    
    return float4(color, 1.0);
}
)";

namespace ne {

MetalRenderer::MetalRenderer() {
}

MetalRenderer::~MetalRenderer() {
    // Metal objects are automatically released by ARC
}

bool MetalRenderer::init(void* view) {
    @autoreleasepool {
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) {
            return false;
        }
        
        m_device = (__bridge void*)device;
        CFRetain((__bridge CFTypeRef)device);
        
        id<MTLCommandQueue> commandQueue = [device newCommandQueue];
        m_commandQueue = (__bridge void*)commandQueue;
        CFRetain((__bridge CFTypeRef)commandQueue);
        
        setup_view(view);
        
        return create_pipeline();
    }
}

void MetalRenderer::setup_view(void* view) {
    @autoreleasepool {
        MTKView* mtkView = (__bridge MTKView*)view;
        if (mtkView) {
            id<MTLDevice> device = (__bridge id<MTLDevice>)m_device;
            mtkView.device = device;
            mtkView.clearColor = MTLClearColorMake(0.1, 0.1, 0.15, 1.0); // Dark blue-gray
            mtkView.colorPixelFormat = MTLPixelFormatBGRA8Unorm;
            mtkView.depthStencilPixelFormat = MTLPixelFormatDepth32Float;
            m_view = (__bridge void*)view;
            CFRetain((__bridge CFTypeRef)view);
        }
    }
}

bool MetalRenderer::create_pipeline() {
    @autoreleasepool {
        id<MTLDevice> device = (__bridge id<MTLDevice>)m_device;
        
        // Compile shader
        NSError* error = nil;
        id<MTLLibrary> library = [device newLibraryWithSource:@(shader_source) options:nil error:&error];
        if (!library) {
            return false;
        }
        
        id<MTLFunction> vertexFunction = [library newFunctionWithName:@"vertex_main"];
        id<MTLFunction> fragmentFunction = [library newFunctionWithName:@"fragment_main"];
        
        if (!vertexFunction || !fragmentFunction) {
            return false;
        }
        
        // Create pipeline descriptor
        MTLRenderPipelineDescriptor* pipelineDescriptor = [[MTLRenderPipelineDescriptor alloc] init];
        pipelineDescriptor.vertexFunction = vertexFunction;
        pipelineDescriptor.fragmentFunction = fragmentFunction;
        pipelineDescriptor.colorAttachments[0].pixelFormat = MTLPixelFormatBGRA8Unorm;
        pipelineDescriptor.depthAttachmentPixelFormat = MTLPixelFormatDepth32Float;
        
        // Vertex layout
        MTLVertexDescriptor* vertexDescriptor = [[MTLVertexDescriptor alloc] init];
        vertexDescriptor.attributes[0].format = MTLVertexFormatFloat3;
        vertexDescriptor.attributes[0].offset = 0;
        vertexDescriptor.attributes[0].bufferIndex = 0;
        vertexDescriptor.attributes[1].format = MTLVertexFormatFloat3;
        vertexDescriptor.attributes[1].offset = 12;
        vertexDescriptor.attributes[1].bufferIndex = 0;
        vertexDescriptor.layouts[0].stride = 24;
        vertexDescriptor.layouts[0].stepRate = 1;
        vertexDescriptor.layouts[0].stepFunction = MTLVertexStepFunctionPerVertex;
        pipelineDescriptor.vertexDescriptor = vertexDescriptor;
        
        id<MTLRenderPipelineState> pipelineState = [device newRenderPipelineStateWithDescriptor:pipelineDescriptor error:&error];
        if (!pipelineState) {
            return false;
        }
        
        m_pipelineState = (__bridge void*)pipelineState;
        CFRetain((__bridge CFTypeRef)pipelineState);
        return true;
    }
}

void MetalRenderer::begin_frame() {
    m_frameStarted = true;
}

void MetalRenderer::end_frame() {
    m_frameStarted = false;
}

void MetalRenderer::render_world(const Registry& reg, const Camera& camera) {
    @autoreleasepool {
        if (!m_view || !m_device || !m_commandQueue || !m_pipelineState) {
            return;
        }
        
        MTKView* mtkView = (__bridge MTKView*)m_view;
        id<MTLDevice> device = (__bridge id<MTLDevice>)m_device;
        id<MTLCommandQueue> commandQueue = (__bridge id<MTLCommandQueue>)m_commandQueue;
        id<MTLRenderPipelineState> pipelineState = (__bridge id<MTLRenderPipelineState>)m_pipelineState;
        
        id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
        if (!commandBuffer) return;
        
        MTLRenderPassDescriptor* renderPassDescriptor = mtkView.currentRenderPassDescriptor;
        if (!renderPassDescriptor) return;
        
        id<MTLRenderCommandEncoder> renderEncoder = [commandBuffer renderCommandEncoderWithDescriptor:renderPassDescriptor];
        if (!renderEncoder) return;
        
        [renderEncoder setRenderPipelineState:pipelineState];
        
        // Simple view/projection setup
        // For now, we'll use a simple orthographic projection
        simd_float4x4 viewMatrix = {
            .columns[0] = {1, 0, 0, 0},
            .columns[1] = {0, 1, 0, 0},
            .columns[2] = {0, 0, 1, 0},
            .columns[3] = {0, 0, -10, 1}
        };
        
        float aspect = mtkView.bounds.size.width / mtkView.bounds.size.height;
        float fov = camera.fov * 3.14159f / 180.0f;
        float near = camera.near_plane;
        float far = camera.far_plane;
        
        // Simple perspective projection
        float f = 1.0f / tanf(fov / 2.0f);
        simd_float4x4 projMatrix = {
            .columns[0] = {f / aspect, 0, 0, 0},
            .columns[1] = {0, f, 0, 0},
            .columns[2] = {0, 0, (far + near) / (near - far), -1},
            .columns[3] = {0, 0, (2 * far * near) / (near - far), 0}
        };
        
        struct Uniforms {
            simd_float4x4 viewMatrix;
            simd_float4x4 projMatrix;
            simd_float3 cameraPos;
        } uniforms;
        uniforms.viewMatrix = viewMatrix;
        uniforms.projMatrix = projMatrix;
        uniforms.cameraPos = {camera.position.x, camera.position.y, camera.position.z};
        
        id<MTLBuffer> uniformBuffer = [device newBufferWithBytes:&uniforms length:sizeof(uniforms) options:MTLResourceStorageModeShared];
        [renderEncoder setVertexBuffer:uniformBuffer offset:0 atIndex:0];
        
        // Generate simple sphere geometry (icosphere approximation)
        // For each entity with sphere, draw it
        const auto& alive = reg.alive();
        int sphere_count = 0;
        for (Entity e : alive) {
            if (!reg.has_alive(e) || !reg.has_sphere(e)) continue;
            sphere_count++;
            
            const auto& t = reg.transform(e);
            const auto& sphere = reg.sphere(e);
            
            // Create a simple quad per sphere (simplified rendering)
            // In full implementation, would use instanced sphere rendering
            // For now, we'll just clear and show we're rendering
        }
        
        // Set material
        float albedo[3] = {m_material.albedo.x, m_material.albedo.y, m_material.albedo.z};
        id<MTLBuffer> albedoBuffer = [device newBufferWithBytes:albedo length:sizeof(albedo) options:MTLResourceStorageModeShared];
        [renderEncoder setFragmentBuffer:albedoBuffer offset:0 atIndex:1];
        
        float metallic = m_material.metallic;
        id<MTLBuffer> metallicBuffer = [device newBufferWithBytes:&metallic length:sizeof(metallic) options:MTLResourceStorageModeShared];
        [renderEncoder setFragmentBuffer:metallicBuffer offset:0 atIndex:2];
        
        float roughness = m_material.roughness;
        id<MTLBuffer> roughnessBuffer = [device newBufferWithBytes:&roughness length:sizeof(roughness) options:MTLResourceStorageModeShared];
        [renderEncoder setFragmentBuffer:roughnessBuffer offset:0 atIndex:3];
        
        // Draw call would go here with actual geometry
        // For now, we ensure the frame is cleared and ready
        
        [renderEncoder endEncoding];
        [commandBuffer presentDrawable:mtkView.currentDrawable];
        [commandBuffer commit];
    }
}

void MetalRenderer::draw_line(const DebugLine& line) {
    // Debug line drawing (would use line rendering in full implementation)
}

void MetalRenderer::draw_sphere(const DebugSphere& sphere) {
    // Debug sphere drawing (would use instanced sphere rendering)
}

void MetalRenderer::draw_contact(const DebugContact& contact) {
    // Contact visualization (would draw contact point and normal)
}

} // namespace ne
