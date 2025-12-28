#include "video_capture.h"
#include "render/debug_draw.h"
#include "render/camera.h"
#include <cmath>
#include <algorithm>
#include <fstream>
#include <cstring>

namespace ne {

VideoCapture::VideoCapture(int width, int height) 
    : m_width(width), m_height(height), m_frame_count(0) {
}

VideoCapture::~VideoCapture() {
    finish();
}

bool VideoCapture::start(const std::string& output_path) {
    m_output_path = output_path;
    m_frame_count = 0;
    m_frames.clear();
    return true;
}

Vec3 VideoCapture::project_point(const Vec3& pos, const Camera& camera) {
    // Simple perspective projection
    Vec3 forward = camera.forward();
    Vec3 right = camera.right();
    Vec3 up = camera.up; // Direct member access
    
    Vec3 to_point = pos - camera.position;
    
    // Project onto camera space (dot product)
    float x = to_point.x * right.x + to_point.y * right.y + to_point.z * right.z;
    float y = to_point.x * up.x + to_point.y * up.y + to_point.z * up.z;
    float z = to_point.x * forward.x + to_point.y * forward.y + to_point.z * forward.z;
    
    if (z <= 0.1f) return {0, 0, -1}; // Behind camera
    
    // Perspective divide
    float fov_rad = camera.fov * 3.14159f / 180.0f;
    float aspect = float(m_width) / float(m_height);
    float f = 1.0f / tanf(fov_rad / 2.0f);
    
    float screen_x = (x / z) * f * aspect;
    float screen_y = (y / z) * f;
    
    // Convert to pixel coordinates
    int px = int((screen_x + 1.0f) * 0.5f * m_width);
    int py = int((1.0f - screen_y) * 0.5f * m_height);
    
    return {float(px), float(py), z};
}

void VideoCapture::set_pixel(int x, int y, const Vec3& color, std::vector<uint8_t>& buffer) {
    if (x < 0 || x >= m_width || y < 0 || y >= m_height) return;
    
    int idx = (y * m_width + x) * 4;
    buffer[idx + 0] = uint8_t(std::clamp(color.x * 255.0f, 0.0f, 255.0f));
    buffer[idx + 1] = uint8_t(std::clamp(color.y * 255.0f, 0.0f, 255.0f));
    buffer[idx + 2] = uint8_t(std::clamp(color.z * 255.0f, 0.0f, 255.0f));
    buffer[idx + 3] = 255; // Alpha
}

Vec3 VideoCapture::get_pixel(int x, int y, const std::vector<uint8_t>& buffer) {
    if (x < 0 || x >= m_width || y < 0 || y >= m_height) {
        return {0, 0, 0};
    }
    int idx = (y * m_width + x) * 4;
    return {
        buffer[idx + 0] / 255.0f,
        buffer[idx + 1] / 255.0f,
        buffer[idx + 2] / 255.0f
    };
}

void VideoCapture::draw_line_3d(const Vec3& p1, const Vec3& p2, const Vec3& color,
                                  const Camera& camera, std::vector<uint8_t>& buffer) {
    Vec3 proj1 = project_point(p1, camera);
    Vec3 proj2 = project_point(p2, camera);
    
    if (proj1.z < 0 || proj2.z < 0) return; // Behind camera
    
    int x1 = int(proj1.x), y1 = int(proj1.y);
    int x2 = int(proj2.x), y2 = int(proj2.y);
    
    int dx = std::abs(x2 - x1);
    int dy = std::abs(y2 - y1);
    int steps = std::max(dx, dy);
    if (steps == 0) return;
    
    // Fade based on depth
    float z1 = proj1.z, z2 = proj2.z;
    
    for (int i = 0; i <= steps; ++i) {
        float t = i / float(steps);
        int x = x1 + int((x2 - x1) * t);
        int y = y1 + int((y2 - y1) * t);
        float z = z1 + (z2 - z1) * t;
        
        Vec3 line_color = color;
        
        // Fade with distance
        if (m_trajectory_fade) {
            float fade = 1.0f / (1.0f + z * 0.1f);
            line_color = line_color * fade;
        }
        
        // Anti-aliased line
        if (m_anti_aliasing) {
            Vec3 existing = get_pixel(x, y, buffer);
            Vec3 blended = existing * 0.5f + line_color * 0.5f;
            set_pixel(x, y, blended, buffer);
        } else {
            set_pixel(x, y, line_color, buffer);
        }
    }
}

void VideoCapture::draw_sphere(const Vec3& center, float radius, const Vec3& color,
                                const Camera& camera, std::vector<uint8_t>& buffer) {
    Vec3 proj_center = project_point(center, camera);
    if (proj_center.z < 0) return; // Behind camera
    
    int cx = int(proj_center.x);
    int cy = int(proj_center.y);
    
    // Calculate screen-space radius
    float screen_radius = (radius / proj_center.z) * m_height * 0.5f;
    float r = screen_radius;
    if (r < 1.0f) r = 1.0f;
    
    // Directional light (from top-right)
    Vec3 light_dir = {0.5f, 1.0f, 0.3f};
    float light_len = std::sqrt(light_dir.x * light_dir.x + light_dir.y * light_dir.y + light_dir.z * light_dir.z);
    light_dir = {light_dir.x / light_len, light_dir.y / light_len, light_dir.z / light_len};
    
    // Calculate sphere normal at center (simplified - assumes sphere center)
    Vec3 to_camera = camera.position - center;
    float to_cam_len = std::sqrt(to_camera.x * to_camera.x + to_camera.y * to_camera.y + to_camera.z * to_camera.z);
    Vec3 normal = {to_camera.x / to_cam_len, to_camera.y / to_cam_len, to_camera.z / to_cam_len};
    
    // Base lighting
    float NdotL = normal.x * light_dir.x + normal.y * light_dir.y + normal.z * light_dir.z;
    float base_light = std::max(0.3f, NdotL * 0.7f + 0.5f);
    
    // Draw filled circle with anti-aliasing
    int r_int = int(r) + 1;
    for (int dy = -r_int; dy <= r_int; ++dy) {
        for (int dx = -r_int; dx <= r_int; ++dx) {
            float dist = std::sqrt(float(dx * dx + dy * dy));
            float dist_sq = float(dx * dx + dy * dy);
            
            if (dist <= r) {
                // Calculate normal at this point on sphere (simplified)
                float u = float(dx) / r;
                float v = float(dy) / r;
                float w = std::sqrt(std::max(0.0f, 1.0f - u * u - v * v));
                
                // Lighting based on normal
                float light = base_light;
                if (m_shadows) {
                    // Simple shadow: darker on bottom
                    float shadow_factor = 1.0f - std::max(0.0f, -v) * 0.3f;
                    light *= shadow_factor;
                }
                
                // Anti-aliasing edge
                float alpha = 1.0f;
                if (m_anti_aliasing && dist > r - 1.0f) {
                    alpha = std::max(0.0f, r - dist);
                }
                
                Vec3 shaded_color = color * light;
                
                // Blend with existing pixel if anti-aliasing
                if (m_anti_aliasing && alpha < 1.0f) {
                    Vec3 existing = get_pixel(cx + dx, cy + dy, buffer);
                    shaded_color = existing * (1.0f - alpha) + shaded_color * alpha;
                }
                
                set_pixel(cx + dx, cy + dy, shaded_color, buffer);
            }
        }
    }
}

void VideoCapture::render_frame_to_buffer(const Registry& reg, const Camera& camera,
                                           std::vector<uint8_t>& buffer,
                                           const std::vector<DebugDraw::Trajectory>* trajectories) {
    buffer.resize(m_width * m_height * 4, 0);
    
    // Clear to dark blue sky
    for (int y = 0; y < m_height; ++y) {
        for (int x = 0; x < m_width; ++x) {
            float sky_factor = float(y) / float(m_height);
            Vec3 sky_color = {0.2f + 0.1f * sky_factor, 
                              0.3f + 0.2f * sky_factor, 
                              0.5f + 0.3f * sky_factor};
            set_pixel(x, y, sky_color, buffer);
        }
    }
    
    // Draw ground plane (simple grid)
    Vec3 ground_color = {0.3f, 0.5f, 0.2f};
    for (int x = 0; x < m_width; ++x) {
        for (int z_step = -10; z_step <= 10; ++z_step) {
            Vec3 ground_pos = {float(x) / float(m_width) * 20.0f - 10.0f, 0.0f, float(z_step)};
            Vec3 proj = project_point(ground_pos, camera);
            if (proj.z > 0 && proj.z < 50.0f) {
                int px = int(proj.x);
                int py = int(proj.y);
                if (px >= 0 && px < m_width && py >= 0 && py < m_height) {
                    // Draw ground line
                    for (int y = py; y < m_height; ++y) {
                        if (y < m_height) {
                            float fade = 1.0f - (y - py) / float(m_height - py) * 0.5f;
                            set_pixel(px, y, ground_color * fade, buffer);
                        }
                    }
                }
            }
        }
    }
    
    // Draw trajectories first (behind spheres) with fade effect
    if (trajectories) {
        for (const auto& traj : *trajectories) {
            if (traj.positions.size() < 2) continue;
            
            for (size_t j = 1; j < traj.positions.size(); ++j) {
                const auto& p1 = traj.positions[j-1];
                const auto& p2 = traj.positions[j];
                
                Vec3 trail_color = traj.color * 0.6f; // Dimmer for trails
                
                // Fade effect: older parts of trail are dimmer
                if (m_trajectory_fade) {
                    float age = float(j) / float(traj.positions.size());
                    float fade = 0.3f + 0.7f * (1.0f - age); // Fade from 1.0 to 0.3
                    trail_color = trail_color * fade;
                }
                
                draw_line_3d(p1, p2, trail_color, camera, buffer);
            }
        }
    }
    
    // Draw entities
    const auto& alive = reg.alive();
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        
        const auto& t = reg.transform(e);
        
        if (reg.has_sphere(e)) {
            const auto& sphere = reg.sphere(e);
            Vec3 sphere_color = {0.8f, 0.3f, 0.2f}; // Red-orange
            draw_sphere(t.pos, sphere.radius, sphere_color, camera, buffer);
        }
    }
}

void VideoCapture::capture_frame(const Registry& reg, const Camera& camera,
                                  const std::vector<DebugDraw::Trajectory>* trajectories) {
    std::vector<uint8_t> frame;
    render_frame_to_buffer(reg, camera, frame, trajectories);
    m_frames.push_back(std::move(frame));
    m_frame_count++;
}

bool VideoCapture::finish() {
    if (m_frames.empty()) return false;
    
    // Write frames as PPM images (simple format)
    // Then user can use ffmpeg to convert to video
    std::string frame_dir = m_output_path + "_frames";
    
    // Create frame directory (simplified - just write frames with prefix)
    std::string base_name = m_output_path;
    size_t ext_pos = base_name.find_last_of('.');
    if (ext_pos != std::string::npos) {
        base_name = base_name.substr(0, ext_pos);
    }
    
    // Write each frame as PPM
    for (size_t i = 0; i < m_frames.size(); ++i) {
        std::string frame_file = base_name + "_frame_" + std::to_string(i) + ".ppm";
        std::ofstream out(frame_file, std::ios::binary);
        if (!out) continue;
        
        out << "P6\n" << m_width << " " << m_height << "\n255\n";
        const auto& frame = m_frames[i];
        for (int y = 0; y < m_height; ++y) {
            for (int x = 0; x < m_width; ++x) {
                int idx = (y * m_width + x) * 4;
                out.write(reinterpret_cast<const char*>(&frame[idx]), 3); // RGB only
            }
        }
    }
    
    // Write FFmpeg command script
    std::string script_file = base_name + "_encode.sh";
    std::ofstream script(script_file);
    if (script) {
        script << "#!/bin/bash\n";
        script << "# FFmpeg command to encode frames to video\n";
        script << "# Run: bash " << script_file << "\n\n";
        script << "ffmpeg -y -framerate 30 -pattern_type glob -i '" 
               << base_name << "_frame_*.ppm' -c:v libx264 -pix_fmt yuv420p "
               << m_output_path << "\n";
        script << "echo \"Video created: " << m_output_path << "\"\n";
        script << "echo \"Cleaning up frame files...\"\n";
        script << "rm " << base_name << "_frame_*.ppm\n";
    }
    
    m_frames.clear();
    return true;
}

} // namespace ne
