from dataclasses import dataclass

import numpy as np
from PIL import Image

PANEL_WIDTH = 1360
PANEL_HEIGHT = 480
PIXELS_PER_BYTE = 4

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

# Palette index is the panel's 2-bit color code: 00 black, 01 white, 10 yellow, 11 red.
PANEL_PALETTE_RGB = (*BLACK, *WHITE, *YELLOW, *RED)


@dataclass(frozen=True)
class FourColorFrame:
    master: bytes
    slave: bytes


def build_frame(image):
    color_codes = _to_color_codes(_require_panel_size(image))
    packed_rows = _pack_rows(color_codes)
    half = packed_rows.shape[1] // 2
    return FourColorFrame(packed_rows[:, :half].tobytes(), packed_rows[:, half:].tobytes())


def _require_panel_size(image):
    if image.size != (PANEL_WIDTH, PANEL_HEIGHT):
        raise ValueError(f"expected {PANEL_WIDTH}x{PANEL_HEIGHT} image, got {image.size[0]}x{image.size[1]}")
    return image


def _to_color_codes(image):
    palette_image = Image.new('P', (1, 1))
    palette_image.putpalette(PANEL_PALETTE_RGB)
    quantized = image.convert('RGB').quantize(palette=palette_image, dither=Image.Dither.NONE)
    return np.asarray(quantized, dtype=np.uint8)


def _pack_rows(color_codes):
    groups = color_codes.reshape(PANEL_HEIGHT, PANEL_WIDTH // PIXELS_PER_BYTE, PIXELS_PER_BYTE)
    return (groups[..., 0] << 6) | (groups[..., 1] << 4) | (groups[..., 2] << 2) | groups[..., 3]
