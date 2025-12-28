// Helper: Generate sphere geometry for Metal rendering
#import <Metal/Metal.h>
#include "../core/types.h"
#include <vector>
#include <cmath>

namespace ne {
namespace metal_helpers {

// Generate sphere vertices and indices
void generate_sphere_geometry(float radius, int segments, 
                               std::vector<float>& vertices,
                               std::vector<uint16_t>& indices) {
    vertices.clear();
    indices.clear();
    
    // Generate sphere vertices
    for (int lat = 0; lat <= segments; ++lat) {
        float theta = 3.14159f * lat / segments;
        float sinTheta = std::sin(theta);
        float cosTheta = std::cos(theta);
        
        for (int lon = 0; lon <= segments; ++lon) {
            float phi = 2.0f * 3.14159f * lon / segments;
            float sinPhi = std::sin(phi);
            float cosPhi = std::cos(phi);
            
            float x = cosPhi * sinTheta;
            float y = cosTheta;
            float z = sinPhi * sinTheta;
            
            // Position
            vertices.push_back(radius * x);
            vertices.push_back(radius * y);
            vertices.push_back(radius * z);
            
            // Normal (same as position for unit sphere)
            vertices.push_back(x);
            vertices.push_back(y);
            vertices.push_back(z);
        }
    }
    
    // Generate indices
    for (int lat = 0; lat < segments; ++lat) {
        for (int lon = 0; lon < segments; ++lon) {
            int first = lat * (segments + 1) + lon;
            int second = first + segments + 1;
            
            indices.push_back(first);
            indices.push_back(second);
            indices.push_back(first + 1);
            
            indices.push_back(second);
            indices.push_back(second + 1);
            indices.push_back(first + 1);
        }
    }
}

// Create Metal buffer from data
id<MTLBuffer> create_buffer(id<MTLDevice> device, const void* data, size_t size) {
    return [device newBufferWithBytes:data length:size options:MTLResourceStorageModeShared];
}

} // namespace metal_helpers
} // namespace ne
