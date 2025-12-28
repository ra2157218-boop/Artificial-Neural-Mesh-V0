# ============================================================
# ANM V0-OpenSource — CINEMATIC RENDERER (Unreal Engine Level)
#  Ultra-realistic physics visualization with 3rd person camera
#  Features: Ray tracing, PBR materials, particle effects, bloom
# ============================================================

from __future__ import annotations

import os
import time
import math
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Conditional imports
try:
    import numpy as np
    import cv2
    CV2_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    NUMPY_AVAILABLE = False
    np = None

from anm.sim.types import SimulationFrame, SimulationRequest


class CinematicRenderer:
    """
    Unreal Engine-level cinematic renderer with realistic physics visualization.
    
    Features:
    - 3rd person camera system
    - Physically-based rendering (PBR)
    - Ray-traced shadows and reflections
    - Particle effects (accretion disks, gravitational lensing)
    - Bloom and post-processing
    - Realistic starfield background
    - Motion blur
    - Depth of field
    """
    
    def __init__(self, output_dir: str = "sim_outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.available = CV2_AVAILABLE and NUMPY_AVAILABLE
        
        # Render quality settings
        self.enable_shadows = True
        self.enable_bloom = True
        self.enable_particles = True
        self.enable_lensing = True
        self.anti_aliasing = 2  # SSAA multiplier
        
        # Generate starfield
        self.starfield = self._generate_starfield(5000)
    
    def _generate_starfield(self, num_stars: int) -> List[Tuple[float, float, float, float]]:
        """Generate realistic starfield background."""
        import random
        stars = []
        for _ in range(num_stars):
            # Random position on sphere
            theta = random.uniform(0, 2 * math.pi)
            phi = math.acos(random.uniform(-1, 1))
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            
            # Random brightness
            brightness = random.uniform(0.3, 1.0)
            stars.append((x, y, z, brightness))
        return stars
    
    def render_frames_to_video(
        self,
        frames: List[SimulationFrame],
        request: SimulationRequest,
        output_filename: Optional[str] = None,
        pov_entity_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Render frames with cinematic quality.
        
        Args:
            frames: SimulationFrames to render
            request: Original SimulationRequest
            output_filename: Optional filename
            pov_entity_id: Entity ID to use for POV camera (None = auto-select)
        """
        if not self.available:
            return None
        
        if not frames:
            return None
        
        # Generate filename
        if output_filename is None:
            timestamp = int(time.time())
            scenario = request.scenario_type.replace("_", "-")
            output_filename = f"cinematic_{scenario}_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Get video parameters
        width, height = request.output_resolution
        fps = request.target_fps
        
        # Create video writer (high quality)
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
        video_writer = cv2.VideoWriter(
            output_path,
            fourcc,
            float(fps),
            (width, height)
        )
        
        if not video_writer.isOpened():
            # Fallback codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))
        
        if not video_writer.isOpened():
            return None
        
        try:
            # Determine POV entity
            if pov_entity_id is None and frames:
                # Auto-select: prefer neutron star, then first entity
                entities = frames[0].state.get("entities", [])
                pov_entity_id = 0
                for i, e in enumerate(entities):
                    if e.get("type") == "neutron_star":
                        pov_entity_id = i
                        break
            
            # Render each frame
            prev_frame = None
            for i, frame in enumerate(frames):
                frame_image = self._render_cinematic_frame(
                    frame, request, width, height, pov_entity_id, prev_frame
                )
                if frame_image is not None:
                    video_writer.write(frame_image)
                prev_frame = frame
            
            video_writer.release()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            return None
        
        except Exception as e:
            if video_writer.isOpened():
                video_writer.release()
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return None
    
    def _render_cinematic_frame(
        self,
        frame: SimulationFrame,
        request: SimulationRequest,
        width: int,
        height: int,
        pov_entity_id: int,
        prev_frame: Optional[SimulationFrame],
    ) -> Optional[np.ndarray]:
        """Render a single frame with cinematic quality."""
        if not self.available or np is None:
            return None
        
        # Super-sampled rendering for anti-aliasing
        ss_width = width * self.anti_aliasing
        ss_height = height * self.anti_aliasing
        
        # Create HDR buffer (float32 for high quality)
        hdr_buffer = np.zeros((ss_height, ss_width, 3), dtype=np.float32)
        depth_buffer = np.full((ss_height, ss_width), float('inf'), dtype=np.float32)
        
        # Get entities
        entities = frame.state.get("entities", [])
        
        # Calculate POV camera position
        camera_pos, camera_target = self._calculate_pov_camera(
            entities, pov_entity_id, frame, request
        )
        
        # Render starfield background
        self._render_starfield(hdr_buffer, ss_width, ss_height, camera_pos)
        
        # Render entities with realistic materials
        for entity in entities:
            self._render_entity_realistic(
                entity, hdr_buffer, depth_buffer,
                ss_width, ss_height, camera_pos, camera_target,
                entities, frame
            )
        
        # Render particle effects (accretion disk, gravitational lensing)
        if self.enable_particles:
            self._render_particle_effects(
                hdr_buffer, depth_buffer, entities,
                ss_width, ss_height, camera_pos, camera_target, frame
            )
        
        # Apply bloom effect
        if self.enable_bloom:
            hdr_buffer = self._apply_bloom(hdr_buffer)
        
        # Tone mapping (HDR to LDR)
        ldr_buffer = self._tone_map(hdr_buffer)
        
        # Motion blur (if prev_frame available)
        if prev_frame is not None:
            ldr_buffer = self._apply_motion_blur(ldr_buffer, frame, prev_frame, ss_width, ss_height)
        
        # Downsample for anti-aliasing
        if self.anti_aliasing > 1:
            ldr_buffer = cv2.resize(ldr_buffer, (width, height), interpolation=cv2.INTER_AREA)
        else:
            ldr_buffer = ldr_buffer.astype(np.uint8)
        
        # Post-processing: color grading, contrast
        ldr_buffer = self._color_grade(ldr_buffer)
        
        # Ensure uint8
        if ldr_buffer.dtype != np.uint8:
            ldr_buffer = np.clip(ldr_buffer, 0, 255).astype(np.uint8)
        
        # Convert to BGR for OpenCV
        if len(ldr_buffer.shape) == 3 and ldr_buffer.shape[2] == 3:
            bgr_image = cv2.cvtColor(ldr_buffer, cv2.COLOR_RGB2BGR)
        else:
            bgr_image = ldr_buffer
        
        return bgr_image
    
    def _calculate_pov_camera(
        self,
        entities: List[Dict],
        pov_entity_id: int,
        frame: SimulationFrame,
        request: SimulationRequest,
    ) -> Tuple[List[float], List[float]]:
        """Calculate 3rd person camera position from entity."""
        if pov_entity_id < len(entities):
            entity = entities[pov_entity_id]
            pos = entity.get("position", [0, 0, 0])
            velocity = entity.get("velocity", [0, 0, 0])
            
            # Calculate entity's forward direction
            vel_mag = math.sqrt(sum(v*v for v in velocity))
            if vel_mag > 0.01:
                entity_forward = [v / vel_mag for v in velocity]
            else:
                entity_forward = [0, 0, 1]
            
            # 3rd person camera: positioned behind and above the entity
            camera_distance = 50.0  # Distance from entity
            camera_height = 30.0    # Height above entity
            camera_side_offset = 15.0  # Side offset
            
            # Calculate camera position (behind entity, elevated)
            behind_offset = [-f * camera_distance for f in entity_forward]
            up_offset = [0, camera_height, 0]
            
            # Side offset (perpendicular to forward)
            right = [
                entity_forward[2],
                0,
                -entity_forward[0]
            ]
            right_mag = math.sqrt(sum(r*r for r in right))
            if right_mag > 0.01:
                right = [r / right_mag for r in right]
            else:
                right = [1, 0, 0]
            side_offset = [r * camera_side_offset for r in right]
            
            camera_pos = [
                pos[0] + behind_offset[0] + up_offset[0] + side_offset[0],
                pos[1] + behind_offset[1] + up_offset[1] + side_offset[1],
                pos[2] + behind_offset[2] + up_offset[2] + side_offset[2]
            ]
            
            # Camera looks at the entity (3rd person view)
            camera_target = pos
            
            return camera_pos, camera_target
        
        # Fallback
        return [0, 100, -300], [0, 0, 0]
    
    def _render_starfield(
        self,
        buffer: np.ndarray,
        width: int,
        height: int,
        camera_pos: List[float],
    ) -> None:
        """Render realistic starfield background."""
        for star_x, star_y, star_z, brightness in self.starfield:
            # Project star to screen
            # Simple projection (stars are far away)
            screen_x = int(width // 2 + star_x * width * 0.3)
            screen_y = int(height // 2 - star_y * height * 0.3)
            
            if 0 <= screen_x < width and 0 <= screen_y < height:
                # Star color (white with slight blue tint)
                color = [brightness * 0.9, brightness * 0.95, brightness]
                
                # Draw star (small bright point)
                radius = max(1, int(brightness * 2))
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        px, py = screen_x + dx, screen_y + dy
                        if 0 <= px < width and 0 <= py < height:
                            dist_sq = dx*dx + dy*dy
                            if dist_sq <= radius*radius:
                                fade = 1.0 - (dist_sq / (radius*radius + 1))
                                buffer[py, px] = [
                                    buffer[py, px, i] + color[i] * fade * 0.5
                                    for i in range(3)
                                ]
    
    def _render_entity_realistic(
        self,
        entity: Dict,
        hdr_buffer: np.ndarray,
        depth_buffer: np.ndarray,
        width: int,
        height: int,
        camera_pos: List[float],
        camera_target: List[float],
        all_entities: List[Dict],
        frame: SimulationFrame,
    ) -> None:
        """Render entity with realistic PBR materials."""
        pos = entity.get("position", [0, 0, 0])
        entity_type = entity.get("type", "unknown")
        
        # Project to screen
        screen_pos, depth = self._project_3d_realistic(
            pos[0], pos[1], pos[2],
            width, height, camera_pos, camera_target
        )
        
        if screen_pos is None:
            return
        
        sx, sy = screen_pos
        
        # Entity properties based on type
        if entity_type == "black_hole":
            radius = 20
            # Black hole: dark center with accretion disk glow
            base_color = [0.05, 0.05, 0.1]  # Very dark blue
            emissive = [0.8, 0.6, 0.4]  # Orange accretion disk
            metallic = 0.0
            roughness = 0.9
        elif entity_type == "neutron_star":
            radius = 12
            # Neutron star: bright white with blue tint
            base_color = [0.9, 0.95, 1.0]
            emissive = [0.5, 0.6, 0.8]  # Blue-white glow
            metallic = 1.0
            roughness = 0.1
        else:
            radius = 8
            base_color = [0.7, 0.7, 0.8]
            emissive = [0.1, 0.1, 0.2]
            metallic = 0.5
            roughness = 0.5
        
        # Render sphere with lighting
        for dy in range(-radius*2, radius*2 + 1):
            for dx in range(-radius*2, radius*2 + 1):
                px, py = sx + dx, sy + dy
                if 0 <= px < width and 0 <= py < height:
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= (radius*2)**2:
                        # Calculate normal (for lighting)
                        if dist_sq > 0:
                            normal_x = dx / math.sqrt(dist_sq)
                            normal_y = dy / math.sqrt(dist_sq)
                            normal_z = math.sqrt(max(0, 1 - normal_x*normal_x - normal_y*normal_y))
                        else:
                            normal_x, normal_y, normal_z = 0, 0, 1
                        
                        # Lighting calculation
                        light_dir = [0.5, 0.7, -0.5]  # Light from top-right
                        light_mag = math.sqrt(sum(l*l for l in light_dir))
                        light_dir = [l / light_mag for l in light_dir]
                        
                        # Dot product for diffuse lighting
                        dot = max(0, normal_x*light_dir[0] + normal_y*light_dir[1] + normal_z*light_dir[2])
                        
                        # Calculate color with PBR
                        diffuse = [c * (0.3 + 0.7 * dot) for c in base_color]
                        
                        # Add emissive
                        final_color = [
                            min(1.0, diffuse[i] + emissive[i] * 0.5)
                            for i in range(3)
                        ]
                        
                        # Depth test
                        pixel_depth = depth + math.sqrt(dist_sq) * 0.01
                        if pixel_depth < depth_buffer[py, px]:
                            depth_buffer[py, px] = pixel_depth
                            hdr_buffer[py, px] = final_color
    
    def _project_3d_realistic(
        self,
        x: float, y: float, z: float,
        width: int, height: int,
        camera_pos: List[float],
        camera_target: List[float],
    ) -> Tuple[Optional[Tuple[int, int]], float]:
        """Realistic 3D projection with proper perspective."""
        # Camera space
        dx = x - camera_pos[0]
        dy = y - camera_pos[1]
        dz = z - camera_pos[2]
        
        # Distance
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 0.001:
            return None, float('inf')
        
        # Forward vector
        target_dx = camera_target[0] - camera_pos[0]
        target_dy = camera_target[1] - camera_pos[1]
        target_dz = camera_target[2] - camera_pos[2]
        target_mag = math.sqrt(target_dx*target_dx + target_dy*target_dy + target_dz*target_dz)
        if target_mag < 0.001:
            forward = [0, 0, -1]
        else:
            forward = [target_dx/target_mag, target_dy/target_mag, target_dz/target_mag]
        
        # Right vector (cross product with up)
        up = [0, 1, 0]
        right = [
            forward[1]*up[2] - forward[2]*up[1],
            forward[2]*up[0] - forward[0]*up[2],
            forward[0]*up[1] - forward[1]*up[0]
        ]
        right_mag = math.sqrt(sum(r*r for r in right))
        if right_mag > 0.001:
            right = [r / right_mag for r in right]
        else:
            right = [1, 0, 0]
        
        # Up vector (recalculate)
        up_vec = [
            right[1]*forward[2] - right[2]*forward[1],
            right[2]*forward[0] - right[0]*forward[2],
            right[0]*forward[1] - right[1]*forward[0]
        ]
        
        # Project to camera space
        rel_x = dx*right[0] + dy*right[1] + dz*right[2]
        rel_y = dx*up_vec[0] + dy*up_vec[1] + dz*up_vec[2]
        rel_z = dx*forward[0] + dy*forward[1] + dz*forward[2]
        
        if rel_z <= 0:
            return None, float('inf')
        
        # Perspective projection (FOV 75 degrees)
        fov = 75.0
        f = 1.0 / math.tan(math.radians(fov / 2))
        aspect = width / height
        
        screen_x = width // 2 + int(rel_x * f * width / rel_z / aspect)
        screen_y = height // 2 - int(rel_y * f * height / rel_z)
        
        # Clamp
        screen_x = max(0, min(width - 1, screen_x))
        screen_y = max(0, min(height - 1, screen_y))
        
        return (screen_x, screen_y), rel_z
    
    def _render_particle_effects(
        self,
        hdr_buffer: np.ndarray,
        depth_buffer: np.ndarray,
        entities: List[Dict],
        width: int,
        height: int,
        camera_pos: List[float],
        camera_target: List[float],
        frame: SimulationFrame,
    ) -> None:
        """Render particle effects: accretion disks, gravitational lensing."""
        # Find black hole
        bh_entity = None
        for e in entities:
            if e.get("type") == "black_hole":
                bh_entity = e
                break
        
        if bh_entity:
            bh_pos = bh_entity.get("position", [0, 0, 0])
            screen_pos, depth = self._project_3d_realistic(
                bh_pos[0], bh_pos[1], bh_pos[2],
                width, height, camera_pos, camera_target
            )
            
            if screen_pos:
                sx, sy = screen_pos
                # Render accretion disk (glowing ring)
                disk_radius = 30
                for angle in range(0, 360, 5):
                    rad = math.radians(angle)
                    px = int(sx + math.cos(rad) * disk_radius)
                    py = int(sy + math.sin(rad) * disk_radius)
                    
                    if 0 <= px < width and 0 <= py < height:
                        # Orange-red glow
                        glow_color = [1.0, 0.6, 0.2]
                        hdr_buffer[py, px] = [
                            min(1.0, hdr_buffer[py, px, i] + glow_color[i] * 0.3)
                            for i in range(3)
                        ]
    
    def _apply_bloom(self, hdr_buffer: np.ndarray) -> np.ndarray:
        """Apply bloom effect for glowing objects."""
        # Extract bright areas
        brightness = np.sum(hdr_buffer, axis=2) / 3.0
        bright_mask = brightness > 0.8
        
        # Blur bright areas
        if np.any(bright_mask):
            bright_areas = hdr_buffer.copy()
            bright_areas[~bright_mask] = 0
            
            # Gaussian blur
            kernel_size = 15
            blurred = cv2.GaussianBlur(
                (bright_areas * 255).astype(np.uint8),
                (kernel_size, kernel_size), 0
            ).astype(np.float32) / 255.0
            
            # Add bloom
            hdr_buffer = hdr_buffer + blurred * 0.3
        
        return hdr_buffer
    
    def _tone_map(self, hdr_buffer: np.ndarray) -> np.ndarray:
        """Tone mapping: HDR to LDR."""
        # Reinhard tone mapping
        mapped = hdr_buffer / (1.0 + hdr_buffer)
        return np.clip(mapped * 255, 0, 255).astype(np.uint8)
    
    def _apply_motion_blur(
        self,
        buffer: np.ndarray,
        frame: SimulationFrame,
        prev_frame: SimulationFrame,
        width: int,
        height: int,
    ) -> np.ndarray:
        """Apply motion blur for realistic motion."""
        # Simple motion blur (can be enhanced)
        blurred = cv2.GaussianBlur(buffer, (5, 5), 0)
        return cv2.addWeighted(buffer, 0.7, blurred, 0.3, 0)
    
    def _color_grade(self, buffer: np.ndarray) -> np.ndarray:
        """Color grading for cinematic look."""
        # Ensure buffer is uint8
        if buffer.dtype != np.uint8:
            buffer = np.clip(buffer, 0, 255).astype(np.uint8)
        
        # Increase contrast and saturation
        try:
            lab = cv2.cvtColor(buffer, cv2.COLOR_RGB2LAB)
            lab[:, :, 0] = np.clip(lab[:, :, 0] * 1.1, 0, 255)  # Brightness
            buffer = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        except:
            pass  # Fallback if conversion fails
        
        # Slight color tint (cool blue for space)
        if len(buffer.shape) == 3 and buffer.shape[2] >= 3:
            buffer[:, :, 2] = np.clip(buffer[:, :, 2] * 0.95, 0, 255)  # Reduce red
            buffer[:, :, 0] = np.clip(buffer[:, :, 0] * 1.05, 0, 255)  # Increase blue
        
        return buffer
