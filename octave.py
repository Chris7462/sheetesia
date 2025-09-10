import cv2
import numpy as np
from typing import List, Tuple, Optional, Union


class Note:
    """Represents a single piano note with its location and state"""

    def __init__(self, code: int, location: Tuple[int, int], default_color: Tuple[int, int, int]):
        self.code = code
        self.location = location  # (x, y)
        self.default_color = default_color  # (B, G, R)
        self.pressed = False

    def set_pressed(self, pressed: bool) -> Union[bool, None]:
        """
        Set the pressed state of the note.
        Returns the new state if changed, None if no change occurred.
        """
        if self.pressed == pressed:
            return None  # No change

        self.pressed = pressed
        return pressed

    def to_string(self) -> str:
        """Return human readable note name"""
        octave_number = (self.code // 12) - 1
        note_number = self.code % 12

        note_strings = ["C ", "C#", "D ", "D#", "E ", "F ", "F#", "G ", "G#", "A ", "A#", "B "]
        return f"{note_strings[note_number]} {octave_number}"


class Octave:
    """Represents a piano octave containing 12 notes"""

    def __init__(self, octave_location: Tuple[int, int], image: np.ndarray, template: np.ndarray):
        self.notes: List[Note] = []
        self._create_notes(octave_location, image, template)

    def _create_notes(self, octave_location: Tuple[int, int], image: np.ndarray, template: np.ndarray):
        """Create notes for this octave by analyzing the image"""
        x_loc, y_loc = octave_location
        template_height, template_width = template.shape[:2]

        # Extract the octave region from the image
        octave_image = image[y_loc:y_loc + template_height, x_loc:x_loc + template_width]
        pixel_diff_thresh = 100

        # For each note in the octave (12 notes)
        for note in range(12):
            # Calculate the pixel range for this note
            min_x = (template_width * note) // 12
            max_x = (template_width * (note + 1)) // 12

            # Find the bounds of the note by comparing with template
            note_min_x = min_x
            note_max_x = max_x

            for x in range(min_x, max_x):
                if x < octave_image.shape[1] and x < template.shape[1]:
                    # Get pixel colors (BGR format)
                    octave_pixel = octave_image[0, x] if octave_image.shape[0] > 0 else [0, 0, 0]
                    template_pixel = template[0, x] if template.shape[0] > 0 else [0, 0, 0]

                    # Calculate color difference
                    pixel_diff = sum(abs(int(template_pixel[i]) - int(octave_pixel[i])) for i in range(3))

                    if pixel_diff < pixel_diff_thresh:
                        note_min_x = min(note_min_x, x)
                        note_max_x = max(note_max_x, x)

            # Calculate average position for the note
            avg_x = (note_min_x + note_max_x) // 2
            note_location = (x_loc + avg_x, y_loc)

            # Get the default color at this location
            if avg_x < octave_image.shape[1] and octave_image.shape[0] > 0:
                default_color = tuple(octave_image[0, avg_x].astype(int))
            else:
                default_color = (0, 0, 0)

            # Create and add the note
            note_obj = Note(
                code=note,
                location=note_location,
                default_color=default_color
            )
            self.notes.append(note_obj)
