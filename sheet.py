import librosa, librosa.display
import matplotlib.pyplot as plt
import scipy.signal as sig
import numpy as np
from music21 import *
import scipy.signal as sg

def read_wav(filename):
    y, sr = librosa.load(filename, sr=22050)
    return y, sr

def get_onsetboundaries(y, sr=22050):
    tempo, beat_times = librosa.beat.beat_track(y, sr=sr, start_bpm=60, units='time')
    hop_length = 300
    onset_samples = librosa.onset.onset_detect(y, sr=sr, units='samples', hop_length=hop_length, backtrack=False,
                                               pre_max=15, post_max=8, pre_avg=90, post_avg=90, delta=0.15,
                                               wait=1)
    onset_boundaries = np.concatenate([[0], onset_samples, [len(y)]])
    return onset_boundaries

def get_pitch(section, sr):
    section = sg.medfilt(section)
    C = np.abs(librosa.cqt(section, sr=sr, norm=1))
    s = []
    for c in C:
        if np.log(sum(c)**2) < 5:
            s.append(0)
        else:
            s.append(sum(c)**2)
    s = np.array(s)
    #print(s)
    indexes = convert_to_pitch(librosa.util.peak_pick(s, pre_max=11, post_max=16, pre_avg=90, post_avg=90, delta=0.2, wait=1))
    return indexes


def convert_to_pitch(chords):
    note = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    notes = []
    for o in range(1, 8):
        for n in note:
            pitch = n + str(o)
            notes.append(pitch)
    result = []
    for c in chords:
        result.append(notes[int(c)])
    return result


def set_duration(ob):   # 맵핑을 어떻게하지?... 0.5, 0.25 등에 맞출 수 있는..
    duration_able = [(1/2)**n for n in range(0, 10)]
    duration_able.append(2)
    duration_able.append(4)
    times = [2*(ob[point+1]-ob[point]) for point in range(len(ob)-1)]
    near = None
    for i, t in enumerate(times):
        m = 9999
        for t_d in duration_able:
            if abs(t-t_d) < m:
                m = abs(t-t_d)
                near = t_d
        times[i] = near
    return times

def init_stream():
    return stream.Stream()

def set_chrod(notes):
    return chord.Chord(notes)

def set_rest(length):
    return note.Rest(quaterLength=length)
'''
# get_pitch() test
test = []
y, sr = read_wav('./aqe.wav')
onset_boundaries = get_onsetboundaries(read_wav('./aqe.wav'))

for i in range(len(onset_boundaries)-1):
    p0 = onset_boundaries[i]
    p1 = onset_boundaries[i+1]
    pitch = get_pitch(y[p0:p1], sr)
    test.append([p for p in pitch])


# test music sheet
times = set_duration(librosa.samples_to_time(onset_boundaries, sr=sr))
print(times)
music_sheet = stream.Stream()
for notes, length in zip(test, times):
    n = chord.Chord(notes)
    n.quarterLength = length
    music_sheet.append(n)


music_sheet.show()
'''


def get_sheet():
    y, sr = read_wav('doremi.wav')
    onset_boundaries = get_onsetboundaries(y, sr)

    chords = []
    for i in range(len(onset_boundaries) - 1):
        p0 = onset_boundaries[i]
        p1 = onset_boundaries[i + 1]
        pitch = get_pitch(y[p0:p1], sr)
        chords.append([p for p in pitch])

    # test music sheet
    times = set_duration(librosa.samples_to_time(onset_boundaries, sr=sr))
    music_sheet = init_stream()
    for notes, length in zip(chords, times):
        n = set_chrod(notes)
        n.quarterLength = length
        music_sheet.append(n)

    music_sheet.show('midi')



if __name__ =='__main__':
    get_sheet()