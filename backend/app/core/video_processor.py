# VideoProcessor
import logging
from midiutil import MIDIFile
from app.crud.process_status import ProcessStatusCRUD
from app.model.schemas import ProcessStatusUpdate
from app.model.process_status import ProcessStatuses
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
from app.core.config import settings
import json
import subprocess
from datetime import datetime
import shutil
import tempfile
import asyncio
from typing import List, Optional, Tuple, Dict
import os
import numpy as np
from midi2audio import FluidSynth

logger = logging.getLogger(__name__)
print(">>> importing VideoProcessor done")


class VideoProcessor:
    def __init__(self, output_dir: str = str(settings.VIDEO_OUTPUT_DIR), soundfont_path: Optional[str] = str(settings.GM2_SOUNDFONT_PATH)):
        print(">>>VideoProcessor  initializing VideoProcessor")
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Check if file exists
        self.soundfont_path = soundfont_path
        if self.soundfont_path and os.path.exists(self.soundfont_path):
            logger.info(f"VideoProcessor Soundfont found at: {
                        self.soundfont_path}")
        else:
            logger.warning(f"VideoProcessor Soundfont not found at: {
                           self.soundfont_path}")
            self.soundfont_path = None

        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def create_video_from_images(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high"
    ) -> Dict:
        """Create H.264 video from images asynchronously"""
        print(f"VideoProcessor create_video_from_images job_id={job_id} image_paths={
              len(image_paths)}")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor,
                self._create_video_sync,
                job_id,
                image_paths,
                output_filename,
                fps,
                resolution,
                transition_type,
                duration_per_image,
                quality
            )
        except Exception as e:
            print(f"Error VideoProcessor create_video_from_images job_id={
                  job_id} {str(e)}")

    """ The _create_video_sync method is being called from a thread pool executor, so it doesn't have access to the database session.
    """

    def _create_video_sync(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high"
    ) -> Dict:
        """Synchronous H.264 video creation"""
        print(f"VideoProcessor _create_video_sync job_id={job_id} image_paths={
              len(image_paths)}")
        db = SessionLocal()           # ← fresh session per task
        try:
            # Validate inputs
            if not image_paths:
                raise ValueError("No images provided")

            # Sort images
            image_paths.sort()

            # Create output filename
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"video_{timestamp}.mp4"

            print(f"VideoProcessor _create_video_sync output_filename={
                  output_filename}")
            # Set quality parameters
            quality_settings = self._get_quality_settings(quality)

            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'],
                               capture_output=True, check=True)
                has_ffmpeg = True
            except:
                has_ffmpeg = False

            print(f"VideoProcessor _create_video_sync has_ffmpeg={
                  has_ffmpeg}, output_filename={output_filename}, image_paths={len(image_paths)}")
            if has_ffmpeg:
                video_path = self._create_video_ffmpeg(
                    job_id=job_id,
                    image_paths=image_paths,
                    output_filename=output_filename,
                    fps=fps,
                    resolution=resolution,
                    transition_type=transition_type,
                    duration_per_image=duration_per_image,
                    quality_settings=quality_settings,
                    background_db=db
                )
            else:
                video_path = self._create_video_opencv(
                    job_id=job_id,
                    image_paths=image_paths,
                    output_filename=output_filename,
                    fps=fps,
                    resolution=resolution,
                    transition_type=transition_type,
                    duration_per_image=duration_per_image,
                    quality_settings=quality_settings,
                    background_db=db
                )

            # Verify the created video
            print(f"VideoProcessor _create_video_sync video created={
                  os.path.exists(video_path)}. video_path={video_path}")
            if not os.path.exists(video_path):
                raise ValueError("Video file was not created")

            # Get video info
            video_size = os.path.getsize(video_path)
            if video_size == 0:
                raise ValueError(
                    "VideoProcessor _create_video_sync Video file is empty")
            video_info = self._get_video_info(video_path)

            print(f"VideoProcessor _create_video_sync updating db_status \n video_info={
                  video_info}, output_filename={output_filename}, video_path={video_path}")

            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.completed,
                    progress=100,
                    video_path=video_path,
                    video_url=f"/api/v1/video/{output_filename}",
                    filename=output_filename,
                    message=f"H.264 video created successfully: {
                        output_filename} ({self._format_bytes(video_size)})",
                    notes=f"codec=H.264, video_size={
                        video_size}, video_info={video_info}"
                )
            )
            print(f"VideoProcessor _create_video_sync return db_status={
                  db_status}")
            return db_status

        except Exception as e:
            logger.error(f"Error VideoProcessor _create_video_sync creating video: {
                         e}", exc_info=True)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.failed,
                    progress=100,
                    message=f"Failed to create video: {str(e)}",
                    error=str(e)
                )
            )
            print(f"Error VideoProcessor _create_video_sync return db_status={
                  db_status}")
            return db_status

    def _get_quality_settings(self, quality: str) -> Dict:
        """Get quality settings based on quality string"""
        quality_presets = {
            "low": {"preset": "ultrafast", "crf": 28, "bitrate": "1000k"},
            "medium": {"preset": "fast", "crf": 23, "bitrate": "2500k"},
            "high": {"preset": "medium", "crf": 20, "bitrate": "5000k"},
            "ultra": {"preset": "slow", "crf": 18, "bitrate": "8000k"}
        }
        return quality_presets.get(quality, quality_presets["medium"])

    def _create_video_opencv(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        transition_type: str,
        duration_per_image: float,
        quality_settings: Dict,
        background_db: Session = None
    ) -> str:
        """Create video using OpenCV with H.264 codec"""
        # video files go to the HomeTheaterLive/video_output/*.mp4
        video_path = os.path.join(self.output_dir, output_filename)
        print(f"VideoProcessor _create_video_opencv video_path={video_path}")

        # Read first image to get dimensions
        import cv2
        first_image = cv2.imread(image_paths[0])
        if first_image is None:
            raise ValueError(f"VideoProcessor _create_video_opencv Could not read first image: {
                             image_paths[0]}")

        # Set resolution
        if resolution:
            height, width = resolution[1], resolution[0]
        else:
            height, width, _ = first_image.shape
            # Ensure even dimensions (required by H.264)
            width = width - (width % 2)
            height = height - (height % 2)

        size = (width, height)

        # Try different H.264 codec configurations
        codecs = [
            ('H264', cv2.VideoWriter_fourcc(*'H264')),
            ('X264', cv2.VideoWriter_fourcc(*'X264')),
            ('AVC1', cv2.VideoWriter_fourcc(*'avc1')),
            ('MP4V', cv2.VideoWriter_fourcc(*'mp4v')),  # Fallback
        ]

        video_writer = None
        codec_used = None

        for codec_name, fourcc in codecs:
            try:
                video_writer = cv2.VideoWriter(
                    video_path,
                    fourcc,
                    fps,
                    size,
                    True
                )

                if video_writer.isOpened():
                    codec_used = codec_name
                    logger.info(f"Using codec: {codec_name}")
                    break
                else:
                    video_writer.release()
            except:
                continue

        print(f"VideoProcessor _create_video_opencv codec_used={
              codec_used}, video_writer={video_writer}")
        if not video_writer or not video_writer.isOpened():
            raise ValueError(
                "VideoProcessor _create_video_opencv Could not create video writer with any codec")

        try:
            frames_per_image = int(duration_per_image * fps)

            # Process each image
            for i, image_path in enumerate(image_paths):
                img = cv2.imread(image_path)
                if img is None:
                    logger.warning(f"Could not read image: {image_path}")
                    continue

                # Resize if needed
                if img.shape[:2] != (height, width):
                    img = cv2.resize(
                        img, size, interpolation=cv2.INTER_LANCZOS4)

                # Write frames for this image
                for _ in range(frames_per_image):
                    video_writer.write(img)

                # Add transition if specified and not last image
                if transition_type != "none" and i < len(image_paths) - 1:
                    next_img = cv2.imread(image_paths[i + 1])
                    if next_img is not None:
                        if next_img.shape[:2] != (height, width):
                            next_img = cv2.resize(next_img, size)

                        if transition_type == "fade":
                            self._add_fade_transition(
                                video_writer, img, next_img, fps, duration=0.5
                            )
                        elif transition_type == "slide":
                            self._add_slide_transition(
                                video_writer, img, next_img, fps, duration=0.5
                            )

            video_writer.release()
            logger.info(f"VideoProcessor _create_video_opencv created with OpenCV using {
                        codec_used}: {video_path}")

            # If not using H.264 codec, convert to H.264 using FFmpeg
            if codec_used != "H264" and codec_used != "X264":
                h264_path = video_path.replace('.mp4', '_h264.mp4')
                self._convert_to_h264_ffmpeg(
                    video_path, h264_path, quality_settings)
                os.replace(h264_path, video_path)  # Replace with H.264 version

            return video_path

        finally:
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()

    """
    Goal                          How to do it                Typical values
    Overall faster/slower         Change bpm = ...            "60–80 slow, 100–130 medium, 140+ fast"
    Speed changes during piece    "Multiple midi.addTempo(track, time, bpm)",Call at different time in beats
    More interesting melody,Use varied pitch lists + phrases,"Add leaps, higher/lower sections"
    More lively rhythm,Variable duration per note,Mix 0.25–2.0 beats
    More dynamic (loud/soft),Vary volume (velocity),"50–70 soft, 90–110 normal, accents 115+"
    
    
    Start with just changing bpm → then add one tempo change → then experiment 
        with melody/rhythm.
    If you share what feeling you're going for (calm ambient, upbeat positive, 
        dramatic, minimal piano, etc.), I can suggest more specific note patterns or progressions.   
    """

    def _generate_background_music(
        self,
        output_wav: str,
        total_duration_sec: float,
        soundfont_path: Optional[str] = None,
        bpm: int = 88
    ) -> None:
        """Generate pleasant piano-based background music via MIDI → WAV"""
        if soundfont_path is None:
            soundfont_path = self.soundfont_path

        print(f"VideoProcessor _generate_background_music soundfont_path={
              os.path.exists(soundfont_path)}")

        if not os.path.exists(soundfont_path):
            raise FileNotFoundError(f"SoundFont not found: {
                                    soundfont_path}. Download FluidR3_GM.sf2")

        midi_path = output_wav.replace(".wav", ".mid")

        midi = MIDIFile(1)  # 1 track
        track = 0
        channel = 0
        time = 0
        midi.addTempo(track, time, bpm)

        # Example: gradual speedup (accelerando)
        # after 8 beats → faster
        midi.addTempo(track, 8,  95)
        # after more time → even faster
        midi.addTempo(track, 24, 110)
        # after 8 beats → faster
        midi.addTempo(track, 8,  95)
        # ritardando / slower part
        midi.addTempo(track, 24, 70)
        # ritardando / slower part
        midi.addTempo(track, 24, 95)
        midi.addTempo(track, 48, 125)                   # later section quicker
        # Or: slow middle section
        # midi.addTempo(track, 32, 70)                  # ritardando / slower part

        # Chord progression: C → Am → F → G (pleasant & common)
        chords = [
            [60, 64, 67],     # C
            [57, 60, 64],     # Am
            [53, 57, 60],     # F
            [55, 59, 62],     # G
        ]
        chord_beats = 4  # beats per chord

        # Repeat chords enough times
        repeats = int(total_duration_sec / (chord_beats * 60 / bpm)) + 2
        for chord in chords * repeats:
            for note in chord:
                midi.addNote(track, channel, note, time, chord_beats, 82)
            time += chord_beats

        # Example: rising then falling phrases + some leaps
        melody_pattern = [
            72, 74, 76, 79, 81, 83, 81, 79,     # rising
            76, 74, 72, 69, 67, 72,             # falling + lower note
            74, 77, 81, 84, 81, 77, 74, 72,     # another phrase with higher peak
            79, 76, 72, 67                      # ending lower
        ]
        melody_notes = melody_pattern * 6  # repeat enough times
        # or even better: create 3-4 short phrases and concatenate them
        # Light melody overlay (channel 1 - e.g. bells or strings)
        # melody_notes = [72, 74, 76, 77, 79, 81, 79, 77, 74] * 12
        # for i, pitch in enumerate(melody_notes):
        #     midi.addNote(track, 1, pitch, i * 0.8, 1.1, 95)

        # Add rhythmic variation (some notes shorter/longer)
        # Example rhythms in beats: 0.5 = eighth note, 1.0 = quarter, 1.5 = dotted quarter, etc.
        # rhythms = [1.0, 0.5, 0.5, 1.0, 0.75, 0.25, 1.0, 0.5] * 10
        # current_time = 0
        # for i, (pitch, dur) in enumerate(zip(melody_notes, rhythms)):
        #     midi.addNote(track, 1, pitch, current_time, dur, 95 +
        #                  (i % 20 - 10))  # slight velocity variation
        #     current_time += dur

        rhythms = [1.0, 0.5, 0.5, 1.0, 0.75, 0.25,
                   1.0, 0.5] * (len(melody_notes) // 8 + 1)
        current_time = 0
        for pitch, dur in zip(melody_notes, rhythms):
            vel = 80 + (pitch - 72) * 3 + (int(current_time * 2) %
                                           20 - 10)  # fluctuation
            vel = max(50, min(115, vel))
            midi.addNote(track, 1, pitch, current_time, dur, vel)
            current_time += dur

        # Optional: speed up towards end
        if current_time > 60:
            midi.addTempo(track, current_time - 8, 105)   # last 8 beats faster

        print(f"VideoProcessor _generate_background_music midi_path={
              midi_path}")

        with open(midi_path, "wb") as f:
            midi.writeFile(f)
        print(f"MIDI written: {midi_path}")

        print(f"VideoProcessor _generate_background_music midi_path={
              os.path.exists(midi_path)}")

        # ── 2. Find fluidsynth.exe ──
        # Common locations on Windows – adjust if yours is different
        possible_fluidsynth_paths = [
            "fluidsynth.exe",  # if in PATH
            r"C:\ProgramData\fluidsynth-v2.5.2-win10-x64-cpp11\bin\fluidsynth.exe"
        ]

        fluidsynth_exe = None
        for path in possible_fluidsynth_paths:
            if os.path.isfile(path):
                fluidsynth_exe = path
                break

        if not fluidsynth_exe:
            raise FileNotFoundError(
                "fluidsynth.exe not found.\n"
                "Download from https://www.fluidsynth.org/download/ (choose Windows binary)\n"
                "Extract and place fluidsynth.exe in one of the paths above or add its folder to system PATH."
            )

        # ── 3. Run FluidSynth command (modern flags that work on Windows) ──
        cmd = [
            fluidsynth_exe,
            "-i",                      # no interactive shell
            "-F", output_wav,           # output file
            "-r", "44100",              # sample rate
            "-g", "0.8",                # gain (0.5–1.5, lower = quieter)
            soundfont_path,             # the .sf2
            midi_path                   # input MIDI
        ]

        print("VideoProcessor _generate_background_music Running:", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False   # we'll check manually
        )

        print(f"VideoProcessor _generate_background_music Running Success → WAV created exists{
              os.path.exists(output_wav)}, output_wav={
              output_wav}, midi_path={midi_path}, cmd result.returncode={result.returncode}")
        if result.returncode != 0:
            print(f"\n FluidSynth stdout: {
                  result.stdout}, \n FluidSynth stderr:\n {result.stderr}")
            raise RuntimeError(
                f"FluidSynth failed (code {result.returncode}) – see output above")

        # ====================== 2. RENDER MIDI → WAV (high quality) ======================
        # Render MIDI → WAV with nice quality using FluidSynth
        """ This is a fallback method
        print(f"VideoProcessor _generate_background_music output_wav={
              output_wav}, soundfont_path={soundfont_path}")
        try:
            fs = FluidSynth(sound_font=soundfont_path)
            fs.midi_to_audio(midi_path, output_wav)
        except Exception as e:
            print(
                f"VideoProcessor _generate_background_music FluidSynth error {str(e)}")
            self._generate_background_music_fallback(
                output_wav, midi_path, soundfont_path)
        """

        # Optional: clean up midi
        try:
            os.remove(midi_path)
        except:
            pass

    def _generate_background_music_fallback(
        self,
        output_wav: str,
        midi_path: str,
        soundfont_path: Optional[str] = None
    ) -> None:
        if soundfont_path is None:
            soundfont_path = self.soundfont_path

        print(f"VideoProcessor _generate_background_music_fallback soundfont_path={
              os.path.exists(soundfont_path)}")
        # ── 2. Find fluidsynth.exe ──
        # Common locations on Windows – adjust if yours is different
        possible_fluidsynth_paths = [
            "fluidsynth.exe",  # if in PATH
            r"C:\ProgramData\fluidsynth-v2.5.2-win10-x64-cpp11\bin\fluidsynth.exe"
        ]

        fluidsynth_exe = None
        for path in possible_fluidsynth_paths:
            if os.path.isfile(path):
                fluidsynth_exe = path
                break

        if not fluidsynth_exe:
            raise FileNotFoundError(
                "fluidsynth.exe not found.\n"
                "Download from https://www.fluidsynth.org/download/ (choose Windows binary)\n"
                "Extract and place fluidsynth.exe in one of the paths above or add its folder to system PATH."
            )

        # ── 3. Run FluidSynth command (modern flags that work on Windows) ──
        cmd = [
            fluidsynth_exe,
            "-ni",                      # no interactive shell
            "-F", output_wav,           # output file
            "-r", "44100",              # sample rate
            "-g", "0.8",                # gain (0.5–1.5, lower = quieter)
            soundfont_path,             # the .sf2
            midi_path                   # input MIDI
        ]

        print("VideoProcessor _generate_background_music_fallback Running:", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False   # we'll check manually
        )

        if result.returncode != 0:
            print("FluidSynth stdout:\n", result.stdout)
            print("FluidSynth stderr:\n", result.stderr)
            raise RuntimeError(
                f"FluidSynth failed (code {result.returncode}) – see output above")

        print(f"VideoProcessor _generate_background_music_fallback Running Success → WAV created: {
              output_wav}, result={result}")

    def _add_music_to_video_ffmpeg(
        self,
        silent_video_path: str,
        music_wav_path: str,
        final_output_path: str,
        music_volume_factor: float = 0.40,   # 40% volume – adjust 0.2–0.7
    ) -> str:
        """Add background music using FFmpeg without re-encoding video"""
        # We'll lower music volume and mix (if you had original audio → but you don't)
        # -shortest is not needed since we generate music long enough
        print(f"VideoProcessor _add_music_to_video_ffmpeg silent_video_path={
              silent_video_path}, music_wav_path={music_wav_path}, final_output_path={final_output_path}")
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', silent_video_path,
            '-i', music_wav_path,
            # Lower music volume
            '-filter_complex', f'[1:a]volume={music_volume_factor}[bg]',
            # Map video copy + new audio
            '-map', '0:v',
            '-map', '[bg]',
            '-c:v', 'copy',           # ← crucial: no video re-encode
            '-c:a', 'aac',
            '-b:a', '192k',           # good quality / size balance
            '-shortest',              # in case music is shorter (safety)
            final_output_path
        ]

        print("VideoProcessor _add_music_to_video_ffmpeg Adding music →",
              " ".join(ffmpeg_cmd))
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )

        print(
            "VideoProcessor _add_music_to_video_ffmpeg ffmpeg_cmd return result={result}")
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg music add failed:\n{result.stderr}")

        return final_output_path

    """
    Quick tuning tips
        1. Music style → change chords, add more tracks in _generate_background_music (strings = program 49, pads = 90, etc.)
        2. Volume → adjust music_volume_factor (0.25–0.5 usually good for background)
        3. SoundFont → try others (e.g. "GeneralUser GS", "Salamander Grand") for different instruments
        4. Want fade in/out? Add to filter_complex: [1:a]volume=0.35, afade=t=in:st=0:d=3, afade=t=out:st={total_duration-4}:d=4[bg]

    This gives good-sounding music without quality loss on the video part.
    Let me know if you want to:
        1. Use a pre-existing MP3 instead of generated MIDI
        3. Add fade effects
        3. Include original audio mixing (if you add narration later)

    """

    def _create_video_ffmpeg(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        transition_type: str,
        duration_per_image: float,
        quality_settings: Dict,
        background_db: Session = None
    ) -> str:
        """Create video using FFmpeg directly (most reliable for H.264)"""
        temp_dir = None  # ← important
        db_none: bool = True
        db = background_db

        if db is None:
            db_none = True
            db = SessionLocal()  # ← important: use SessionLocal directly
        print(f"VideoProcessor _create_video_ffmpeg job_id={job_id}, db_none={
            db_none}, image_paths={len(image_paths)}")

        try:
            # ── Your original silent video path ──
            silent_video = os.path.join(
                self.output_dir, f"silent_{output_filename}")
            final_video_path = os.path.join(self.output_dir, output_filename)
            print(f"VideoProcessor _create_video_ffmpeg silent_video={
                  silent_video}, final_video_path={final_video_path}")

            # use the passed db (from route / Depends)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.processing,
                    progress=8,
                    video_path=final_video_path,
                    filename=output_filename,
                    message="Creating silent video with FFmpeg...",
                    updated_at=datetime.utcnow()
                )
            )

            # Create a temporary directory for processed images
            temp_dir = tempfile.mkdtemp(prefix="htl_video_")

            from PIL import Image
            # Read first image to get dimensions
            first_image = Image.open(image_paths[0])
            # Set resolution
            if resolution:
                width, height = resolution
            else:
                width, height = first_image.size
                # Ensure even dimensions
                width = width - (width % 2)
                height = height - (height % 2)

            # Calculation to a proper playback spped
            # """
            frames_per_image = max(1, int(fps * duration_per_image))
            global_frame_idx = 0
            import cv2
            for i, img_path in enumerate(image_paths):
                img = cv2.imread(img_path)
                if img is not None:
                    # Resize to even dimensions for H.264 compatibility
                    height, width = img.shape[:2]
                    width &= ~1  # Bitwise trick to ensure even number
                    height &= ~1

                    if img.shape[:2] != (height, width):
                        img = cv2.resize(img, (width, height),
                                         interpolation=cv2.INTER_LANCZOS4)

                    # Write the same image multiple times to create "duration"
                    for _ in range(frames_per_image):
                        temp_path = os.path.join(
                            temp_dir, f"frame_{global_frame_idx:06d}.png")
                        cv2.imwrite(temp_path, img)
                        global_frame_idx += 1

                progress = 10 + (i / len(image_paths)) * 50
                print(
                    f"VideoProcessor _create_video_ffmpeg *** looping progress={int(progress)}")
                # use the passed db (from route / Depends)
                db_status = ProcessStatusCRUD.update(
                    db,
                    job_id,
                    ProcessStatusUpdate(
                        progress=int(progress),
                        message=f"Preparing frames: progress value: {
                            int(progress)}",
                        updated_at=datetime.utcnow()
                    )
                )
                print(f"VideoProcessor _create_video_ffmpeg update_progress value: {
                      int(progress)}, db_status={db_status}")

            frame_count = global_frame_idx
            total_duration = frame_count / fps
            print(f"VideoProcessor _create_video_ffmpeg settings fps={
                  fps}, frame_count={frame_count}, total_duration={total_duration}")
            # """

            # Create FFmpeg command for H.264 encoding
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',  # H.264 codec
                '-preset', quality_settings['preset'],
                '-crf', str(quality_settings['crf']),
                '-pix_fmt', 'yuv420p',  # Required for broad compatibility
                '-movflags', '+faststart',  # Enable streaming
                '-vf', f'scale={width}:{height}:flags=lanczos',
                '-vf', f'scale={width}:{height}:flags=lanczos',
                silent_video
            ]

            print(f"VideoProcessor _create_video_ffmpeg Running FFmpeg command:\n {
                  ' '.join(ffmpeg_cmd)}, \n db_status={db_status}")
            # Execute FFmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")

            # use the passed db (from route / Depends)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.processing,
                    progress=92,
                    video_path=final_video_path,
                    message="Generating background music ...",
                    completed_at=datetime.utcnow()
                )
            )

            # ── Generate music matching video length ──
            if not self.soundfont_path:
                raise RuntimeError(f"Cannot add music since soundfont_path does not exist: {
                                   self.soundfont_path}")
            music_wav = os.path.join(
                tempfile.gettempdir(), f"bgm_{job_id}.wav")
            self._generate_background_music(
                music_wav,
                total_duration_sec=total_duration + 5,  # slightly longer → safe
                soundfont_path=self.soundfont_path         # ← adjust if needed
            )
            """
            Download a good SoundFont (e.g. FluidR3_GM.sf2 ~140 MB) from:
                https://musical-artifacts.com/artifacts/1346 (or similar)
                Place it in your project folder (or set full path in code)

            Quick Comparison & Recommendation
                1. GM2_Map_Soundfont.sf2 (~63 MB) → Best choice for your purpose,
                    But 9 times out of 10 for your current style of music,
                    GM2_Map_Soundfont.sf2 will give the nicest result with the least hassle.
                2. OnuteFont.sf2 (203 MB) → Good but probably overkill / not the best fit here
                3. GM_V2.01_Piano_(Lite_HD).sf2 (207 MB) → Strong piano focus, but limited overall
                4. GM_V2.01_Piano_(HD).sf2 (828 MB) → Strong piano focus, but limited overall
            """

            # use the passed db (from route / Depends)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.processing,
                    progress=94,
                    video_path=final_video_path,
                    message="Final mux - adding music to video ...",
                    completed_at=datetime.utcnow()
                )
            )

            # ── Final mux: video copy + audio aac ──
            self._add_music_to_video_ffmpeg(
                silent_video,
                music_wav,
                final_video_path,
                # ← tune this (0.2 = quiet, 0.6 = loud)
                music_volume_factor=0.35
            )

            # Cleanup
            try:
                os.remove(silent_video)
                os.remove(music_wav)
            except:
                pass

            # use the passed db (from route / Depends)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.processing,
                    progress=96,
                    video_path=final_video_path,
                    message="Return for success Video created with FFmpeg and added music",
                    completed_at=datetime.utcnow()
                )
            )
            print(f"VideoProcessor _create_video_ffmpeg return for success Video created with FFmpeg: \n final_video_path={
                  final_video_path}, \n db_status={db_status}")

            # C:\Users\javau\dev\projects\python\HomeTheaterLive\backend\video_output\video_20260204_170404.mp4
            return final_video_path

        except Exception as e:
            # use the passed db (from route / Depends)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.failed,
                    progress=100,
                    message=str(e),
                    error=str(e),
                    completed_at=datetime.utcnow()
                )
            )
            print(f"VideoProcessor _create_video_ffmpeg exception={
                  str(e)}, \n db_status={db_status}")
            raise RuntimeError(f"Error _create_video_ffmpeg: {str(e)}")

        finally:
            print(
                f"DEBUG:backend/app/core/video-processor.py _create_video_ffmpeg finally temp_dir: {temp_dir}")
            if temp_dir is not None and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up {
                                   temp_dir} with error {str(e)}")
            if db_none:
                db.commit()
                db.close()

    def _convert_to_h264_ffmpeg(self, input_path: str, output_path: str, quality_settings: Dict):
        """Convert any video to H.264 using FFmpeg"""
        print(f"VideoProcessor _convert_to_h264_ffmpeg input_path: {
              input_path}, output_path={output_path}")
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', quality_settings['preset'],
            '-crf', str(quality_settings['crf']),
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'aac',  # Add audio codec (even if no audio)
            '-b:a', '128k',
            output_path
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    def _add_fade_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add fade transition between two images"""
        transition_frames = int(duration * fps)
        import cv2
        print(f"VideoProcessor _add_fade_transition transition_frames: {
              transition_frames}")
        for i in range(transition_frames):
            alpha = i / transition_frames
            beta = 1 - alpha
            blended = cv2.addWeighted(img1, beta, img2, alpha, 0)
            writer.write(blended)

    def _add_slide_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add slide transition between two images"""
        transition_frames = int(duration * fps)
        height, width = img1.shape[:2]
        print(f"VideoProcessor _add_slide_transition transition_frames: {
              transition_frames}")

        for i in range(transition_frames):
            offset = int((i / transition_frames) * width)

            # Create sliding effect
            frame = np.zeros_like(img1)

            # Left part from img1
            if offset > 0:
                frame[:, :width-offset] = img1[:, offset:]

            # Right part from img2
            if offset < width:
                frame[:, width-offset:] = img2[:, :offset]

            writer.write(frame)

    def _get_video_info(self, video_path: str) -> Dict:
        """Get information about the created video"""
        print(f"VideoProcessor _get_video_info video_path: {video_path}")
        try:
            # Use FFprobe to get video info
            ffprobe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(
                ffprobe_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Extract video stream info
                video_stream = None
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break

                if video_stream:
                    return {
                        "duration": float(info.get('format', {}).get('duration', 0)),
                        "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                        "codec": video_stream.get('codec_name', 'Unknown'),
                        "bitrate": info.get('format', {}).get('bit_rate', 'Unknown')
                    }

            # Fallback to OpenCV if FFprobe fails
            import cv2
            cap = cv2.VideoCapture(video_path)
            print(f"VideoProcessor _get_video_info video_path: {
                  video_path} \n cap={cap}")
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0

                cap.release()

                return {
                    "duration": duration,
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "frame_count": frame_count
                }

            return {"duration": 0, "resolution": "Unknown"}

        except Exception as e:
            logger.warning(f"Could not get video info: {e}")
            return {"duration": 0, "resolution": "Unknown"}

    def _format_bytes(self, size: int) -> str:
        """Format bytes to human readable"""
        print(f"VideoProcessor _format_bytes size: {size}")
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# Global processor instance
# video_processor = VideoProcessor()# -*- coding: utf-8 -*-
_video_processor: VideoProcessor | None = None


def get_video_processor() -> VideoProcessor:
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor
