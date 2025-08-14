from flask import Flask, request, jsonify
from flask_cors import CORS
from music21 import stream, note, key, roman, pitch, interval, scale, chord
import os
from itertools import combinations, product
import copy
import itertools
import replicate

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
            3: ['I6'],  # 3rd degree: I6 (3rd of I) - avoid iii
            4: ['IV', 'ii6', 'I6/4'],  # 4th degree: IV (root), ii6 (3rd), I6/4 (5th of I)
            5: ['V', 'V7', 'I6/4'],  # 5th degree: V (root) - avoid iii6
            6: ['vi', 'IV6'],  # 6th degree: vi (root), IV6 (3rd of IV)
            7: ['vii°', 'V7', 'V6/5']  # 7th degree: vii° (root), V7 (3rd)
        }
    else:  # minor mode
        chord_options = {
            1: ['i', 'VI6'],
            2: ['ii°', 'vii°6', 'V7'],
            3: ['i6'],  # 3rd degree: i6 (3rd of i) - avoid III
            4: ['iv', 'ii°6', 'i6/4'],
            5: ['V', 'v'],  # 5th degree: V, v - avoid III6
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
    
    # Heavy penalty for iii chords (rare and awkward in classical harmony)
    for chord in progression:
        if 'iii' in chord or 'III' in chord:
            score -= 30  # Significant penalty for iii chords
    
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
        ('vii°', 'vi'), ('V7', 'IV'), ('iii', 'IV'),
        ('iii', 'V'), ('iii', 'vi'), ('I', 'iii'),
        ('IV', 'iii'), ('vi', 'iii')  # Additional iii chord penalties
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
        satb_realization, compromises = generate_satb_harmonization(chord_progression, bass_notes, key_name)
        
        # Validate SATB rules and provide analysis (including compromises in scoring)
        validation_results = validate_satb_rules(satb_realization, chord_progression, key_name, compromises)
        print(f"Validation errors found: {len(validation_results.get('errors', []))}")
        print(f"Validation warnings found: {len(validation_results.get('warnings', []))}")
        
        # Add compromise information to validation results
        validation_results['compromises'] = compromises
        print(f"Total compromises being sent: {len(compromises)}")
        
        return jsonify({
            'satb_harmonization': satb_realization,
            'validation': validation_results
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
        # Prioritize complete chords - double the root first (most stable)
        if chord_obj.root().name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.root().name])
        # double the fifth (good for stability)
        if chord_obj.fifth and chord_obj.fifth.name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.fifth.name])
        # double the third (less preferred, but acceptable)
        if chord_obj.third.name != leadingTone:
            yield from _voiceChord(noteNames + [chord_obj.third.name])
        # REMOVED: option to omit the fifth - always use complete chords

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

    # Contrary motion is good, parallel fifths and octaves are bad
    for i in range(4):
        for j in range(i + 1, 4):
            t1, t2 = chord1.pitches[j], chord2.pitches[j]
            b1, b2 = chord1.pitches[i], chord2.pitches[i]
            if t1 == t2 and b1 == b2:  # No motion
                continue
            i1, i2 = t1.midi - b1.midi, t2.midi - b2.midi
            
            # STRENGTHENED: Parallel fifths (very bad)
            if i1 % 12 == i2 % 12 == 7:  # Parallel fifth
                cost += 200  # Increased penalty
            
            # STRENGTHENED: Parallel octaves (extremely bad)
            if i1 % 12 == i2 % 12 == 0:  # Parallel octave
                cost += 300  # Increased penalty
                
            # STRENGTHENED: Parallel unisons (also very bad)
            if abs(i1) == abs(i2) == 0:  # Parallel unison
                cost += 250
                
            # Hidden/direct fifths and octaves (outer voices)
            if i == 0 and j == 3:  # Bass and soprano
                if (t2.midi > t1.midi and b2.midi > b1.midi) or (t2.midi < t1.midi and b2.midi < b1.midi):
                    # Similar motion in outer voices
                    if abs(i2) % 12 == 7 or abs(i2) % 12 == 0:  # Landing on fifth or octave
                        cost += 50  # Hidden parallel penalty
                    else:
                        cost += 2  # General similar motion penalty

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
    
    # HEAVILY penalize incomplete chords
    pitch_classes = [p.pitchClass for p in chord_obj.pitches]
    unique_pitch_classes = set(pitch_classes)
    
    # Check for missing chord tones (root, third, fifth)
    root_pc = chord_obj.root().pitchClass
    third_pc = chord_obj.third.pitchClass if chord_obj.third else None
    fifth_pc = chord_obj.fifth.pitchClass if chord_obj.fifth else None
    
    if root_pc not in unique_pitch_classes:
        cost += 500  # Missing root is very bad
    if third_pc and third_pc not in unique_pitch_classes:
        cost += 300  # Missing third is very bad
    if fifth_pc and fifth_pc not in unique_pitch_classes:
        cost += 200  # Missing fifth is bad
    
    # Prefer to double the root in root position chords
    if chord_obj.inversion() == 0:
        if pitch_classes.count(root_pc) <= 1:
            cost += 10  # Light penalty for not doubling root
    
    # Penalize doubling leading tone
    leading_tone_pc = key_obj.getLeadingTone().pitchClass
    if pitch_classes.count(leading_tone_pc) > 1:
        cost += 100  # Heavy penalty for doubling leading tone
    
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

def voiceProgressionWithFixedBass(key_obj, chord_progression, bass_notes):
    """Voice a chord progression with a fixed bass line using dynamic programming."""
    if isinstance(chord_progression, str):
        chord_progression = list(filter(None, chord_progression.split()))

    dp = [{} for _ in chord_progression]
    
    for i, numeral in enumerate(chord_progression):
        chord_symbol = roman.RomanNumeral(numeral, key_obj)
        fixed_bass = bass_notes[i]  # The bass note we must use
        
        # Generate voicings that include our required bass note
        print(f"Calling voiceChordWithFixedBass for chord {i+1}: {numeral}")
        voicings = voiceChordWithFixedBass(key_obj, chord_symbol, fixed_bass)
        print(f"Got {len(voicings)} voicings for chord {i+1}")
        
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

    if not dp[-1]:
        # Fallback if no valid voicings found
        fallback_compromises = [{
            'type': 'fallback_used',
            'severity': 'high',
            'description': 'Unable to generate proper voice leading - using fallback harmonization',
            'explanation': 'The bass line and chord progression combination was too constraining for the algorithm to find valid SATB voice leading.'
        }]
        return generate_simple_fallback_chords(chord_progression, bass_notes), float('inf'), fallback_compromises
    
    cur, (totalCost, _) = min(dp[-1].items(), key=lambda p: p[1][0])
    ret = []
    chord_costs = []  # Track individual chord costs for compromise analysis
    
    for i in reversed(range(len(chord_progression))):
        chord_obj = chord.Chord(cur, lyric=chord_progression[i])
        ret.append(chord_obj)
        # Store the cost for this specific chord
        chord_costs.append(dp[i][cur][0] - (dp[i-1][dp[i][cur][1]][0] if i > 0 and dp[i][cur][1] else 0))
        cur = dp[i][cur][1]
    
    # Analyze compromises made
    compromises = analyze_compromises(list(reversed(ret)), list(reversed(chord_costs)), totalCost)
    
    return list(reversed(ret)), totalCost, compromises

def analyze_compromises(chords, chord_costs, total_cost):
    """Analyze what compromises were made during SATB generation."""
    compromises = []
    
    # Define cost thresholds for different types of issues
    HIGH_COST_THRESHOLD = 100  # Serious voice leading violations
    MEDIUM_COST_THRESHOLD = 50   # Moderate issues
    LOW_COST_THRESHOLD = 20      # Minor style issues
    
    # Analyze overall cost
    avg_cost_per_chord = total_cost / len(chords) if chords else 0
    
    if total_cost > HIGH_COST_THRESHOLD * len(chords):
        compromises.append({
            'type': 'overall_quality',
            'severity': 'high',
            'description': f'High overall cost ({total_cost:.0f}) indicates multiple voice leading compromises were necessary',
            'explanation': 'The bass line or chord progression forced the algorithm to violate several SATB rules to complete the harmonization.'
        })
    elif total_cost > MEDIUM_COST_THRESHOLD * len(chords):
        compromises.append({
            'type': 'overall_quality', 
            'severity': 'medium',
            'description': f'Moderate cost ({total_cost:.0f}) indicates some voice leading compromises',
            'explanation': 'Some SATB conventions were bent to accommodate the given bass line and chord progression.'
        })
    
    # Analyze individual chord costs
    for i, (chord_obj, cost) in enumerate(zip(chords, chord_costs)):
        chord_num = i + 1
        
        if cost > HIGH_COST_THRESHOLD:
            compromises.append({
                'type': 'chord_compromise',
                'severity': 'high', 
                'location': f'Chord {chord_num}',
                'description': f'Significant compromises made in chord {chord_num} (cost: {cost:.0f})',
                'explanation': f'This chord likely contains parallel motion, voice crossing, or missing chord tones due to constraints from the fixed bass line.'
            })
        elif cost > MEDIUM_COST_THRESHOLD:
            compromises.append({
                'type': 'chord_compromise',
                'severity': 'medium',
                'location': f'Chord {chord_num}', 
                'description': f'Moderate compromises in chord {chord_num} (cost: {cost:.0f})',
                'explanation': f'This chord may have wide spacing, large leaps, or suboptimal doubling due to bass line constraints.'
            })
    
    # Check for specific forced compromises
    for i in range(len(chords) - 1):
        current_chord = chords[i]
        next_chord = chords[i + 1]
        
        # Check if parallel motion was forced
        for j in range(4):
            for k in range(j + 1, 4):
                try:
                    interval1 = interval.Interval(current_chord.pitches[j], current_chord.pitches[k])
                    interval2 = interval.Interval(next_chord.pitches[j], next_chord.pitches[k])
                    
                    if (interval1.simpleName == 'P5' and interval2.simpleName == 'P5') or \
                       (interval1.simpleName == 'P8' and interval2.simpleName == 'P8'):
                        voice_names = ['Bass', 'Tenor', 'Alto', 'Soprano']
                        compromises.append({
                            'type': 'forced_parallels',
                            'severity': 'high',
                            'location': f'Chords {i+1}-{i+2}',
                            'description': f'Parallel {interval1.simpleName.lower()}s between {voice_names[j]} and {voice_names[k]} were unavoidable',
                            'explanation': 'The fixed bass line made it impossible to avoid this parallel motion while maintaining proper voice leading elsewhere.'
                        })
                except:
                    continue
    
    return compromises

def voiceChordWithFixedBass(key_obj, chord_symbol, fixed_bass):
    """Generate voicings for a chord with a specific bass note - COMPLETELY REWRITTEN."""
    voicings = []
    
    # Get the chord tones (root, third, fifth, seventh if present)
    root = chord_symbol.root()
    third = chord_symbol.third  
    fifth = chord_symbol.fifth
    seventh = chord_symbol.seventh if chord_symbol.containsSeventh() else None
    
    # All available chord tones
    chord_tones = [root.name, third.name, fifth.name]
    if seventh:
        chord_tones.append(seventh.name)
    
    print(f"Generating voicings for {chord_symbol} with bass={fixed_bass.nameWithOctave}")
    print(f"Chord tones: {chord_tones}")
    
    # STRATEGY: Generate COMPLETE triads with proper doubling
    # Priority: 1) Root doubling, 2) Fifth doubling, 3) Third doubling (avoid leading tone doubling)
    
    leading_tone = key_obj.getLeadingTone().name
    
    # Define voice ranges more strictly
    soprano_range = (pitch.Pitch("C4"), pitch.Pitch("G5"))
    alto_range = (pitch.Pitch("G3"), pitch.Pitch("C5"))  
    tenor_range = (pitch.Pitch("C3"), pitch.Pitch("G4"))
    
    # Generate complete chord voicings
    doubling_priority = []
    if root.name != leading_tone:
        doubling_priority.append(root.name)  # Root doubling first
    if fifth and fifth.name != leading_tone:
        doubling_priority.append(fifth.name)  # Fifth doubling second  
    if third.name != leading_tone:
        doubling_priority.append(third.name)  # Third doubling last
    
    for double_note in doubling_priority:
        # Create a complete triad with one note doubled
        triad_notes = [root.name, third.name, fifth.name, double_note]
        
        # Generate all permutations for tenor, alto, soprano (bass is fixed)
        import itertools
        for soprano_note, alto_note, tenor_note in itertools.permutations(triad_notes[1:], 3):
            # Try different octaves
            for sop_oct in range(4, 6):
                for alto_oct in range(3, 5):
                    for ten_oct in range(3, 5):
                        try:
                            soprano = pitch.Pitch(soprano_note + str(sop_oct))
                            alto = pitch.Pitch(alto_note + str(alto_oct))
                            tenor = pitch.Pitch(tenor_note + str(ten_oct))
                            
                            # Check voice ranges
                            if not (soprano_range[0] <= soprano <= soprano_range[1]):
                                continue
                            if not (alto_range[0] <= alto <= alto_range[1]):
                                continue  
                            if not (tenor_range[0] <= tenor <= tenor_range[1]):
                                continue
                            
                            # Check voice ordering: Bass < Tenor < Alto < Soprano
                            if not (fixed_bass.pitch < tenor < alto < soprano):
                                continue
                                
                            # Check spacing (upper voices within octave)
                            if soprano.midi - alto.midi > 12:  # Soprano-Alto > octave
                                continue
                            if alto.midi - tenor.midi > 12:  # Alto-Tenor > octave  
                                continue
                            
                            # Create the chord
                            voicing = chord.Chord([fixed_bass.pitch, tenor, alto, soprano])
                            voicings.append(voicing)
                            
                        except:
                            continue
        
        # Limit voicings to prevent explosion
        if len(voicings) > 20:
            break
    
    print(f"Generated {len(voicings)} voicings")
    
    # If no voicings found, create a simple fallback
    if not voicings:
        print("No valid voicings found, creating fallback")
        try:
            # Simple fallback: root position with doubled root
            soprano = pitch.Pitch(root.name + "5")
            alto = pitch.Pitch(third.name + "4") 
            tenor = pitch.Pitch(fifth.name + "4")
            if alto < tenor:  # Fix ordering if needed
                alto, tenor = tenor, alto
            voicing = chord.Chord([fixed_bass.pitch, tenor, alto, soprano])
            voicings.append(voicing)
        except:
            # Last resort fallback
            voicing = chord.Chord([fixed_bass.pitch, fixed_bass.pitch.transpose(4), fixed_bass.pitch.transpose(7), fixed_bass.pitch.transpose(12)])
            voicings.append(voicing)
    
    return voicings[:10]  # Return best 10

def create_simple_voicing_with_bass(chord_symbol, fixed_bass):
    """Create a simple voicing when complex voicing fails."""
    # Use the fixed bass and add simple chord tones above it
    chord_pitches = [p.name for p in chord_symbol.pitches]
    
    # Find appropriate octaves for upper voices
    tenor = pitch.Pitch(chord_pitches[0] + "4")  # Root in octave 4
    alto = pitch.Pitch(chord_pitches[1 % len(chord_pitches)] + "4")  # 3rd
    soprano = pitch.Pitch(chord_pitches[2 % len(chord_pitches)] + "5")  # 5th in octave 5
    
    return chord.Chord([fixed_bass.pitch, tenor, alto, soprano])

def generate_simple_fallback_chords(chord_progression, bass_notes):
    """Generate simple fallback chords when DP fails."""
    chords = []
    for i, bass_note in enumerate(bass_notes):
        # Create a simple triad with the given bass
        tenor = pitch.Pitch(bass_note.name + "4")
        alto = pitch.Pitch(bass_note.name + "4") 
        soprano = pitch.Pitch(bass_note.name + "5")
        chords.append(chord.Chord([bass_note.pitch, tenor, alto, soprano]))
    return chords

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
        
        # Convert bass notes to music21 Note objects with proper octaves
        bass_note_objects = []
        for bass_note_name in bass_notes:
            # Ensure octave is present
            if not any(char.isdigit() for char in bass_note_name):
                bass_note_name += '3'  # Default bass octave
            bass_note_objects.append(note.Note(bass_note_name))
        
        # Use constrained voice leading that preserves the original bass line
        chords, totalCost, compromises = voiceProgressionWithFixedBass(key_obj, chord_progression, bass_note_objects)
        
        # Convert to our API format
        satb_voices = []
        for i, chord_obj in enumerate(chords):
            # Sort pitches by octave (bass, tenor, alto, soprano)
            sorted_pitches = sorted(chord_obj.pitches, key=lambda p: p.midi)
            
            # Ensure the bass matches our input exactly
            original_bass = bass_note_objects[i].nameWithOctave
            
            # Correct SATB voice assignment: Bass (lowest) -> Tenor -> Alto -> Soprano (highest)
            satb_voices.append({
                'bass': original_bass,  # Use the original bass note exactly
                'tenor': sorted_pitches[1].nameWithOctave,  # Second lowest
                'alto': sorted_pitches[2].nameWithOctave,   # Third lowest  
                'soprano': sorted_pitches[3].nameWithOctave, # Highest
                'chord': chord_progression[i]
            })
        
        print(f"Generated SATB with fixed bass line, total cost: {totalCost}")
        print(f"Compromises found: {len(compromises)}")
        print(f"First chord voices: S={satb_voices[0]['soprano']}, A={satb_voices[0]['alto']}, T={satb_voices[0]['tenor']}, B={satb_voices[0]['bass']}")
        return satb_voices, compromises
        
    except Exception as e:
        print(f"Error in SATB generation: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback harmonization
        return generate_fallback_satb(len(chord_progression)), []



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
    return jsonify({'status': 'healthy'})

def validate_satb_rules(satb_data, chord_progression, key_name, compromises=None):
    """Comprehensive SATB rule validation with specific error identification and solutions."""
    
    if not satb_data or len(satb_data) < 2:
        return {
            'errors': [],
            'warnings': [],
            'score': 100,
            'suggestions': []
        }
    
    errors = []
    warnings = []
    suggestions = []
    
    try:
        # Parse key
        key_obj = key.Key(key_name.split()[0], key_name.split()[1] if len(key_name.split()) > 1 else 'major')
        
        # Convert SATB data to Music21 objects for analysis
        chords = []
        print(f"Validating {len(satb_data)} chords...")
        for i, chord_data in enumerate(satb_data):
            try:
                soprano_pitch = pitch.Pitch(chord_data['soprano'])
                alto_pitch = pitch.Pitch(chord_data['alto'])
                tenor_pitch = pitch.Pitch(chord_data['tenor'])
                bass_pitch = pitch.Pitch(chord_data['bass'])
                
                chord_obj = chord.Chord([bass_pitch, tenor_pitch, alto_pitch, soprano_pitch])
                chords.append(chord_obj)
                print(f"Chord {i+1}: B={bass_pitch.nameWithOctave}, T={tenor_pitch.nameWithOctave}, A={alto_pitch.nameWithOctave}, S={soprano_pitch.nameWithOctave}")
            except Exception as e:
                print(f"Error parsing chord {i+1}: {e}")
                continue
        
        if len(chords) < 2:
            return {
                'errors': ['Unable to analyze harmonization'],
                'warnings': [],
                'score': 0,
                'suggestions': ['Try generating a new harmonization']
            }
        
        # Analyze each chord pair for voice leading errors
        for i in range(len(chords) - 1):
            current_chord = chords[i]
            next_chord = chords[i + 1]
            chord_num = i + 1
            
            # Check voice ranges
            current_pitches = [current_chord.pitches[j] for j in range(4)]
            next_pitches = [next_chord.pitches[j] for j in range(4)]
            
            voice_names = ['Bass', 'Tenor', 'Alto', 'Soprano']
            voice_ranges = [BASS_RANGE, TENOR_RANGE, ALTO_RANGE, SOPRANO_RANGE]
            
            for j, (current_p, next_p, voice_name, voice_range) in enumerate(zip(current_pitches, next_pitches, voice_names, voice_ranges)):
                # Voice range violations
                if not (voice_range[0] <= current_p <= voice_range[1]):
                    errors.append({
                        'type': 'voice_range',
                        'location': f'Chord {chord_num}',
                        'voice': voice_name,
                        'description': f'{voice_name} note {current_p.name}{current_p.octave} is outside normal range',
                        'severity': 'error'
                    })
                    suggestions.append(f'Move {voice_name} to within {voice_range[0].name}{voice_range[0].octave}-{voice_range[1].name}{voice_range[1].octave}')
                
                if not (voice_range[0] <= next_p <= voice_range[1]):
                    errors.append({
                        'type': 'voice_range',
                        'location': f'Chord {chord_num + 1}',
                        'voice': voice_name,
                        'description': f'{voice_name} note {next_p.name}{next_p.octave} is outside normal range',
                        'severity': 'error'
                    })
            
            # Check for parallel fifths and octaves
            for j in range(4):
                for k in range(j + 1, 4):
                    interval1 = interval.Interval(current_pitches[j], current_pitches[k])
                    interval2 = interval.Interval(next_pitches[j], next_pitches[k])
                    
                    print(f"Checking {voice_names[j]}-{voice_names[k]}: {interval1.simpleName} -> {interval2.simpleName}")
                    
                    # Parallel fifths
                    if interval1.simpleName == 'P5' and interval2.simpleName == 'P5':
                        if current_pitches[j] != next_pitches[j] or current_pitches[k] != next_pitches[k]:
                            print(f"FOUND PARALLEL FIFTHS: {voice_names[j]} and {voice_names[k]}")
                            errors.append({
                                'type': 'parallel_fifths',
                                'location': f'Chords {chord_num}-{chord_num + 1}',
                                'voice': f'{voice_names[j]} and {voice_names[k]}',
                                'description': f'Parallel fifths between {voice_names[j]} and {voice_names[k]}',
                                'severity': 'error'
                            })
                            suggestions.append(f'Change chord voicing or try different chord progression at position {chord_num}')
                    
                    # Parallel octaves AND unisons (P1 = unison = same note)
                    if (interval1.simpleName == 'P8' and interval2.simpleName == 'P8') or \
                       (interval1.simpleName == 'P1' and interval2.simpleName == 'P1'):
                        if current_pitches[j] != next_pitches[j] or current_pitches[k] != next_pitches[k]:
                            interval_type = "unisons" if interval1.simpleName == 'P1' else "octaves"
                            print(f"FOUND PARALLEL {interval_type.upper()}: {voice_names[j]} and {voice_names[k]}")
                            errors.append({
                                'type': f'parallel_{interval_type}',
                                'location': f'Chords {chord_num}-{chord_num + 1}',
                                'voice': f'{voice_names[j]} and {voice_names[k]}',
                                'description': f'Parallel {interval_type} between {voice_names[j]} and {voice_names[k]}',
                                'severity': 'error'
                            })
                            suggestions.append(f'Change chord voicing or try different chord progression at position {chord_num}')
                    
                    # Parallel unisons (same note repeated in different voices)
                    if current_pitches[j].nameWithOctave == current_pitches[k].nameWithOctave and next_pitches[j].nameWithOctave == next_pitches[k].nameWithOctave:
                        if current_pitches[j] != next_pitches[j] or current_pitches[k] != next_pitches[k]:
                            errors.append({
                                'type': 'parallel_unisons',
                                'location': f'Chords {chord_num}-{chord_num + 1}',
                                'voice': f'{voice_names[j]} and {voice_names[k]}',
                                'description': f'Parallel unisons between {voice_names[j]} and {voice_names[k]}',
                                'severity': 'error'
                            })
                            suggestions.append(f'Separate {voice_names[j]} and {voice_names[k]} to different pitches')
            
            # Check for voice crossing
            for j in range(3):
                if current_pitches[j] > current_pitches[j + 1]:
                    errors.append({
                        'type': 'voice_crossing',
                        'location': f'Chord {chord_num}',
                        'voice': f'{voice_names[j]} and {voice_names[j + 1]}',
                        'description': f'{voice_names[j]} crosses above {voice_names[j + 1]}',
                        'severity': 'error'
                    })
                    suggestions.append(f'Reorder voices: {voice_names[j + 1]} should be higher than {voice_names[j]}')
            
            # Check for incomplete chords
            current_pitch_classes = set(p.pitchClass for p in current_pitches)
            
            # For major/minor triads, we need root, third, and fifth
            if len(current_pitch_classes) < 3:
                missing_tones = []
                root_pc = current_chord.root().pitchClass if current_chord.root() else None
                third_pc = current_chord.third.pitchClass if current_chord.third else None
                fifth_pc = current_chord.fifth.pitchClass if current_chord.fifth else None
                
                if root_pc and root_pc not in current_pitch_classes:
                    missing_tones.append('root')
                if third_pc and third_pc not in current_pitch_classes:
                    missing_tones.append('third')
                if fifth_pc and fifth_pc not in current_pitch_classes:
                    missing_tones.append('fifth')
                
                if missing_tones:
                    errors.append({
                        'type': 'incomplete_chord',
                        'location': f'Chord {chord_num}',
                        'voice': 'All voices',
                        'description': f'Incomplete chord: missing {", ".join(missing_tones)}',
                        'severity': 'error'
                    })
                    suggestions.append(f'Include all chord tones (root, third, fifth) in chord {chord_num}')
            
            # Check for large melodic leaps
            for j, voice_name in enumerate(voice_names):
                leap = abs(current_pitches[j].midi - next_pitches[j].midi)
                max_leap = 12 if j == 0 else 6  # Bass can leap up to octave, others max 6th
                
                if leap > max_leap:
                    severity = 'error' if leap > 12 else 'warning'
                    errors.append({
                        'type': 'large_leap',
                        'location': f'Chords {chord_num}-{chord_num + 1}',
                        'voice': voice_name,
                        'description': f'{voice_name} leaps {leap} semitones (>{max_leap} limit)',
                        'severity': severity
                    })
                    if severity == 'error':
                        suggestions.append(f'Reduce {voice_name} leap by changing chord voicing or progression')
            
            # Check for proper resolution of tendency tones
            if i < len(chord_progression) - 1:
                current_roman = chord_progression[i]
                next_roman = chord_progression[i + 1]
                
                # Leading tone resolution
                if 'V' in current_roman and ('I' in next_roman or 'i' in next_roman):
                    leading_tone = key_obj.getLeadingTone()
                    tonic = key_obj.getTonic()
                    
                    # Find leading tone in current chord
                    for j, p in enumerate(current_pitches):
                        if p.name == leading_tone.name:
                            next_p = next_pitches[j]
                            if next_p.name != tonic.name:
                                warnings.append({
                                    'type': 'tendency_tone',
                                    'location': f'Chords {chord_num}-{chord_num + 1}',
                                    'voice': voice_names[j],
                                    'description': f'Leading tone in {voice_names[j]} should resolve to tonic',
                                    'severity': 'warning'
                                })
                                suggestions.append(f'Resolve leading tone in {voice_names[j]} upward to tonic')
            
            # Check chord spacing
            soprano_alto = current_pitches[3].midi - current_pitches[2].midi
            alto_tenor = current_pitches[2].midi - current_pitches[1].midi
            
            if soprano_alto > 12:  # More than an octave
                warnings.append({
                    'type': 'wide_spacing',
                    'location': f'Chord {chord_num}',
                    'voice': 'Soprano-Alto',
                    'description': f'Wide spacing between Soprano and Alto ({soprano_alto} semitones)',
                    'severity': 'warning'
                })
                suggestions.append('Keep upper voices within an octave of each other')
            
            if alto_tenor > 12:  # More than an octave
                warnings.append({
                    'type': 'wide_spacing',
                    'location': f'Chord {chord_num}',
                    'voice': 'Alto-Tenor',
                    'description': f'Wide spacing between Alto and Tenor ({alto_tenor} semitones)',
                    'severity': 'warning'
                })
                suggestions.append('Keep upper voices within an octave of each other')
        
        # Calculate overall score including compromises
        error_count = len([e for e in errors if e['severity'] == 'error'])
        warning_count = len([e for e in errors if e['severity'] == 'warning'])
        
        # Count compromises and apply penalties
        compromise_penalty = 0
        if compromises:
            for compromise in compromises:
                if compromise.get('severity') == 'high':
                    compromise_penalty += 15  # High severity compromises
                elif compromise.get('severity') == 'medium':
                    compromise_penalty += 10  # Medium severity compromises
                else:
                    compromise_penalty += 5   # Low severity compromises
        
        score = max(0, 100 - (error_count * 20) - (warning_count * 5) - compromise_penalty)
        
        # Add summary suggestions
        if error_count > 0:
            suggestions.insert(0, f'Found {error_count} serious errors - consider trying a different chord progression')
        elif warning_count > 2:
            suggestions.insert(0, f'Found {warning_count} minor issues - harmonization could be improved')
        elif error_count == 0 and warning_count <= 1:
            suggestions.insert(0, 'Good SATB writing! Minor or no issues found.')
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score': score,
            'suggestions': list(set(suggestions))  # Remove duplicates
        }
        
    except Exception as e:
        return {
            'errors': [{'type': 'analysis_error', 'description': f'Error analyzing harmonization: {str(e)}', 'severity': 'error'}],
            'warnings': [],
            'score': 0,
            'suggestions': ['Try generating a new harmonization']
        }

@app.route('/generate_ai_music', methods=['POST'])
def generate_ai_music():
    """Generate AI music based on chord progression using Replicate API."""
    try:
        data = request.get_json()
        chord_progression = data.get('chord_progression', [])
        key_signature = data.get('key', 'C major')
        
        if not chord_progression:
            return jsonify({'error': 'No chord progression provided'}), 400
        
        # Set up Replicate API key
        api_key = os.environ.get('REPLICATE_API_KEY') or os.environ.get('REPLICATE_API_TOKEN')
        if not api_key:
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
    # Use environment variable for port (for deployment) or default to 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port) 