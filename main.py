from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
from Components.Subtitles import add_subtitles_to_video
import sys
import os
import uuid
import re

# Generate unique session ID for this run (for concurrent execution support)
session_id = str(uuid.uuid4())[:8]
print(f"Session ID: {session_id}")

# Check if URL/file was provided as command-line argument
if len(sys.argv) > 1:
    url_or_file = sys.argv[1]
    print(f"Using input from command line: {url_or_file}")
else:
    url_or_file = input("Enter YouTube video URL or local video file path: ")

# Check if input is a local file
video_title = None
if os.path.isfile(url_or_file):
    print(f"Using local video file: {url_or_file}")
    Vid = url_or_file
    # Extract title from filename
    video_title = os.path.splitext(os.path.basename(url_or_file))[0]
else:
    # Assume it's a YouTube URL
    print(f"Downloading from YouTube: {url_or_file}")
    Vid = download_youtube_video(url_or_file)
    if Vid:
        Vid = Vid.replace(".webm", ".mp4")
        print(f"Downloaded video and audio files successfully! at {Vid}")
        # Extract title from downloaded file path
        video_title = os.path.splitext(os.path.basename(Vid))[0]

# Clean and slugify title for filename
def clean_filename(title):
    # Convert to lowercase
    cleaned = title.lower()
    # Remove or replace invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*\[\]]', '', cleaned)
    # Replace spaces and underscores with hyphens
    cleaned = re.sub(r'[\s_]+', '-', cleaned)
    # Remove multiple consecutive hyphens
    cleaned = re.sub(r'-+', '-', cleaned)
    # Remove leading/trailing hyphens
    cleaned = cleaned.strip('-')
    # Limit length
    return cleaned[:80]

# Process video (works for both local files and downloaded videos)
if Vid:
    # Create unique temporary filenames
    audio_file = f"audio_{session_id}.wav"
    temp_clip = f"temp_clip_{session_id}.mp4"
    temp_cropped = f"temp_cropped_{session_id}.mp4"
    temp_subtitled = f"temp_subtitled_{session_id}.mp4"
    
    Audio = extractAudio(Vid, audio_file)
    if Audio:

        transcriptions = transcribeAudio(Audio)
        if len(transcriptions) > 0:
            print(f"\n{'='*60}")
            print(f"TRANSCRIPTION SUMMARY: {len(transcriptions)} segments")
            print(f"{'='*60}\n")
            TransText = ""

            for text, start, end in transcriptions:
                TransText += (f"{start} - {end}: {text}\n")

            print("Analyzing transcription to find best highlight...")
            start , stop = GetHighlight(TransText)
            print(f"✓ Highlight selected: {start}s - {stop}s")
            #handle the case when the highlight starts from 0s
            if start>0 and stop>0 and stop>start:
                print(f"\nCreating short video: {start}s - {stop}s ({stop-start}s duration)")
                print(f"Start: {start} , End: {stop}")

                print("Step 1/4: Extracting clip from original video...")
                crop_video(Vid, temp_clip, start, stop)

                print("Step 2/4: Cropping to vertical format (9:16)...")
                crop_to_vertical(temp_clip, temp_cropped)
                
                print("Step 3/4: Adding subtitles to video...")
                add_subtitles_to_video(temp_cropped, temp_subtitled, transcriptions, video_start_time=start)
                
                # Generate final output filename
                clean_title = clean_filename(video_title) if video_title else "output"
                final_output = f"{clean_title}_short.mp4"
                
                print("Step 4/4: Adding audio to final video...")
                combine_videos(temp_clip, temp_subtitled, final_output)
                print(f"\n{'='*60}")
                print(f"✓ SUCCESS: {final_output} is ready!")
                print(f"{'='*60}\n")
                
                # Clean up temporary files
                try:
                    for temp_file in [audio_file, temp_clip, temp_cropped, temp_subtitled]:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    print(f"Cleaned up temporary files for session {session_id}")
                except Exception as e:
                    print(f"Warning: Could not clean up some temporary files: {e}")
            else:
                print("Error in getting highlight")
        else:
            print("No transcriptions found")
    else:
        print("No audio file found")
else:
    print("Unable to process the video")