class tone():
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration

class arrangement:
    def __init__(self, soprano, alt, tenor, bass, possible_keys):
        self.soprano = soprano
        self.alt = alt
        self.tenor = tenor
        self.bass = bass
        self.possible_keys = possible_keys
