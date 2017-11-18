from music21 import *
import numpy as np
import os

'''
This method returns a dict mapping part name to dicts, each of which contains a list of midi pitches in order for buttons, a list of note pitches (by button list index), a list of note durations (in seconds), and a list of note starting times (in seconds).
'''
def parse_XML(fname, tempo):
    s = converter.parse(fname)
    data = {}
    song = fname.split('.')[0]
    if not os.path.exists('../songs/'+song):
        os.makedirs('../songs/'+song)

    parts = []

    # figure out how to get tempo ideally

    for part in s.getElementsByClass(["Part"]):
        num_measures = 0
        pitches = []
        durations = []
        times = []
        parts.append(part.partName + '\n')

        for m in part.getElementsByClass(["Measure"]):
            num_measures += 1
            for note in m.getElementsByClass(["Note"]):
                pitches.append(note.pitch.midi)
                times.append(60./tempo*(m.offset+note.offset))
                durations.append(60./tempo*(note.duration.quarterLength))
        pitches = np.array(pitches).astype(int)
        buttons = np.unique(pitches)
        pitches = [int(np.where(buttons==pitch)[0]) for pitch in pitches]
        f = open('../songs/'+song + '/' +part.partName+'.txt', 'w')
        f.write(' '.join(map(str,buttons))+'\n')
        for i in range(len(pitches)):
            f.write('\t'.join(map(str,[times[i], durations[i], pitches[i]]))+'\n')
        f.close()
        part.write('midi', fp='../songs/'+song+'/'+part.partName+'.midi')
    b = open('../songs/'+song+'/barlines.txt', 'w')
    b.writelines([str(x*240./tempo) + '\n' for x in range(num_measures)])
    b.close()
    t = open('../songs/'+song+'/beats.txt', 'w')
    t.writelines([str(x*60./tempo) + '\n' for x in range(4*num_measures)])
    t.close()
    p = open('../songs/'+song+'/parts.txt', 'w')
    p.writelines(parts)
    p.close()

    
parse_XML('wdik.xml', 115)

#output first line is midi notes, next lines are time, duration, lane, syllable 
#output partName.txt, partName.midi, all.midi, barlines.txt
