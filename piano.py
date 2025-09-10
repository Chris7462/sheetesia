import cv2
import numpy as np
from typing import List, Tuple
from key import Key


class Piano:
    """Represents a piano with 88 keys detected from a defined region"""

    def __init__(self, image: np.ndarray, region: dict):
        self.keys: List[Key] = []
        self.region = region
        self._create_88_keys(image, region)

    def _create_88_keys(self, image: np.ndarray, region: dict):
        """Create all 88 piano keys based on the defined region"""
        x1, y1 = region["x1"], region["y1"]
        x2, y2 = region["x2"], region["y2"]
        width = x2 - x1
        height = y2 - y1

        # Piano has 52 white keys and 36 black keys
        white_key_width = width / 52
        black_key_width = white_key_width * 0.6  # Standard ratio

        # Y positions - black keys are in top portion to avoid white key overlap
        white_key_y = y1 + int(height * 0.8)  # 80% down from top
        black_key_y = y1 + int(height * 0.4)  # 40% down from top

        # Track white key positions for black key placement
        white_key_positions = []

        # Create all 88 keys (MIDI 21-108)
        for midi_note in range(21, 109):  # A0 to C8
            key_color = self._get_default_color_for_key(image, midi_note, x1, y1, width, height,
                                                        white_key_width, black_key_width,
                                                        white_key_y, black_key_y,
                                                        white_key_positions)

            key_location = self._calculate_key_position(midi_note, x1, y1, width, height,
                                                        white_key_width, black_key_width,
                                                        white_key_y, black_key_y,
                                                        white_key_positions)

            key = Key(midi_note, key_location, key_color)
            self.keys.append(key)

    def _calculate_key_position(self, midi_note: int, x1: int, y1: int,
                                width: int, height: int, white_key_width: float,
                                black_key_width: float, white_key_y: int, black_key_y: int,
                                white_key_positions: List[int]) -> Tuple[int, int]:
        """Calculate the (x, y) position for a given MIDI note"""
        is_black_key = self._is_black_key(midi_note)

        if is_black_key:
            # Black key - position relative to surrounding white keys
            x = self._get_black_key_x_position(midi_note, x1, white_key_width, white_key_positions)
            y = black_key_y
        else:
            # White key - evenly spaced across the width
            white_key_index = self._get_white_key_index(midi_note)
            x = x1 + int(white_key_index * white_key_width + white_key_width / 2)
            y = white_key_y
            white_key_positions.append(x)

        return (x, y)

    def _get_default_color_for_key(self, image: np.ndarray, midi_note: int,
                                   x1: int, y1: int, width: int, height: int,
                                   white_key_width: float, black_key_width: float,
                                   white_key_y: int, black_key_y: int,
                                   white_key_positions: List[int]) -> Tuple[int, int, int]:
        """Get the default color for a key at its calculated position"""
        location = self._calculate_key_position(midi_note, x1, y1, width, height,
                                                white_key_width, black_key_width,
                                                white_key_y, black_key_y,
                                                white_key_positions.copy())

        x, y = location

        # Bounds checking
        if y >= image.shape[0] or x >= image.shape[1] or x < 0 or y < 0:
            return (0, 0, 0)  # Default to black if out of bounds

        return tuple(image[y, x].astype(int))

    def _is_black_key(self, midi_note: int) -> bool:
        """Determine if a MIDI note represents a black key"""
        note_in_octave = (midi_note - 21) % 12
        return note_in_octave in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#

    def _get_white_key_index(self, midi_note: int) -> int:
        """Get the index of a white key (0-51) for positioning"""
        # Count white keys from A0 (MIDI 21) to this note
        white_key_count = 0

        for note in range(21, midi_note + 1):
            if not self._is_black_key(note):
                if note == midi_note:
                    return white_key_count
                white_key_count += 1

        return 0

    def _get_black_key_x_position(self, midi_note: int, x1: int, white_key_width: float,
                                  white_key_positions: List[int]) -> int:
        """Calculate X position for black keys relative to white keys"""
        # Black keys are positioned between specific white keys
        note_in_octave = (midi_note - 21) % 12
        octave_start_midi = midi_note - note_in_octave

        # Find the surrounding white keys for this black key
        if note_in_octave == 1:  # C#
            left_white = octave_start_midi  # C
            right_white = octave_start_midi + 2  # D
        elif note_in_octave == 3:  # D#
            left_white = octave_start_midi + 2  # D
            right_white = octave_start_midi + 4  # E
        elif note_in_octave == 6:  # F#
            left_white = octave_start_midi + 5  # F
            right_white = octave_start_midi + 7  # G
        elif note_in_octave == 8:  # G#
            left_white = octave_start_midi + 7  # G
            right_white = octave_start_midi + 9  # A
        elif note_in_octave == 10:  # A#
            left_white = octave_start_midi + 9  # A
            right_white = octave_start_midi + 11  # B
        else:
            # This shouldn't happen for black keys
            return x1

        # Get white key indices and calculate position between them
        left_white_index = self._get_white_key_index(left_white)
        right_white_index = self._get_white_key_index(right_white)

        left_x = x1 + int(left_white_index * white_key_width + white_key_width / 2)
        right_x = x1 + int(right_white_index * white_key_width + white_key_width / 2)

        # Black key positioned between the two white keys
        return int((left_x + right_x) / 2)

    def draw_keys(self, image: np.ndarray) -> np.ndarray:
        """Draw all 88 keys on the image for visualization"""
        image_show = image.copy()

        # Draw region boundary
        x1, y1 = self.region["x1"], self.region["y1"]
        x2, y2 = self.region["x2"], self.region["y2"]
        cv2.rectangle(image_show, (x1, y1), (x2, y2), (255, 255, 0), 2)

        # Draw each key
        for key in self.keys:
            if key.is_black_key:
                color = (100, 100, 255) if key.pressed else (200, 100, 100)  # Red for black keys
                radius = 3
            else:
                color = (100, 255, 100) if key.pressed else (100, 200, 255)  # Blue for white keys
                radius = 4

            cv2.circle(image_show, key.location, radius, color, -1)

            # Draw key number for debugging (only every 12th key to avoid clutter)
            if key.midi_note % 12 == 0:  # Show only C notes
                cv2.putText(image_show, str(key.midi_note),
                            (key.location[0] - 10, key.location[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        return image_show

    def get_key_by_midi_note(self, midi_note: int) -> Key:
        """Get a specific key by its MIDI note number"""
        for key in self.keys:
            if key.midi_note == midi_note:
                return key
        raise ValueError(f"Key with MIDI note {midi_note} not found")

    def get_pressed_keys(self) -> List[Key]:
        """Get all currently pressed keys"""
        return [key for key in self.keys if key.pressed]
