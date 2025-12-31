# ============================================================
#  ANM-V3 — RETRO 2D RENDERER
#  Pixel-perfect retro game visuals
#  8-bit/16-bit aesthetic with clean, crisp graphics
# ============================================================

from __future__ import annotations

import os
import time
import math
from typing import List, Optional, Tuple, Dict, Any
import warnings

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import Metal
    METAL_AVAILABLE = True
except ImportError:
    METAL_AVAILABLE = False
    Metal = None

from anm.sim.types import SimulationFrame, SimulationRequest


# ============================================================
#  RETRO COLOR PALETTES (8-bit/16-bit style)
# ============================================================

# Classic NES-inspired palette
RETRO_PALETTE = {
    # Backgrounds
    "sky": (135, 206, 235),         # Sky blue
    "sky_dark": (25, 25, 112),      # Midnight blue
    "space": (10, 10, 30),          # Deep space
    
    # Ground/Environment
    "ground": (139, 90, 43),        # Brown
    "ground_dark": (101, 67, 33),   # Dark brown
    "grass": (34, 139, 34),         # Forest green
    "grass_light": (50, 205, 50),   # Lime green
    "water": (65, 105, 225),        # Royal blue
    
    # Objects
    "red": (220, 20, 60),           # Crimson
    "red_light": (255, 99, 71),     # Tomato
    "red_dark": (139, 0, 0),        # Dark red
    
    "green": (34, 139, 34),         # Forest green
    "green_light": (144, 238, 144), # Light green
    
    "blue": (30, 144, 255),         # Dodger blue
    "blue_light": (135, 206, 250),  # Light sky blue
    "blue_dark": (0, 0, 139),       # Dark blue
    
    "yellow": (255, 215, 0),        # Gold
    "yellow_light": (255, 255, 0),  # Yellow
    
    "orange": (255, 140, 0),        # Dark orange
    "orange_light": (255, 165, 0),  # Orange
    
    "purple": (148, 0, 211),        # Dark violet
    "pink": (255, 105, 180),        # Hot pink
    
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "gray_light": (192, 192, 192),
    "gray_dark": (64, 64, 64),
    
    # UI
    "text": (255, 255, 255),
    "text_shadow": (0, 0, 0),
    "ui_bg": (32, 32, 64),
    "ui_border": (255, 255, 255),
}

# Entity color mapping
ENTITY_COLORS = {
    "apple": {
        "fill": RETRO_PALETTE["red"],
        "outline": RETRO_PALETTE["red_dark"],
        "highlight": RETRO_PALETTE["red_light"],
        "stem": RETRO_PALETTE["green"],
    },
    "ball": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "highlight": RETRO_PALETTE["blue_light"],
    },
    "box": {
        "fill": RETRO_PALETTE["orange"],
        "outline": RETRO_PALETTE["ground_dark"],
        "highlight": RETRO_PALETTE["orange_light"],
    },
    "ground": {
        "fill": RETRO_PALETTE["ground"],
        "outline": RETRO_PALETTE["ground_dark"],
        "top": RETRO_PALETTE["grass"],
    },
    "wall": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
    },
    "black_hole": {
        "fill": RETRO_PALETTE["black"],
        "outline": RETRO_PALETTE["purple"],
        "glow": RETRO_PALETTE["purple"],
    },
    "neutron_star": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["blue_light"],
        "glow": RETRO_PALETTE["blue_light"],
    },
    "star": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["orange"],
        "glow": RETRO_PALETTE["yellow_light"],
    },
    "planet": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
    },
    "default": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["white"],
    },
}


class Renderer2D:
    """
    RETRO 2D Renderer for ANM simulations.
    
    Features:
    - Pixel-perfect retro game visuals
    - 8-bit/16-bit color palettes
    - Chunky sprites with bold outlines
    - Scanline effects (optional)
    - Clean, crisp graphics
    - General purpose - works with any entities
    """
    
    def __init__(
        self,
        output_dir: str = "sim_outputs",
        pixel_scale: int = 4,          # Pixel size multiplier for retro look
        enable_scanlines: bool = False, # CRT scanline effect
        enable_shadows: bool = True,    # Drop shadows
    ):
        self.output_dir = output_dir
        self.pixel_scale = pixel_scale
        self.enable_scanlines = enable_scanlines
        self.enable_shadows = enable_shadows
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.available = False
        self.device = None
        
        if not NUMPY_AVAILABLE or not CV2_AVAILABLE:
            return
        
        try:
            if METAL_AVAILABLE:
                import Metal
                self.device = Metal.MTLCreateSystemDefaultDevice()
            self.available = True
        except Exception as e:
            warnings.warn(f"Renderer2D: GPU init warning: {e}", RuntimeWarning)
            self.available = True  # Still works without Metal
    
    def render_frames_to_video(
        self,
        frames: List[SimulationFrame],
        request: SimulationRequest,
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """Render 2D frames to video with retro game visuals."""
        if not self.available or np is None or cv2 is None:
            return None
        
        if not frames:
            return None
        
        if output_filename is None:
            timestamp = int(time.time())
            scenario = request.scenario_type.replace("_", "-")
            output_filename = f"retro2d_{scenario}_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        width, height = request.output_resolution
        fps = request.target_fps
        
        # Try video codecs
        codecs = [('avc1', 'H.264'), ('mp4v', 'MPEG-4')]
        video_writer = None
        
        for fourcc_str, _ in codecs:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            video_writer = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))
            if video_writer.isOpened():
                break
        
        if video_writer is None or not video_writer.isOpened():
            return None
        
        try:
            for i, frame in enumerate(frames):
                frame_image = self._render_retro_frame(
                    frame, request, width, height, i, len(frames)
                )
                
                if frame_image is not None:
                    video_writer.write(frame_image)
            
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
                except Exception:
                    pass
            warnings.warn(f"Renderer2D: Rendering failed: {e}", RuntimeWarning)
            return None
    
    def _render_retro_frame(
        self,
        frame: SimulationFrame,
        request: SimulationRequest,
        width: int,
        height: int,
        frame_index: int,
        total_frames: int,
    ) -> Optional[np.ndarray]:
        """Render a single frame with retro game aesthetics."""
        if np is None or cv2 is None:
            return None
        
        # Create canvas
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        entities = frame.state.get("entities", [])
        
        # Determine scene type for background
        scene_type = self._detect_scene_type(entities, request)
        
        # Render layered scene
        self._render_background(image, scene_type, width, height)
        
        # Calculate camera
        camera_pos, camera_scale = self._calculate_camera(entities, width, height)
        
        # Render grid (retro style)
        self._render_retro_grid(image, camera_pos, camera_scale, width, height, scene_type)
        
        # Render environment (ground, walls, etc.)
        self._render_environment(image, entities, camera_pos, camera_scale, width, height)
        
        # Render entities (sorted by y-position for proper layering)
        sorted_entities = sorted(
            [e for e in entities if e.get("type") not in ("ground", "wall", "floor")],
            key=lambda e: e.get("position", [0, 0])[1],
            reverse=True
        )
        
        for entity in sorted_entities:
            self._render_retro_entity(image, entity, camera_pos, camera_scale, width, height)
        
        # Render UI overlay
        self._render_retro_ui(image, frame, frame_index, total_frames, width, height)
        
        # Apply retro effects
        if self.enable_scanlines:
            self._apply_scanlines(image)
        
        # Convert RGB to BGR for OpenCV
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    def _detect_scene_type(self, entities: List[Dict], request: SimulationRequest) -> str:
        """Detect the type of scene for appropriate styling."""
        entity_types = [e.get("type", "").lower() for e in entities]
        scenario = request.scenario_type.lower()
        
        if any(t in entity_types for t in ["black_hole", "neutron_star", "star", "planet"]):
            return "space"
        elif any(t in entity_types for t in ["ground", "floor", "grass"]):
            return "outdoor"
        elif "gravity" in scenario or "fall" in scenario:
            return "outdoor"
        else:
            return "default"
    
    def _render_background(
        self,
        image: np.ndarray,
        scene_type: str,
        width: int,
        height: int,
    ):
        """Render retro-style background with gradient."""
        if scene_type == "space":
            # Deep space gradient
            for y in range(height):
                t = y / height
                r = int(10 + t * 15)
                g = int(10 + t * 10)
                b = int(30 + t * 20)
                image[y, :] = [r, g, b]
            
            # Add retro stars (pixel-perfect)
            np.random.seed(42)  # Consistent stars
            num_stars = 100
            for _ in range(num_stars):
                sx = np.random.randint(0, width)
                sy = np.random.randint(0, height)
                brightness = np.random.choice([150, 200, 255])
                size = np.random.choice([1, 2])
                if size == 1:
                    image[sy, sx] = [brightness, brightness, brightness]
                else:
                    y1, y2 = max(0, sy-1), min(height, sy+2)
                    x1, x2 = max(0, sx-1), min(width, sx+2)
                    image[y1:y2, x1:x2] = [brightness, brightness, brightness]
        
        elif scene_type == "outdoor":
            # Sky gradient (retro style - banded)
            sky_bands = 8
            for band in range(sky_bands):
                y_start = int(band * height * 0.6 / sky_bands)
                y_end = int((band + 1) * height * 0.6 / sky_bands)
                t = band / sky_bands
                r = int(135 - t * 50)
                g = int(206 - t * 50)
                b = int(250 - t * 20)
                image[y_start:y_end, :] = [r, g, b]
            
            # Fill bottom with ground color
            ground_start = int(height * 0.6)
            image[ground_start:, :] = RETRO_PALETTE["grass"]
        
        else:
            # Default: clean gradient
            for y in range(height):
                t = y / height
                r = int(60 + t * 30)
                g = int(60 + t * 40)
                b = int(80 + t * 40)
                image[y, :] = [r, g, b]
    
    def _calculate_camera(
        self,
        entities: List[Dict],
        width: int,
        height: int,
    ) -> Tuple[List[float], float]:
        """Calculate camera position and scale."""
        if not entities:
            return [0.0, 0.0], 1.0
        
        # Find bounds
        positions = [e.get("position", [0, 0]) for e in entities]
        radii = [e.get("radius", 10) for e in entities]
        
        min_x = min(p[0] - r for p, r in zip(positions, radii))
        max_x = max(p[0] + r for p, r in zip(positions, radii))
        min_y = min(p[1] - r for p, r in zip(positions, radii))
        max_y = max(p[1] + r for p, r in zip(positions, radii))
        
        # Center
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        
        # Scale with padding
        entity_width = max_x - min_x + 100
        entity_height = max_y - min_y + 100
        
        scale_x = (width * 0.7) / entity_width if entity_width > 0 else 1.0
        scale_y = (height * 0.7) / entity_height if entity_height > 0 else 1.0
        scale = min(scale_x, scale_y)
        
        # Clamp scale
        scale = max(0.5, min(scale, 10.0))
        
        return [center_x, center_y], scale
    
    def _render_retro_grid(
        self,
        image: np.ndarray,
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
        scene_type: str,
    ):
        """Render subtle retro grid."""
        if cv2 is None:
            return
        
        if scene_type == "space":
            grid_color = (30, 30, 50)
        else:
            grid_color = (200, 220, 200)
        
        grid_spacing = 50.0
        center_x = width // 2
        center_y = height // 2
        
        # Vertical lines
        world_x = camera_pos[0] - (width / 2) / camera_scale
        world_x = math.floor(world_x / grid_spacing) * grid_spacing
        while world_x < camera_pos[0] + (width / 2) / camera_scale:
            screen_x = int((world_x - camera_pos[0]) * camera_scale + center_x)
            if 0 <= screen_x < width:
                # Dotted line effect
                for y in range(0, height, 8):
                    if y + 2 < height:
                        image[y:y+2, screen_x] = grid_color
            world_x += grid_spacing
        
        # Horizontal lines
        world_y = camera_pos[1] - (height / 2) / camera_scale
        world_y = math.floor(world_y / grid_spacing) * grid_spacing
        while world_y < camera_pos[1] + (height / 2) / camera_scale:
            screen_y = int((world_y - camera_pos[1]) * camera_scale + center_y)
            if 0 <= screen_y < height:
                for x in range(0, width, 8):
                    if x + 2 < width:
                        image[screen_y, x:x+2] = grid_color
            world_y += grid_spacing
    
    def _render_environment(
        self,
        image: np.ndarray,
        entities: List[Dict],
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
    ):
        """Render environment entities (ground, walls)."""
        if cv2 is None:
            return
        
        for entity in entities:
            entity_type = entity.get("type", "").lower()
            
            if entity_type in ("ground", "floor"):
                pos = entity.get("position", [0, 100])
                screen_y = int((pos[1] - camera_pos[1]) * camera_scale + height / 2)
                
                if screen_y < height:
                    # Ground fill
                    colors = ENTITY_COLORS.get("ground", ENTITY_COLORS["default"])
                    
                    # Grass top layer (pixelated)
                    grass_height = 8
                    if screen_y - grass_height >= 0:
                        image[screen_y-grass_height:screen_y, :] = colors["top"]
                    
                    # Main ground
                    if screen_y < height:
                        image[screen_y:, :] = colors["fill"]
                    
                    # Ground texture (retro brick pattern)
                    brick_height = 16
                    brick_width = 32
                    for by in range(screen_y, height, brick_height):
                        offset = (by // brick_height % 2) * (brick_width // 2)
                        for bx in range(offset, width, brick_width):
                            # Brick outline
                            if by + brick_height < height:
                                cv2.rectangle(
                                    image,
                                    (bx, by),
                                    (min(bx + brick_width, width), min(by + brick_height, height)),
                                    colors["outline"],
                                    1
                                )
            
            elif entity_type == "wall":
                pos = entity.get("position", [0, 0])
                wall_width = entity.get("width", 20)
                wall_height = entity.get("height", 100)
                
                screen_x = int((pos[0] - camera_pos[0]) * camera_scale + width / 2)
                screen_y = int((pos[1] - camera_pos[1]) * camera_scale + height / 2)
                w = int(wall_width * camera_scale)
                h = int(wall_height * camera_scale)
                
                colors = ENTITY_COLORS.get("wall", ENTITY_COLORS["default"])
                cv2.rectangle(image, (screen_x - w//2, screen_y - h//2),
                             (screen_x + w//2, screen_y + h//2), colors["fill"], -1)
                cv2.rectangle(image, (screen_x - w//2, screen_y - h//2),
                             (screen_x + w//2, screen_y + h//2), colors["outline"], 2)
    
    def _render_retro_entity(
        self,
        image: np.ndarray,
        entity: Dict,
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
    ):
        """Render entity with retro pixel-art style."""
        if cv2 is None:
            return
        
        pos = entity.get("position", [0, 0])
        entity_type = entity.get("type", "default").lower()
        base_radius = entity.get("radius", 10)
        
        # Screen position
        screen_x = int((pos[0] - camera_pos[0]) * camera_scale + width / 2)
        screen_y = int((pos[1] - camera_pos[1]) * camera_scale + height / 2)
        
        # Screen radius (minimum 20 pixels for visibility)
        radius = max(20, int(base_radius * camera_scale))
        
        # Get colors
        colors = ENTITY_COLORS.get(entity_type, ENTITY_COLORS["default"])
        fill_color = colors.get("fill", RETRO_PALETTE["gray"])
        outline_color = colors.get("outline", RETRO_PALETTE["gray_dark"])
        highlight_color = colors.get("highlight", RETRO_PALETTE["white"])
        
        # Shadow (retro drop shadow)
        if self.enable_shadows:
            shadow_offset = max(4, radius // 4)
            cv2.circle(image, (screen_x + shadow_offset, screen_y + shadow_offset),
                      radius, (0, 0, 0), -1)
        
        # Main shape (chunky circle with thick outline)
        cv2.circle(image, (screen_x, screen_y), radius, fill_color, -1)
        
        # Thick retro outline
        outline_thickness = max(3, radius // 6)
        cv2.circle(image, (screen_x, screen_y), radius, outline_color, outline_thickness)
        
        # Highlight (top-left shine for 3D effect)
        highlight_radius = max(4, radius // 4)
        highlight_x = screen_x - radius // 3
        highlight_y = screen_y - radius // 3
        cv2.circle(image, (highlight_x, highlight_y), highlight_radius, highlight_color, -1)
        
        # Entity-specific decorations
        if entity_type == "apple":
            self._draw_apple_details(image, screen_x, screen_y, radius, colors)
        elif entity_type in ("black_hole", "neutron_star", "star"):
            self._draw_cosmic_details(image, screen_x, screen_y, radius, entity_type, colors)
        elif entity_type == "ball":
            self._draw_ball_details(image, screen_x, screen_y, radius, colors)
        
        # Velocity vector (retro arrow)
        velocity = entity.get("velocity", [0, 0])
        vel_mag = math.sqrt(velocity[0]**2 + velocity[1]**2)
        if vel_mag > 1.0:
            self._draw_retro_arrow(image, screen_x, screen_y, velocity, vel_mag, camera_scale)
    
    def _draw_apple_details(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        radius: int,
        colors: Dict,
    ):
        """Draw apple-specific details (stem, leaf)."""
        if cv2 is None:
            return
        
        stem_color = colors.get("stem", RETRO_PALETTE["green"])
        
        # Stem (rectangle)
        stem_w = max(4, radius // 4)
        stem_h = max(8, radius // 2)
        cv2.rectangle(
            image,
            (x - stem_w//2, y - radius - stem_h),
            (x + stem_w//2, y - radius + 2),
            RETRO_PALETTE["ground_dark"],
            -1
        )
        
        # Leaf (simple triangle approximation using filled polygon)
        leaf_points = np.array([
            [x + 2, y - radius - stem_h + 4],
            [x + radius//2, y - radius - stem_h - 4],
            [x + radius//3, y - radius - 2],
        ], np.int32)
        cv2.fillPoly(image, [leaf_points], stem_color)
    
    def _draw_cosmic_details(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        radius: int,
        entity_type: str,
        colors: Dict,
    ):
        """Draw cosmic entity details (glow rings, etc.)."""
        if cv2 is None:
            return
        
        glow_color = colors.get("glow", RETRO_PALETTE["purple"])
        
        if entity_type == "black_hole":
            # Event horizon glow rings
            for i in range(3):
                ring_radius = radius + 4 + i * 4
                cv2.circle(image, (x, y), ring_radius, glow_color, 2)
        
        elif entity_type == "neutron_star":
            # Pulsing rays (8 directions)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                end_x = int(x + math.cos(rad) * (radius + 20))
                end_y = int(y + math.sin(rad) * (radius + 20))
                cv2.line(image, (x, y), (end_x, end_y), glow_color, 2)
        
        elif entity_type == "star":
            # Star points
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                end_x = int(x + math.cos(rad) * (radius + 15))
                end_y = int(y + math.sin(rad) * (radius + 15))
                cv2.line(image, (x, y), (end_x, end_y), glow_color, 3)
    
    def _draw_ball_details(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        radius: int,
        colors: Dict,
    ):
        """Draw ball details (stripe pattern)."""
        if cv2 is None:
            return
        
        # Horizontal stripe
        stripe_color = colors.get("highlight", RETRO_PALETTE["white"])
        stripe_y = y - radius // 4
        stripe_height = max(4, radius // 4)
        
        # Draw stripe within circle bounds
        for sy in range(stripe_y, stripe_y + stripe_height):
            if 0 <= sy < image.shape[0]:
                # Calculate x bounds at this y
                dy = abs(sy - y)
                if dy < radius:
                    dx = int(math.sqrt(radius * radius - dy * dy))
                    x1 = max(0, x - dx + 4)
                    x2 = min(image.shape[1], x + dx - 4)
                    if x1 < x2:
                        image[sy, x1:x2] = stripe_color
    
    def _draw_retro_arrow(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        velocity: List[float],
        vel_mag: float,
        camera_scale: float,
    ):
        """Draw retro-style velocity arrow."""
        if cv2 is None:
            return
        
        # Arrow length
        arrow_len = min(60, max(20, vel_mag * camera_scale * 0.3))
        
        # Direction
        dx = velocity[0] / vel_mag
        dy = velocity[1] / vel_mag
        
        end_x = int(x + dx * arrow_len)
        end_y = int(y + dy * arrow_len)
        
        # Yellow arrow with black outline
        cv2.line(image, (x, y), (end_x, end_y), RETRO_PALETTE["black"], 6)
        cv2.line(image, (x, y), (end_x, end_y), RETRO_PALETTE["yellow"], 4)
        
        # Arrow head
        head_len = 10
        angle = math.atan2(dy, dx)
        for offset in [-0.5, 0.5]:
            hx = int(end_x - head_len * math.cos(angle + offset))
            hy = int(end_y - head_len * math.sin(angle + offset))
            cv2.line(image, (end_x, end_y), (hx, hy), RETRO_PALETTE["black"], 6)
            cv2.line(image, (end_x, end_y), (hx, hy), RETRO_PALETTE["yellow"], 4)
    
    def _render_retro_ui(
        self,
        image: np.ndarray,
        frame: SimulationFrame,
        frame_index: int,
        total_frames: int,
        width: int,
        height: int,
    ):
        """Render retro-style UI overlay."""
        if cv2 is None:
            return
        
        # UI panel background (top)
        panel_height = 40
        cv2.rectangle(image, (0, 0), (width, panel_height), RETRO_PALETTE["ui_bg"], -1)
        cv2.line(image, (0, panel_height), (width, panel_height), RETRO_PALETTE["ui_border"], 2)
        
        # Time display (pixel font style using simple text)
        time_text = f"TIME: {frame.time_seconds:.2f}s"
        self._draw_retro_text(image, time_text, 10, 28, RETRO_PALETTE["text"])
        
        # Frame counter
        frame_text = f"FRAME: {frame_index + 1}/{total_frames}"
        self._draw_retro_text(image, frame_text, width - 200, 28, RETRO_PALETTE["text"])
        
        # Progress bar
        bar_width = 200
        bar_height = 8
        bar_x = (width - bar_width) // 2
        bar_y = 16
        
        # Bar background
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     RETRO_PALETTE["gray_dark"], -1)
        
        # Progress fill
        progress = (frame_index + 1) / max(total_frames, 1)
        fill_width = int(bar_width * progress)
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                     RETRO_PALETTE["green"], -1)
        
        # Bar border
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     RETRO_PALETTE["ui_border"], 1)
    
    def _draw_retro_text(
        self,
        image: np.ndarray,
        text: str,
        x: int,
        y: int,
        color: Tuple[int, int, int],
    ):
        """Draw text with retro shadow effect."""
        if cv2 is None:
            return
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.6
        thickness = 2
        
        # Shadow
        cv2.putText(image, text, (x + 2, y + 2), font, scale, RETRO_PALETTE["text_shadow"], thickness)
        # Main text
        cv2.putText(image, text, (x, y), font, scale, color, thickness)
    
    def _apply_scanlines(self, image: np.ndarray):
        """Apply CRT scanline effect."""
        if np is None:
            return
        
        # Darken every other line
        for y in range(0, image.shape[0], 2):
            image[y, :] = (image[y, :].astype(np.float32) * 0.85).astype(np.uint8)
