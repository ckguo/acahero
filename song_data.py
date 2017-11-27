# holds data for gems and barlines.
class SongData(object):
    def __init__(self):
        super(SongData, self).__init__()
        self.gem_data = {}
        self.barline_data = []
        self.lanes = []
        self.beat_data = []

    # read the gems and song data. You may want to add a secondary filepath
    # argument if your barline data is stored in a different txt file.
    def read_data(self, gemFile, barlineFile, beatFile):
    # TODO: figure out how gem and barline data should be accessed...
        gems = open(gemFile, 'r').readlines()
        barlines = open(barlineFile, 'r').readlines()
        beats = open(beatFile, 'r').readlines()

        for i, gem in enumerate(gems):
            if (i==0):
                self.lanes = [int(x) for x in gem.split(" ")]
                continue

            time, duration, lane, lyric = gem.split("\t")
            lyric = lyric.strip()
            if lyric == "None":
                lyric = "-"
            self.gem_data.setdefault(int(lane), []).append((float(time), float(duration), lyric))

        for barline in barlines:
            time = barline.strip()
            self.barline_data.append(float(time))

        for beat in beats:
            time = beat.strip()
            self.beat_data.append(float(time))

        return self.lanes, self.gem_data, self.barline_data, self.beat_data
