from collections import Counter
import re
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
import pypianoroll
import matplotlib.pyplot as plt
import numpy as np
import logging

const = 15000
BPM = 90
PPQ = int(const/BPM)
beatspermeasure = 4  # beats per measure
# PPQ = 163
mid = MidiFile(ticks_per_beat=PPQ)
track = MidiTrack()
mid.tracks.append(track)

# TODO:
# Achteldurchgänge ( über listen pro Zeitschritt)
# Ranges für Voices definieren und bewegung in Mittelstimmen gering halten, jedoch zwischen äußeren Stimmen.

range_soprano = ['C5', 'A6']
range_alt = ['F4', 'D6']
range_tenor = ['B3', 'G5']
range_bass = ['E3', 'C5']

notedict = {}
tonality = 'F-Major'
# melody = [['F5', 0, 0.25], ['A5', 0.25, 0.25], ['Bb5', 0.5, 0.25], ['C6', 0.75, 0.25], [
# 'C6', 1, 0.25], ['D6', 1.25, 0.25], ['E6', 1.5, 0.25], ['F6', 1.75, 0.25]]
melody = [['A5', 0, 0.25], ['F5', 0.25, 0.25], ['A5', 0.5, 0.25], ['A5', 0.75, 0.25], [
    'Bb5', 1, 0.25], ['D6', 1.25, 0.25], ['Bb5', 1.5, 0.25], ['A5', 1.75, 0.25]]

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


track.append(MetaMessage('key_signature', key='F', time=0))
track.append(MetaMessage('time_signature', numerator=4,
             denominator=4, clocks_per_click=200))
track.append(MetaMessage('set_tempo', tempo=bpm2tempo(BPM)))


def convert_notedict(notes):
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
    tone = re.findall('[A-Z]b?#?', note_string)[0]
    octave = int(re.findall('\d+', note_string)[0])
    return letter_to_note[tone] + octave * 12


def scalestep_to_note(step, tonality, baseoctave):
    tonality_base = tonality.split('-')[0]
    basetone = re.findall('(.?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)

    if tonality_base in ['G', 'D', 'A', 'E', 'H,' 'F#']:
        letter = step_to_note_sharps[(scale_major[step]+basepitch) % 12]
    if tonality_base in ['F', 'Bb', 'Eb', 'Ab', 'Db,' 'Gb']:
        letter = step_to_note_flats[(scale_major[step]+basepitch) % 12]
    if int(step) > 1:
        return letter + str(baseoctave + 1)
    else:
        return letter + str(baseoctave)


def addnote(note, start_val, duration_val, veloticy_param=100):
    duration = int(60000/(BPM) * duration_val)
    start = int(60000/(BPM) * start_val)
    if isinstance(note, str):
        pitch = note_to_pitch(note)
    elif not isinstance(note, int):
        pitch = int(note)
    else:
        pitch = note
    if start not in notedict.keys():
        notedict[start] = [{'event': 'note_on',
                            'pitch': pitch, 'velocity': veloticy_param}]
    else:
        notedict[start].append({'event': 'note_on',
                                'pitch': pitch, 'velocity': veloticy_param})
    if start + duration not in notedict.keys():
        notedict[start + duration] = [{'event': 'note_off',
                                       'pitch': pitch, 'velocity': veloticy_param}]
    else:
        notedict[start + duration].append({'event': 'note_off',
                                           'pitch': pitch, 'velocity': veloticy_param})


def getscaledegree(tone, tonality):
    basetone = re.findall('(.?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)
    relative_pitch = (note_to_pitch(tone) - basepitch) % 12
    return scale_major_tone_to_step[relative_pitch]


def get_notes_of_melody(melody):
    steplist = []
    for tone in melody:
        steplist.append(tone[0])
    return steplist


def getchords(scalesteps, tonality):
    chordlist = []
    for note in scalesteps:
        chordlist.append(functiondict[getscaledegree(note, tonality)])
    for i in range(len(chordlist)-1, 0, -1):
        if chordlist[i] == 'T/D':
            if chordlist[i+1] == 'S':
                chordlist[i] = 'T'
            if chordlist[i+1] == 'T' and chordlist[i-1] != 'D':
                chordlist[i] = 'D'
    return chordlist


def correct_octaves(line):
    for i in range(1, len(line), 1):
        pitch_diff = note_to_pitch(line[i]) - note_to_pitch(line[i-1])
        octave = re.findall('\d', line[i])[0]
        tone = line[i].replace(octave, '')
        if line[i] == line[i-1]:
            if abs(note_to_pitch(line[i]) - note_to_pitch(line[i+1])) > abs(note_to_pitch(tone + str(int(octave)+1)) - note_to_pitch(line[i+1])):
                line[i] = tone + str(int(octave)+1)
            elif abs(note_to_pitch(line[i]) - note_to_pitch(line[i+1])) > abs(note_to_pitch(tone + str(int(octave)-1)) - note_to_pitch(line[i+1])):
                line[i] = tone + str(int(octave)-1)
        elif pitch_diff > 12:
            line[i] = tone + str(int(octave)-1)
        elif pitch_diff < -12:
            line[i] = tone + str(int(octave)+1)
    return line


def composebass(soprano_line, chords, tonality):
    bassline = []
    if len(soprano_line) != len(chords):
        return "Error"
    for i, tone in enumerate(soprano_line):
        note = getscaledegree(tone, tonality)
        if note == '1' or note == '3':
            bassline.append('1')
        elif note == '2':
            bassline.append('7')
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
    for i, tone in enumerate(bassline):
        bassline[i] = scalestep_to_note(tone, tonality, 3)
    bassline = correct_octaves(bassline)
    return bassline


def unrolltimestep(timestep, start, duration):
    if len(timestep) == 1:
        pitch = note_to_pitch(timestep[0])
        addnote(pitch, start, duration)
    else:
        for i, step in enumerate(timestep):
            subedevide_start = start + duration/len(timestep)*i
            duration_devided = duration/len(timestep)
            unrolltimestep(step, subedevide_start, duration_devided)


def write_voices_to_midi(melody, altline, tenorline, bassline):

    for i, note in enumerate(bassline):
        unrolltimestep(note, melody[i][1], melody[i][2])
    for i, note in enumerate(altline):
        unrolltimestep(note, melody[i][1], melody[i][2])
    for i, note in enumerate(tenorline):
        unrolltimestep(note, melody[i][1], melody[i][2])


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
        for i, tone in enumerate(options):
            if tone == bass_tone or tone == soprano_tone:
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
            # useful?
            if chord == 'S':
                missingtones.append('6')
            else:
                missingtones.append(chorddict[chord][0])
        missingharmonies.append(missingtones
                                )
    for i, tones in enumerate(missingharmonies):
        if i == 0:
            tone1 = scalestep_to_note(tones[1], tonality, 3)
            tone2 = scalestep_to_note(tones[0], tonality, 4)
            altline.append(tone2)
            tenorline.append(tone1)
        else:
            if i == 3:
                print('debug')
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
                alt_in_line = altline[i-1] in tone1options + tone2options
                if alt_in_line:
                    option1try = altline[i-1]
                    for option in tone2options:
                        if note_to_pitch(option) < note_to_pitch(option1try):
                            altline.append(option1try)
                            tenorline.append(option)
                            break
                elif tenorline[i-1] in tone1options + tone2options and not alt_in_line:
                    option1try = tenorline[i-1]
                    for option in tone2options:
                        if note_to_pitch(option) > note_to_pitch(option1try):
                            altline.append(option)
                            tenorline.append(option1try)
                            break
                else:
                    logging.warning('Not implemented tone select case')

    check_for_conflicts(soprano_line, altline, tenorline, bassline)
    return altline, tenorline


for note in melody:
    addnote(note[0], note[1], note[2])


soprano_line = get_notes_of_melody(melody)
chords = getchords(soprano_line, tonality)

bassline = composebass(soprano_line, chords, tonality)

altline, tenorline = compose_middlevoicings(
    soprano_line, bassline, chords, tonality)


def elementstolist(array):
    array = [[x] if not isinstance(x, list) else x for x in array]
    return array


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
            array[i-1] = [[array[i-1]],
                          [str(scalestep_to_note(str(int((step2 + step1)/2)), tonality, octave-1))]]
    return array


# scaledegrees = elementstolist(scaledegrees)
altline = simpleornaments(altline, tonality)
tenorline = simpleornaments(tenorline, tonality)
bassline = simpleornaments(bassline, tonality)

soprano_line = elementstolist(soprano_line)
altline = elementstolist(altline)
tenorline = elementstolist(tenorline)
bassline = elementstolist(bassline)

write_voices_to_midi(melody, altline, tenorline, bassline)
convert_notedict(notedict)
savepath = r'I:\code\Local-Github-Repos\Autoarranger\new_song.mid'
mid.save(savepath)

multitrack = pypianoroll.read(savepath)
print(multitrack)
# multitrack.binarize()
img = multitrack.plot()
plt.show()
