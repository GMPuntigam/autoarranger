from flask import Flask, flash, redirect, render_template, request, url_for
from app.utils.abjad_wrapper import voices_to_staff
from app.utils.classes import tone
from app.musiclogic import arrangement_from_melody


webapp = Flask(__name__)
webapp.debug = True

melody1 = [tone('A5', 4), tone('F5', 2), tone('D6', 4), tone('C6', 2), tone('Bb5', 4), tone('A5', 2), tone('G5', 4)]
melody2 = [tone('C6', 2), tone('Bb5', 4), tone('A5', 4), tone('G5', 2),  tone('C5', 2), tone('D5', 4), tone('E5', 4), tone('F5', 4), tone('A5', 4), tone('G5', 1)]
melody3 = [tone('A5', 4), tone('Bb5', 4), tone('A5', 4), tone('G5', 4), tone('F5', 2), tone('E5', 2), tone('F5', 1)]
melody4 = [tone('F5', 4), tone('A5', 4), tone('C6', 2), tone('D6', 4), tone('C6', 4), tone('Bb5', 2), tone('A5', 2), tone('G5', 1)]


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
    if 'dropdowns' not in globals():
        # generate initially
        global dropdowns
        arrangement, dropdowns = arrangement_from_melody(melody1, samplename)
        note_positions = voices_to_staff(arrangement, dropdowns[0]['selected'], samplename)
    new_selections = []
    for dropdown in dropdowns:
        select = request.form.get(dropdown['id'])
        new_selections.append(select)
        if 'selections' not in globals():
            global selections
            selections = new_selections
    if selections != new_selections:
        print('A chord has been changed. A new Arrangement would be generated.')
        selections = new_selections
    dropdowns = change_dropdown_selection(dropdowns, selections)
    print(str(selections))
    return render_template('index.html', dropdowns=dropdowns)

if __name__ == "__main__":
    webapp.run(debug=True)