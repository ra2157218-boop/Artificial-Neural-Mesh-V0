# ============================================================
# ANM V0-OpenSource — VIDEO RENDERER
#  Renders SimulationFrames to MP4 video files
# ============================================================

from __future__ import annotations

import os
import time
import math
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Conditional imports for optional dependencies
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


class VideoRenderer:
    """
    Renders SimulationFrames to MP4 video files.
    
    Uses OpenCV to create videos from simulation frames.
    """
    
    def __init__(self, output_dir: str = "sim_outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.available = CV2_AVAILABLE and NUMPY_AVAILABLE
        
        if not self.available:
            import warnings
            if not NUMPY_AVAILABLE:
                warnings.warn(
                    "VideoRenderer: NumPy not available. "
                    "Install with: pip install numpy",
                    RuntimeWarning
                )
            if not CV2_AVAILABLE:
                warnings.warn(
                    "VideoRenderer: OpenCV (cv2) not available. "
                    "Install with: pip install opencv-python",
                    RuntimeWarning
                )
    
    def render_frames_to_video(
        self,
        frames: List[SimulationFrame],
        request: SimulationRequest,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Render SimulationFrames to MP4 video.
        
        Args:
            frames: List of SimulationFrames to render
            request: Original SimulationRequest (for metadata)
            output_filename: Optional custom filename
            
        Returns:
            Path to created video file, or None if failed
        """
        if not self.available:
            return None
        
        if not frames:
            return None
        
        # Generate filename
        if output_filename is None:
            timestamp = int(time.time())
            scenario = request.scenario_type.replace("_", "-")
            output_filename = f"sim_{scenario}_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Get video parameters
        width, height = request.output_resolution
        fps = request.target_fps
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            output_path,
            fourcc,
            float(fps),
            (width, height)
        )
        
        if not video_writer.isOpened():
            return None
        
        try:
            # Render each frame
            for frame in frames:
                frame_image = self._render_frame(frame, request, width, height)
                if frame_image is not None:
                    video_writer.write(frame_image)
            
            video_writer.release()
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                return None
        
        except Exception as e:
            if video_writer.isOpened():
                video_writer.release()
            # Clean up partial file
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            return None
    
    def _render_frame(
        self,
        frame: SimulationFrame,
        request: SimulationRequest,
        width: int,
        height: int,
    ) -> Optional[np.ndarray]:
        """
        Render a single SimulationFrame to an image array.
        
        Args:
            frame: SimulationFrame to render
            request: Original SimulationRequest
            width: Output width
            height: Output height
            
        Returns:
            BGR image array (for OpenCV), or None if failed
        """
        if not self.available or np is None:
            return None
        
        # Create blank image (dark blue space background)
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background gradient (space-like)
        for y in range(height):
            factor = y / height
            r = int(20 + 10 * factor)
            g = int(30 + 20 * factor)
            b = int(50 + 30 * factor)
            image[y, :] = [b, g, r]  # BGR for OpenCV
        
        # Get entities from frame state
        entities = frame.state.get("entities", [])
        scenario = frame.state.get("scenario", request.scenario_type)
        
        # Render entities
        for entity in entities:
            if "position" in entity:
                pos = entity["position"]
                entity_type = entity.get("type", "unknown")
                
                # Project 3D position to 2D screen
                screen_x, screen_y = self._project_3d_to_2d(
                    pos[0], pos[1], pos[2],
                    width, height,
                    frame.state.get("camera_pos", [0, 100, -300]),
                    frame.state.get("camera_target", [0, 0, 0]),
                )
                
                # Draw entity based on type
                if entity_type == "black_hole":
                    self._draw_circle(image, screen_x, screen_y, 15, (0, 0, 255))  # Red
                    self._draw_circle(image, screen_x, screen_y, 20, (0, 0, 100))  # Dark red halo
                elif entity_type == "neutron_star":
                    self._draw_circle(image, screen_x, screen_y, 8, (255, 255, 255))  # White
                    self._draw_circle(image, screen_x, screen_y, 10, (200, 200, 255))  # Light blue halo
                else:
                    # Generic entity
                    self._draw_circle(image, screen_x, screen_y, 5, (100, 200, 255))  # Cyan
        
        # Draw trajectory trails (if available)
        if "trajectory" in frame.state:
            self._draw_trajectory(image, frame.state["trajectory"], width, height)
        
        # Add text overlay with simulation info
        self._draw_text_overlay(image, frame, request, width, height)
        
        return image
    
    def _project_3d_to_2d(
        self,
        x: float, y: float, z: float,
        width: int, height: int,
        camera_pos: List[float],
        camera_target: List[float],
    ) -> Tuple[int, int]:
        """Project 3D coordinates to 2D screen coordinates."""
        # Simple perspective projection
        # Move to camera space
        dx = x - camera_pos[0]
        dy = y - camera_pos[1]
        dz = z - camera_pos[2]
        
        # Distance from camera
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 0.001:
            return (width // 2, height // 2)
        
        # Simple perspective (fov ~60 degrees)
        fov = 60.0
        scale = width / (2 * math.tan(math.radians(fov / 2)))
        
        # Project
        if dz > 0:  # In front of camera
            screen_x = int(width // 2 + dx * scale / dz)
            screen_y = int(height // 2 - dy * scale / dz)  # Flip Y
        else:
            # Behind camera, project to edge
            screen_x = int(width // 2 + dx * 0.1)
            screen_y = int(height // 2 - dy * 0.1)
        
        # Clamp to screen bounds
        screen_x = max(0, min(width - 1, screen_x))
        screen_y = max(0, min(height - 1, screen_y))
        
        return (screen_x, screen_y)
    
    def _draw_circle(
        self,
        image: np.ndarray,
        x: int, y: int,
        radius: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Draw a filled circle on the image."""
        if not CV2_AVAILABLE:
            return
        
        cv2.circle(image, (x, y), radius, color, -1)
    
    def _draw_trajectory(
        self,
        image: np.ndarray,
        trajectory: Any,
        width: int,
        height: int,
    ) -> None:
        """Draw trajectory trail."""
        if not CV2_AVAILABLE:
            return
        
        # If trajectory is a list of points
        if isinstance(trajectory, list) and len(trajectory) > 1:
            points = []
            for point in trajectory:
                if isinstance(point, (list, tuple)) and len(point) >= 3:
                    x, y, z = point[0], point[1], point[2]
                    sx, sy = self._project_3d_to_2d(x, y, z, width, height, [0, 100, -300], [0, 0, 0])
                    points.append((sx, sy))
            
            # Draw lines
            for i in range(len(points) - 1):
                cv2.line(image, points[i], points[i+1], (100, 100, 255), 1)
    
    def _draw_text_overlay(
        self,
        image: np.ndarray,
        frame: SimulationFrame,
        request: SimulationRequest,
        width: int,
        height: int,
    ) -> None:
        """Draw text overlay with simulation info."""
        if not CV2_AVAILABLE:
            return
        
        # Text info
        time_str = f"Time: {frame.time_seconds:.2f}s"
        scenario_str = f"Scenario: {request.scenario_type}"
        frame_str = f"Frame: {frame.index}"
        
        # Draw text (white, small font)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (255, 255, 255)
        thickness = 1
        
        y_offset = 20
        cv2.putText(image, time_str, (10, y_offset), font, font_scale, color, thickness)
        cv2.putText(image, scenario_str, (10, y_offset + 20), font, font_scale, color, thickness)
        cv2.putText(image, frame_str, (10, y_offset + 40), font, font_scale, color, thickness)
