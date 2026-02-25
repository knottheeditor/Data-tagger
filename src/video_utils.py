import subprocess
import os
import json

class VideoUtils:
    @staticmethod
    def get_duration(file_path):
        """Returns the duration of a video in seconds."""
        cmd = [
            'ffprobe', '-v', 'error', 
            '-probesize', '10M', '-analyzeduration', '10M',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ]
        try:
            output = subprocess.check_output(cmd, timeout=120).decode('utf-8').strip()
            return float(output)
        except subprocess.TimeoutExpired:
            print(f"VideoUtils: Duration probe timed out for {file_path}")
            return 0
        except Exception as e:
            print(f"FFprobe error: {e}")
            return 0

    @staticmethod
    def extract_frame(video_path, timestamp, output_path, width=None, brighten=False):
        """Extracts a single frame at the given timestamp, optionally resizing and brightening."""
        # -q:v 2 for high quality, -vf scale for resizing
        filter_chain = []
        if width:
            filter_chain.append(f"scale={width}:-1")
        if brighten:
            # High-intensity boost for dark/neon forensic analysis
            filter_chain.append("eq=brightness=0.3:contrast=1.4:saturation=1.2")
        
        filters = ",".join(filter_chain) if filter_chain else None
        
        cmd = ['ffmpeg', '-ss', str(timestamp), '-i', video_path]
        if filters:
            cmd += ['-vf', filters]
        cmd += ['-frames:v', '1', '-q:v', '2', '-y', output_path]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=180)
            return True
        except subprocess.TimeoutExpired:
            print(f"VideoUtils: Extract frame timed out for {video_path}")
            return False
        except subprocess.CalledProcessError as e:
            # Truncate error to avoid console spam for corrupt files
            err_msg = e.stderr.decode().strip().split('\n')[-1] if e.stderr else "Unknown error"
            print(f"FFmpeg warning at {timestamp}s: {err_msg}")
            return False
        except Exception as e:
            print(f"Unexpected frame extraction error: {e}")
            return False

    @staticmethod
    def generate_clip(video_path, start_time, duration, output_path, vertical=False, ratio_1_1=False):
        """Generates a clip. If vertical=True, applies a 9:16 crop. If ratio_1_1, applies a 1:1 center crop."""
        cmd = ['ffmpeg', '-ss', str(start_time), '-t', str(duration), '-i', video_path]
        
        if ratio_1_1:
            # 1:1 Center Crop: crop to the smallest dimension
            cmd += ['-vf', 'crop=min(ih\\,iw):min(ih\\,iw):(iw-min(ih\\,iw))/2:(ih-min(ih\\,iw))/2']
        elif vertical:
            # Simple center crop for 9:16 (assuming 16:9 input)
            cmd += ['-vf', 'crop=ih*9/16:ih:(iw-ow)/2:0']
            
        cmd += ['-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-c:a', 'aac', '-y', output_path]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg clipping error: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"Unexpected clipping error: {e}")
            return False

    @staticmethod
    def extract_thumbnail_candidates(video_path, output_dir, num_frames=5):
        """
        Extracts multiple candidate frames at key moments for thumbnail selection.
        Returns a list of output file paths.
        """
        duration = VideoUtils.get_duration(video_path)
        if duration <= 0:
            return []
        
        # Extract frames at 10%, 25%, 50%, 75%, 90% of the video
        percentages = [0.10, 0.25, 0.50, 0.75, 0.90][:num_frames]
        timestamps = [duration * p for p in percentages]
        
        os.makedirs(output_dir, exist_ok=True)
        output_paths = []
        
        for i, ts in enumerate(timestamps):
            output_path = os.path.join(output_dir, f"thumb_candidate_{i+1}.png")
            if VideoUtils.extract_frame(video_path, ts, output_path):
                output_paths.append(output_path)
        
        return output_paths

    @staticmethod
    def random_thumbnail_candidate(video_path, output_dir):
        """Picks a random frame between 10% and 90% of the video."""
        import random
        duration = VideoUtils.get_duration(video_path)
        if duration <= 0: return None
        
        # Avoid boring intro/outro
        ts = random.uniform(duration * 0.1, duration * 0.9)
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "random_thumb.png")
        if VideoUtils.extract_frame(video_path, ts, output_path):
            return output_path
        return None

    @staticmethod
    def get_aspect_ratio(video_path):
        """Returns the aspect ratio of a video as a string (e.g., '16:9', '9:16')."""
        cmd = [
            'ffprobe', '-v', 'error', 
            '-probesize', '10M', '-analyzeduration', '10M',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json', video_path
        ]
        try:
            output = subprocess.check_output(cmd, timeout=120).decode('utf-8')
            data = json.loads(output)
            width = data['streams'][0]['width']
            height = data['streams'][0]['height']
            
            ratio = width / height
            if ratio > 1.5:
                return "16:9"
            elif ratio < 0.7:
                return "9:16"
            else:
                return "1:1"
        except subprocess.TimeoutExpired:
            print(f"VideoUtils: AR probe timed out for {video_path}")
            return "16:9"
        except Exception as e:
            print(f"Aspect ratio detection error: {e}")
            return "16:9"
