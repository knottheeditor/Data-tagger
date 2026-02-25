"""
Quick Thumbnail Extractor
Analyzes a video and extracts the best frame for a thumbnail.
Scores frames based on sharpness, brightness, and contrast.
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path


def calculate_sharpness(frame):
    """Calculate sharpness using Laplacian variance."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def calculate_brightness(frame):
    """Calculate average brightness."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return np.mean(hsv[:, :, 2])


def calculate_contrast(frame):
    """Calculate contrast using standard deviation."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.std(gray)


def score_frame(frame):
    """
    Score a frame based on multiple quality metrics.
    Higher score = better thumbnail candidate.
    """
    sharpness = calculate_sharpness(frame)
    brightness = calculate_brightness(frame)
    contrast = calculate_contrast(frame)
    
    # Normalize scores
    # Ideal brightness is around 100-150 (not too dark, not too bright)
    brightness_score = 100 - abs(brightness - 125)
    
    # Combine scores (weighted)
    # Sharpness is most important for thumbnails
    total_score = (sharpness * 0.5) + (brightness_score * 0.25) + (contrast * 0.25)
    
    return total_score, sharpness, brightness, contrast


def extract_best_thumbnail(video_path, sample_count=50):
    """
    Extract the best frame from a video for use as a thumbnail.
    
    Args:
        video_path: Path to the video file
        sample_count: Number of frames to sample (default 50)
    
    Returns:
        Path to the saved thumbnail
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return None
    
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Video: {video_path.name}")
    print(f"Duration: {duration:.1f}s | Frames: {total_frames} | FPS: {fps:.1f}")
    print(f"Sampling {sample_count} frames...")
    
    # Skip first and last 5% to avoid intro/outro
    start_frame = int(total_frames * 0.05)
    end_frame = int(total_frames * 0.95)
    
    # Calculate frame positions to sample
    if end_frame - start_frame < sample_count:
        sample_positions = range(start_frame, end_frame)
    else:
        step = (end_frame - start_frame) // sample_count
        sample_positions = range(start_frame, end_frame, step)
    
    best_score = -1
    best_frame = None
    best_position = 0
    best_metrics = None
    
    for i, frame_pos in enumerate(sample_positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        score, sharpness, brightness, contrast = score_frame(frame)
        
        if score > best_score:
            best_score = score
            best_frame = frame.copy()
            best_position = frame_pos
            best_metrics = (sharpness, brightness, contrast)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Analyzed {i + 1}/{len(list(sample_positions))} frames...")
    
    cap.release()
    
    if best_frame is None:
        print("Error: Could not extract any valid frames")
        return None
    
    # Calculate timestamp of best frame
    best_timestamp = best_position / fps if fps > 0 else 0
    
    print(f"\nBest frame found at {best_timestamp:.1f}s (frame {best_position})")
    print(f"  Sharpness: {best_metrics[0]:.1f}")
    print(f"  Brightness: {best_metrics[1]:.1f}")
    print(f"  Contrast: {best_metrics[2]:.1f}")
    
    # Save thumbnail to same folder as video
    output_path = video_path.parent / f"{video_path.stem}_thumbnail.jpg"
    
    # Save with high quality
    cv2.imwrite(str(output_path), best_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    print(f"\nThumbnail saved: {output_path}")
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python thumbnail_extractor.py <video_path> [sample_count]")
        print("\nExample:")
        print("  python thumbnail_extractor.py video.mp4")
        print("  python thumbnail_extractor.py video.mp4 100")
        sys.exit(1)
    
    video_path = sys.argv[1]
    sample_count = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    extract_best_thumbnail(video_path, sample_count)


if __name__ == "__main__":
    main()
