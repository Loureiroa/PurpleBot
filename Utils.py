import subprocess

ffmpeg_path = "F:\\ffmpeg\\ffmpeg.exe"

def check_ffmpeg_path():
    try:
        result = subprocess.run([ffmpeg_path, "-version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False