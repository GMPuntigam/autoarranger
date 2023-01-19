import abjad
import re
import os
from app.utils.svg_utils import crop_svg, get_notepositions
import time

def uniform_pitch_to_case_pitch(pitch_str):
    pitch_letter = " ".join(re.findall("[a-zA-Z#]+", pitch_str))
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



def voices_to_staff(arrangement, tonality, save_render_path):
    sop_string = generate_abjad_string(arrangement.soprano)
    voice_sop = abjad.Voice(sop_string, name="Soprano")
    voice_alt = abjad.Voice(generate_abjad_string(arrangement.alt), name="Alt")
    voice_ten = abjad.Voice(generate_abjad_string(arrangement.tenor), name="Tenor")
    voice_bas = abjad.Voice(generate_abjad_string(arrangement.bass), name="Bass")
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
    # abjad.show(score)
    savepath_temp = os.path.join('generated',save_render_path + '.svg')
    savepath_final = os.path.join('flask', 'static', 'generated_svg',save_render_path + '.svg')
    filepath = abjad.persist.as_svg(score, savepath_temp)
    dir_name = os.path.dirname(savepath_temp)
    test = os.listdir(dir_name)
    time.sleep(0.5)
    for item in test:
        if item.endswith(".ly"):
            os.remove(os.path.join(dir_name, item))

    with open(savepath_temp, 'r') as f:
        contents = f.read()
    with open(savepath_temp, 'w') as f:
        re_pattern = r'<g(?<=<g).+?(?=<\/g>)<\/g>'
        g_tags = re.findall(re_pattern, contents, flags=re.DOTALL)
        new_contents = contents
        for tag_str in g_tags:
            if 'lilypond' in tag_str:
                new_contents = new_contents.replace(tag_str, '')
        f.write(new_contents)

    crop_svg(savepath_temp, savepath_final)
    
    os.remove(savepath_temp)
    note_positions = get_notepositions(savepath_final)
    # print('SVG-File: {}, Positions: {}'.format(savepath_final, note_positions))
    return note_positions