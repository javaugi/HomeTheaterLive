#frontend/src/myapp/utils/images.py
import os
import cv2

def resize_images_in_directory(directory, target_size=(1920, 1080)):
    """
    Resize all images in directory to target size
    """
    import glob
    from PIL import Image
    
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(directory, ext)))
    
    for img_path in image_files:
        img = Image.open(img_path)
        img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
        img_resized.save(img_path)

def add_transition_effect(video_path, output_path, transition_duration=0.5, fps=30):
    """
    Add transition effects between frames
    """
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    
    # Add crossfade transitions
    transition_frames = int(transition_duration * fps)
    
    for i in range(len(frames) - 1):
        # Write original frame
        for _ in range(fps):  # Show each frame for 1 second
            out.write(frames[i])
        
        # Add transition
        if i < len(frames) - 1:
            for j in range(transition_frames):
                alpha = j / transition_frames
                blended = cv2.addWeighted(frames[i], 1 - alpha, frames[i + 1], alpha, 0)
                out.write(blended)
    
    # Write last frame
    for _ in range(fps):
        out.write(frames[-1])
    
    out.release()
    cv2.destroyAllWindows()

def extract_frames_from_video(video_path, output_dir, fps=1):
    """
    Extract frames from video (reverse operation)
    """
    cap = cv2.VideoCapture(video_path)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    frame_count = 0
    success = True
    
    while success:
        success, frame = cap.read()
        if success and frame_count % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            cv2.imwrite(os.path.join(output_dir, f"frame_{frame_count:04d}.jpg"), frame)
        frame_count += 1
    
    cap.release()# -*- coding: utf-8 -*-

