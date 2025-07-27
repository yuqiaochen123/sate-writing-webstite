// Audio Player for SATB Harmonization
// Uses Tone.js for high-quality audio playback

class SATBAudioPlayer {
    constructor() {
        this.synth = null;
        this.isInitialized = false;
        this.currentProgression = null;
        this.tempo = 120; // BPM
    }

    async initialize() {
        try {
            // Initialize Tone.js
            await Tone.start();
            
            // Create high-quality effects chain
            const reverb = new Tone.Reverb({
                decay: 1.5,
                preDelay: 0.01,
                wet: 0.2
            }).toDestination();
            
            const compressor = new Tone.Compressor({
                threshold: -24,
                ratio: 3,
                attack: 0.003,
                release: 0.1
            });
            
            const eq = new Tone.EQ3({
                low: 0,
                mid: 2,
                high: 1
            });
            
            // Chain effects: compressor -> EQ -> reverb
            compressor.connect(eq);
            eq.connect(reverb);
            
            // Create high-quality synthesizers with different characters for each voice
            this.synth = {
                soprano: new Tone.PolySynth(Tone.Synth, {
                    oscillator: {
                        type: 'fatsine4',
                        modulationType: 'sine',
                        modulationIndex: 2
                    },
                    envelope: {
                        attack: 0.02,
                        decay: 0.1,
                        sustain: 0.9,
                        release: 1.2
                    },
                    filter: {
                        Q: 8,
                        type: 'lowpass',
                        rolloff: -24,
                        frequency: 3000
                    },
                    filterEnvelope: {
                        attack: 0.02,
                        decay: 0.2,
                        sustain: 0.8,
                        release: 1.2,
                        baseFrequency: 300,
                        octaves: 4
                    }
                }).connect(compressor),
                
                alto: new Tone.PolySynth(Tone.Synth, {
                    oscillator: {
                        type: 'fatsawtooth',
                        modulationType: 'triangle',
                        modulationIndex: 1.5
                    },
                    envelope: {
                        attack: 0.03,
                        decay: 0.15,
                        sustain: 0.8,
                        release: 1.5
                    },
                    filter: {
                        Q: 6,
                        type: 'lowpass',
                        rolloff: -24,
                        frequency: 2000
                    },
                    filterEnvelope: {
                        attack: 0.03,
                        decay: 0.3,
                        sustain: 0.7,
                        release: 1.5,
                        baseFrequency: 200,
                        octaves: 3
                    }
                }).connect(compressor),
                
                tenor: new Tone.PolySynth(Tone.Synth, {
                    oscillator: {
                        type: 'fatsquare',
                        modulationType: 'sine',
                        modulationIndex: 1
                    },
                    envelope: {
                        attack: 0.04,
                        decay: 0.2,
                        sustain: 0.7,
                        release: 1.8
                    },
                    filter: {
                        Q: 4,
                        type: 'lowpass',
                        rolloff: -24,
                        frequency: 1500
                    },
                    filterEnvelope: {
                        attack: 0.04,
                        decay: 0.4,
                        sustain: 0.6,
                        release: 1.8,
                        baseFrequency: 150,
                        octaves: 2.5
                    }
                }).connect(compressor),
                
                bass: new Tone.PolySynth(Tone.Synth, {
                    oscillator: {
                        type: 'fatsawtooth',
                        modulationType: 'square',
                        modulationIndex: 0.8
                    },
                    envelope: {
                        attack: 0.05,
                        decay: 0.3,
                        sustain: 0.6,
                        release: 2.0
                    },
                    filter: {
                        Q: 2,
                        type: 'lowpass',
                        rolloff: -24,
                        frequency: 800
                    },
                    filterEnvelope: {
                        attack: 0.05,
                        decay: 0.5,
                        sustain: 0.5,
                        release: 2.0,
                        baseFrequency: 80,
                        octaves: 2
                    }
                }).connect(compressor)
            };
            
            // Set individual voice volumes for better balance
            this.synth.soprano.volume.value = -8;  // Slightly quieter
            this.synth.alto.volume.value = -6;     // Medium volume
            this.synth.tenor.volume.value = -4;    // Slightly louder
            this.synth.bass.volume.value = -2;     // Loudest for foundation
            
            this.isInitialized = true;
            console.log('High-quality audio player initialized successfully');
        } catch (error) {
            console.error('Failed to initialize audio player:', error);
        }
    }

    playProgression(satbHarmonization, rhythm) {
        if (!this.isInitialized || !satbHarmonization) {
            console.error('Audio player not initialized or no harmonization available');
            return;
        }

        // Stop any currently playing audio
        Tone.Transport.stop();
        Tone.Transport.cancel();
        
        // Set transport tempo
        Tone.Transport.bpm.value = this.tempo;

        const voices = ['soprano', 'alto', 'tenor', 'bass'];
        
        // Schedule all notes using Tone.js Transport for precise timing
        voices.forEach((voice) => {
            satbHarmonization[voice].forEach((note, noteIndex) => {
                const duration = this.getNoteDuration(rhythm[noteIndex] || 'q');
                const startTime = noteIndex * duration;
                
                // Schedule each note on the transport timeline
                Tone.Transport.schedule((time) => {
                    this.synth[voice].triggerAttackRelease(
                        note,
                        duration * 0.95,  // Slightly shorter for cleaner separation
                        time
                    );
                }, startTime);
            });
        });

        // Start the transport
        Tone.Transport.start();
        
        // Schedule transport to stop after all notes finish
        const totalDuration = satbHarmonization.soprano.length * this.getNoteDuration('q');
        Tone.Transport.schedule(() => {
            Tone.Transport.stop();
        }, totalDuration + 0.5);
    }

    getNoteDuration(rhythm) {
        const quarterNote = 60 / this.tempo; // Duration of a quarter note in seconds
        
        switch(rhythm) {
            case 'w': return quarterNote * 4; // Whole note
            case 'h': return quarterNote * 2; // Half note
            case 'q': return quarterNote;     // Quarter note
            case '8': return quarterNote / 2; // Eighth note
            default: return quarterNote;
        }
    }

    stop() {
        // Stop and clear the transport
        Tone.Transport.stop();
        Tone.Transport.cancel();
        
        // Release all currently playing notes
        Object.values(this.synth).forEach(synth => {
            synth.releaseAll();
        });
    }

    setTempo(bpm) {
        this.tempo = bpm;
        Tone.Transport.bpm.value = bpm;
    }
}

// Global audio player instance
window.satbAudioPlayer = new SATBAudioPlayer();

// Initialize audio player when page loads
document.addEventListener('DOMContentLoaded', () => {
    satbAudioPlayer.initialize();
}); 