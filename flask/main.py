from flask import Flask, flash, redirect, render_template, request, url_for
from app.utils.abjad_wrapper import voices_to_staff
from app.utils.classes import tone
from app.musiclogic import arrangement_from_melody, get_dropdowns
from app.generate_css import generate_css
import os


webapp = Flask(__name__)
webapp.debug = True

test_melodies = {
    'sample1' : [tone('A5', 4), tone('F5', 2), tone('D6', 4), tone('C6', 2), tone('Bb5', 4), tone('A5', 2), tone('G5', 4)],
    'sample2' : [tone('C6', 2), tone('Bb5', 4), tone('A5', 4), tone('G5', 2),  tone('C5', 2), tone('D5', 4), tone('E5', 4), tone('F5', 4), tone('A5', 4), tone('G5', 2), tone('G5', 2), tone('F5', 1)],
    'sample3' : [tone('A5', 4), tone('Bb5', 4), tone('A5', 4), tone('G5', 4), tone('F5', 2), tone('E5', 2), tone('F5', 1)],
    'sample4' : [tone('F5', 4), tone('A5', 4), tone('C6', 2), tone('D6', 4), tone('C6', 4), tone('Bb5', 2), tone('A5', 2), tone('G5', 1)]

}
# arrangement_from_melody(melody1, "sample1")
# arrangement_from_melody(melody2, "sample2")
# arrangement_from_melody(melody3, "sample3")
# arrangement_from_melody(melody4, "sample4")



def change_dropdown_selection(dropdowns, selections):
    for i, dropdown in enumerate(dropdowns):
        dropdowns[i]['selected'] = selections[i]
    return dropdowns


@webapp.route('/', methods=['POST', 'GET'])
def dropdown():
    #initial state
    samplename =  "sample1"
    svg_path = 'static\generated_svg\{}.svg'.format(samplename)
    audio_path = r'static\audio\{}.mid'.format(samplename)
    melody = test_melodies[samplename]
    if 'dropdowns' not in globals():
        # generate initially
        global dropdowns
        arrangement =  arrangement_from_melody(melody, samplename)
        dropdowns = get_dropdowns(melody)
        # sometimes generation is too slow, maybe wait
        note_positions = voices_to_staff(arrangement, dropdowns[0]['selected'], samplename)
        css_path = os.path.join('flask','static', 'css', 'dropdowns.css')
        generate_css(note_positions, os.path.abspath(css_path))
        initial_selection = [dropdowns[i]['selected'] for i in range(len(dropdowns))]
        new_selections = initial_selection

    
    if 'selections' not in globals():
        global selections
        selections = initial_selection
    else:
        new_selections = ['new_value']*len(dropdowns)
        for i, dropdown in enumerate(dropdowns):
            select = request.form.get(dropdown['id'])
            new_selections[i] = select
        
    if selections != new_selections:
        arrangement = arrangement_from_melody(melody, samplename, selected_chords = new_selections[1:])
        note_positions = voices_to_staff(arrangement, dropdowns[0]['selected'], samplename)
        css_path = os.path.join('flask','static', 'css', 'dropdowns.css')
        generate_css(note_positions, os.path.abspath(css_path))
        selections = new_selections
        dropdowns = change_dropdown_selection(dropdowns, selections)
    return render_template('index.html', dropdowns=dropdowns, svg=svg_path, audio_path = audio_path)

if __name__ == "__main__":
    webapp.run(debug=True)