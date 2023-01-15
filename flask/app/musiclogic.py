from mido import Message, bpm2tempo
import re
import os
import logging
from mido import MidiFile, MidiTrack, MetaMessage, bpm2tempo
from app.utils.classes import tone, arrangement

functiondict = {'1': 'T', '2': 'D', '3': 'T',
                '4': 'S', '5': 'T/D', '6': 'S', '7': 'D'}

chorddict = {'T': ['1', '3', '5'], 'S': ['4', '6', '1'], 'D': ['5', '7', '2']}

letter_to_note = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
                  'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,  'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11}

scale_major = {'1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11}
scale_major_tone_to_step = {}
for key in scale_major.keys():
    scale_major_tone_to_step[scale_major[key]] = key
scale_minor = {'1': 0, '2': 2, '3': 3, '4': 5, '5': 7, '6': 8, '7': 10}
scale_minor_tone_to_step = {}
for key in scale_minor.keys():
    scale_minor_tone_to_step[scale_minor[key]] = key

step_to_note_sharps = {0: 'C', 1: 'C#', 2: 'D', 3: 'D#', 4: 'E', 5:  'F',
                       6: 'F#', 7: 'G', 8: 'G#', 9: 'A', 10: 'A#', 11: 'B'}
step_to_note_flats = {0: 'C', 1: 'Db', 2: 'D', 3: 'Eb', 4: 'E', 5:  'F',
                      6: 'Gb', 7: 'G', 8: 'Ab', 9: 'A', 10: 'Bb', 11: 'Cb'}

def convert_notedict(notes, track):
    deltatime = 0
    for time in sorted(notes):
        note_appended = False
        for note in notes[time]:
            if note['event'] == 'note_on':
                if note_appended == False:
                    track.append(Message('note_on', note=note['pitch'],
                                         velocity=note['velocity'], time=time - deltatime))
                    note_appended = True
                    deltatime = time
                else:
                    track.append(Message('note_on', note=note['pitch'],
                                         velocity=note['velocity'], time=0))
            if note['event'] == 'note_off':
                if note_appended == False:
                    track.append(Message('note_off', note=note['pitch'],
                                         velocity=note['velocity'], time=time - deltatime))
                    note_appended = True
                    deltatime = time
                else:
                    track.append(Message('note_off', note=note['pitch'],
                                         velocity=note['velocity'], time=0))


def note_to_pitch(note_string):
    tone_str = re.findall('[A-Z]b?#?', note_string)[0]
    octave = int(re.findall('\d+', note_string)[0])
    return letter_to_note[tone_str] + octave * 12


def scalestep_to_note(step, tonality, baseoctave):
    tonality_base = tonality.split('-')[0]
    basetone = re.findall('(.?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)

    if tonality_base in ['G', 'D', 'A', 'E', 'H,' 'F#']:
        letter = step_to_note_sharps[(scale_major[step]+basepitch) % 12]
    if tonality_base in ['F', 'Bb', 'Eb', 'Ab', 'Db,' 'Gb']:
        letter = step_to_note_flats[(scale_major[step]+basepitch) % 12]
    return letter + str(baseoctave)

class track():
    def __init__(self, BPM):
        self.BPM=BPM
        self.notedict = {}
    def addnote(self, note, start_val, duration_val, veloticy_param=100):
        '''midi write wrapper'''
        duration = int(60000/(self.BPM) * duration_val)
        start = int(60000/(self.BPM) * start_val)
        if isinstance(note, str):
            pitch = note_to_pitch(note)
        elif not isinstance(note, int):
            pitch = int(note)
        else:
            pitch = note
        if start not in self.notedict.keys():
            self.notedict[start] = [{'event': 'note_on',
                                'pitch': pitch, 'velocity': veloticy_param}]
        else:
            self.notedict[start].append({'event': 'note_on',
                                    'pitch': pitch, 'velocity': veloticy_param})
        if start + duration not in self.notedict.keys():
            self.notedict[start + duration] = [{'event': 'note_off',
                                        'pitch': pitch, 'velocity': veloticy_param}]
        else:
            self.notedict[start + duration].append({'event': 'note_off',
                                            'pitch': pitch, 'velocity': veloticy_param})

    def unrolltimestep(self, timestep, start, duration):
        if not isinstance(timestep, list):
            pitch = note_to_pitch(timestep)
            self.addnote(pitch, start, duration)
        else:
            for i, step in enumerate(timestep):
                subedevide_start = start + duration/len(timestep)*i
                duration_devided = duration/len(timestep)
                self.unrolltimestep(step, subedevide_start, duration_devided)

    def write_voices_to_midi(self, melody, altline, tenorline, bassline):
        starttime = 0
        for i, note in enumerate(bassline):
            self.unrolltimestep(note, starttime, 1/melody[i].duration)
            starttime = starttime + 1/melody[i].duration
        starttime = 0
        for i, note in enumerate(altline):
            self.unrolltimestep(note, starttime, 1/melody[i].duration)
            starttime = starttime + 1/melody[i].duration
        starttime = 0
        for i, note in enumerate(tenorline):
            self.unrolltimestep(note, starttime, 1/melody[i].duration)
            starttime = starttime + 1/melody[i].duration


def getscaledegree(tone_str, tonality):
    basetone = re.findall('(.?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)
    relative_pitch = (note_to_pitch(tone_str) - basepitch) % 12
    return scale_major_tone_to_step[relative_pitch]


def get_notes_of_melody(melody):
    steplist = []
    for tone_str in melody:
        steplist.append(tone_str.pitch)
    return steplist


def getchords(scalesteps, tonality):
    chordlist = []
    for note in scalesteps:
        chordlist.append(functiondict[getscaledegree(note, tonality)])
    for i in range(len(chordlist), 0, -1):
        if chordlist[i-1] == 'T/D':
            if chordlist[i] == 'S':
                chordlist[i-1] = 'T'
            elif chordlist[i] == 'T' and chordlist[i-1] != 'D':
                chordlist[i-1] = 'D'
            else:
                chordlist[i-1] = 'T'
                print("new debugger is weird")

    return chordlist


def correct_octaves(line):
    for i in range(1, len(line), 1):
        pitch_diff = note_to_pitch(line[i]) - note_to_pitch(line[i-1])
        octave = re.findall('\d', line[i])[0]
        tone_str = line[i].replace(octave, '')
        if line[i] == line[i-1]:
            if abs(note_to_pitch(line[i]) - note_to_pitch(line[i+1])) > abs(note_to_pitch(tone_str + str(int(octave)+1)) - note_to_pitch(line[i+1])):
                line[i] = tone_str + str(int(octave)+1)
            elif abs(note_to_pitch(line[i]) - note_to_pitch(line[i+1])) > abs(note_to_pitch(tone_str + str(int(octave)-1)) - note_to_pitch(line[i+1])):
                line[i] = tone_str + str(int(octave)-1)
        elif pitch_diff > 10:
            line[i] = tone_str + str(int(octave)-1)
        elif pitch_diff < -10:
            line[i] = tone_str + str(int(octave)+1)
    return line

def correct_low_thirds(bassline, chords, tonality):
    for i, tone_str in enumerate(bassline):
        note = getscaledegree(tone_str, tonality)
        if note_to_pitch(tone_str) < note_to_pitch('G3'):
            if note == '3':
                bassline[i] = scalestep_to_note('1', tonality, 3)
            if note == '6': 
                #this is wonky because of the c
                bassline[i] = scalestep_to_note('4', tonality, 3)
            if note == '7': 
                bassline[i] = scalestep_to_note('5', tonality, 4)
    return bassline


def composebass(soprano_line, chords, tonality):
    bassline = []
    if len(soprano_line) != len(chords):
        return "Error"
    for i, tone_str in enumerate(soprano_line):
        note = getscaledegree(tone_str, tonality)
        if i ==0:
            bassline.append('1')
            continue
        elif note == '1' and chords[i] == 'T':
            bassline.append('3')
        elif note == '1' and chords[i] == 'S':
            bassline.append('6')
        elif note == '2':
            bassline.append('7')
        elif note == '3':
            bassline.append('1')
        elif note == '4':
            bassline.append('6')
        elif note == '5' and chords[i] == 'T':
            bassline.append('3')
        elif note == '5' and chords[i] == 'D':
            bassline.append('7')
        elif note == '6':
            bassline.append('4')
        elif note == '7':
            bassline.append('2')
    for i, tone_str in enumerate(bassline):
        bassline[i] = scalestep_to_note(tone_str, tonality, 3)
    bassline = correct_octaves(bassline)
    bassline = correct_low_thirds(bassline, chords, tonality)
    return bassline

def check_for_conflicts(melody_line, altline, tenorline, bassline):
    ziptuples = zip(melody_line, altline, tenorline, bassline)
    laststep = None
    for s, step in enumerate(ziptuples):
        if laststep != None:

            voicemovements = list(zip(step, laststep))
            # offene parallelen und oktaven
            uniques = set(voicemovements)
            if len(uniques) != len(voicemovements):
                print("Unison Parallel or octave at step {}".format(s))
            # offene quinten
            stepdiffs = [note_to_pitch(voice[1])-note_to_pitch(voice[0])
                         for voice in voicemovements]
            for i, diff in enumerate(stepdiffs):
                for i2, diff2 in enumerate(stepdiffs[i+1:]):
                    if diff == diff2 and abs(note_to_pitch(voicemovements[i][0]) - note_to_pitch(voicemovements[i2+1][0])) == 7:
                        print("Unison Fifth at step {}".format(s))
        laststep = step
    pass


def find_tones_between(tone_look, lower_limit, upper_limit, octave_lower, octave_upper, bass_tone, soprano_tone, tonality):
    options = []
    for i in range(octave_lower, octave_upper+1, 1):
        notepitch = note_to_pitch(scalestep_to_note(tone_look, tonality, i))
        if notepitch >= lower_limit and notepitch <= upper_limit:
            options.append(scalestep_to_note(tone_look, tonality, i))
    if len(options) > 1:
        for i, tone_str in enumerate(options):
            if tone_str == bass_tone or tone_str == soprano_tone:
                options.pop(i)
    return options


def gettoneoptions(soprano_tone, bass_tone, tones, tonality):
    lower_limit = note_to_pitch(bass_tone)
    upper_limit = note_to_pitch(soprano_tone)
    octave_lower = int(re.findall('\d', bass_tone)[0])
    octave_upper = int(re.findall('\d', soprano_tone)[0])
    tone1options = find_tones_between(
        tones[0], lower_limit, upper_limit, octave_lower, octave_upper, bass_tone, soprano_tone, tonality)
    tone2options = find_tones_between(
        tones[1], lower_limit, upper_limit, octave_lower, octave_upper, bass_tone, soprano_tone, tonality)
    return tone1options, tone2options


def get_initial_tones(tone1options, tone2options, soprano_tone, bass_tone, tonality):
    pitch_diff = note_to_pitch(soprano_tone) - note_to_pitch(bass_tone)
    if pitch_diff > 24:
        spread = True
    else: 
        spread = False
    soprano_degree = getscaledegree(soprano_tone, tonality)
    pitch_sort_dict = {}
    total_options = tone1options + tone2options
    for tone in total_options:
        pitch_sort_dict[note_to_pitch(tone)] = tone
    sorted_dict = sorted(pitch_sort_dict, reverse=True)
    if spread == True:
        alt_tone = pitch_sort_dict[sorted_dict[1]]
    else:
        alt_tone = pitch_sort_dict[sorted_dict[0]]
    if alt_tone in tone1options:
        for tone in tone1options:
             pitch_sort_dict.pop(note_to_pitch(tone), None)
    else:
        for tone in tone2options:
            pitch_sort_dict.pop(note_to_pitch(tone), None)
    sorted_dict = sorted(pitch_sort_dict, reverse=True)
    if spread == True:    
        ten_tone = pitch_sort_dict[sorted_dict[1]]
    else:
        ten_tone = pitch_sort_dict[sorted_dict[0]]
    return alt_tone, ten_tone



def compose_middlevoicings(soprano_line, bassline, chords, tonality):
    missingharmonies = []
    altline = []
    tenorline = []
    for i, chord in enumerate(chords):
        soprano_degree = getscaledegree(soprano_line[i], tonality)
        bass_degree = getscaledegree(bassline[i], tonality)
        missingtones = list(
            set(chorddict[chord]) - set([soprano_degree, bass_degree]))
        if len(missingtones) == 1:
            missingtones.append(chorddict[chord][0])
        missingharmonies.append(missingtones
                                )
    for i, tones in enumerate(missingharmonies):
        if i == 0:
            tone1options, tone2options = gettoneoptions(
                soprano_line[0], bassline[0], tones, tonality)
            tone1, tone2 = get_initial_tones(tone1options, tone2options, soprano_line[0], bassline[0], tonality)
            altline.append(tone1)
            tenorline.append(tone2)
        else:
            tone1options, tone2options = gettoneoptions(
                soprano_line[i], bassline[i], tones, tonality)
            samelen = len(tone1options) == 1 and len(tone2options) == 1
            if samelen:
                # case priority 1: chord must be filled, one choice
                if note_to_pitch(tone1options[0]) > note_to_pitch(tone2options[0]):
                    altline.append(tone1options[0])
                    tenorline.append(tone2options[0])
                else:
                    altline.append(tone2options[0])
                    tenorline.append(tone1options[0])
            elif tone1options == tone2options and not samelen:
                altline.append(tone1options[1])
                tenorline.append(tone1options[0])
            else:
                # case priority 2: one voice can keep same tone, other one doesn't cross
                alt_in_line = altline[-1] in tone1options + tone2options
                if alt_in_line:
                    option1try = altline[-1]
                    if option1try in tone2options:
                        for option in tone1options:
                            if note_to_pitch(option) < note_to_pitch(option1try):
                                altline.append(option1try)
                                tenorline.append(option)
                                break
                    elif option1try in tone1options:
                        for option in tone2options:
                            if note_to_pitch(option) < note_to_pitch(option1try):
                                altline.append(option1try)
                                tenorline.append(option)
                                break
                elif tenorline[-1] in tone1options + tone2options and not alt_in_line:
                    option1try = tenorline[-1]
                    if option1try in tone2options:
                        for option in tone1options:
                            if note_to_pitch(option) > note_to_pitch(option1try):
                                altline.append(option)
                                tenorline.append(option1try)
                                break
                    elif option1try in tone1options:
                        for option in tone2options:
                            if note_to_pitch(option) > note_to_pitch(option1try):
                                altline.append(option)
                                tenorline.append(option1try)
                                break
                else:
                    altline.append(tone1options[-1])
                    tenorline.append(tone2options[0])
                    logging.info('roughly inplemented tone select case')

    check_for_conflicts(soprano_line, altline, tenorline, bassline)
    return altline, tenorline

def simpleornaments(array, tonality):
    for i in range(1, len(array), 1):
        step1 = int(getscaledegree(array[i], tonality))
        step2 = int(getscaledegree(array[i-1], tonality))
        if abs(step1 - step2) == 2:
            octave1 = int(re.findall('\d', array[i-1])[0])
            octave2 = int(re.findall('\d', array[i])[0])
            if octave1 > octave2:
                octave = octave2
            else:
                octave = octave1
            array[i-1] = [array[i-1], str(scalestep_to_note(str(int((step2 + step1)/2)), tonality, octave))]
    return array

def convert_fit_to_melody(voice, melody):
    return_voice = []
    starttime = 0
    for note_voice, note_melody in zip(voice, melody):
        if isinstance(note_voice, list):
            for note in note_voice:
                return_voice.append(tone(note, int(note_melody.duration*len(note_voice))))
        else:
             return_voice.append(tone(note_voice, int(note_melody.duration))) 
    return return_voice




def arrangement_from_melody(melody, savename):
    const = 15000
    BPM = 90
    PPQ = int(const/BPM)
    beatspermeasure = 4  # beats per measure
    mid = MidiFile(ticks_per_beat=PPQ)
    midtrack = MidiTrack()
    mid.tracks.append(midtrack)

    # TODO:
    # Ranges für Voices definieren und bewegung in Mittelstimmen gering halten, jedoch zwischen äußeren Stimmen.
    range_soprano = ['C5', 'A6']
    range_alt = ['F4', 'D6']
    range_tenor = ['B3', 'G5']
    range_bass = ['E3', 'C5']
    newtrack = track(BPM)
    tonality = 'F-Major'
    midtrack.append(MetaMessage('key_signature', key='F', time=0))
    midtrack.append(MetaMessage('time_signature', numerator=4,
                denominator=4, clocks_per_click=200))
    midtrack.append(MetaMessage('set_tempo', tempo=bpm2tempo(BPM)))

    starttime = 0
    for note in melody:
        newtrack.addnote(note.pitch, starttime, 1/note.duration)
        starttime = starttime + 1/note.duration


    soprano_line = get_notes_of_melody(melody)
    chords = getchords(soprano_line, tonality)

    bassline = composebass(soprano_line, chords, tonality)

    altline, tenorline = compose_middlevoicings(
        soprano_line, bassline, chords, tonality)

    # scaledegrees = elementstolist(scaledegrees)
    altline = simpleornaments(altline, tonality)
    tenorline = simpleornaments(tenorline, tonality)
    bassline = simpleornaments(bassline, tonality)

    newtrack.write_voices_to_midi(melody, altline, tenorline, bassline)
    convert_notedict(newtrack.notedict, midtrack)

    savepath = os.path.join('flask', 'static', 'audio',savename + '.mid')
    mid.save(savepath)
    altline = convert_fit_to_melody(altline, melody)
    tenorline = convert_fit_to_melody(tenorline, melody)
    bassline = convert_fit_to_melody(bassline, melody)

    arranged = arrangement(melody, altline, tenorline, bassline)

    dropdowns = [{'id': 'dropdown1', 'chords': ['F-Major', 'D-Minor'], 'selected': 'F-Major'},
             {'id': 'dropdown2', 'chords': ['F', 'Dm'], 'selected': 'F'},
             {'id': 'dropdown3', 'chords': ['F', 'Bb', 'Dm'], 'selected': 'F'},
             {'id': 'dropdown4', 'chords': ['Bb', 'Dm'], 'selected': 'Bb'},
             {'id': 'dropdown5', 'chords': ['F', 'C'], 'selected': 'F'},
             {'id': 'dropdown6', 'chords': ['Bb', 'Gm'], 'selected': 'Bb'},
             {'id': 'dropdown7', 'chords': ['F', 'Dm'], 'selected': 'F'},
             {'id': 'dropdown8', 'chords': ['C', 'Gm'], 'selected': 'C'}]

    return arranged, dropdowns