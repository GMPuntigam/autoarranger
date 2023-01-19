from mido import Message, bpm2tempo
import re
import os
import logging
from mido import MidiFile, MidiTrack, MetaMessage, bpm2tempo
try:
    from app.utils.classes import tone, arrangement
except:
    from utils.classes import tone, arrangement

functiondict = {'1': 'T', '2': 'D', '3': 'T',
                '4': 'S', '5': 'T/D', '6': 'S', '7': 'D'}

chorddict = {'1': ['1', '3', '5'], 
             '2': ['2', '4', '6'], 
             '3': ['3', '5', '7'], 
             '4': ['4', '6', '1'], 
             '5': ['5', '7', '2'],
             '6': ['6', '1', '3'], 
             '7': ['7', '2', '4'], }

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


def get_tonelist(tonality_gender, tonality_base):
    if tonality_gender == 'Major':
        if tonality_base in ['G', 'D', 'A', 'E', 'B', 'F#']:
            tone_list = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']    
        if tonality_base in ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']:
            tone_list = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
    return tone_list

def functions_to_chords(function_chords, key):
    tonality_base, tonality_gender = key.split('-')
    tone_list = get_tonelist(tonality_gender, tonality_base)
    tone_index = tone_list.index(tonality_base)
    return_chords = []
    for functions_chord in function_chords:
        if functions_chord == 'T':
            return_chords.append(tonality_base)
        elif functions_chord == 'S':
            return_chords.append(tone_list[(tone_index+5)%12])
        elif functions_chord == 'D':
            return_chords.append(tone_list[tone_index-5])    
    return return_chords


def get_all_possible_chords(melody, key):
    tonality_base, tonality_gender = key.split('-')
    tone_list = get_tonelist(tonality_gender, tonality_base)
    tone_index = tone_list.index(tonality_base)

    step_to_possible_chords = {
        '1': [tonality_base, tone_list[tone_index-3] + 'm', tone_list[(tone_index+5)%12]],
        '2': [tone_list[(tone_index+2)%12] + 'm', tone_list[tone_index-5], tone_list[tone_index-1] + 'dim'],
        '3': [tonality_base, tone_list[(tone_index+4)%12] + 'm', tone_list[tone_index-3] + 'm'],
        '4': [tone_list[(tone_index+5)%12], tone_list[(tone_index+2)%12] + 'm', tone_list[tone_index-2]],
        '5': [tonality_base, tone_list[tone_index-5], tone_list[(tone_index+4)%12] + 'm'],
        '6': [tone_list[(tone_index+2)%12] + 'm', tone_list[tone_index-3] + 'm', tone_list[(tone_index+5)%12]],
        '7': [tone_list[tone_index-5], tone_list[(tone_index+4)%12] + 'm']
    }
    chordoptions = []
    for tone in melody:
        scalestep = getscaledegree(tone.pitch, key)
        chordoptions.append(step_to_possible_chords[scalestep])
    return chordoptions




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
    basetone = re.findall('(.+?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)

    if tonality_base in ['G', 'D', 'A', 'E', 'B', 'F#']:
        letter = step_to_note_sharps[(scale_major[step]+basepitch) % 12]
    if tonality_base in ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']:
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
    basetone = re.findall('(.+?(?=-.*))', tonality)[0] + '0'
    basepitch = note_to_pitch(basetone)
    relative_pitch = (note_to_pitch(tone_str) - basepitch) % 12
    return scale_major_tone_to_step[relative_pitch]

def getscaledegree_chord(chord, tonality):
    if chord[-1] == 'm':
        chord = chord[:-1]
    tone_str = chord + '1'
    return getscaledegree(tone_str, tonality)



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
        elif pitch_diff > 8:
            line[i] = tone_str + str(int(octave)-1)
        elif pitch_diff < -8:
            line[i] = tone_str + str(int(octave)+1)
    return line

def correct_low_thirds(bassline, chords, tonality):
    for i, tone_str in enumerate(bassline):
        chord = chords[i]
        chord_step = getscaledegree_chord(chord, tonality)
        note = getscaledegree(tone_str, tonality)
        if note_to_pitch(tone_str) < note_to_pitch('G3'):
            if chorddict[chord_step][1] == note:
                # bass is on third of chord
                option1 = scalestep_to_note(chorddict[chord_step][0], tonality, 3)
                option2 = scalestep_to_note(chorddict[chord_step][0], tonality, 4)
                if abs(note_to_pitch(bassline[i-1]) - note_to_pitch(option1)) <  abs(note_to_pitch(bassline[i-1]) - note_to_pitch(option2)):
                    bassline[i] = option1
                else:
                    bassline[i] = option2
    return bassline


def composebass(soprano_line, chords, tonality):
    bassline = []
    if len(soprano_line) != len(chords):
        print("Error: Soprano line length doesn\'t match chord line length")
        return 'Error'
    for i, tone_str in enumerate(soprano_line):
        note = getscaledegree(tone_str, tonality)
        chord_on_scale = getscaledegree_chord(chords[i], tonality)
        if note == '1': 
            if chord_on_scale == '1':
                if i == 1 or i ==len(soprano_line)-1:
                    bassline.append('1')
                else:
                    bassline.append('3')
                continue
            if chord_on_scale == '6':
                bassline.append('3')
                continue
            if chord_on_scale == '4':
                bassline.append('6')
                continue
        if note == '2':
            if chord_on_scale == '5':
                bassline.append('7')
                continue
            if chord_on_scale == '2':
                bassline.append('4')
                continue
            if chord_on_scale == '7':
                bassline.append('7')
                continue
        if note == '3':
            if chord_on_scale == '1':
                bassline.append('1')
                continue
            if chord_on_scale == '3':
                bassline.append('5')
                continue
            if chord_on_scale == '6':
                bassline.append('1')
                continue
        if note == '4':
            if chord_on_scale == '4':
                bassline.append('6')
                continue
            if chord_on_scale == '6':
                bassline.append('6')
                continue
            if chord_on_scale == '2':
                bassline.append('2')
                continue
        if note == '5':
            if chord_on_scale == '1':
                bassline.append('3')
                continue
            if chord_on_scale == '5':
                bassline.append('7')
                continue
            if chord_on_scale == '3':
                bassline.append('3')
                continue
        if note == '6':
            if chord_on_scale == '4':
                bassline.append('4')
                continue
            if chord_on_scale == '6':
                bassline.append('1')
                continue
            if chord_on_scale == '2':
                bassline.append('4')
                continue
        if note == '7':
            if chord_on_scale == '5':
                bassline.append('5')
                continue
            if chord_on_scale == '3':
                bassline.append('5')
                continue
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
    if tone1options == tone2options:
        alt_tone = tone1options[1]
        ten_tone = tone1options[0]
        return alt_tone, ten_tone
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


def get_missing_tones(soprano_degree, bass_degree, chord, chorddict):
    return list(set(chorddict[chord]) - set([soprano_degree, bass_degree]))


def get_second_voice_options(voice1tone, second_voice_options):
    return_voice_options = second_voice_options.copy()
    voice1tone_str = re.findall('[A-Z]b?#?', voice1tone)[0]
    for option2 in return_voice_options:
        if voice1tone_str in option2:
            return_voice_options.pop(return_voice_options.index(option2))
    return return_voice_options
    


def compose_middlevoicings(soprano_line, bassline, chords, tonality):
    missingharmonies = []
    altline = []
    tenorline = []
    for i, chord in enumerate(chords):
        soprano_degree = getscaledegree(soprano_line[i], tonality)
        bass_degree = getscaledegree(bassline[i], tonality)
        chord_on_scale = getscaledegree_chord(chord, tonality)
        missingtones = get_missing_tones(soprano_degree, bass_degree, chord_on_scale, chorddict)
        if len(missingtones) == 1:
            missingtones.append(chorddict[chord_on_scale][0])
        missingharmonies.append(missingtones
                                )
    for i, tones in enumerate(missingharmonies):
        if i == 0:
            tone1options, tone2options = gettoneoptions(
                soprano_line[0], bassline[0], tones, tonality)
            tone1, tone2 = get_initial_tones(tone1options, tone2options, soprano_line[0], bassline[0], tonality)
            altline.append(tone1)
            tenorline.append(tone2)
            continue
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
            continue
        if tone1options == tone2options and not samelen:
            altline.append(tone1options[1])
            tenorline.append(tone1options[0])
            continue
        # new rule to develop: no low thirds in tenor
        chord_on_scale = getscaledegree_chord(chords[i], tonality)
        chord_tones = chorddict[chord_on_scale]
        # check if first tone is third of chord
        tenoroptions = tone1options + tone2options
        altoptions = tone1options + tone2options
        to_pop = []
        for option in tenoroptions:
            # print('checking {} in {}'.format(option, tenoroptions))
            if getscaledegree(option, tonality) == chord_tones[1] and note_to_pitch(option) < note_to_pitch('C4'):
                to_pop.append(option)
                #print('avoiding thirds in the tenor, removed {}'.format(option))
                continue
            if abs(note_to_pitch(option) - note_to_pitch(bassline[i])) > 12:
                to_pop.append(option)
                #print('avoiding too large gaps in tenor and bass voice, removed {}'.format(option))
        for option in to_pop:
            tenoroptions.pop(tenoroptions.index(option))
        to_pop = []
        for option in altoptions:
            # print('checking {} in {}'.format(option, altoptions))
            if note_to_pitch(option) < note_to_pitch('A4'):
                to_pop.append(option)
                #print('avoiding low tones in the alt, removed {}'.format(option))
                continue    
            if abs(note_to_pitch(option) - note_to_pitch(soprano_line[i])) > 12:
                to_pop.append(option)
                #print('avoiding too large gaps in soprano and alt voice, removed {}'.format(option))
        for option in to_pop:
            altoptions.pop(altoptions.index(option))
        if len(altoptions) == 1 and len(tenoroptions) == 1:
            altline.append(altoptions[0])
            tenorline.append(tenoroptions[0])
            #print('selected tones by exclusion')
            continue
        # case priority 2: one voice can keep same tone, other one doesn't cross
        alt_in_line = altline[-1] in altoptions
        tenor_in_line = tenorline[-1] in tenoroptions
        appended = False
        if len(altoptions) == 1:
            tenoroptions = get_second_voice_options(altoptions[0], tenoroptions)
        elif len(tenoroptions) == 1:
            altoptions = get_second_voice_options(tenoroptions[0], altoptions)
        if alt_in_line:
            option1try = altline[-1]
            options_second_voice = get_second_voice_options(option1try, tenoroptions)
            for option in options_second_voice:
                if note_to_pitch(option) > note_to_pitch(option1try):
                    options_second_voice.pop(options_second_voice.index(option))
            if len(options_second_voice) > 0:
                for option in options_second_voice:
                    smallest_step = 12
                    if (note_to_pitch(option) - note_to_pitch(tenorline[-1])) < smallest_step:
                        smallest_step = note_to_pitch(option) - note_to_pitch(tenorline[-1])
                        selected_option = option
                    altline.append(option1try)
                    tenorline.append(selected_option)
                    appended = True
                    break
        if tenor_in_line and not alt_in_line:
            option1try = tenorline[-1]
            options_second_voice = get_second_voice_options(option1try, altoptions)
            for option in options_second_voice:
                if note_to_pitch(option) < note_to_pitch(option1try):
                    options_second_voice.pop(options_second_voice.index(option))
            if len(options_second_voice) > 0:
                for option in options_second_voice:
                    smallest_step = 12
                    if (note_to_pitch(option) - note_to_pitch(altline[-1])) < smallest_step:
                        smallest_step = note_to_pitch(option) - note_to_pitch(altline[-1])
                        selected_option = option
                    tenorline.append(option1try)
                    altline.append(selected_option)
                    appended = True
                    break
        if not appended:
            #prefer the 5th in tenor
            selected_tenor = None
            if len(tenoroptions) >1:
                for option in tenoroptions:
                    if getscaledegree(option, tonality) == chord_tones[2]:
                        selected_tenor = option
                        break
            if selected_tenor != None:
                options_second_voice = get_second_voice_options(selected_tenor, altoptions)
                for option in options_second_voice:
                    smallest_step = 12
                    if (note_to_pitch(option) - note_to_pitch(altline[-1])) < smallest_step:
                        smallest_step = note_to_pitch(option) - note_to_pitch(altline[-1])
                        selected_option = option
                tenorline.append(selected_tenor)
                altline.append(selected_option)
                continue      
            altline.append(altoptions[0])
            tenorline.append(tenoroptions[0])    
            print('roughly inplemented tone select case')
            print(altoptions)
            print(tenoroptions)
    check_for_conflicts(soprano_line, altline, tenorline, bassline)
    return altline, tenorline

def simpleornaments(array, tonality):
    for i in range(1, len(array), 1):
        step1 = int(getscaledegree(array[i], tonality))
        step2 = int(getscaledegree(array[i-1], tonality))
        if abs(step1 - step2) == 2:
            octave1 = int(re.findall('\d', array[i-1])[0])
            octave2 = int(re.findall('\d', array[i])[0])
            # wonky because of C
            if octave1 > octave2:
                octave = octave2
                tone = str(scalestep_to_note(str(int((step2 + step1)/2)), tonality, octave))
                tone_str = re.findall('[A-Z]b?#?', tone)[0]
                if tone_str == 'C':
                    octave = octave+1
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

def generate_scale(tonality):
    tone_list = get_tonelist(tonality_gender = 'Major', tonality_base=tonality)
    tone_index = tone_list.index(tonality)
    scale = []
    for key in scale_major.keys():
        scale.append(tone_list[(tone_index+scale_major[key])%12])
    return scale

def detect_key(melody):
    sharp_keys = ['G', 'D', 'A', 'E', 'B', 'F#']
    flat_keys = ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']
    notes = get_notes_of_melody(melody)
    tone_strs = [re.findall('[A-Z]b?#?', note_string)[0] for note_string in notes]
    possible_keys = []
    for tonality_base in sharp_keys + flat_keys:
        scale = generate_scale(tonality_base)
        if set(tone_strs).issubset(set(scale)):
            possible_keys.append(tonality_base + '-Major')
    return possible_keys


def arrangement_from_melody(melody, savename, selected_chords = None, selected_key = None):
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
    possible_keys = detect_key(melody)
    if selected_key == None:
        tonality = possible_keys[0]
    else:
        tonality = selected_key
    tonality_base = tonality.split('-')[0]
    midtrack.append(MetaMessage('key_signature', key=tonality_base, time=0))
    midtrack.append(MetaMessage('time_signature', numerator=4,
                denominator=4, clocks_per_click=200))
    midtrack.append(MetaMessage('set_tempo', tempo=bpm2tempo(BPM)))

    starttime = 0
    for note in melody:
        newtrack.addnote(note.pitch, starttime, 1/note.duration)
        starttime = starttime + 1/note.duration

    soprano_line = get_notes_of_melody(melody)
    if selected_chords == None:
        chords = getchords(soprano_line, tonality)
        selected_chords = functions_to_chords(chords, tonality)
    bassline = composebass(soprano_line, selected_chords, tonality)

    altline, tenorline = compose_middlevoicings(
        soprano_line, bassline, selected_chords, tonality)

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

    arranged = arrangement(melody, altline, tenorline, bassline, possible_keys)

    return arranged


def get_dropdowns(melody, possible_keys, tonality = None):
    if tonality == None:
        tonality = possible_keys[0]
    soprano_line = get_notes_of_melody(melody)
    chordoptions = get_all_possible_chords(melody, tonality)
    chords = getchords(soprano_line, tonality)
    selected_chords = functions_to_chords(chords, tonality)
    dropdowns = [{'id': 'dropdown{}'.format(i+2), 'chords': chordoptions[i], 'selected': selected_chord} for i, selected_chord in enumerate(selected_chords)]
    dropdowns = [{'id': 'dropdown1', 'chords': possible_keys, 'selected': tonality}] + dropdowns
    return dropdowns

if __name__ == "__main__":
    # for debugging
    melody = [tone('C6', 2), tone('Bb5', 4), tone('A5', 4), tone('G5', 2),  tone('C5', 2), tone('D5', 4), tone('E5', 4), tone('F5', 4), tone('A5', 4), tone('G5', 1)]
    samplename =  "sample2"
    selected_chords = ['F', 'Gm', 'Dm', 'Cm', 'F', 'G', 'C', 'Dm', 'F', 'C']
    arrangement_from_melody(melody, samplename, selected_chords)