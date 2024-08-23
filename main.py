from flask import Flask, request, render_template
import whisper
import torch
import os

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")
model = model.to("cuda" if torch.cuda.is_available() else "cpu")

def transcribe(audio_path):
    # Load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    # Make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # Ensure the tensor is in the right type (Float32)
    if mel.dtype != torch.float32:
        mel = mel.float()

    # Detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # Decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)
    return result.text

@app.route('/', methods=['GET', 'POST'])
def index():
    transcription = ""
    if request.method == 'POST':
        if 'audio' not in request.files:
            return 'No file uploaded', 400

        audio_file = request.files['audio']
        
        # Ensure the 'uploads' directory exists
        uploads_dir = os.path.join(app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        # Save the audio file with its filename in the 'uploads' directory
        audio_path = os.path.join(uploads_dir, audio_file.filename)
        audio_file.save(audio_path)

        # Perform transcription
        transcription = transcribe(audio_path)

    return render_template('index.html', transcription=transcription)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

