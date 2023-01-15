from nicegui import ui

ui.label('Hello NiceGUI!')
ui.add_static_files('/generated_svg', 'generated_svg')
ui.image('generated_svg/TestPng_backup.svg').style('height: 10%')
select1 = ui.select(['C', "am"], value="C").style('margin-top: 20%')
ui.run()

