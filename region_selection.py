import cv2
import sys
import json
import os


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
                print(f"Using frame {i+1} for region selection (frame 1 was black)")
            return ret, frame

    return None, None


def validate_region_aspect_ratio(x1, y1, x2, y2):
    """Validate that the selected region has a reasonable piano aspect ratio"""
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    if width == 0 or height == 0:
        return False, "Selected region has zero width or height"

    aspect_ratio = width / height

    # Piano keyboards typically have aspect ratios between 8:1 to 15:1
    # This is a reasonable range for most piano video layouts
    min_ratio, max_ratio = 8.0, 15.0

    if aspect_ratio < min_ratio:
        return False, f"Region too tall for piano keyboard (aspect ratio: {aspect_ratio:.2f})"
    elif aspect_ratio > max_ratio:
        return False, f"Region too wide for piano keyboard (aspect ratio: {aspect_ratio:.2f})"

    return True, f"Good aspect ratio: {aspect_ratio:.2f}"


def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python select_region.py <video_path>")
        print("This script helps you select the keyboard region in your piano video.")
        sys.exit(1)

    video_path = sys.argv[1]

    # Check if video exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found")
        sys.exit(1)

    # Load video
    try:
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            print(f"Error: Could not open video file '{video_path}'")
            sys.exit(1)
        print(f"Loaded video: {video_path}")
    except Exception as e:
        print(f"Error loading video: {e}")
        sys.exit(1)

    # Get first valid frame
    ret, frame = get_first_valid_frame(video)
    if not ret or frame is None:
        print("Error: Could not read any valid frames from video")
        sys.exit(1)

    print("Found valid frame for region selection")

    # Instructions for user
    print("\n" + "="*60)
    print("KEYBOARD REGION SELECTION")
    print("="*60)
    print("Instructions:")
    print("1. A window will open showing the video frame")
    print("2. Click and drag to select the ENTIRE 88-key keyboard region")
    print("3. Make sure to include all keys from leftmost to rightmost")
    print("4. Press SPACE or ENTER to confirm selection")
    print("5. Press ESC to cancel")
    print("="*60)

    # Create window for region selection
    cv2.namedWindow("Select Keyboard Region", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select Keyboard Region", 1200, 800)

    # Let user select region
    print("\nSelecting region... (click and drag to select keyboard area)")
    region = cv2.selectROI("Select Keyboard Region", frame, showCrosshair=True)

    # Extract coordinates
    x, y, w, h = region

    # Check if user cancelled (selectROI returns (0,0,0,0) on cancel)
    if w == 0 or h == 0:
        print("Region selection cancelled")
        cv2.destroyAllWindows()
        video.release()
        sys.exit(0)

    # Convert to corner coordinates
    x1, y1 = x, y
    x2, y2 = x + w, y + h

    print(f"Selected region: ({x1}, {y1}) to ({x2}, {y2})")
    print(f"Region size: {w} x {h} pixels")

    # Validate aspect ratio
    is_valid, message = validate_region_aspect_ratio(x1, y1, x2, y2)
    print(f"Validation: {message}")

    if not is_valid:
        print("\nWarning: The selected region may not be suitable for a piano keyboard.")
        response = input("Do you want to continue anyway? (y/N): ").strip().lower()
        if response != 'y' and response != 'yes':
            print("Region selection cancelled")
            cv2.destroyAllWindows()
            video.release()
            sys.exit(0)

    # Save region data
    region_data = {
            "video_path": video_path,
            "region": {
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2)
                },
            "width": int(w),
            "height": int(h),
            "aspect_ratio": float(w / h)
            }

    # Save to JSON file
    output_file = "keyboard_region.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(region_data, f, indent=2)
        print(f"\nRegion saved to '{output_file}'")
        print("You can now run the main script to process your video!")

        # Show confirmation
        confirmation_frame = frame.copy()
        cv2.rectangle(confirmation_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(confirmation_frame, "Selected Keyboard Region",
                    (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Selected Keyboard Region", confirmation_frame)
        print("\nPress any key to close...")
        cv2.waitKey(0)

    except Exception as e:
        print(f"Error saving region data: {e}")
        sys.exit(1)

    # Cleanup
    cv2.destroyAllWindows()
    video.release()


if __name__ == "__main__":
    main()
