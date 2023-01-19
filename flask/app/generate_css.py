import os

def generate_css(note_positions, css_path):
    css_text = ''
    for i, percent in enumerate(note_positions[0:-1]): 
        percent = "{:.2f}".format(percent)
        css_text = css_text + 'div#dropdown{}'.format(i+1) +  '{\n    left: ' + '{}%;\n    position: absolute;\n    max-width: fit-content;\n'.format(percent) + '}\n'
    percent = "{:.2f}".format(note_positions[-1])
    i = i+1
    css_text = css_text + 'div#dropdown{}'.format(i+1) +  '{\n    left: ' + '{}%;\n    position: relative;\n    max-width: fit-content;\n'.format(percent) + '}\n'
    with open(css_path, "w") as text_file:
        text_file.write(css_text)