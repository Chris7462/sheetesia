from typing import Tuple, Union


class Key:
    """Represents a single piano key with its MIDI note number, location, and state"""

    def __init__(self, midi_note: int, location: Tuple[int, int], default_color: Tuple[int, int, int]):
        self.midi_note = midi_note  # MIDI note number (21-108 for 88-key piano)
        self.location = location    # (x, y) pixel coordinates
        self.default_color = default_color  # (B, G, R) default color
        self.pressed = False
        self.is_black_key = self._determine_if_black_key()
        self.note_name = self._get_note_name()

    def _determine_if_black_key(self) -> bool:
        """Determine if this is a black key based on MIDI note number"""
        # In a 12-note octave, black keys are at positions 1, 3, 6, 8, 10
        # (C#, D#, F#, G#, A#)
        note_in_octave = (self.midi_note - 21) % 12
        return note_in_octave in [1, 3, 6, 8, 10]

    def _get_note_name(self) -> str:
        """Convert MIDI note number to note name (e.g., A0, C4, C8)"""
        # MIDI note 21 = A0, MIDI note 60 = C4
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        # Calculate octave (A0 is in octave 0)
        # MIDI 21 (A0) to MIDI 23 (B0) are octave 0
        # MIDI 24 (C1) to MIDI 35 (B1) are octave 1, etc.
        octave = ((self.midi_note - 12) // 12)
        note_index = (self.midi_note - 21) % 12

        # Adjust for the fact that A0 starts the sequence
        if note_index >= 9:  # A, A#, B
            adjusted_octave = octave
            adjusted_note_index = note_index
        else:  # C, C#, D, D#, E, F, F#, G, G#
            adjusted_octave = octave + 1
            adjusted_note_index = note_index + 3  # Shift C to position 3 in our array
            if adjusted_note_index >= 12:
                adjusted_note_index -= 12

        return f"{note_names[adjusted_note_index]}{adjusted_octave}"

    def set_pressed(self, pressed: bool) -> Union[bool, None]:
        """
        Set the pressed state of the key.
        Returns the new state if changed, None if no change occurred.
        """
        if self.pressed == pressed:
            return None  # No change

        self.pressed = pressed
        return pressed

    def to_string(self) -> str:
        """Return human readable note name with MIDI number"""
        return f"{self.note_name} (MIDI {self.midi_note})"

    def __repr__(self) -> str:
        """String representation for debugging"""
        key_type = "Black" if self.is_black_key else "White"
        return f"Key({self.note_name}, MIDI={self.midi_note}, {key_type}, pos={self.location})"
