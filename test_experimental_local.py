"""
Quick local smoke test for the experimental pipeline.

Usage:
    FIREWORKS_API_KEY=... python test_experimental_local.py <path_to_video.mp4>
"""
import os
import re
import sys
import tempfile
import subprocess

from pipeline.analyze import analyze_video
from pipeline.caption import generate_captions


def _get_ffmpeg_binary() -> str:
    """Return the ffmpeg executable, falling back to imageio-ffmpeg if needed."""
    import shutil
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except Exception:
        raise RuntimeError(
            "ffmpeg not found in PATH and imageio_ffmpeg is not installed."
        )


FFMPEG = _get_ffmpeg_binary()


def extract_some_frames(video_path: str, output_dir: str, count: int = 6) -> list[str]:
    """Extract *count* midpoint frames from a local video for quick testing."""
    # Get duration.
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", video_path],
        capture_output=True, text=True, timeout=30
    )
    import re
    match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError("Could not determine video duration")
    hours, minutes, seconds = match.groups()
    duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    frame_paths = []
    step = duration / count
    for i in range(count):
        ts = step * (i + 0.5)
        out_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        subprocess.run(
            [
                FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-ss", str(ts),
                "-i", video_path,
                "-frames:v", "1",
                "-vf", "scale=768:768:force_original_aspect_ratio=decrease",
                "-q:v", "4",
                out_path,
            ],
            check=True,
            timeout=30,
        )
        frame_paths.append(out_path)
    return frame_paths


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_experimental_local.py <video.mp4>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="exp_test_") as tmpdir:
        print(f"Extracting frames from {video_path}...")
        frames = extract_some_frames(video_path, tmpdir)
        print(f"Using {len(frames)} frames: {frames}")

        print("\nAnalyzing video...")
        description = analyze_video(frames, transcript="")
        print(f"\nDescription:\n{description}\n")

        print("Generating captions...")
        captions = generate_captions(description)
        for style, text in captions.items():
            word_count = len(text.split())
            print(f"\n[{style}] ({word_count} words): {text}")


if __name__ == "__main__":
    main()
