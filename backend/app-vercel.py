from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import replicate

app = Flask(__name__)
CORS(app, origins=['https://satbwritingwebsite.netlify.app', 'http://127.0.0.1:5500', 'http://localhost:5500'])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/generate_ai_music', methods=['POST'])
def generate_ai_music():
    """Generate AI music based on chord progression using Replicate API."""
    try:
        data = request.get_json()
        chord_progression = data.get('chord_progression', [])
        key_signature = data.get('key', 'C major')
        
        if not chord_progression:
            return jsonify({'error': 'No chord progression provided'}), 400
        
        # Set up Replicate API key - try multiple possible environment variable names
        api_key = (os.environ.get('REPLICATE_API_KEY') or 
                  os.environ.get('REPLICATE_API_TOKEN') or
                  os.environ.get('REPLICATE_TOKEN'))
        
        if not api_key:
            print(f"Available environment variables: {list(os.environ.keys())}")
            return jsonify({'error': 'Replicate API key not configured'}), 500
        
        # Set the API key for replicate
        os.environ['REPLICATE_API_TOKEN'] = api_key
        
        # Create a descriptive prompt for the AI
        progression_text = ' - '.join(chord_progression)
        prompt = f"A beautiful instrumental piece in {key_signature} with the chord progression: {progression_text}. The piece should be melodic, harmonious, and suitable for background music. Duration: 30 seconds."
        
        # Use MusicGen model for music generation
        output = replicate.run(
            "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            api_token=api_key,
            input={
                "prompt": prompt,
                "duration": 10,  # Reduced from 30 to 10 seconds for faster generation
                "temperature": 1.0,
                "continuation": False,
                "model_version": "stereo-large",
                "output_format": "mp3",
                "normalization_strategy": "peak",
                "top_k": 250,
                "top_p": 0.0,
                "classifier_free_guidance": 3.0
            }
        )
        
        if output:
            # Convert FileOutput to string URL
            audio_url = str(output)
            
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'prompt': prompt,
                'chord_progression': chord_progression,
                'key': key_signature
            })
        else:
            return jsonify({'error': 'No audio generated'}), 500
            
    except Exception as e:
        print(f"Error generating AI music: {str(e)}")
        return jsonify({'error': f'Error generating music: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
