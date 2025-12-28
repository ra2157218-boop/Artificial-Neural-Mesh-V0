# ============================================================
#  ANM-V3 — UNIVERSAL RETRO 2D RENDERER
#  Render ANY entity type with beautiful retro game visuals
#  Pixel-perfect • 8-bit/16-bit aesthetic • Truly general purpose
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import math
import os

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


# ============================================================
#  EXPANDED RETRO COLOR PALETTES
# ============================================================

RETRO_PALETTE = {
    # Backgrounds
    "sky": (135, 206, 235),
    "sky_dark": (25, 25, 112),
    "sky_sunset": (255, 127, 80),
    "space": (10, 10, 30),
    "space_nebula": (30, 10, 50),
    
    # Ground/Environment
    "ground": (139, 90, 43),
    "ground_dark": (101, 67, 33),
    "grass": (34, 139, 34),
    "grass_light": (50, 205, 50),
    "sand": (238, 214, 175),
    "sand_dark": (210, 180, 140),
    "water": (65, 105, 225),
    "water_light": (100, 149, 237),
    "water_dark": (0, 0, 139),
    "ice": (200, 240, 255),
    "lava": (255, 69, 0),
    "wood": (139, 69, 19),
    "metal": (192, 192, 192),
    "stone": (128, 128, 128),
    
    # Basic colors
    "red": (220, 20, 60),
    "red_light": (255, 99, 71),
    "red_dark": (139, 0, 0),
    "green": (34, 139, 34),
    "green_light": (144, 238, 144),
    "green_dark": (0, 100, 0),
    "blue": (30, 144, 255),
    "blue_light": (135, 206, 250),
    "blue_dark": (0, 0, 139),
    "yellow": (255, 215, 0),
    "yellow_light": (255, 255, 0),
    "yellow_dark": (218, 165, 32),
    "orange": (255, 140, 0),
    "orange_light": (255, 165, 0),
    "orange_dark": (255, 69, 0),
    "purple": (148, 0, 211),
    "purple_light": (186, 85, 211),
    "purple_dark": (75, 0, 130),
    "pink": (255, 105, 180),
    "cyan": (0, 255, 255),
    "brown": (139, 69, 19),
    "brown_light": (205, 133, 63),
    "brown_dark": (101, 67, 33),
    
    # Neutral
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "gray_light": (192, 192, 192),
    "gray_dark": (64, 64, 64),
    
    # Special
    "gold": (255, 215, 0),
    "silver": (192, 192, 192),
    "bronze": (205, 127, 50),
    "glow_blue": (100, 200, 255),
    "glow_green": (100, 255, 100),
    "glow_red": (255, 100, 100),
    "glow_purple": (200, 100, 255),
    
    # UI
    "text": (255, 255, 255),
    "text_shadow": (0, 0, 0),
    "ui_bg": (32, 32, 64),
    "ui_border": (255, 255, 255),
}


# ============================================================
#  UNIVERSAL ENTITY VISUALS
# ============================================================

ENTITY_VISUALS = {
    # === FRUITS ===
    "apple": {
        "fill": RETRO_PALETTE["red"],
        "outline": RETRO_PALETTE["red_dark"],
        "highlight": RETRO_PALETTE["red_light"],
        "detail": RETRO_PALETTE["green"],
        "shape": "circle",
        "has_stem": True,
        "has_leaf": True,
    },
    "orange": {
        "fill": RETRO_PALETTE["orange"],
        "outline": RETRO_PALETTE["orange_dark"],
        "highlight": RETRO_PALETTE["orange_light"],
        "shape": "circle",
        "texture": "dots",
    },
    "banana": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["yellow_dark"],
        "highlight": RETRO_PALETTE["yellow_light"],
        "shape": "crescent",
    },
    "watermelon": {
        "fill": RETRO_PALETTE["green"],
        "outline": RETRO_PALETTE["green_dark"],
        "highlight": RETRO_PALETTE["green_light"],
        "inner": RETRO_PALETTE["red"],
        "shape": "circle",
        "has_stripes": True,
    },
    "grape": {
        "fill": RETRO_PALETTE["purple"],
        "outline": RETRO_PALETTE["purple_dark"],
        "highlight": RETRO_PALETTE["purple_light"],
        "shape": "circle",
    },
    "egg": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["gray_light"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "oval",
    },
    
    # === SPORTS BALLS ===
    "ball": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "highlight": RETRO_PALETTE["blue_light"],
        "shape": "circle",
        "has_stripe": True,
    },
    "basketball": {
        "fill": RETRO_PALETTE["orange"],
        "outline": RETRO_PALETTE["brown_dark"],
        "highlight": RETRO_PALETTE["orange_light"],
        "lines": RETRO_PALETTE["brown_dark"],
        "shape": "circle",
        "has_lines": True,
    },
    "football": {
        "fill": RETRO_PALETTE["brown"],
        "outline": RETRO_PALETTE["brown_dark"],
        "highlight": RETRO_PALETTE["brown_light"],
        "laces": RETRO_PALETTE["white"],
        "shape": "oval",
        "has_laces": True,
    },
    "soccer_ball": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["black"],
        "pattern": RETRO_PALETTE["black"],
        "shape": "circle",
        "has_pentagons": True,
    },
    "tennis_ball": {
        "fill": RETRO_PALETTE["yellow_light"],
        "outline": RETRO_PALETTE["yellow_dark"],
        "seam": RETRO_PALETTE["white"],
        "shape": "circle",
        "has_seam": True,
    },
    "golf_ball": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["gray_light"],
        "dimples": RETRO_PALETTE["gray"],
        "shape": "circle",
        "has_dimples": True,
    },
    "bowling_ball": {
        "fill": RETRO_PALETTE["purple_dark"],
        "outline": RETRO_PALETTE["black"],
        "holes": RETRO_PALETTE["black"],
        "shape": "circle",
        "has_holes": True,
    },
    "marble": {
        "fill": RETRO_PALETTE["blue_light"],
        "outline": RETRO_PALETTE["blue_dark"],
        "highlight": RETRO_PALETTE["white"],
        "swirl": RETRO_PALETTE["yellow"],
        "shape": "circle",
        "has_swirl": True,
    },
    
    # === VEHICLES ===
    "car": {
        "fill": RETRO_PALETTE["red"],
        "outline": RETRO_PALETTE["red_dark"],
        "windows": RETRO_PALETTE["blue_light"],
        "wheels": RETRO_PALETTE["black"],
        "shape": "rectangle",
        "has_wheels": True,
    },
    "truck": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "windows": RETRO_PALETTE["blue_light"],
        "wheels": RETRO_PALETTE["black"],
        "shape": "rectangle",
        "has_wheels": True,
    },
    "rocket": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["gray"],
        "nose": RETRO_PALETTE["red"],
        "flame": RETRO_PALETTE["orange"],
        "shape": "triangle",
        "has_flame": True,
    },
    "airplane": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray_dark"],
        "windows": RETRO_PALETTE["blue_light"],
        "wings": RETRO_PALETTE["gray"],
        "shape": "airplane",
    },
    "boat": {
        "fill": RETRO_PALETTE["brown"],
        "outline": RETRO_PALETTE["brown_dark"],
        "sail": RETRO_PALETTE["white"],
        "shape": "boat",
    },
    "bike": {
        "fill": RETRO_PALETTE["red"],
        "outline": RETRO_PALETTE["red_dark"],
        "wheels": RETRO_PALETTE["black"],
        "shape": "bike",
    },
    
    # === COSMIC ===
    "sun": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["orange"],
        "glow": RETRO_PALETTE["yellow_light"],
        "shape": "circle",
        "has_rays": True,
        "has_glow": True,
    },
    "star": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["orange"],
        "glow": RETRO_PALETTE["yellow_light"],
        "shape": "star",
        "has_glow": True,
    },
    "planet": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "highlight": RETRO_PALETTE["blue_light"],
        "shape": "circle",
    },
    "earth": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "land": RETRO_PALETTE["green"],
        "shape": "circle",
        "has_continents": True,
    },
    "moon": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray"],
        "craters": RETRO_PALETTE["gray_dark"],
        "shape": "circle",
        "has_craters": True,
    },
    "black_hole": {
        "fill": RETRO_PALETTE["black"],
        "outline": RETRO_PALETTE["purple"],
        "glow": RETRO_PALETTE["glow_purple"],
        "shape": "circle",
        "has_event_horizon": True,
        "has_glow": True,
    },
    "neutron_star": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["blue_light"],
        "glow": RETRO_PALETTE["glow_blue"],
        "shape": "circle",
        "has_pulsar_rays": True,
        "has_glow": True,
    },
    "asteroid": {
        "fill": RETRO_PALETTE["brown"],
        "outline": RETRO_PALETTE["brown_dark"],
        "craters": RETRO_PALETTE["gray_dark"],
        "shape": "irregular",
    },
    "comet": {
        "fill": RETRO_PALETTE["cyan"],
        "outline": RETRO_PALETTE["blue_light"],
        "tail": RETRO_PALETTE["white"],
        "shape": "circle",
        "has_tail": True,
    },
    "satellite": {
        "fill": RETRO_PALETTE["silver"],
        "outline": RETRO_PALETTE["gray_dark"],
        "panels": RETRO_PALETTE["blue"],
        "shape": "rectangle",
        "has_solar_panels": True,
    },
    "galaxy": {
        "fill": RETRO_PALETTE["purple_light"],
        "outline": RETRO_PALETTE["purple"],
        "glow": RETRO_PALETTE["glow_purple"],
        "shape": "spiral",
        "has_glow": True,
    },
    
    # === PHYSICS OBJECTS ===
    "pendulum": {
        "fill": RETRO_PALETTE["gold"],
        "outline": RETRO_PALETTE["brown_dark"],
        "string": RETRO_PALETTE["gray"],
        "shape": "circle",
        "has_string": True,
    },
    "weight": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["gray_light"],
        "shape": "circle",
    },
    "magnet": {
        "fill_n": RETRO_PALETTE["red"],
        "fill_s": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "horseshoe",
    },
    "spring": {
        "fill": RETRO_PALETTE["silver"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "spring",
    },
    
    # === PARTICLES ===
    "particle": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["gray_light"],
        "glow": RETRO_PALETTE["white"],
        "shape": "circle",
        "has_glow": True,
    },
    "electron": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "glow": RETRO_PALETTE["glow_blue"],
        "shape": "circle",
        "has_glow": True,
    },
    "proton": {
        "fill": RETRO_PALETTE["red"],
        "outline": RETRO_PALETTE["red_dark"],
        "glow": RETRO_PALETTE["glow_red"],
        "shape": "circle",
        "has_glow": True,
    },
    "neutron": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "circle",
    },
    "atom": {
        "fill": RETRO_PALETTE["purple"],
        "outline": RETRO_PALETTE["purple_dark"],
        "orbitals": RETRO_PALETTE["blue_light"],
        "shape": "circle",
        "has_orbitals": True,
    },
    "photon": {
        "fill": RETRO_PALETTE["yellow_light"],
        "outline": RETRO_PALETTE["yellow"],
        "glow": RETRO_PALETTE["yellow_light"],
        "shape": "wave",
        "has_glow": True,
    },
    
    # === NATURE ===
    "rock": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["gray_light"],
        "shape": "irregular",
    },
    "boulder": {
        "fill": RETRO_PALETTE["stone"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "irregular",
    },
    "leaf": {
        "fill": RETRO_PALETTE["green"],
        "outline": RETRO_PALETTE["green_dark"],
        "vein": RETRO_PALETTE["green_light"],
        "shape": "leaf",
    },
    "feather": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["gray_light"],
        "shape": "feather",
    },
    "raindrop": {
        "fill": RETRO_PALETTE["water_light"],
        "outline": RETRO_PALETTE["water"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "drop",
    },
    "snowflake": {
        "fill": RETRO_PALETTE["white"],
        "outline": RETRO_PALETTE["ice"],
        "shape": "snowflake",
    },
    "bubble": {
        "fill": (200, 230, 255),
        "outline": RETRO_PALETTE["white"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "circle",
        "transparent": True,
    },
    "drop": {
        "fill": RETRO_PALETTE["water"],
        "outline": RETRO_PALETTE["water_dark"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "drop",
    },
    
    # === ANIMALS ===
    "bird": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["orange"],
        "beak": RETRO_PALETTE["orange"],
        "wing": RETRO_PALETTE["yellow_dark"],
        "shape": "bird",
    },
    "fish": {
        "fill": RETRO_PALETTE["orange"],
        "outline": RETRO_PALETTE["orange_dark"],
        "fin": RETRO_PALETTE["red"],
        "shape": "fish",
    },
    "butterfly": {
        "fill": RETRO_PALETTE["pink"],
        "outline": RETRO_PALETTE["purple"],
        "pattern": RETRO_PALETTE["blue_light"],
        "shape": "butterfly",
    },
    "bee": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["black"],
        "stripes": RETRO_PALETTE["black"],
        "wings": RETRO_PALETTE["white"],
        "shape": "bee",
    },
    
    # === STRUCTURES ===
    "box": {
        "fill": RETRO_PALETTE["brown"],
        "outline": RETRO_PALETTE["brown_dark"],
        "highlight": RETRO_PALETTE["brown_light"],
        "shape": "square",
    },
    "crate": {
        "fill": RETRO_PALETTE["wood"],
        "outline": RETRO_PALETTE["brown_dark"],
        "slats": RETRO_PALETTE["brown_dark"],
        "shape": "square",
        "has_slats": True,
    },
    "barrel": {
        "fill": RETRO_PALETTE["brown"],
        "outline": RETRO_PALETTE["brown_dark"],
        "bands": RETRO_PALETTE["gray"],
        "shape": "barrel",
    },
    "block": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "square",
    },
    "cube": {
        "fill": RETRO_PALETTE["blue"],
        "outline": RETRO_PALETTE["blue_dark"],
        "shape": "square",
    },
    "pyramid": {
        "fill": RETRO_PALETTE["sand"],
        "outline": RETRO_PALETTE["sand_dark"],
        "shape": "triangle",
    },
    
    # === PEOPLE/ROBOTS ===
    "person": {
        "fill": RETRO_PALETTE["pink"],
        "outline": RETRO_PALETTE["brown"],
        "clothes": RETRO_PALETTE["blue"],
        "shape": "person",
    },
    "robot": {
        "fill": RETRO_PALETTE["metal"],
        "outline": RETRO_PALETTE["gray_dark"],
        "eyes": RETRO_PALETTE["red"],
        "shape": "robot",
    },
    
    # === ABSTRACT ===
    "node": {
        "fill": RETRO_PALETTE["cyan"],
        "outline": RETRO_PALETTE["blue"],
        "glow": RETRO_PALETTE["glow_blue"],
        "shape": "circle",
        "has_glow": True,
    },
    "data": {
        "fill": RETRO_PALETTE["green"],
        "outline": RETRO_PALETTE["green_dark"],
        "binary": RETRO_PALETTE["green_light"],
        "shape": "square",
        "has_binary": True,
    },
    "energy": {
        "fill": RETRO_PALETTE["yellow"],
        "outline": RETRO_PALETTE["orange"],
        "glow": RETRO_PALETTE["yellow_light"],
        "shape": "star",
        "has_glow": True,
    },
    
    # === ENVIRONMENT ===
    "ground": {
        "fill": RETRO_PALETTE["ground"],
        "outline": RETRO_PALETTE["ground_dark"],
        "top": RETRO_PALETTE["grass"],
        "shape": "ground",
    },
    "wall": {
        "fill": RETRO_PALETTE["gray"],
        "outline": RETRO_PALETTE["gray_dark"],
        "shape": "wall",
    },
    
    # === DEFAULT ===
    "default": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "circle",
    },
    "object": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "circle",
    },
    "thing": {
        "fill": RETRO_PALETTE["gray_light"],
        "outline": RETRO_PALETTE["gray_dark"],
        "highlight": RETRO_PALETTE["white"],
        "shape": "circle",
    },
}


class UniversalRenderer:
    """
    Universal Retro 2D Renderer.
    
    Can render ANY entity type with beautiful retro game visuals.
    Supports 50+ entity types with unique pixel-art appearances.
    """
    
    def __init__(
        self,
        output_dir: str = "sim_outputs",
        pixel_scale: int = 4,
        enable_scanlines: bool = False,
        enable_shadows: bool = True,
        enable_glow: bool = True,
    ):
        self.output_dir = output_dir
        self.pixel_scale = pixel_scale
        self.enable_scanlines = enable_scanlines
        self.enable_shadows = enable_shadows
        self.enable_glow = enable_glow
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.available = NUMPY_AVAILABLE and CV2_AVAILABLE
    
    def render_entity(
        self,
        image: np.ndarray,
        entity: Dict[str, Any],
        x: int,
        y: int,
        radius: int,
    ) -> None:
        """Render any entity with appropriate retro visuals."""
        if not self.available or cv2 is None:
            return
        
        entity_type = entity.get("type", "default").lower()
        visuals = ENTITY_VISUALS.get(entity_type, ENTITY_VISUALS["default"])
        
        fill_color = visuals.get("fill", RETRO_PALETTE["gray"])
        outline_color = visuals.get("outline", RETRO_PALETTE["gray_dark"])
        highlight_color = visuals.get("highlight", RETRO_PALETTE["white"])
        
        shape = visuals.get("shape", "circle")
        
        # Draw shadow
        if self.enable_shadows:
            shadow_offset = max(4, radius // 4)
            self._draw_shape(image, shape, x + shadow_offset, y + shadow_offset, 
                           radius, (0, 0, 0), (0, 0, 0), fill_only=True)
        
        # Draw glow effect
        if self.enable_glow and visuals.get("has_glow"):
            glow_color = visuals.get("glow", RETRO_PALETTE["white"])
            for i in range(3, 0, -1):
                glow_radius = radius + i * 4
                alpha = 0.3 / i
                self._draw_glow(image, x, y, glow_radius, glow_color, alpha)
        
        # Draw main shape
        self._draw_shape(image, shape, x, y, radius, fill_color, outline_color)
        
        # Draw highlight
        if shape == "circle":
            highlight_radius = max(4, radius // 4)
            highlight_x = x - radius // 3
            highlight_y = y - radius // 3
            cv2.circle(image, (highlight_x, highlight_y), highlight_radius, 
                      highlight_color, -1)
        
        # Draw entity-specific details
        self._draw_details(image, entity_type, x, y, radius, visuals)
    
    def _draw_shape(
        self,
        image: np.ndarray,
        shape: str,
        x: int,
        y: int,
        radius: int,
        fill_color: Tuple,
        outline_color: Tuple,
        fill_only: bool = False,
    ) -> None:
        """Draw basic shape."""
        if cv2 is None:
            return
        
        outline_thickness = max(3, radius // 6)
        
        if shape == "circle":
            cv2.circle(image, (x, y), radius, fill_color, -1)
            if not fill_only:
                cv2.circle(image, (x, y), radius, outline_color, outline_thickness)
        
        elif shape == "square":
            half = radius
            cv2.rectangle(image, (x - half, y - half), (x + half, y + half), 
                        fill_color, -1)
            if not fill_only:
                cv2.rectangle(image, (x - half, y - half), (x + half, y + half), 
                            outline_color, outline_thickness)
        
        elif shape == "triangle":
            pts = np.array([
                [x, y - radius],
                [x - radius, y + radius],
                [x + radius, y + radius],
            ], np.int32)
            cv2.fillPoly(image, [pts], fill_color)
            if not fill_only:
                cv2.polylines(image, [pts], True, outline_color, outline_thickness)
        
        elif shape == "oval":
            cv2.ellipse(image, (x, y), (radius, int(radius * 1.3)), 0, 0, 360, 
                       fill_color, -1)
            if not fill_only:
                cv2.ellipse(image, (x, y), (radius, int(radius * 1.3)), 0, 0, 360, 
                           outline_color, outline_thickness)
        
        elif shape == "star":
            self._draw_star(image, x, y, radius, fill_color, outline_color)
        
        elif shape == "drop":
            # Water drop shape
            cv2.circle(image, (x, y + radius // 3), int(radius * 0.8), fill_color, -1)
            pts = np.array([
                [x, y - radius],
                [x - int(radius * 0.6), y + radius // 3],
                [x + int(radius * 0.6), y + radius // 3],
            ], np.int32)
            cv2.fillPoly(image, [pts], fill_color)
            if not fill_only:
                cv2.circle(image, (x, y + radius // 3), int(radius * 0.8), 
                          outline_color, outline_thickness)
        
        else:
            # Default to circle
            cv2.circle(image, (x, y), radius, fill_color, -1)
            if not fill_only:
                cv2.circle(image, (x, y), radius, outline_color, outline_thickness)
    
    def _draw_star(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        radius: int,
        fill_color: Tuple,
        outline_color: Tuple,
    ) -> None:
        """Draw a 5-pointed star."""
        if cv2 is None:
            return
        
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = radius if i % 2 == 0 else radius // 2
            px = int(x + r * math.cos(angle))
            py = int(y + r * math.sin(angle))
            points.append([px, py])
        
        pts = np.array(points, np.int32)
        cv2.fillPoly(image, [pts], fill_color)
        cv2.polylines(image, [pts], True, outline_color, 2)
    
    def _draw_glow(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        radius: int,
        color: Tuple,
        alpha: float,
    ) -> None:
        """Draw glow effect."""
        if cv2 is None or np is None:
            return
        
        overlay = image.copy()
        cv2.circle(overlay, (x, y), radius, color, -1)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
    
    def _draw_details(
        self,
        image: np.ndarray,
        entity_type: str,
        x: int,
        y: int,
        radius: int,
        visuals: Dict,
    ) -> None:
        """Draw entity-specific details."""
        if cv2 is None:
            return
        
        # Apple stem and leaf
        if entity_type == "apple" or visuals.get("has_stem"):
            stem_w = max(4, radius // 4)
            stem_h = max(8, radius // 2)
            cv2.rectangle(
                image,
                (x - stem_w // 2, y - radius - stem_h),
                (x + stem_w // 2, y - radius + 2),
                RETRO_PALETTE["brown"],
                -1
            )
            if visuals.get("has_leaf"):
                leaf_pts = np.array([
                    [x + 2, y - radius - stem_h + 4],
                    [x + radius // 2, y - radius - stem_h - 4],
                    [x + radius // 3, y - radius - 2],
                ], np.int32)
                cv2.fillPoly(image, [leaf_pts], visuals.get("detail", RETRO_PALETTE["green"]))
        
        # Ball stripe
        if visuals.get("has_stripe") and entity_type in ("ball",):
            stripe_y = y - radius // 4
            stripe_h = max(4, radius // 4)
            for sy in range(stripe_y, stripe_y + stripe_h):
                if 0 <= sy < image.shape[0]:
                    dy = abs(sy - y)
                    if dy < radius:
                        dx = int(math.sqrt(radius * radius - dy * dy))
                        x1 = max(0, x - dx + 4)
                        x2 = min(image.shape[1], x + dx - 4)
                        if x1 < x2:
                            image[sy, x1:x2] = visuals.get("highlight", RETRO_PALETTE["white"])
        
        # Cosmic glow rings
        if visuals.get("has_event_horizon"):
            glow_color = visuals.get("glow", RETRO_PALETTE["purple"])
            for i in range(3):
                ring_radius = radius + 4 + i * 4
                cv2.circle(image, (x, y), ring_radius, glow_color, 2)
        
        # Pulsar rays
        if visuals.get("has_pulsar_rays"):
            glow_color = visuals.get("glow", RETRO_PALETTE["blue_light"])
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                end_x = int(x + math.cos(rad) * (radius + 20))
                end_y = int(y + math.sin(rad) * (radius + 20))
                cv2.line(image, (x, y), (end_x, end_y), glow_color, 2)
        
        # Sun rays
        if visuals.get("has_rays"):
            ray_color = visuals.get("glow", RETRO_PALETTE["yellow"])
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                start_x = int(x + math.cos(rad) * radius)
                start_y = int(y + math.sin(rad) * radius)
                end_x = int(x + math.cos(rad) * (radius + 15))
                end_y = int(y + math.sin(rad) * (radius + 15))
                cv2.line(image, (start_x, start_y), (end_x, end_y), ray_color, 3)
        
        # Comet tail
        if visuals.get("has_tail"):
            tail_color = visuals.get("tail", RETRO_PALETTE["white"])
            for i in range(5):
                tail_x = x + radius + i * 10
                tail_width = max(1, radius - i * 3)
                if tail_width > 0:
                    cv2.circle(image, (tail_x, y), tail_width, tail_color, -1)
        
        # Orbitals for atoms
        if visuals.get("has_orbitals"):
            orbital_color = visuals.get("orbitals", RETRO_PALETTE["blue_light"])
            for angle in [0, 60, 120]:
                cv2.ellipse(image, (x, y), (radius + 15, 8), angle, 0, 360, 
                           orbital_color, 1)
        
        # Basketball lines
        if visuals.get("has_lines"):
            lines_color = visuals.get("lines", RETRO_PALETTE["brown_dark"])
            cv2.line(image, (x, y - radius), (x, y + radius), lines_color, 2)
            cv2.ellipse(image, (x, y), (radius, radius // 3), 0, 0, 360, lines_color, 2)
        
        # Soccer ball pentagons (simplified)
        if visuals.get("has_pentagons"):
            pattern = visuals.get("pattern", RETRO_PALETTE["black"])
            cv2.circle(image, (x, y), radius // 2, pattern, -1)
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                px = int(x + math.cos(rad) * radius * 0.65)
                py = int(y + math.sin(rad) * radius * 0.65)
                cv2.circle(image, (px, py), radius // 5, pattern, -1)


# Create convenience instance
_universal_renderer = None


def get_universal_renderer() -> UniversalRenderer:
    """Get shared universal renderer instance."""
    global _universal_renderer
    if _universal_renderer is None:
        _universal_renderer = UniversalRenderer()
    return _universal_renderer
