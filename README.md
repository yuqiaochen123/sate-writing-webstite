# SATB Four-Part Writing Website

A comprehensive web application for generating SATB (Soprano, Alto, Tenor, Bass) four-part harmonizations from bass lines, following strict voice leading conventions.

## 🎼 Features

### Core Functionality
- **Bass Line Input**: Interactive music notation input with rhythm selection
- **Chord Progression Analysis**: AI-powered suggestion of musically sound chord progressions
- **SATB Harmonization**: Automatic generation of four-part harmony following voice leading rules
- **Voice Leading Validation**: Checks for parallel fifths/octaves, voice crossing, and other violations
- **Professional Notation**: VexFlow-powered music notation display

### Advanced Features
- **Audio Playback**: Real-time playback using Tone.js synthesizers
- **Multiple Export Formats**: MusicXML, MIDI, SVG export capabilities
- **Interactive UI**: Modern, responsive design with intuitive controls
- **Educational Analysis**: Detailed explanations of chord functions and cadences

## 🚀 Quick Start

### 1. Basic Setup
```html
<!-- Include required libraries -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/vexflow/4.2.2/vexflow.min.js"></script>
<script src="https://unpkg.com/tone@14.7.77/build/Tone.js"></script>

<!-- Include custom scripts -->
<script src="audio-player.js"></script>
<script src="enhanced-notation.js"></script>
<script src="export-utilities.js"></script>
```

### 2. Usage
1. **Input Bass Line**: Enter notes using the text input or click on the staff
2. **Select Rhythm**: Choose note values (quarter, half, whole, eighth notes)
3. **Analyze**: Click "Analyze Bass Line" to get chord progression suggestions
4. **Choose Progression**: Select your preferred progression from the suggestions
5. **Generate SATB**: The system automatically creates four-part harmony
6. **Play & Export**: Listen to the result and export in various formats

## 📁 Project Structure

```
SATB-writing-website/
├── index.html              # Main application file
├── audio-player.js         # Audio playback functionality
├── enhanced-notation.js    # Music notation rendering
├── export-utilities.js     # File export capabilities
└── README.md              # This file
```

## 🔧 Integration with Personal Website

### Method 1: Direct Integration
```html
<!-- Add to your personal website -->
<div id="satb-container">
    <!-- Copy the entire content from index.html -->
</div>
```

### Method 2: Iframe Embedding
```html
<!-- Embed as a separate page -->
<iframe src="path/to/satb/index.html" width="100%" height="800px"></iframe>
```

### Method 3: Component Integration
```javascript
// Load SATB functionality dynamically
function loadSATBComponent() {
    // Load required scripts
    const scripts = [
        'https://cdnjs.cloudflare.com/ajax/libs/vexflow/4.2.2/vexflow.min.js',
        'https://unpkg.com/tone@14.7.77/build/Tone.js',
        'audio-player.js',
        'enhanced-notation.js',
        'export-utilities.js'
    ];
    
    scripts.forEach(src => {
        const script = document.createElement('script');
        script.src = src;
        document.head.appendChild(script);
    });
}
```

## 🎵 Technical Details

### Voice Leading Rules Implemented
- **Parallel Fifths/Octaves**: Detection and prevention
- **Voice Crossing**: Ensures proper voice ranges
- **Large Leaps**: Limits melodic intervals
- **Leading Tone Resolution**: Proper resolution of dominant harmonies
- **Seventh Resolution**: Correct resolution of seventh chords

### Chord Database
The system includes a comprehensive database of:
- **Triads**: I, ii, iii, IV, V, vi, vii°
- **Seventh Chords**: V7
- **Inversions**: I6, ii6, IV6, V6, vi6
- **Function Analysis**: Tonic, Predominant, Dominant functions

### Export Formats
- **MusicXML**: Standard format for music notation software
- **MIDI**: Compatible with DAWs and music software
- **SVG**: Scalable vector graphics for web display
- **PDF**: Professional print-ready format (planned)

## 🛠️ Customization

### Styling
```css
/* Customize the appearance */
.satb-container {
    --primary-color: #3498db;
    --secondary-color: #e74c3c;
    --success-color: #27ae60;
    --background-color: #faf9f6;
}
```

### Key Signatures
```javascript
// Add support for different keys
const keySignatures = {
    'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6,
    'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6
};
```

### Voice Ranges
```javascript
// Customize voice ranges
const VOICE_RANGES = {
    soprano: { min: 60, max: 81 },  // C4 to A5
    alto: { min: 55, max: 72 },     // G3 to C5  
    tenor: { min: 48, max: 67 },    // C3 to G4
    bass: { min: 40, max: 64 }      // E2 to E4
};
```

## 🔌 APIs and Libraries Used

### Core Libraries
- **VexFlow**: Music notation rendering
- **Tone.js**: Audio synthesis and playback
- **Web Audio API**: Browser audio capabilities

### Optional Enhancements
- **ABC.js**: ABC notation support
- **MuseScore**: Advanced notation features
- **LilyPond**: Professional notation quality
- **jsPDF**: PDF export functionality
- **midi-writer-js**: Enhanced MIDI export

## 🎓 Educational Applications

This tool is perfect for:
- **Music Theory Classes**: Teaching voice leading principles
- **Composition Students**: Learning SATB writing techniques
- **Choral Directors**: Creating arrangements
- **Self-Study**: Understanding harmonic progressions

## 🚀 Future Enhancements

### Planned Features
- [ ] Support for minor keys and modal harmony
- [ ] Advanced voice leading algorithms
- [ ] Real-time collaboration features
- [ ] Mobile app version
- [ ] Integration with music education platforms

### Technical Improvements
- [ ] WebAssembly for faster processing
- [ ] Machine learning for better progression suggestions
- [ ] Cloud storage for saving compositions
- [ ] Social sharing features

## 📞 Support

For questions or contributions:
1. Check the code comments for implementation details
2. Review the voice leading rules in the JavaScript files
3. Test with different bass lines to understand the system

## 📄 License

This project is open source and available for educational and personal use.

---

**Happy Harmonizing! 🎼** 