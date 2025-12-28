#pragma once
#include "core/types.h"
#include "ecs/registry.h"
#include "render/camera.h"
#include "render/debug_draw.h"
#include <vector>
#include <string>

namespace ne {

// Frame capture system for video output
class VideoCapture {
public:
    VideoCapture(int width = 1920, int height = 1080);
    ~VideoCapture();
    
    // Start capturing frames
    bool start(const std::string& output_path);
    
    // Capture a frame from the world state
    void capture_frame(const Registry& reg, const Camera& camera, 
                       const std::vector<DebugDraw::Trajectory>* trajectories = nullptr);
    
    // Finish capturing and encode video
    bool finish();
    
    // Get current frame count
    int frame_count() const { return m_frame_count; }
    
    // Quality settings
    void set_anti_aliasing(bool enabled) { m_anti_aliasing = enabled; }
    void set_shadows(bool enabled) { m_shadows = enabled; }
    void set_trajectory_fade(bool enabled) { m_trajectory_fade = enabled; }
    
private:
    int m_width, m_height;
    int m_frame_count;
    std::string m_output_path;
    std::vector<std::vector<uint8_t>> m_frames; // RGBA frames
    
    // Quality settings
    bool m_anti_aliasing = true;
    bool m_shadows = true;
    bool m_trajectory_fade = true;
    
    void render_frame_to_buffer(const Registry& reg, const Camera& camera, 
                                std::vector<uint8_t>& buffer,
                                const std::vector<DebugDraw::Trajectory>* trajectories = nullptr);
    void draw_sphere(const Vec3& center, float radius, const Vec3& color,
                     const Camera& camera, std::vector<uint8_t>& buffer);
    void draw_line_3d(const Vec3& p1, const Vec3& p2, const Vec3& color,
                      const Camera& camera, std::vector<uint8_t>& buffer);
    Vec3 project_point(const Vec3& pos, const Camera& camera);
    void set_pixel(int x, int y, const Vec3& color, std::vector<uint8_t>& buffer);
    Vec3 get_pixel(int x, int y, const std::vector<uint8_t>& buffer);
};

} // namespace ne
