import cv2
import numpy as np
import sys
import mido
from typing import List, Tuple
from piano import Piano


def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    # Load video and template
    try:
        video = cv2.VideoCapture(video_path)
        template = cv2.imread("res/template.png", cv2.IMREAD_COLOR)

        if not video.isOpened() or template is None:
            print("Error loading video or template")
            sys.exit(1)

        print(f"Loaded video: {video_path}")

    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    # Create window for display
    cv2.namedWindow("Piano Detection", cv2.WINDOW_AUTOSIZE)

    # Read first frame and find piano
    ret, frame = video.read()
    if not ret:
        print("Could not read first frame")
        sys.exit(1)

    print("Finding piano...")
    try:
        piano = Piano(frame, template)
        print("Piano detected successfully!")
    except Exception as e:
        print(f"Error detecting piano: {e}")
        sys.exit(1)

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
    microseconds_per_quarter_note = int(fps * 1000000)
    tempo_msg = mido.MetaMessage('set_tempo', tempo=microseconds_per_quarter_note)
    track.append(tempo_msg)

    # MIDI timing
    ticks_per_quarter_note = mid.ticks_per_beat  # Default is 480
    ticks_per_frame = int(fps)

    # Initialize previous frame colors for each note
    previous_frame_note_colors = []
    for octave in piano.octaves:
        octave_colors = []
        for note in octave.notes:
            octave_colors.append(note.default_color)
        previous_frame_note_colors.append(octave_colors)

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

        key_pressed_or_released_in_this_frame = False

        # Check each note in every octave
        for octave_index, octave in enumerate(piano.octaves):
            for note_index, note in enumerate(octave.notes):
                x, y = note.location

                # Skip if coordinates are out of bounds
                if y >= frame.shape[0] or x >= frame.shape[1]:
                    continue

                # Get current note color
                note_color = tuple(frame[y, x].astype(int))

                # Check if color changed significantly from previous frame
                prev_color = previous_frame_note_colors[octave_index][note_index]
                diff_with_previous_frame = sum(abs(note_color[i] - prev_color[i]) for i in range(3))

                # If color changed significantly, check if note was pressed/released
                if diff_with_previous_frame > between_frames_thresh:
                    # Compare with default color to determine press state
                    diff_with_default_color = sum(abs(note_color[i] - note.default_color[i]) for i in range(3))

                    # Determine if note should be pressed
                    should_be_pressed = diff_with_default_color > color_thresh
                    result = note.set_pressed(should_be_pressed)

                    # If state actually changed, add MIDI event
                    if result is not None:
                        progress = (frame_count / total_frames) * 100
                        delta_time = (frame_count - frame_count_on_last_event) * ticks_per_frame

                        if result:  # Note pressed
                            print(f"{note.to_string()}\tpressed \t@ frame {frame_count} of {total_frames}\t({progress:.2f}%)")
                            msg = mido.Message('note_on',
                                             channel=0,
                                             note=note.code,
                                             velocity=127,
                                             time=delta_time)
                        else:  # Note released
                            print(f"{note.to_string()}\treleased\t@ frame {frame_count} of {total_frames}\t({progress:.2f}%)")
                            msg = mido.Message('note_off',
                                             channel=0,
                                             note=note.code,
                                             velocity=127,
                                             time=delta_time)

                        track.append(msg)
                        key_pressed_or_released_in_this_frame = True
                        frame_count_on_last_event = frame_count

                # Update previous frame color
                previous_frame_note_colors[octave_index][note_index] = note_color

        # Display frame if there was activity
        if key_pressed_or_released_in_this_frame:
            # Draw notes on frame for visualization
            display_frame = piano.draw_notes(frame)
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
