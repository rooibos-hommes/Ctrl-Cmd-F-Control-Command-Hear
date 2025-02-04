import os
import subprocess
import speech_recognition as sr
import csv
from pydub import AudioSegment
import math
import yt_dlp  # ✅ Replaces `pytube` for video downloading

# Function to download YouTube audio using yt-dlp
def download_youtube_audio(youtube_url, output_path):
    try:
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, "audio.mp4")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_file,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        return output_file
    except Exception as e:
        print(f"❌ ERROR: Failed to download video: {e}")
        return None

# Function to convert MP4 audio to WAV
def convert_audio_to_wav(input_file, output_file):
    try:
        subprocess.run(["ffmpeg", "-i", input_file, output_file, "-y"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_file
    except Exception as e:
        print(f"❌ ERROR: Failed to convert audio: {e}")
        return None

# Function to transcribe audio to text
def audio_to_text(audio_file):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return f"❌ ERROR: Google Speech API request failed: {e}"

# Function to save transcription
def save_transcription(text, output_file):
    if text:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text + "\n")
        print(f"✅ Transcription saved: {output_file}")
    else:
        print("❌ ERROR: No transcription generated.")

# Extract timestamps from audio
def extract_timestamps(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    duration_seconds = len(audio) / 1000
    return [i for i in range(math.floor(duration_seconds) + 1)]

# Log words and timestamps to CSV
def log_words_and_timestamps(words, timestamps, output_csv_file, youtube_url):
    if not words or not timestamps:
        print("❌ ERROR: No words or timestamps found!")
        return
    
    with open(output_csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Timestamp (seconds)", "YouTube URL"])
        for word, timestamp in zip(words, timestamps):
            youtube_url_with_timestamp = f"{youtube_url}&t={int(timestamp)}"
            writer.writerow([word, timestamp, youtube_url_with_timestamp])
    
    print(f"✅ CSV file created: {output_csv_file}")

# Create HTML file with clickable timestamps
def create_html_with_hyperlinks(csv_file, output_html_file):
    if not os.path.exists(csv_file):
        print("❌ ERROR: CSV missing! Cannot generate hyperlinks.")
        return

    with open(csv_file, "r", encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)

        html_content = "<html><body><h2>Click a word to jump to its timestamp</h2><ul>"
        for row in csv_reader:
            word, _, youtube_url = row
            html_content += f'<li><a href="{youtube_url}" target="_blank">{word}</a></li>'
        html_content += "</ul></body></html>"

        with open(output_html_file, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
    
    print(f"✅ Hyperlinks file created: {output_html_file}")

# Main execution
if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=fcPWU59Luoc&ab_channel=T%26H-Inspiration%26Motivation"
    output_dir = "generated_html/allanWatts"
    os.makedirs(output_dir, exist_ok=True)

    audio_file = download_youtube_audio(youtube_url, output_dir)
    if audio_file:
        print(f"✅ Audio downloaded: {audio_file}")

        wav_audio_file = os.path.join(output_dir, "audio.wav")
        if convert_audio_to_wav(audio_file, wav_audio_file):
            print(f"✅ Audio converted to WAV: {wav_audio_file}")

            transcription_text = audio_to_text(wav_audio_file)
            transcript_file = os.path.join(output_dir, "transcript.txt")
            save_transcription(transcription_text, transcript_file)

            if transcription_text:
                words = transcription_text.split()
                timestamps = extract_timestamps(wav_audio_file)

                csv_file = os.path.join(output_dir, "words_and_timestamps.csv")
                log_words_and_timestamps(words, timestamps, csv_file, youtube_url)

                # Ensure CSV exists before generating hyperlinks
                if os.path.exists(csv_file):
                    html_file = os.path.join(output_dir, "hyperlinks.html")
                    create_html_with_hyperlinks(csv_file, html_file)
                else:
                    print("❌ ERROR: CSV not found. Hyperlinks file not created.")
            else:
                print("❌ ERROR: Transcription failed. No CSV generated.")
        else:
            print("❌ ERROR: Audio conversion failed.")
    else:
        print("❌ ERROR: Video download failed. Check the YouTube URL.")
