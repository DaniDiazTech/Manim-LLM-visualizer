"""Utility functions for video generation and manipulation with Manim."""

import json
import logging
import os
import subprocess

from manim_generator.utils.rendering import extract_scene_class_names

logger = logging.getLogger(__name__)


def render_and_concat(script_file: str, output_media_dir: str, final_output: str) -> str | None:
    """
    Runs a Manim script as a subprocess, then concatenates the rendered scene videos
    (in the order they appear in the script) into one final video using ffmpeg.

    Parameters:
      script_file (str): Path to the Manim Python script (e.g. "video.py")
      output_media_dir (str): The media directory specified to Manim (e.g. "output")
      final_output (str): The filename for the concatenated final video (e.g. "final_video.mp4")

    Returns:
      str | None: Absolute path to the final concatenated video file, or None if rendering failed
    """

    # run Manim as a subprocess with real-time output
    manim_command = [
        "manim",
        "-qh",
        script_file,
        "--write_all",
        "--media_dir",
        output_media_dir,
    ]
    process = subprocess.Popen(
        manim_command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
        bufsize=1,
        universal_newlines=True,
    )

    # print output in real-time
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
            logger.info(output.strip())

    if process.returncode != 0:
        logger.error("Error during Manim rendering")
        return
    else:
        logger.info("Manim rendering completed successfully.")

    # extract scene names
    with open(script_file, encoding="utf-8") as f:
        content = f.read()
    scene_names = extract_scene_class_names(content)

    logger.info("Found scene names in order: %s", scene_names)

    # Build the path to the rendered videos.
    script_basename = os.path.splitext(os.path.basename(script_file))[0]

    # The quality folder is "1080p60" since the -pqh argument
    quality_folder = "1080p60"
    videos_dir = os.path.join(output_media_dir, "videos", script_basename, quality_folder)
    if not os.path.exists(videos_dir):
        logger.error("Rendered videos folder not found: %s", videos_dir)
        return

    # create a temporary file for ffmpeg's concat list in the output directory
    concat_list_path = os.path.join(output_media_dir, "ffmpeg_concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as file_list:
        for scene in scene_names:
            video_path = os.path.join(videos_dir, f"{scene}.mp4")
            if not os.path.exists(video_path):
                logger.warning(
                    "Expected video file for scene '%s' not found at %s",
                    scene,
                    video_path,
                )
            abs_path = os.path.abspath(video_path)
            file_list.write(f"file '{abs_path}'\n")

    final_output_path = os.path.join(output_media_dir, final_output)
    final_output_path = os.path.abspath(final_output_path)

    # use ffmpeg to concat individual scenes
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-c",
        "copy",
        final_output_path,
    ]
    logger.info("Concatenating videos with ffmpeg: %s", " ".join(ffmpeg_command))

    ffmpeg_proc = subprocess.Popen(
        ffmpeg_command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )

    # print ffmpeg output in real-time
    while True:
        output = ffmpeg_proc.stdout.readline()
        if output == "" and ffmpeg_proc.poll() is not None:
            break
        if output:
            print(output.strip())
            logger.info(output.strip())

    if ffmpeg_proc.returncode != 0:
        logger.error("Error during ffmpeg concatenation")
        return None
    else:
        logger.info("Final concatenated video created at: %s", final_output_path)
    os.remove(concat_list_path)

    # autoplay final video
    play_command = []
    if os.name == "nt":  # Windows
        final_output_path = os.path.abspath(final_output_path)
        try:
            subprocess.run(["cmd", "/c", "start", "", final_output_path], shell=True)
            logger.info("Playing video with default media player")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to play video: %s", str(e))
    elif os.name == "posix":  # Linux/Mac
        if os.uname().sysname == "Linux":
            abs_path = os.path.abspath(final_output_path)
            try:
                subprocess.run(["xdg-open", abs_path], check=True, env=os.environ.copy())
                logger.info("Playing video with xdg-open")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error("Failed to play video with xdg-open: %s", str(e))
                try:
                    # fallbacks
                    for player in ["vlc", "mpv", "ffplay", "mplayer"]:
                        try:
                            subprocess.run(["which", player], check=True, stdout=subprocess.PIPE)
                            subprocess.run([player, abs_path], check=False)
                            logger.info(f"Playing video with {player}")
                            break
                        except subprocess.CalledProcessError:
                            continue
                except Exception as e:
                    logger.error("Failed to play video with fallback players: %s", str(e))
        else:  # Mac
            play_command = ["open", final_output_path]
            try:
                subprocess.run(play_command, check=True)
                logger.info("Playing video with default media player")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to play video: %s", str(e))
    else:
        logger.error("Could not determine appropriate video player command for this system")

    return final_output_path


def get_video_duration(video_path: str) -> float | None:
    """
    Get the duration of a video file in seconds using ffprobe.

    Args:
        video_path: Path to the video file

    Returns:
        float: Duration in seconds, or None if error
    """
    try:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=30
        )
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError, subprocess.TimeoutExpired) as e:
        logger.error(f"Error getting video duration: {e}")
        return None


def extend_video_to_duration(
    input_path: str, output_path: str, target_duration: float
) -> bool:
    """
    Extend a video to a target duration by looping it using ffmpeg.

    Args:
        input_path: Path to input video file
        output_path: Path to output video file
        target_duration: Target duration in seconds

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current duration
        current_duration = get_video_duration(input_path)
        if current_duration is None:
            logger.error("Could not determine input video duration")
            return False

        if current_duration >= target_duration:
            # Video is already long enough, just copy it
            import shutil
            shutil.copy2(input_path, output_path)
            logger.info(f"Video already {current_duration:.2f}s, copying as-is")
            return True

        # Calculate how many times we need to loop
        loops_needed = int(target_duration / current_duration) + 1
        logger.info(
            f"Extending video from {current_duration:.2f}s to {target_duration:.2f}s "
            f"(looping {loops_needed} times)"
        )

        # Create a temporary concat file
        concat_file = output_path + ".concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            abs_input = os.path.abspath(input_path)
            for _ in range(loops_needed):
                f.write(f"file '{abs_input}'\n")

        # Use ffmpeg to concatenate (loop) the video
        command = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",
            output_path,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        # Clean up concat file
        try:
            os.remove(concat_file)
        except Exception:
            pass

        if result.returncode != 0:
            logger.error(f"Error extending video: {result.stderr}")
            return False

        # Trim to exact target duration if needed
        final_duration = get_video_duration(output_path)
        if final_duration and final_duration > target_duration:
            return trim_video_to_duration(output_path, output_path, target_duration)

        return True
    except Exception as e:
        logger.exception(f"Error extending video: {e}")
        return False


def trim_video_to_duration(
    input_path: str, output_path: str, target_duration: float
) -> bool:
    """
    Trim a video to a target duration using ffmpeg.

    Args:
        input_path: Path to input video file
        output_path: Path to output video file
        target_duration: Target duration in seconds

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-t",
            str(target_duration),
            "-c",
            "copy",
            "-y",  # Overwrite output file
            output_path,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Error trimming video: {result.stderr}")
            return False

        logger.info(f"Trimmed video to {target_duration:.2f}s")
        return True
    except Exception as e:
        logger.exception(f"Error trimming video: {e}")
        return False


def adjust_video_duration(
    video_path: str, min_duration: float | None = None, max_duration: float | None = None
) -> str | None:
    """
    Adjust video duration to be within min_duration and max_duration.

    Args:
        video_path: Path to the video file
        min_duration: Minimum duration in seconds (extend if shorter)
        max_duration: Maximum duration in seconds (trim if longer)

    Returns:
        str: Path to adjusted video (may be same as input if no adjustment needed), or None if error
    """
    if min_duration is None and max_duration is None:
        return video_path

    current_duration = get_video_duration(video_path)
    if current_duration is None:
        logger.error("Could not determine video duration")
        return None

    # Determine target duration (respect max if both are set)
    target_duration = min_duration
    if max_duration and min_duration:
        # If both are set, use min but don't exceed max
        target_duration = min(min_duration, max_duration)
    elif max_duration and not min_duration:
        # Only max is set, use current duration if it's already within limit
        if current_duration <= max_duration:
            return video_path
        target_duration = max_duration

    needs_adjustment = False
    if min_duration and current_duration < min_duration:
        needs_adjustment = True
        logger.info(
            f"Video duration {current_duration:.2f}s is shorter than minimum {min_duration:.2f}s"
        )
    if max_duration and current_duration > max_duration:
        needs_adjustment = True
        logger.info(
            f"Video duration {current_duration:.2f}s is longer than maximum {max_duration:.2f}s"
        )

    if not needs_adjustment:
        return video_path

    # Create temporary output path
    base, ext = os.path.splitext(video_path)
    temp_output = f"{base}_adjusted{ext}"

    # Extend if too short (but don't exceed max_duration if set)
    if min_duration and current_duration < min_duration:
        extend_to = min_duration
        if max_duration:
            extend_to = min(min_duration, max_duration)
        
        if not extend_video_to_duration(video_path, temp_output, extend_to):
            return None
        
        # Update paths for potential trimming
        if os.path.exists(temp_output):
            if video_path != temp_output:
                try:
                    os.remove(video_path)
                except Exception:
                    pass
            video_path = temp_output
            current_duration = get_video_duration(video_path)
            if current_duration is None:
                return None

    # Trim if too long (after extension, might need trimming)
    if max_duration and current_duration and current_duration > max_duration:
        final_output = f"{base}_final{ext}"
        if not trim_video_to_duration(video_path, final_output, max_duration):
            return None
        # Clean up intermediate file if it exists
        if video_path != final_output and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
        return final_output

    return video_path
