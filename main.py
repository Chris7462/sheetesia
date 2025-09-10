import cv2
import numpy as np
import sys
import json
import os
import mido
from typing import List, Tuple
from piano import Piano


def get_first_valid_frame(video):
    """Get the first non-black frame from video"""
    for i in range(10):  # Try first 10 frames
        ret, frame = video.read()
        if not ret:
            return None, None

        # Check if frame is not completely black
        mean_brightness = cv2.mean(frame)[0]
        if mean_brightness > 1.0:
            if i > 0:
                print(f"Using frame {i+1} for piano detection (frame 1 was black)")
            return ret, frame

    return None, None


def load_keyboard_region():
    """Load the keyboard region from the JSON file"""
    region_file = "keyboard_region.json"

    if not os.path.exists(region_file):
        print(f"Error: {region_file} not found!")
        print("Please run 'python select_region.py <video_path>' first to select the keyboard region.")
        sys.exit(1)

    try:
        with open(region_file, 'r') as f:
            data = json.load(f)
        return data["region"]
    except Exception as e:
        print(f"Error loading region file: {e}")
        sys.exit(1)


def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        print("Make sure you've run 'python select_region.py <video_path>' first!")
        sys.exit(1)

    video_path = sys.argv[1]

    # Load keyboard region
    region = load_keyboard_region()
    print(f"Loaded keyboard region: ({region['x1']}, {region['y1']}) to ({region['x2']}, {region['y2']})")

    # Load video
    try:
        video = cv2.VideoCapture(video_path)

        if not video.isOpened():
            print("Error loading video")
            sys.exit(1)

        print(f"Loaded video: {video_path}")

    except Exception as e:
        print(f"Error loading video: {e}")
        sys.exit(1)

    # Create window for display
    cv2.namedWindow("Piano Detection", cv2.WINDOW_AUTOSIZE)

    # Read first valid frame and create piano
    ret, frame = get_first_valid_frame(video)
    if not ret or frame is None:
        print("Could not read any valid frames")
        sys.exit(1)

    print("Creating 88-key piano layout...")
    try:
        piano = Piano(frame, region)
        print("Piano created successfully!")
        print(f"Created {len(piano.keys)} keys (should be 88)")

        if len(piano.keys) != 88:
            print(f"Error: Expected 88 keys, got {len(piano.keys)}")
            sys.exit(1)

    except Exception as e:
        print(f"Error creating piano: {e}")
        sys.exit(1)

    # Reset video to beginning for processing
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # Setup MIDI
    print("Detecting notes!")

    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo (convert FPS to MIDI tempo)
#   microseconds_per_quarter_note = int(fps * 1000000)
#   tempo_msg = mido.MetaMessage('set_tempo', tempo=microseconds_per_quarter_note)
#   track.append(tempo_msg)

#   # MIDI timing - adjust ticks per frame based on FPS for proper timing
#   ticks_per_quarter_note = mid.ticks_per_beat  # Default is 480
#   ticks_per_frame = max(1, int(ticks_per_quarter_note / fps))  # Scale based on video FPS
# MIDI timing setup based on video FPS

    ticks_per_quarter_note = mid.ticks_per_beat  # usually 480

    # Microseconds per quarter note so that 1 frame ~ 1 tick
    microseconds_per_quarter_note = int((ticks_per_quarter_note / fps) * 1_000_000)

    # Clamp to valid MIDI range
    microseconds_per_quarter_note = min(microseconds_per_quarter_note, 0xFFFFFF)

    tempo_msg = mido.MetaMessage('set_tempo', tempo=microseconds_per_quarter_note)
    track.append(tempo_msg)

    # Each video frame corresponds to 1 MIDI tick
    ticks_per_frame = 1

    # Initialize previous frame colors for each key
    previous_frame_colors = []
    for key in piano.keys:
        previous_frame_colors.append(key.default_color)

    # Video processing variables
    frame_count = 0
    frame_count_on_last_event = 0
    between_frames_thresh = 150
    color_thresh = 200

    # Process video frames
    while True:
        ret, frame = video.read()
        if not ret:
            print("Video processing complete!")
            break

        # Skip completely black frames
        if cv2.mean(frame)[0] < 1.0:
            frame_count += 1
            continue

        key_pressed_or_released_in_this_frame = False

        # Check each of the 88 keys
        for key_index, key in enumerate(piano.keys):
            x, y = key.location

            # Skip if coordinates are out of bounds
            if y >= frame.shape[0] or x >= frame.shape[1] or x < 0 or y < 0:
                continue

            # Get current key color
            key_color = tuple(frame[y, x].astype(int))

            # Check if color changed significantly from previous frame
            prev_color = previous_frame_colors[key_index]
            diff_with_previous_frame = sum(abs(key_color[i] - prev_color[i]) for i in range(3))

            # If color changed significantly, check if key was pressed/released
            if diff_with_previous_frame > between_frames_thresh:
                # Compare with default color to determine press state
                diff_with_default_color = sum(abs(key_color[i] - key.default_color[i]) for i in range(3))

                # Determine if key should be pressed
                should_be_pressed = diff_with_default_color > color_thresh
                result = key.set_pressed(should_be_pressed)

                # If state actually changed, add MIDI event
                if result is not None:
                    progress = (frame_count / total_frames) * 100
                    delta_time = (frame_count - frame_count_on_last_event) * ticks_per_frame

                    if result:  # Key pressed
                        print(f"{key.to_string()}\tpressed \t@ frame {frame_count} of {total_frames}\t({progress:.2f}%)")
                        msg = mido.Message('note_on',
                                           channel=0,
                                           note=key.midi_note,
                                           velocity=127,
                                           time=delta_time)
                    else:  # Key released
                        print(f"{key.to_string()}\treleased\t@ frame {frame_count} of {total_frames}\t({progress:.2f}%)")
                        msg = mido.Message('note_off',
                                           channel=0,
                                           note=key.midi_note,
                                           velocity=127,
                                           time=delta_time)

                    track.append(msg)
                    key_pressed_or_released_in_this_frame = True
                    frame_count_on_last_event = frame_count

            # Update previous frame color
            previous_frame_colors[key_index] = key_color

        # Display frame if there was activity
        if key_pressed_or_released_in_this_frame:
            # Draw keys on frame for visualization
            display_frame = piano.draw_keys(frame)
            cv2.imshow("Piano Detection", display_frame)
            cv2.waitKey(1)

        frame_count += 1

    # Save MIDI file
    try:
        mid.save("out.mid")
        print("MIDI file saved as 'out.mid'")
    except Exception as e:
        print(f"Error saving MIDI file: {e}")

    # Cleanup
    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
