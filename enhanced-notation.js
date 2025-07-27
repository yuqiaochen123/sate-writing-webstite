// Enhanced Music Notation for SATB
// Uses VexFlow for professional-quality music notation

class SATBNotationRenderer {
    constructor() {
        this.renderer = null;
        this.context = null;
        this.isInitialized = false;
    }

    initialize(containerId) {
        try {
            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container ${containerId} not found`);
            }

            // Clear container
            container.innerHTML = '';

            // Initialize VexFlow renderer
            this.renderer = new Vex.Flow.Renderer(container, Vex.Flow.Renderer.Backends.SVG);
            this.renderer.resize(800, 400);
            this.context = this.renderer.getContext();

            this.isInitialized = true;
            console.log('Notation renderer initialized successfully');
        } catch (error) {
            console.error('Failed to initialize notation renderer:', error);
        }
    }

    renderSATBScore(satbHarmonization, rhythm, key = 'C', timeSignature = '4/4') {
        if (!this.isInitialized || !satbHarmonization) {
            console.error('Notation renderer not initialized or no harmonization available');
            return;
        }

        try {
            // Clear previous content
            this.context.clear();

            const voices = ['soprano', 'alto', 'tenor', 'bass'];
            const clefs = ['treble', 'treble', 'treble_8vb', 'bass'];
            const staves = [];
            const voiceGroups = [];

            // Create staves for each voice
            voices.forEach((voice, index) => {
                const y = index * 80 + 20;
                const stave = new Vex.Flow.Stave(10, y, 750);
                
                stave.addClef(clefs[index]);
                if (index === 0) {
                    stave.addKeySignature(key);
                    stave.addTimeSignature(timeSignature);
                }
                
                stave.setContext(this.context).draw();
                staves.push(stave);
            });

            // Create notes for each voice
            voices.forEach((voice, voiceIndex) => {
                const notes = [];
                const stave = staves[voiceIndex];

                satbHarmonization[voice].forEach((note, noteIndex) => {
                    const duration = this.convertRhythmToVexFlow(rhythm[noteIndex] || 'q');
                    const vexNote = this.createVexFlowNote(note, duration);
                    notes.push(vexNote);
                });

                // Create voice group
                const voiceGroup = new Vex.Flow.Voice({ time: { num_beats: 4, beat_value: 4 } });
                voiceGroup.addTickables(notes);
                voiceGroups.push(voiceGroup);

                // Format and draw
                const formatter = new Vex.Flow.Formatter();
                formatter.joinVoices(voiceGroups);
                formatter.format(voiceGroups, 750);

                voiceGroup.draw(this.context, stave);
            });

        } catch (error) {
            console.error('Error rendering SATB score:', error);
            this.renderFallbackDisplay(satbHarmonization);
        }
    }

    createVexFlowNote(noteName, duration) {
        // Convert note name (e.g., "C4") to VexFlow format
        const note = noteName.replace(/\d+/, '');
        const octave = noteName.match(/\d+/)?.[0] || '4';
        
        return new Vex.Flow.StaveNote({
            clef: this.getClefForNote(noteName),
            keys: [`${note}/${octave}`],
            duration: duration
        });
    }

    getClefForNote(noteName) {
        // Determine appropriate clef based on note range
        const octave = parseInt(noteName.match(/\d+/)?.[0] || '4');
        
        if (octave >= 5) return 'treble';
        if (octave <= 3) return 'bass';
        return 'treble'; // Default
    }

    convertRhythmToVexFlow(rhythm) {
        switch(rhythm) {
            case 'w': return 'w';  // Whole note
            case 'h': return 'h';  // Half note
            case 'q': return 'q';  // Quarter note
            case '8': return '8';  // Eighth note
            default: return 'q';
        }
    }

    renderBassLine(bassLine, rhythm) {
        if (!this.isInitialized) return;

        try {
            this.context.clear();

            const stave = new Vex.Flow.Stave(10, 40, 750);
            stave.addClef('bass').addTimeSignature('4/4');
            stave.setContext(this.context).draw();

            const notes = bassLine.map((note, index) => {
                const duration = this.convertRhythmToVexFlow(rhythm[index] || 'q');
                return this.createVexFlowNote(note, duration);
            });

            const voice = new Vex.Flow.Voice({ time: { num_beats: 4, beat_value: 4 } });
            voice.addTickables(notes);

            const formatter = new Vex.Flow.Formatter();
            formatter.joinVoices([voice]);
            formatter.format([voice], 750);

            voice.draw(this.context, stave);

        } catch (error) {
            console.error('Error rendering bass line:', error);
        }
    }

    renderFallbackDisplay(satbHarmonization) {
        const container = this.renderer?.container;
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 20px; background-color: white; border-radius: 8px;">
                <h3 style="text-align: center; margin-bottom: 20px;">SATB Score (Text Display)</h3>
                <div style="font-family: monospace; line-height: 2;">
                    <div><strong>Soprano:</strong> ${satbHarmonization.soprano.join(' - ')}</div>
                    <div><strong>Alto:</strong> ${satbHarmonization.alto.join(' - ')}</div>
                    <div><strong>Tenor:</strong> ${satbHarmonization.tenor.join(' - ')}</div>
                    <div><strong>Bass:</strong> ${satbHarmonization.bass.join(' - ')}</div>
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 15px;">
                    Advanced staff notation will be available when VexFlow loads properly
                </p>
            </div>
        `;
    }

    exportToSVG() {
        if (!this.renderer) return null;
        
        const svgElement = this.renderer.container.querySelector('svg');
        if (svgElement) {
            return svgElement.outerHTML;
        }
        return null;
    }
}

// Global notation renderer instance
window.satbNotationRenderer = new SATBNotationRenderer(); 