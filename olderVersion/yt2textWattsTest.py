import os
import subprocess
import speech_recognition as sr
from pytube import YouTube
import csv
from pydub import AudioSegment
import math

# Function to download a YouTube video using the video ID
def download_youtube_video(video_id, output_path):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        ys = yt.streams.filter(only_audio=True).first()
        ys.download(output_path)
        return os.path.join(output_path, ys.default_filename)
    except Exception as e:
        print(f"An error occurred while downloading the video: {e}")
        return None

# Function to extract video ID from a YouTube URL
def extract_video_id(youtube_url):
    video_id = None
    if "youtube.com/watch?v=" in youtube_url:
        video_id = youtube_url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
    return video_id

# Function to convert audio to text using SpeechRecognition
def audio_to_text(audio_file):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)  # Record the entire audio file
        text = r.recognize_google(audio)  # Use Google Web Speech API for conversion

        # Check if the recognition result is empty or contains a placeholder
        if text.strip():
            return text
        else:
            return None
    except sr.UnknownValueError:
        return None  # Indicate unrecognizable audio
    except sr.RequestError as e:
        return f"Could not request results from Google Web Speech API; {e}"
    except Exception as e:
        print(f"An error occurred while processing the audio file: {e}")
        return None

# Function to save the transcription to a text file
def save_transcription_to_text(text, output_file):
    with open(output_file, "a", encoding="utf-8") as file:  # Append to the text file
        if text is not None:
            file.write(text + " ")  # Append recognized text with a space

# Function to delete audio files
def delete_audio_files(output_dir):
    for file in os.listdir(output_dir):
        if file.endswith(".wav"):
            file_path = os.path.join(output_dir, file)
            os.remove(file_path)

# Function to extract timestamps from the entire audio file
def extract_timestamps_from_audio(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    duration_seconds = len(audio) / 1000  # Convert milliseconds to seconds
    timestamps = [i for i in range(math.floor(duration_seconds) + 1)]
    return timestamps

# Function to log words and timestamps in a CSV file
def log_words_and_timestamps(words, timestamps, output_csv_file, youtube_url):
    with open(output_csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Timestamp (seconds)", "YouTube URL"])
        for word, timestamp in zip(words, timestamps):
            youtube_url_with_timestamp = f"{youtube_url}&t={int(timestamp)}"
            writer.writerow([word, timestamp, youtube_url_with_timestamp])

# Function to create an HTML file with hyperlinks for words
def create_html_with_hyperlinks(csv_file, output_html_file):
    with open(csv_file, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row

        html_content = "<html><body><ul>"
        for row in csv_reader:
            word, _, youtube_url = row
            html_content += f'<li><a href="{youtube_url}">{word}</a></li>'
        html_content += "</ul></body></html>"

        with open(output_html_file, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

if __name__ == "__main__":
    # Replace 'YOUR_YOUTUBE_URL' with the URL of the YouTube video you want to process
   # Replace 'YOUR_YOUTUBE_URL' with the URL of the YouTube video you want to process
    youtube_url = "https://www.youtube.com/watch?v=mMRrCYPxD0I&ab_channel=T%26H-Inspiration%26Motivation"
    output_dir = "defaultOutput"
    os.makedirs(output_dir, exist_ok=True)

    video_id = extract_video_id(youtube_url)

    if video_id:
        video_file = download_youtube_video(video_id, output_dir)
        if video_file:
            print(f"Video downloaded to {video_file}")

            # Convert the MP4 video file to audio using FFmpeg
            converted_audio_file = os.path.join(output_dir, "audio.wav")
            try:
                subprocess.run(["ffmpeg", "-i", video_file, converted_audio_file])
                print(f"Audio converted to {converted_audio_file}")

                # Load the audio using pydub
                audio = AudioSegment.from_wav(converted_audio_file)

                # Split the audio into 30-second chunks
                chunk_duration = 30 * 1000  # 30 seconds in milliseconds
                total_duration = len(audio)
                chunks = []

                for start_time in range(0, total_duration, chunk_duration):
                    end_time = min(start_time + chunk_duration, total_duration)
                    chunk = audio[start_time:end_time]
                    chunks.append(chunk)

                # Perform transcription on each chunk and recombine the output text
                combined_text = ""
                for i, chunk in enumerate(chunks):
                    chunk_audio_file = os.path.join(output_dir, f"chunk_{i}.wav")
                    chunk.export(chunk_audio_file, format="wav")

                    chunk_text = audio_to_text(chunk_audio_file)
                    if chunk_text is not None:
                        print(f"Transcription for chunk {i+1}:")
                        print(chunk_text)
                        combined_text += chunk_text + " "

                # Save combined transcription to a text file
                text_file = os.path.join(output_dir, "transcription.txt")
                save_transcription_to_text(combined_text, text_file)
                print(f"Combined transcription saved to {text_file}")

                # Extract timestamps from the entire audio file
                timestamps = extract_timestamps_from_audio(converted_audio_file)

                # Tokenize the transcription into words
                words = combined_text.split()

                # Log words, timestamps, and YouTube URL in a CSV file
                csv_file = os.path.join(output_dir, "words_and_timestamps.csv")
                log_words_and_timestamps(words, timestamps, csv_file, youtube_url)
                print(f"Words, timestamps, and YouTube URL logged to {csv_file}")

                # Create an HTML file with hyperlinks
                html_file = os.path.join(output_dir, "hyperlinks.html")
                create_html_with_hyperlinks(csv_file, html_file)
                print(f"HTML file with hyperlinks created at {html_file}")

                # Delete audio files
                delete_audio_files(output_dir)
                print("Audio files deleted.")
            except Exception as e:
                print(f"An error occurred during audio conversion: {e}")
