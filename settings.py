def getAudioFiles(song, part):
    bg_filename = 'songs/{}/{}-All.wav'.format(song, song)
    part_filename = 'songs/{}/{}-{}.wav'.format(song, song, part)
    return bg_filename, part_filename

def getDisplayFiles(song, part):
    gems_txt = 'songs/{}/{}.txt'.format(song, part)
    barlines_txt = 'songs/{}/barlines.txt'.format(song)
    beats_txt = 'songs/{}/beats.txt'.format(song)
    return gems_txt, barlines_txt, beats_txt
