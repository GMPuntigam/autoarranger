from classes import tone
from utils import arrangement_from_melody


# melody = [['F5', 0, 0.25], ['A5', 0.25, 0.25], ['Bb5', 0.5, 0.25], ['C6', 0.75, 0.25], [
# 'C6', 1, 0.25], ['D6', 1.25, 0.25], ['E6', 1.5, 0.25], ['F6', 1.75, 0.25]]



# melody = [tone('A5', 0, 0.25), tone('F5', 0.25, 0.25), tone('A5', 0.5, 0.25), tone('A5', 0.75, 0.25), tone('Bb5', 1, 0.25), tone('D6', 1.25, 0.25), tone('Bb5', 1.5, 0.25), tone('A5', 1.75, 0.25)]

melody1 = [tone('A5', 4), tone('F5', 2), tone('D6', 4), tone('C6', 2), tone('Bb5', 4), tone('A5', 2), tone('G5', 4)]
melody2 = [tone('C6', 2), tone('Bb5', 4), tone('A5', 4), tone('G5', 2),  tone('C5', 2), tone('D5', 4), tone('E5', 4), tone('F5', 4), tone('A5', 4), tone('G5', 1)]
melody3 = [tone('A5', 4), tone('Bb5', 4), tone('A5', 4), tone('G5', 4), tone('F5', 2), tone('E5', 2), tone('F5', 1)]
melody4 = [tone('F5', 4), tone('A5', 4), tone('C6', 2), tone('D6', 4), tone('C6', 4), tone('Bb5', 2), tone('A5', 2), tone('G5', 1)]


arrangement_from_melody(melody1, "sample1")
arrangement_from_melody(melody2, "sample2")
arrangement_from_melody(melody3, "sample3")
arrangement_from_melody(melody4, "sample4")
