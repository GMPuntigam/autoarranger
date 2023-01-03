import abjad
import re
# string = "a'4 f' a' a' bf' d'' bf' a'"
# voice_1 = abjad.Voice(string, name="Voice_1")
# staff_1 = abjad.Staff([voice_1], name="Staff_1")
# abjad.show(staff_1)


def uniform_pitch_to_case_pitch(pitch_str):
    pitch_letter = " ".join(re.findall("[a-zA-Z]+", pitch_str))
    pitch_letter = pitch_letter.replace('b', 'f')
    pitch_letter = pitch_letter.replace('#', 's')
    pitch_letter = pitch_letter.lower() 
    pitch_number = "".join(re.findall("[0-9]", pitch_str))
    pitch_number = str(int(pitch_number)-1)
    if int(pitch_number) < 3:
        pitch_int = 3-int(pitch_number)
        pitch_number = r","*(pitch_int)
    elif int(pitch_number) > 2:
        pitch_int = int(pitch_number)-3
        pitch_number = r"'"*(pitch_int)
    return pitch_letter + pitch_number

def generate_abjad_string(voice):
    steplist = []
    for timestep in voice:
            steplist.append(uniform_pitch_to_case_pitch(timestep.pitch)+str(timestep.duration))
    returnstr = ' '.join(steplist)
    return returnstr



def voices_to_staff(melody, altline, tenorline, bassline, tonality):
    sop_string = generate_abjad_string(melody)
    voice_sop = abjad.Voice(sop_string, name="Soprano")
    voice_alt = abjad.Voice(generate_abjad_string(altline), name="Alt")
    voice_ten = abjad.Voice(generate_abjad_string(tenorline), name="Tenor")
    voice_bas = abjad.Voice(generate_abjad_string(bassline), name="Bass")
    rh_staff = abjad.Staff([voice_sop, voice_alt], name="Treble Clef", simultaneous=True)
    lh_staff = abjad.Staff([voice_ten, voice_bas], name="LH_Voice", simultaneous=True)
    literal = abjad.LilyPondLiteral(r"\voiceOne")
    abjad.attach(literal, voice_sop)
    abjad.attach(literal, voice_ten)
    literal = abjad.LilyPondLiteral(r"\voiceTwo")
    abjad.attach(literal, voice_alt)
    abjad.attach(literal, voice_bas)
    
    staff_group = abjad.StaffGroup(
        [rh_staff, lh_staff],
        lilypond_type="PianoStaff",
        name="Piano_Staff",
    )
    score = abjad.Score([staff_group], name="Score")
    leaf = abjad.select.leaf(score["LH_Voice"], 0)
    clef = abjad.Clef("bass")
    key, mode = tonality.split('-')
    key_signature = abjad.KeySignature(
    abjad.NamedPitchClass(key.lower()), abjad.Mode(mode.lower())
    )
    note = abjad.select.note(rh_staff, 0)
    abjad.attach(key_signature, note)
    note = abjad.select.note(lh_staff, 0)
    abjad.attach(key_signature, note)
    abjad.attach(clef, leaf)
    abjad.show(score)