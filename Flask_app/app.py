
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
from google.cloud import speech_v1
from google.cloud import language_v1
from datetime import datetime
import wave
import pyaudio
import threading
import time
import soundfile as sf
import librosa
import numpy as np

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Create necessary directories
for directory in ['uploads', 'transcripts', 'templates']:
    os.makedirs(directory, exist_ok=True)

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
recording = False
frames = []
audio = pyaudio.PyAudio()
stream = None
recording_thread = None

# Initialize Google Cloud clients
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
speech_client = speech_v1.SpeechClient()
language_client = language_v1.LanguageServiceClient()

def save_analysis_to_txt(transcript, sentiment_analysis, timestamp):
    """Save transcript and sentiment analysis to a text file in specified format."""
    content = f"""Transcript:
{transcript}

Sentiment Analysis:
Overall Sentiment: {sentiment_analysis['overall_sentiment']}
Confidence Score: {sentiment_analysis['confidence_score']*100:.1f}%

Timestamp: {timestamp}"""
    
    filename = f"analysis_{timestamp.replace(' ', '_').replace(':', '-')}.txt"
    filepath = os.path.join('transcripts', filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename
    except Exception as e:
        print(f"Error saving analysis to file: {str(e)}")
        return None

def convert_to_wav(input_path):
    """Convert audio file to WAV format with proper settings."""
    try:
        print(f"Converting file: {input_path}")
        y, sr = librosa.load(input_path, sr=RATE, mono=True)
        output_path = os.path.splitext(input_path)[0] + '_converted.wav'
        sf.write(output_path, y, sr, subtype='PCM_16')
        print(f"Successfully converted to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in convert_to_wav: {str(e)}")
        return None

def record_audio():
    """Record audio in a separate thread."""
    global recording, frames, stream
    
    try:
        stream = audio.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
        
        print("Recording started...")
        while recording:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                print(f"Error recording audio: {str(e)}")
                break
    except Exception as e:
        print(f"Error initializing audio stream: {str(e)}")

def analyze_audio(audio_path):
    """Analyze audio using Google Cloud APIs."""
    try:
        print(f"Starting analysis of: {audio_path}")
        
        wav_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            wav_path = convert_to_wav(audio_path)
            if not wav_path:
                return {"status": "error", "message": "Failed to convert audio format"}

        with open(wav_path, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
            enable_automatic_punctuation=True,
            use_enhanced=True,
            model='default',
            audio_channel_count=1
        )

        print("Sending request to Speech-to-Text API...")
        response = speech_client.recognize(config=config, audio=audio)
        
        if not response.results:
            return {"status": "error", "message": "No speech detected"}

        transcript = ' '.join(result.alternatives[0].transcript 
                            for result in response.results)
        
        document = language_v1.Document(
            content=transcript,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        
        sentiment = language_client.analyze_sentiment(
            request={'document': document}
        ).document_sentiment

        sentiment_score = sentiment.score
        normalized_score = (sentiment_score + 1) / 2

        sentiment_analysis = {
            "overall_sentiment": "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral",
            "confidence_score": normalized_score
        }

        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to text file
        filename = save_analysis_to_txt(transcript, sentiment_analysis, timestamp)
        if not filename:
            return {"status": "error", "message": "Failed to save analysis"}

        return {
            "status": "success",
            "transcript": transcript,
            "sentiment_analysis": sentiment_analysis,
            "timestamp": timestamp,
            "filename": filename
        }

    except Exception as e:
        print(f"Error in analyze_audio: {str(e)}")
        return {"status": "error", "message": f"Failed to analyze audio: {str(e)}"}

@app.route('/')
def index():
    # Get list of saved transcript files
    transcript_files = []
    for filename in os.listdir('transcripts'):
        if filename.endswith('.txt'):
            filepath = os.path.join('transcripts', filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sections = content.split('\n\n')
                    
                    # Extract transcript preview
                    transcript_section = next(s for s in sections if s.startswith('Transcript:'))
                    transcript_text = transcript_section.replace('Transcript:', '').strip()
                    
                    # Extract sentiment
                    sentiment_section = next(s for s in sections if s.startswith('Sentiment Analysis:'))
                    sentiment_lines = sentiment_section.split('\n')
                    overall_sentiment = sentiment_lines[1].replace('Overall Sentiment:', '').strip()
                    confidence = sentiment_lines[2].replace('Confidence Score:', '').strip()
                    
                    # Extract timestamp
                    timestamp_section = next(s for s in sections if s.startswith('Timestamp:'))
                    timestamp = timestamp_section.replace('Timestamp:', '').strip()
                    
                    transcript_files.append({
                        'filename': filename,
                        'timestamp': timestamp,
                        'preview': transcript_text[:100],
                        'sentiment': overall_sentiment,
                        'confidence': confidence
                    })
            except Exception as e:
                print(f"Error reading file {filename}: {str(e)}")
                continue
    
    # Sort files by timestamp (newest first)
    transcript_files.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('index.html', transcript_files=transcript_files)

@app.route('/transcripts/<filename>')
def get_transcript(filename):
    try:
        filepath = os.path.join('transcripts', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse content sections
        sections = content.split('\n\n')
        
        # Extract transcript
        transcript_section = next(s for s in sections if s.startswith('Transcript:'))
        transcript = transcript_section.replace('Transcript:', '').strip()
        
        # Extract sentiment analysis
        sentiment_section = next(s for s in sections if s.startswith('Sentiment Analysis:'))
        sentiment_lines = sentiment_section.split('\n')
        overall_sentiment = sentiment_lines[1].replace('Overall Sentiment:', '').strip()
        confidence_text = sentiment_lines[2].replace('Confidence Score:', '').replace('%', '').strip()
        confidence_score = float(confidence_text) / 100
        
        return jsonify({
            "status": "success",
            "transcript": transcript,
            "sentiment_analysis": {
                "overall_sentiment": overall_sentiment,
                "confidence_score": confidence_score
            }
        })
    except Exception as e:
        print(f"Error reading transcript {filename}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to load transcript: {str(e)}"
        }), 404

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording, frames, recording_thread
    
    if not recording:
        recording = True
        frames = []
        recording_thread = threading.Thread(target=record_audio)
        recording_thread.start()
        return jsonify({"status": "success", "message": "Recording started"})
    return jsonify({"status": "error", "message": "Already recording"})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, frames, stream, recording_thread
    
    if recording:
        recording = False
        if recording_thread:
            recording_thread.join()
        
        if stream:
            stream.stop_stream()
            stream.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join('uploads', filename)
        
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            
            result = analyze_audio(filepath)
            
            # Clean up the WAV file
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return jsonify(result)
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": f"Failed to save recording: {str(e)}"
            })
    
    return jsonify({"status": "error", "message": "Not recording"})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No audio file provided"
        }), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "No selected file"
        }), 400
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upload_{timestamp}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        print(f"Processing uploaded file: {filepath}")
        result = analyze_audio(filepath)
        
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return jsonify(result)
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to process upload: {str(e)}"
        })

if __name__ == '__main__':
    try:
        print("Starting Flask server...")
        port = int(os.environ.get("PORT", 8080))  # Default to 8080
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
    finally:
        print("Cleaning up resources...")
        if 'stream' in globals() and stream is not None:
            stream.stop_stream()
            stream.close()
        if 'audio' in globals() and audio is not None:
            audio.terminate()

