# Piano Note Detection

Sheetesia detects piano key presses from video files and generates MIDI output.

## Features

- **Computer Vision**: Uses OpenCV template matching to detect piano octaves in video frames
- **Real-time Note Detection**: Tracks color changes at key locations to detect press/release events
- **MIDI Generation**: Outputs detected notes as a standard MIDI file using the `mido` library
- **Visualization**: Shows detected notes and octaves overlaid on the video

## Requirements

- Python 3.8+
- OpenCV
- NumPy
- mido (for MIDI file generation)

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Make sure you have the template image in the `res/` directory:
```
res/template.png
```

## Usage

```bash
python main.py <path_to_video_file>
```

The program will:
1. Load the video and template image
2. Detect piano octaves in the first frame
3. Process each frame to detect key presses/releases
4. Generate a MIDI file (`out.mid`) with the detected notes
5. Display frames with activity in a window

## Project Structure

```
├── main.py          # Main application entry point
├── piano.py         # Piano class with octave detection logic
├── octave.py        # Note and Octave classes
├── requirements.txt # Python dependencies
├── res/
│   └── template.png # Template image for octave detection
└── out.mid         # Generated MIDI file (created after running)
```

## How It Works

1. **Template Matching**: Uses OpenCV's `matchTemplate` to find piano octaves in the video
2. **Note Location**: Divides each detected octave into 12 equal sections for the chromatic notes
3. **Color Analysis**: Monitors pixel color changes at each note location
4. **State Detection**: Compares current colors with default colors to detect press/release
5. **MIDI Output**: Converts detected events to MIDI messages with proper timing

## Key Differences from Rust Version

- **Error Handling**: Uses Python exceptions instead of `Result<T,E>` types
- **Memory Management**: Automatic garbage collection instead of manual memory management
- **Type System**: Dynamic typing with optional type hints for clarity
- **Libraries**:
  - `cv2` (OpenCV-Python) instead of opencv-rust
  - `mido` instead of ghakuf for MIDI handling
  - `numpy` arrays instead of OpenCV Mat objects
- **Code Style**: More Pythonic idioms and structure

## Troubleshooting

- **"No piano octaves found"**: Adjust the template matching thresholds in `piano.py`
- **Poor detection accuracy**: Fine-tune the color difference thresholds (`between_frames_thresh`, `color_thresh`)
- **Performance issues**: The Python version may be slower than Rust, especially for high-resolution videos

## Configuration

You can adjust detection sensitivity by modifying these values in `main.py`:
- `between_frames_thresh = 150`: Threshold for detecting color changes between frames
- `color_thresh = 200`: Threshold for determining if a key is pressed vs released
