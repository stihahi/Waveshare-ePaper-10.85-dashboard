import os
import sys
import unittest

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from panel_frame import PANEL_HEIGHT, PANEL_WIDTH, RED, WHITE, YELLOW, build_frame

HALF_ROW_BYTES = PANEL_WIDTH // 2 // 4
ALL_WHITE_BYTE = 0x55


def white_mono_image():
    return Image.new('1', (PANEL_WIDTH, PANEL_HEIGHT), 255)


def white_rgb_image():
    return Image.new('RGB', (PANEL_WIDTH, PANEL_HEIGHT), WHITE)


class BuildFrameTest(unittest.TestCase):
    def test_white_image_fills_both_halves_with_white_code(self):
        frame = build_frame(white_mono_image())

        self.assertEqual(frame.master, bytes([ALL_WHITE_BYTE]) * HALF_ROW_BYTES * PANEL_HEIGHT)
        self.assertEqual(frame.slave, bytes([ALL_WHITE_BYTE]) * HALF_ROW_BYTES * PANEL_HEIGHT)

    def test_black_pixel_is_packed_into_most_significant_bits(self):
        image = white_mono_image()
        image.putpixel((0, 0), 0)

        frame = build_frame(image)

        self.assertEqual(frame.master[0], 0b00_01_01_01)

    def test_right_half_pixels_go_to_slave_controller(self):
        image = white_mono_image()
        image.putpixel((PANEL_WIDTH // 2, 0), 0)

        frame = build_frame(image)

        self.assertEqual(frame.slave[0], 0b00_01_01_01)
        self.assertEqual(set(frame.master), {ALL_WHITE_BYTE})

    def test_red_and_yellow_map_to_their_color_codes(self):
        image = white_rgb_image()
        image.putpixel((3, 0), RED)
        image.putpixel((1, 1), YELLOW)

        frame = build_frame(image)

        self.assertEqual(frame.master[0], 0b01_01_01_11)
        self.assertEqual(frame.master[HALF_ROW_BYTES], 0b01_10_01_01)

    def test_rejects_image_with_wrong_size(self):
        with self.assertRaises(ValueError):
            build_frame(Image.new('1', (PANEL_HEIGHT, PANEL_WIDTH), 255))


if __name__ == '__main__':
    unittest.main()
