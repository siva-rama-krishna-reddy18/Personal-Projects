  **Audio Analyzer Application**

A web-based application that provides advanced speech analysis capabilities, combining speech recognition with sentiment analysis to help users understand both the content and emotional context of spoken words.
Show Image
Overview
The Audio Analyzer Application enables users to analyze audio through file uploads or direct recording. It leverages Google Cloud Speech-to-Text and Language APIs to provide accurate transcription and sentiment analysis of spoken content.
**Features**

Real-time audio recording with browser APIs
Multiple audio format support (WAV, MP3, OGG, M4A, WEBM)
High-accuracy speech-to-text conversion
Sentiment analysis with confidence scoring
Comprehensive analysis history with search and filtering
Analysis file download capabilities
Responsive web interface optimized for various devices

**Technical Architecture**
System Components

**Frontend Layer:**

HTML5/JavaScript web interface
Real-time audio recording using RecordRTC
File upload handling and validation
Results visualization
Analysis history display


**Application Layer (Google Cloud Run)**:

Flask web server
Audio processing pipeline
File management
Local storage handling
Error handling and logging


**API Integration:**

Google Cloud Speech-to-Text API
Google Cloud Language API



**Data Flow**

User Input → Audio Capture/Upload
Audio Processing → Speech-to-Text Conversion
Text Analysis → Sentiment Detection
Result Storage → Local File System
User Interface → Results Display

**Installation**

Clone the repository:
bashCopygit clone https://github.com/siva-rama-krishna-reddy18/audio-analyzer.git
cd audio-analyzer

Install dependencies:
bashCopypip install -r requirements.txt

Set up environment variables:
bashCopyexport GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json

Run the application locally:
bashCopypython app.py


**Deployment to Google Cloud Run**

Build the Docker container:
bashCopygcloud builds submit --tag gcr.io/your-project-id/audio-analyzer

Deploy to Cloud Run:
bashCopygcloud run deploy audio-analyzer --image gcr.io/your-project-id/audio-analyzer --platform managed


Project Structure
Copyaudio-analyzer/
├── app.py              # Main Flask application
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
├── static/             # Static assets
├── templates/          # HTML templates
│   └── index.html      # Main application interface
├── uploads/            # Temporary audio file storage
└── transcripts/        # Analysis results storage
Dependencies

Flask: Web framework
google-cloud-speech: Speech-to-Text API client
google-cloud-language: Natural Language API client
librosa: Audio processing
soundfile: Audio file handling
gunicorn: WSGI HTTP Server
Tailwind CSS: Frontend styling

Limitations and Future Improvements
Current Limitations

Maximum audio file size: 16MB
Recording time limit: 5 minutes
English language support only

Planned Improvements

Batch processing capability
Additional language support
Real-time analysis streaming
User authentication system
Analysis categorization
Enhanced error recovery
Custom vocabulary support
.
**Acknowledgments**

Google Cloud Platform

RecordRTC library for audio recording capabilities

**Author**
Siva Rama Krishna Reddy Kunchala
kunchalas2023@fau.edu
GCP Project Information

Project Name/Id: cproject/cproject-436307

Cloud Run Service Name: audio-analyzer
