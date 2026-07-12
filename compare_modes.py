"""
Compare CAPTION_MODE=sequential vs CAPTION_MODE=formal_grounded on the same clip.

Usage:
    FIREWORKS_API_KEY=... python compare_modes.py <video.mp4>
"""
import os
import re
import sys
import tempfile
import subprocess

from pipeline.analyze import analyze_video
from pipeline.caption import generate_captions


def _get_ffmpeg_binary() -> str:
    import shutil
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("ffmpeg not found")


FFMPEG = _get_ffmpeg_binary()


def extract_frames(video_path: str, output_dir: str, count: int = 6) -> list[str]:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", video_path],
        capture_output=True, text=True, timeout=30
    )
    match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        raise RuntimeError("Could not determine duration")
    hours, minutes, seconds = match.groups()
    duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    frame_paths = []
    step = duration / count
    for i in range(count):
        ts = step * (i + 0.5)
        out_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
             "-ss", str(ts), "-i", video_path,
             "-frames:v", "1",
             "-vf", "scale=768:768:force_original_aspect_ratio=decrease",
             "-q:v", "4", out_path],
            check=True, timeout=30,
        )
        frame_paths.append(out_path)
    return frame_paths


def run_mode(description: str, mode: str) -> dict[str, str]:
    os.environ["CAPTION_MODE"] = mode
    # Reimport to pick up env change.
    from pipeline import caption as cap_module
    import importlib
    importlib.reload(cap_module)
    return cap_module.generate_captions(description)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_modes.py <video.mp4>")
        sys.exit(1)

    video_path = sys.argv[1]
    with tempfile.TemporaryDirectory(prefix="cmp_") as tmpdir:
        frames = extract_frames(video_path, tmpdir)
        print("Analyzing video...")
        description = analyze_video(frames, transcript="")
        print(f"\nDescription:\n{description}\n")

        for mode in ("sequential", "formal_grounded"):
            print(f"\n{'='*60}")
            print(f"MODE: {mode}")
            print('='*60)
            captions = run_mode(description, mode)
            for style, text in captions.items():
                word_count = len(text.split())
                print(f"\n[{style}] ({word_count} words): {text}")


if __name__ == "__main__":
    main()
