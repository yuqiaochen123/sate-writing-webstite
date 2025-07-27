from flask import Flask, request, jsonify
from flask_cors import CORS
from music21 import stream, note, key, roman, pitch, interval, scale, chord
import os
from itertools import combinations, product
import copy
import itertools

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your frontend

@app.route('/analyze_bassline', methods=['POST'])
def analyze_bassline():
    try:
        data = request.get_json()
        bass_notes = data.get('bass_notes', [])
        user_key = data.get('key', 'C major')  # Get user-selected key
        
        if not bass_notes:
            return jsonify({'error': 'No bass notes provided'}), 400
        
        # Convert bass notes to music21 format
        bass_stream = stream.Stream()
        for note_name in bass_notes:
            # Handle octave if not provided
            if not any(char.isdigit() for char in note_name):
                note_name += '3'  # Default to octave 3 for bass
            n = note.Note(note_name)
            bass_stream.append(n)
        
        # Use user-selected key or detect from bass line if not provided
        if user_key and user_key != 'auto':
            try:
                # Clean up the key string and create the key object
                key_parts = user_key.split()
                if len(key_parts) == 2:
                    tonic = key_parts[0]
                    mode = key_parts[1].lower()
                    
                    # Handle flat keys - Music21 expects different formats
                    if 'b' in tonic:
                        tonic = tonic.replace('b', '-')
                    
                    detected_key = key.Key(tonic, mode)
                else:
                    detected_key = key.Key('C', 'major')  # Fallback
            except Exception as e:
                print(f"Error creating key from '{user_key}': {e}")
                detected_key = key.Key('C', 'major')  # Safe fallback
        else:
            detected_key = detect_key_from_bass(bass_stream)
        
        # Generate multiple progression options
        progressions = generate_progression_options(bass_stream, detected_key)
        
        return jsonify({
            'key': detected_key.name,
            'progressions': progressions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def detect_key_from_bass(bass_stream):
    """Detect the most likely key from the bass line using Music21's analysis."""
    try:
        # Use Music21's key detection algorithm
        detected_key = bass_stream.analyze('key')
        
        # If detection fails or gives unusual result, default to C major/A minor
        if detected_key is None or detected_key.name not in ['C major', 'G major', 'F major', 'D major', 'A major', 'E major', 'B- major', 'A minor', 'E minor', 'B minor', 'D minor', 'F# minor']:
            # Analyze the first and last notes for a simple heuristic
            first_note = bass_stream.notes[0]
            last_note = bass_stream.notes[-1]
            
            # If it starts and ends on the same note, likely tonic
            if first_note.pitch.pitchClass == last_note.pitch.pitchClass:
                tonic_name = first_note.pitch.name
                detected_key = key.Key(tonic_name, 'major')
            else:
                detected_key = key.Key('C', 'major')  # Default fallback
                
    except:
        detected_key = key.Key('C', 'major')  # Safe fallback
    
    return detected_key

def generate_progression_options(bass_stream, detected_key):
    """Generate musically intelligent progression options based on the actual bass notes."""
    bass_notes = list(bass_stream.notes)
    
    # Generate progressions that actually match the bass line
    progressions = generate_bass_specific_progressions(bass_notes, detected_key)
    
    # Score and sort progressions
    scored_progressions = []
    for prog in progressions:
        score = score_progression(prog, bass_notes, detected_key)
        scored_progressions.append({
            'roman_numerals': prog,
            'score': score,
            'style': get_progression_style(prog),
            'description': get_progression_description(prog, detected_key)
        })
    
    # Sort by score and return top 5
    scored_progressions.sort(key=lambda x: x['score'], reverse=True)
    return scored_progressions[:5]

def generate_bass_specific_progressions(bass_notes, detected_key):
    """Generate progressions that actually fit the given bass notes."""
    progressions = []
    
    # For each bass note, find all possible chords where it can function as bass
    bass_chord_options = []
    for i, bass_note in enumerate(bass_notes):
        possible_chords = get_chords_for_bass_note(bass_note, detected_key, i, len(bass_notes))
        bass_chord_options.append(possible_chords)
    
    # Generate multiple progression combinations
    from itertools import product
    
    # Smart limitation based on bass line length
    max_combinations = min(100, 4 ** min(len(bass_chord_options), 6))  # More combinations for shorter lines
    options_per_note = max(2, 8 // len(bass_chord_options)) if len(bass_chord_options) > 0 else 3
    
    # Limit options per bass note to keep combinations manageable
    limited_options = [options[:options_per_note] for options in bass_chord_options]
    
    # Generate all combinations up to the limit
    if limited_options:
        all_combinations = list(product(*limited_options))
        for combination in all_combinations[:max_combinations]:
            progressions.append(list(combination))
    
    return progressions

def get_chords_for_bass_note(bass_note, detected_key, position, total_length):
    """Get chords where the given bass note can logically function as the bass."""
    bass_pitch = bass_note.pitch
    try:
        scale_degree = detected_key.getScaleDegreeFromPitch(bass_pitch)
    except:
        # Fallback calculation
        tonic_pitch = detected_key.tonic
        interval_from_tonic = interval.Interval(tonic_pitch, bass_note.pitch)
        scale_degree = ((interval_from_tonic.semitones % 12) // 1) + 1
    
    possible_chords = []
    
    # Based on scale degree, determine what chords can have this note in the bass
    if detected_key.mode == 'major':
        chord_options = {
            1: ['I', 'vi6'],  # 1st degree: I (root), vi6 (3rd of vi)
            2: ['ii', 'vii°6', 'V7'],  # 2nd degree: ii (root), vii°6 (3rd), V7 (5th)
            3: ['iii', 'I6'],  # 3rd degree: iii (root), I6 (3rd of I)
            4: ['IV', 'ii6', 'I6/4'],  # 4th degree: IV (root), ii6 (3rd), I6/4 (5th of I)
            5: ['V', 'V7', 'iii6', 'I6/4'],  # 5th degree: V (root), iii6 (3rd)
            6: ['vi', 'IV6'],  # 6th degree: vi (root), IV6 (3rd of IV)
            7: ['vii°', 'V7', 'V6/5']  # 7th degree: vii° (root), V7 (3rd)
        }
    else:  # minor mode
        chord_options = {
            1: ['i', 'VI6'],
            2: ['ii°', 'vii°6', 'V7'],
            3: ['III', 'i6'],
            4: ['iv', 'ii°6', 'i6/4'],
            5: ['V', 'v', 'III6'],
            6: ['VI', 'iv6'],
            7: ['vii°', 'V7']
        }
    
    # Get the basic options for this scale degree
    if scale_degree in chord_options:
        possible_chords = chord_options[scale_degree][:]
    else:
        possible_chords = ['I'] if detected_key.mode == 'major' else ['i']
    
    # Add position-specific logic
    if position == 0:  # First chord - prefer stable chords
        if scale_degree == 1:
            possible_chords = ['I'] if detected_key.mode == 'major' else ['i']
        elif scale_degree == 5:
            possible_chords = ['V', 'V7']
    elif position == total_length - 1:  # Last chord - prefer tonic
        if scale_degree == 1:
            possible_chords = ['I'] if detected_key.mode == 'major' else ['i']
        elif scale_degree == 5:
            possible_chords = ['V7']  # Leading to implied tonic
    
    return possible_chords[:3]  # Limit to top 3 options

def get_contextual_chords(bass_note, detected_key, position, total_length):
    """Get possible chords for a bass note considering its position in the progression."""
    try:
        scale_degree = detected_key.getScaleDegreeFromPitch(bass_note.pitch)
    except:
        # Fallback calculation
        tonic_pitch = detected_key.tonic
        interval_from_tonic = interval.Interval(tonic_pitch, bass_note.pitch)
        scale_degree = (interval_from_tonic.semitones % 12) + 1
    
    # Position-aware chord suggestions
    if position == 0:  # First chord
        if scale_degree == 1:
            return ['I', 'I6']
        elif scale_degree == 5:
            return ['V', 'V7']
        elif scale_degree == 6:
            return ['vi', 'I6']
    elif position == total_length - 1:  # Last chord
        if scale_degree == 1:
            return ['I']
        elif scale_degree == 5:
            return ['V', 'V7']
    
    # General chord mappings by scale degree
    chord_mappings = {
        1: ['I', 'I6', 'vi6'],
        2: ['ii', 'ii6', 'V7', 'vii°6'],
        3: ['iii', 'I6', 'vi'],
        4: ['IV', 'ii6', 'I6/4'],
        5: ['V', 'V7', 'iii6', 'I6/4'],
        6: ['vi', 'IV6', 'I'],
        7: ['vii°', 'V7', 'V6/5']
    }
    
    return chord_mappings.get(scale_degree, ['I'])

def score_progression(progression, bass_notes, detected_key):
    """Score a progression based on music theory principles."""
    score = 100  # Start with perfect score
    
    # Check for good voice leading patterns
    for i in range(len(progression) - 1):
        current_chord = progression[i]
        next_chord = progression[i + 1]
        
        # Reward common progressions
        if is_strong_progression(current_chord, next_chord):
            score += 20
        elif is_weak_progression(current_chord, next_chord):
            score -= 10
    
    # Check beginning and ending
    if progression[0] in ['I', 'i']:
        score += 15  # Good to start on tonic
    if progression[-1] in ['I', 'i']:
        score += 25  # Very good to end on tonic
    
    # Penalize too many repeated chords
    unique_chords = len(set(progression))
    if unique_chords < len(progression) * 0.6:
        score -= 15
    
    # Reward proper cadences
    if len(progression) >= 2:
        if progression[-2] in ['V', 'V7'] and progression[-1] in ['I', 'i']:
            score += 30  # Authentic cadence
        elif progression[-2] in ['IV'] and progression[-1] in ['I', 'i']:
            score += 20  # Plagal cadence
    
    return max(0, score)  # Don't go below 0

def is_strong_progression(chord1, chord2):
    """Check if this is a strong harmonic progression."""
    strong_progressions = [
        ('I', 'V'), ('I', 'V7'), ('I', 'vi'), ('I', 'IV'),
        ('ii', 'V'), ('ii', 'V7'), ('ii7', 'V7'),
        ('IV', 'V'), ('IV', 'V7'), ('IV', 'I'),
        ('V', 'I'), ('V7', 'I'), ('V', 'vi'),
        ('vi', 'IV'), ('vi', 'ii'), ('vi', 'V'),
        ('iii', 'vi'), ('iii', 'IV')
    ]
    return (chord1, chord2) in strong_progressions

def is_weak_progression(chord1, chord2):
    """Check if this is a weak or awkward progression."""
    weak_progressions = [
        ('V', 'IV'), ('I', 'ii'), ('iii', 'ii'), 
        ('vii°', 'vi'), ('V7', 'IV')
    ]
    return (chord1, chord2) in weak_progressions

def get_progression_style(progression):
    """Determine the style of the progression."""
    if any('7' in chord for chord in progression):
        return 'Jazz/Extended'
    elif 'vi' in progression and 'IV' in progression:
        return 'Popular'
    else:
        return 'Classical'

def get_progression_description(progression, detected_key):
    """Generate a human-readable description of the progression."""
    style = get_progression_style(progression)
    chord_sequence = ' - '.join(progression[:4])  # Show first 4 chords
    
    descriptions = {
        'Classical': f'Classical progression in {detected_key.name}: {chord_sequence}',
        'Popular': f'Popular progression in {detected_key.name}: {chord_sequence}',
        'Jazz/Extended': f'Jazz progression in {detected_key.name}: {chord_sequence}'
    }
    
    return descriptions.get(style, f'Progression in {detected_key.name}: {chord_sequence}')

@app.route('/realize_satb', methods=['POST'])
def realize_satb():
    """Realize SATB harmonization for a given chord progression."""
    try:
        data = request.get_json()
        chord_progression = data.get('chord_progression', [])
        bass_notes = data.get('bass_notes', [])
        key_name = data.get('key', 'C major')
        
        if not chord_progression:
            return jsonify({'error': 'No chord progression provided'}), 400
        if not bass_notes:
            return jsonify({'error': 'No bass notes provided'}), 400
        
        # Generate SATB harmonization with proper voice leading
        satb_realization = generate_satb_harmonization(chord_progression, bass_notes, key_name)
        
        return jsonify({
            'satb_harmonization': satb_realization
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Voice ranges from ekzhang/harmony
SOPRANO_RANGE = (pitch.Pitch("C4"), pitch.Pitch("G5"))
ALTO_RANGE = (pitch.Pitch("G3"), pitch.Pitch("C5"))
TENOR_RANGE = (pitch.Pitch("C3"), pitch.Pitch("G4"))
BASS_RANGE = (pitch.Pitch("E2"), pitch.Pitch("C4"))

def voiceNote(noteName, pitchRange):
    """Generates voicings for a note in a given pitch range."""
    lowerOctave = pitchRange[0].octave
    upperOctave = pitchRange[1].octave
    for octave in range(lowerOctave, upperOctave + 1):
        n = pitch.Pitch(noteName + str(octave))
        if pitchRange[0] <= n <= pitchRange[1]:
            yield n

def _voiceTriadUnordered(noteNames):
    assert len(noteNames) == 3
    for tenor, alto, soprano in itertools.permutations(noteNames, 3):
        for sopranoNote in voiceNote(soprano, SOPRANO_RANGE):
            altoMin = max((ALTO_RANGE[0], sopranoNote.transpose("-P8")))
            altoMax = min((ALTO_RANGE[1], sopranoNote))
            for altoNote in voiceNote(alto, (altoMin, altoMax)):
                tenorMin = max((TENOR_RANGE[0], altoNote.transpose("-P8")))
                tenorMax = min((TENOR_RANGE[1], altoNote))
                for tenorNote in voiceNote(tenor, (tenorMin, tenorMax)):
                    yield chord.Chord([tenorNote, altoNote, sopranoNote])

def _voiceChord(noteNames):
    assert len(noteNames) == 4
    bass = noteNames.pop(0)
    for chord_obj in _voiceTriadUnordered(noteNames):
        for bassNote in voiceNote(bass, BASS_RANGE):
            if bassNote <= chord_obj.bass():
                chord4 = copy.deepcopy(chord_obj)
                chord4.add(bassNote)
                yield chord4

def voiceChord(key_obj, chord_obj):
    """Generates four-part voicings for a fifth or seventh chord."""
    leadingTone = key_obj.getLeadingTone().name
    noteNames = [p.name for p in chord_obj.pitches]
    if chord_obj.containsSeventh():
        yield from _voiceChord(noteNames)
    elif chord_obj.inversion() == 2:
        # must double the fifth
        yield from _voiceChord(noteNames + [chord_obj.fifth.name])
    else:
        # double the root
        if chord_obj.root().name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.root().name])
        # double the third
        if chord_obj.third.name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.third.name])
        # double the fifth
        if chord_obj.fifth.name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.fifth.name])
        # option to omit the fifth
        if chord_obj.romanNumeral == "I" and chord_obj.inversion() == 0:
            yield from _voiceChord([chord_obj.root().name] * 3 + [chord_obj.third.name])

def progressionCost(key_obj, chord1, chord2):
    """Computes elements of cost between two chords: contrary motion, etc."""
    cost = 0

    # Overlapping voices
    if (
        chord2[0] > chord1[1]
        or chord2[1] < chord1[0]
        or chord2[1] > chord1[2]
        or chord2[2] < chord1[1]
        or chord2[2] > chord1[3]
        or chord2[3] < chord1[2]
    ):
        cost += 40

    # Avoid big jumps
    diff = [abs(chord1.pitches[i].midi - chord2.pitches[i].midi) for i in range(4)]
    cost += (diff[3] // 3) ** 2 if diff[3] else 1
    cost += diff[2] ** 2 // 3
    cost += diff[1] ** 2 // 3
    cost += diff[0] ** 2 // 50 if diff[0] != 12 else 0

    # Contrary motion is good, parallel fifths are bad
    for i in range(4):
        for j in range(i + 1, 4):
            t1, t2 = chord1.pitches[j], chord2.pitches[j]
            b1, b2 = chord1.pitches[i], chord2.pitches[i]
            if t1 == t2 and b1 == b2:  # No motion
                continue
            i1, i2 = t1.midi - b1.midi, t2.midi - b2.midi
            if i1 % 12 == i2 % 12 == 7:  # Parallel fifth
                cost += 60
            if i1 % 12 == i2 % 12 == 0:  # Parallel octave
                cost += 100
            if i == 0 and j == 3:  # Soprano and bass not contrary
                if (t2 > t1 and b2 > b1) or (t2 < t1 and b2 < b1):
                    cost += 2

    # Chordal 7th should resolve downward or stay
    if chord1.seventh:
        seventhVoice = chord1.pitches.index(chord1.seventh)
        delta = chord2.pitches[seventhVoice].midi - chord1.seventh.midi
        if delta < -2 or delta > 0:
            cost += 100

    # V->I means ti->do or ti->sol
    pitches = key_obj.getPitches()
    pitches[6] = key_obj.getLeadingTone()
    if (
        chord1.root().name
        in (
            pitches[4].name,
            pitches[6].name,
        )
        and chord2.root().name in (pitches[0].name, pitches[5].name)
        and pitches[6].name in chord1.pitchNames
    ):
        voice = chord1.pitchNames.index(pitches[6].name)
        delta = chord2.pitches[voice].midi - chord1.pitches[voice].midi
        if not (delta == 1 or (delta == -4 and voice >= 1 and voice <= 2)):
            cost += 100

    return cost

def chordCost(key_obj, chord_obj):
    """Computes elements of cost that only pertain to a single chord."""
    cost = 0
    if chord_obj.inversion() == 0:
        # Slightly prefer to double the root in a R.P. chord
        if chord_obj.pitchClasses.count(chord_obj.root().pitchClass) <= 1:
            cost += 1
    return cost

def voiceProgression(key_obj, chordProgression):
    """Voices a chord progression in a specified key using DP."""
    if isinstance(chordProgression, str):
        chordProgression = list(filter(None, chordProgression.split()))

    dp = [{} for _ in chordProgression]
    for i, numeral in enumerate(chordProgression):
        chord_obj = roman.RomanNumeral(numeral, key_obj)
        voicings = voiceChord(key_obj, chord_obj)
        if i == 0:
            for v in voicings:
                dp[0][v.pitches] = (chordCost(key_obj, v), None)
        else:
            for v in voicings:
                best = (float("inf"), None)
                for pv_pitches, (pcost, _) in dp[i - 1].items():
                    pv = chord.Chord(pv_pitches)
                    ccost = pcost + progressionCost(key_obj, pv, v)
                    if ccost < best[0]:
                        best = (ccost, pv_pitches)
                dp[i][v.pitches] = (best[0] + chordCost(key_obj, v), best[1])

    cur, (totalCost, _) = min(dp[-1].items(), key=lambda p: p[1][0])
    ret = []
    for i in reversed(range(len(chordProgression))):
        ret.append(chord.Chord(cur, lyric=chordProgression[i]))
        cur = dp[i][cur][1]
    return list(reversed(ret)), totalCost

def generate_satb_harmonization(chord_progression, bass_notes, key_name):
    """Generate a complete SATB harmonization with proper voice leading using ekzhang/harmony algorithms."""
    try:
        # Parse the key
        key_parts = key_name.split()
        if len(key_parts) == 2:
            tonic = key_parts[0]
            mode = key_parts[1].lower()
            if 'b' in tonic:
                tonic = tonic.replace('b', '-')
            key_obj = key.Key(tonic, mode)
        else:
            key_obj = key.Key('C', 'major')
        
        # Use the sophisticated voice leading from ekzhang/harmony
        chords, totalCost = voiceProgression(key_obj, chord_progression)
        
        # Convert to our API format
        satb_voices = []
        for i, chord_obj in enumerate(chords):
            # Sort pitches by octave (bass, tenor, alto, soprano)
            sorted_pitches = sorted(chord_obj.pitches, key=lambda p: p.midi)
            
            satb_voices.append({
                'bass': sorted_pitches[0].nameWithOctave,
                'tenor': sorted_pitches[1].nameWithOctave,
                'alto': sorted_pitches[2].nameWithOctave,
                'soprano': sorted_pitches[3].nameWithOctave,
                'chord': chord_progression[i]
            })
        
        print(f"Generated SATB with total cost: {totalCost}")
        return satb_voices
        
    except Exception as e:
        print(f"Error in SATB generation: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback harmonization
        return generate_fallback_satb(len(chord_progression))



def generate_fallback_satb(num_chords):
    """Generate a fallback SATB harmonization."""
    fallback = []
    for i in range(num_chords):
        fallback.append({
            'soprano': 'C5',
            'alto': 'G4', 
            'tenor': 'E4',
            'bass': 'C3',
            'chord': 'I'
        })
    return fallback

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'SATB Backend is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 