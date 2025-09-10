import cv2
import numpy as np
from typing import List, Tuple
from octave import Octave

# Note constants
NOTE_C = 0
NOTE_CSHARP = 1
NOTE_D = 2
NOTE_DSHARP = 3
NOTE_E = 4
NOTE_F = 5
NOTE_FSHARP = 6
NOTE_G = 7
NOTE_GSHARP = 8
NOTE_A = 9
NOTE_ASHARP = 10
NOTE_B = 11


class Piano:
    """Represents a piano with multiple octaves detected from an image"""

    def __init__(self, image: np.ndarray, unscaled_template: np.ndarray):
        self.octaves: List[Octave] = []
        self._detect_octaves(image, unscaled_template)

    def _detect_octaves(self, image: np.ndarray, unscaled_template: np.ndarray):
        """Detect all octaves in the image using template matching"""
        # Scale template to fit the image
        template = self._get_scaled_template(image, unscaled_template)

        # Perform template matching
        result = cv2.matchTemplate(image, template, cv2.TM_SQDIFF_NORMED)

        # Find octaves using adaptive thresholding
        thresh = 0.0
        thresh_step = 0.02

        while thresh <= 1.0:
            # Threshold the result
            _, threshold_result = cv2.threshold(result, thresh, 1.0, cv2.THRESH_BINARY)
            threshold_result = threshold_result.astype(np.uint8)

            # Find all matches
            temp_octaves = []
            result_copy = threshold_result.copy()

            while True:
                # Find the best match
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_copy)

                # Stop if no more matches
                if max_val == min_val:
                    break

                # Create octave at this location
                octave = Octave(min_loc, image, template)
                temp_octaves.append(octave)

                # Remove this match area to find the next one
                cv2.rectangle(result_copy,
                            (min_loc[0] - 10, 0),
                            (min_loc[0] + template.shape[1] + 10, image.shape[0]),
                            (1,), -1)

            # If we found octaves, use them
            if temp_octaves:
                self.octaves = temp_octaves
                break

            thresh += thresh_step

        if not self.octaves:
            raise RuntimeError("No piano octaves found in the image")

        # Sort octaves and assign proper note codes
        self._sort_octaves(image)

    def _get_scaled_template(self, image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """Scale the template to best match the image"""
        img_height, img_width = image.shape[:2]
        tmpl_height, tmpl_width = template.shape[:2]

        found_scaled_width = tmpl_width
        found_min_val = 1.0

        # Try different scales
        for scaled_width in range(tmpl_width, img_width):
            # Calculate proportional height
            scale_proportion = scaled_width / img_width
            scaled_height = int(img_height * scale_proportion)

            # Resize image to this scale
            image_scaled = cv2.resize(image, (scaled_width, scaled_height),
                                    interpolation=cv2.INTER_NEAREST)

            # Skip if template is larger than scaled image
            if template.shape[0] > image_scaled.shape[0] or template.shape[1] > image_scaled.shape[1]:
                continue

            # Perform template matching
            try:
                result_scaled = cv2.matchTemplate(image_scaled, template, cv2.TM_SQDIFF_NORMED)
                min_val, _, _, _ = cv2.minMaxLoc(result_scaled)

                # Store if this is the best match so far
                if min_val < found_min_val:
                    found_scaled_width = scaled_width
                    found_min_val = min_val

                # Exit early if perfect match
                if min_val == 0.0:
                    break

                # Heuristic: stop if no improvement for a while
                if scaled_width - found_scaled_width > 100:
                    break

            except cv2.error:
                continue

        # Scale the template
        scale = img_width // found_scaled_width
        scaled_template = cv2.resize(template,
                                   (tmpl_width * scale, tmpl_height),
                                   interpolation=cv2.INTER_NEAREST)

        return scaled_template

    def _sort_octaves(self, image: np.ndarray):
        """Sort octaves from left to right and assign proper MIDI note codes"""
        # Sort by x coordinate (left to right)
        self.octaves.sort(key=lambda octave: octave.notes[NOTE_C].location[0])

        # Find middle C by looking for a gray dot
        middle_c_octave_index = 0

        for index, octave in enumerate(self.octaves):
            note_c = octave.notes[NOTE_C]
            x, y = note_c.location

            # Look for a gray pixel below the note
            thresh = 10
            for check_y in range(y, min(y + 20, image.shape[0] - 20)):
                if check_y < image.shape[0] and x < image.shape[1]:
                    pixel = image[check_y, x]

                    # Check if pixel is significantly different from default color
                    color_diff = abs(int(note_c.default_color[0]) - int(pixel[0]))
                    if color_diff > thresh:
                        middle_c_octave_index = index
                        break

        # Calculate octave number offset (middle C = C4, MIDI note 60)
        # C4 = octave 5 in our numbering (since we start from 0)
        index_to_octave_number = 5 - middle_c_octave_index

        # Update note codes for all octaves
        for octave_index, octave in enumerate(self.octaves):
            for note in octave.notes:
                octave_number = octave_index + index_to_octave_number
                note.code = (octave_number * 12) + note.code

    def draw_notes(self, image: np.ndarray) -> np.ndarray:
        """Draw detected notes and octaves on the image for visualization"""
        image_show = image.copy()

        for octave in self.octaves:
            # Draw octave bounding box
            c_note_pos = octave.notes[NOTE_C].location
            b_note_pos = octave.notes[NOTE_B].location

            cv2.rectangle(image_show, c_note_pos, b_note_pos, (50, 170, 255), 2)

            # Draw each note
            for note in octave.notes:
                cv2.circle(image_show, note.location, 4, (70, 170, 202), -1)

        return image_show
