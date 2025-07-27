// Export Utilities for SATB Harmonization
// Handles MusicXML, MIDI, and other export formats

class SATBExportManager {
    constructor() {
        this.supportedFormats = ['musicxml', 'midi', 'svg', 'pdf'];
    }

    // Enhanced MusicXML Export
    exportMusicXML(satbHarmonization, rhythm, progression, metadata = {}) {
        const title = metadata.title || 'SATB Harmonization';
        const composer = metadata.composer || 'SATB Harmonizer';
        const key = metadata.key || 'C';
        const timeSignature = metadata.timeSignature || '4/4';

        let xml = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <work>
    <work-title>${title}</work-title>
  </work>
  <identification>
    <creator type="composer">${composer}</creator>
    <encoding>
      <software>SATB Harmonizer</software>
      <encoding-date>${new Date().toISOString().split('T')[0]}</encoding-date>
    </encoding>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Soprano</part-name>
      <instrument-name>Voice</instrument-name>
    </score-part>
    <score-part id="P2">
      <part-name>Alto</part-name>
      <instrument-name>Voice</instrument-name>
    </score-part>
    <score-part id="P3">
      <part-name>Tenor</part-name>
      <instrument-name>Voice</instrument-name>
    </score-part>
    <score-part id="P4">
      <part-name>Bass</part-name>
      <instrument-name>Voice</instrument-name>
    </score-part>
  </part-list>`;

        // Generate each voice part
        const voices = ['soprano', 'alto', 'tenor', 'bass'];
        const clefs = ['treble', 'treble', 'treble_8vb', 'bass'];

        voices.forEach((voice, index) => {
            xml += this.generateVoicePart(voice, satbHarmonization[voice], rhythm, clefs[index], key, timeSignature, index + 1);
        });

        xml += `
</score-partwise>`;

        return xml;
    }

    generateVoicePart(voiceName, notes, rhythm, clef, key, timeSignature, partId) {
        let xml = `
  <part id="P${partId}">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>${this.getKeySignature(key)}</fifths>
        </key>
        <time>
          <beats>${timeSignature.split('/')[0]}</beats>
          <beat-type>${timeSignature.split('/')[1]}</beat-type>
        </time>
        <clef>
          <sign>${clef === 'bass' ? 'F' : 'G'}</sign>
          <line>${clef === 'bass' ? '4' : '2'}</line>
        </clef>
      </attributes>`;

        notes.forEach((note, noteIndex) => {
            xml += this.generateNoteElement(note, rhythm[noteIndex] || 'q');
        });

        xml += `
    </measure>
  </part>`;

        return xml;
    }

    generateNoteElement(note, duration) {
        const noteName = note.replace(/\d+/, '');
        const octave = note.match(/\d+/)?.[0] || '4';
        const durationValue = this.getDurationValue(duration);
        const noteType = this.getNoteType(duration);

        let xml = `
      <note>
        <pitch>
          <step>${noteName.charAt(0)}</step>`;

        if (noteName.includes('#')) {
            xml += `
          <alter>1</alter>`;
        } else if (noteName.includes('b')) {
            xml += `
          <alter>-1</alter>`;
        }

        xml += `
          <octave>${octave}</octave>
        </pitch>
        <duration>${durationValue}</duration>
        <type>${noteType}</type>
      </note>`;

        return xml;
    }

    getKeySignature(key) {
        const keySignatures = {
            'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6,
            'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6
        };
        return keySignatures[key] || 0;
    }

    getDurationValue(duration) {
        switch(duration) {
            case 'w': return '4';
            case 'h': return '2';
            case 'q': return '1';
            case '8': return '0.5';
            default: return '1';
        }
    }

    getNoteType(duration) {
        switch(duration) {
            case 'w': return 'whole';
            case 'h': return 'half';
            case 'q': return 'quarter';
            case '8': return 'eighth';
            default: return 'quarter';
        }
    }

    // MIDI Export
    exportMIDI(satbHarmonization, rhythm, tempo = 120) {
        // This is a simplified MIDI export
        // For full MIDI support, consider using libraries like midi-writer-js
        
        const midiData = {
            format: 1,
            tracks: []
        };

        const voices = ['soprano', 'alto', 'tenor', 'bass'];
        const channels = [0, 1, 2, 3]; // Different channels for each voice

        // Add tempo track
        midiData.tracks.push({
            name: 'Tempo',
            events: [
                { type: 'tempo', value: tempo },
                { type: 'timeSignature', numerator: 4, denominator: 4 }
            ]
        });

        // Add voice tracks
        voices.forEach((voice, index) => {
            const track = {
                name: voice.charAt(0).toUpperCase() + voice.slice(1),
                channel: channels[index],
                events: []
            };

            let time = 0;
            satbHarmonization[voice].forEach((note, noteIndex) => {
                const duration = this.getMIDIDuration(rhythm[noteIndex] || 'q', tempo);
                const midiNote = this.noteToMIDI(note);

                track.events.push({
                    type: 'noteOn',
                    note: midiNote,
                    velocity: 64,
                    time: time
                });

                track.events.push({
                    type: 'noteOff',
                    note: midiNote,
                    velocity: 0,
                    time: time + duration
                });

                time += duration;
            });

            midiData.tracks.push(track);
        });

        return this.generateMIDIFile(midiData);
    }

    noteToMIDI(noteName) {
        const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
        const note = noteName.replace(/\d+/, '');
        const octave = parseInt(noteName.match(/\d+/)?.[0] || '4');
        
        const noteIndex = noteNames.indexOf(note);
        return noteIndex + (octave + 1) * 12;
    }

    getMIDIDuration(rhythm, tempo) {
        const quarterNote = 60 / tempo; // Duration of a quarter note in seconds
        
        switch(rhythm) {
            case 'w': return quarterNote * 4;
            case 'h': return quarterNote * 2;
            case 'q': return quarterNote;
            case '8': return quarterNote / 2;
            default: return quarterNote;
        }
    }

    generateMIDIFile(midiData) {
        // Simplified MIDI file generation
        // In a real implementation, you'd use a proper MIDI library
        return `MIDI file data for ${midiData.tracks.length} tracks`;
    }

    // SVG Export (from VexFlow)
    exportSVG() {
        if (window.satbNotationRenderer) {
            return window.satbNotationRenderer.exportToSVG();
        }
        return null;
    }

    // PDF Export (requires additional libraries)
    exportPDF(satbHarmonization, rhythm) {
        // This would require a PDF generation library like jsPDF
        // For now, return a placeholder
        return 'PDF export requires additional libraries (jsPDF, etc.)';
    }

    // Download file utility
    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    // Export all formats
    exportAll(satbHarmonization, rhythm, progression, metadata = {}) {
        const exports = {};

        // MusicXML
        exports.musicxml = this.exportMusicXML(satbHarmonization, rhythm, progression, metadata);
        
        // MIDI
        exports.midi = this.exportMIDI(satbHarmonization, rhythm, metadata.tempo || 120);
        
        // SVG
        exports.svg = this.exportSVG();

        return exports;
    }
}

// Global export manager instance
window.satbExportManager = new SATBExportManager(); 