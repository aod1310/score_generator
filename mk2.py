import pyaudio, wave
import librosa, librosa.display
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.animation import FuncAnimation
import numpy as np
import sys, os, time
import librosa, librosa.display
from PyQt5 import QtCore as qtcore
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sheet as st

form_class = uic.loadUiType("./ui.ui")[0]

# timer variable
h=0
m=0
ms=0
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 오디오스트림을 위한 변수 선언
        self.frames = []
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100
        self.CHANNEL = 1
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=self.FORMAT,
                                   channels=self.CHANNEL,
                                   rate=self.RATE,
                                   input=True,
                                   output=True,
                                   input_device_index=1,
                                   stream_callback=self.callback)  # 1=mic, #2=stereomix, #3=ux1
        # 악보객체를 위한 변수
        self.music_sheet = None
        # 그래프를 그리기 위한 변수 선언
        self.t = np.arange(0, self.CHUNK * 100)
        self.sample = np.zeros([102400])
        self.freq = np.fft.rfftfreq(1024, 1 / self.RATE)
        self.spec = np.zeros([1024], dtype=complex)
        self.fig = plt.figure()
        self.canvas = Canvas(self.fig)
        self.plot = self.fig.add_subplot(111, xlim=(0, 3500), ylim=(0, 800000))
        self.graph, = self.plot.plot([], [])
        self.plot.axes.get_xaxis().set_visible(False)
        self.plot.axes.get_yaxis().set_visible(False)
        self.canvas.draw()
        self.ani = FuncAnimation(self.canvas.figure, self.graph_update, frames=50, interval=20, repeat=True)
        self.QV_plot.addWidget(self.canvas)

        # 스톱워치관련
        self.timer = qtcore.QTimer()
        self.stopwatch_reset()
        self.timer.timeout.connect(self.stopwatch_run)
        # 시그널 연결
        self.pbtn_start.clicked.connect(self.start_recording)
        self.pbtn_stop.clicked.connect(self.stop_recording)
        self.pbtn_save.clicked.connect(self.show_sheet_musescore)
        self.pbtn_midi.clicked.connect(self.play_sheet_MIDI)
        self.pbtn_play.clicked.connect(self.play_recoded_wav)
        self.pbtn_pause.clicked.connect(self.pause_recorded_wav)
        # ui기본설정
        self.pbtn_play.setEnabled(False)
        self.pbtn_save.setEnabled(False)
        self.pbtn_midi.setEnabled(False)
        self.pbtn_stop.setEnabled(False)
        self.pbtn_pause.setEnabled(False)
        self.pbtn_start.setStyleSheet('QPushButton {color: red;}')
        #button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')

    def callback(self, in_data, frame_count, time_info, flag):
        self.frames.append(in_data)
        in_data = np.fromstring(in_data, np.int16)
        for i in np.arange(99, 0, -1):
            self.sample[i * 1024:(i + 1) * 1024] = self.sample[(i - 1) * 1024:i * 1024]
        self.sample[0:1024] = in_data
        # fft
        self.spec = np.fft.rfft(self.sample[0:1024])
        #self.graph_update(self.sample)
        #self.canvas.draw()
        return (in_data, pyaudio.paContinue)

    def graph_update(self, sample):
        self.graph.set_data(self.freq, self.spec)
        self.canvas.draw()
        return True

    def graph_init(self):
        return self.graph,

    def start_recording(self):
        self.frames = []
        print('** recording **')
        self.pbtn_stop.setEnabled(True)
        self.pbtn_start.setEnabled(False)
        self.pbtn_play.setEnabled(False)
        self.pbtn_save.setEnabled(False)
        self.pbtn_midi.setEnabled(False)
        self.pbtn_pause.setEnabled(False)
        self.stopwatch_reset()
        self.stopwatch_start()
        self.stream.start_stream()

        return self

    def stop_recording(self):
        self.stream.stop_stream()
        self.pbtn_stop.setEnabled(False)
        self.pbtn_start.setEnabled(True)
        self.pbtn_play.setEnabled(True)
        self.pbtn_save.setEnabled(True)
        self.pbtn_midi.setEnabled(True)
        self.pbtn_pause.setEnabled(True)
        wf = wave.open('./temp.wav', 'wb')
        wf.setnchannels(self.CHANNEL)
        wf.setsampwidth(self.pa.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print('** done recording **')
        self.stopwatch_reset()
        #self.frames.clear()
        self.get_sheet()
        return self

    # 스톱워치 초기화
    def stopwatch_reset(self):
        global m, s, ms
        m = 0
        s = 0
        ms = 0
        self.timer.stop()

        start_time = "{0:02d}:{1:02d}.{2:02d}".format(m, s, ms)
        self.lcd_timer.setDigitCount(len(start_time))
        self.lcd_timer.display(start_time)

    # 스톱워치 시작
    def stopwatch_start(self):
        self.timer.start(10)   # 0.01초단위

    # 스톱워치 구현
    def stopwatch_run(self):
        global m, s, ms

        if ms < 99:
            ms += 1
        else:
            if s < 59:
                ms = 0
                s += 1
            elif s == 59 and m < 4:   # 녹음길이 최대 4분
                m += 1
                s = 0
                ms = 0
            else:
                self.stopwatch_reset()
                self.stop_recording()

        time = "{0:02d}:{1:02d}.{2:02d}".format(m, s, ms)
        self.lcd_timer.setDigitCount(len(time))
        self.lcd_timer.display(time)

    def get_sheet(self):
        y, sr = st.read_wav('temp.wav')
        onset_boundaries = st.get_onsetboundaries(y, sr)

        chords = []
        for i in range(len(onset_boundaries) - 1):
            p0 = onset_boundaries[i]
            p1 = onset_boundaries[i + 1]
            pitch = st.get_pitch(y[p0:p1], sr)
            chords.append([p for p in pitch])

        # test music sheet
        times = st.set_duration(librosa.samples_to_time(onset_boundaries, sr=sr))
        self.music_sheet = st.init_stream()
        for notes, length in zip(chords, times):
            #if notes == []:
            #    continue
            if notes == []:
                n = st.set_rest(length)
                self.music_sheet.append(n)
                continue
            n = st.set_chrod(notes)
            n.quarterLength = length
            self.music_sheet.append(n)

    def show_sheet_musescore(self):
        self.music_sheet.show()

    def play_sheet_MIDI(self):
        self.music_sheet.show('midi')

    def play_recoded_wav(self):
        self.wf = wave.open('temp.wav', 'rb')
        self.play_pa = pyaudio.PyAudio()
        self.play_stream = self.play_pa.open(format=self.play_pa.get_format_from_width(self.wf.getsampwidth()),
                         channels=self.wf.getnchannels(),
                         rate=self.wf.getframerate(),
                         output=True,
                         stream_callback=self.play)
        self.stopwatch_reset()
        self.stopwatch_start()
        self.pbtn_pause.setEnabled(True)
        self.pbtn_play.setEnabled(False)
        #data = wf.readframes(self.CHUNK)
        #while data:
        #    stream.write(data)
        #    data = wf.readframes(self.CHUNK)
        #stream.stop_stream()
        self.play_stream.start_stream()
        #while stream.is_active():
        #    time.sleep(0.1)
        #stream.stop_stream()
        #self.wf.close()
        #stream.close()
        #pa.terminate()
        #self.stopwatch_reset()

        return self

    def pause_recorded_wav(self):
        if not self.play_stream.is_stopped():
            self.pbtn_pause.setText('PLAY')
            self.play_stream.stop_stream()
            self.timer.stop()
        else:
            self.pbtn_pause.setText('PAUSE')
            self.play_stream.start_stream()
            self.timer.start()
        return self

    def play(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)

        if data == b'':
            self.pbtn_pause.setEnabled(False)
            self.pbtn_play.setEnabled(True)
            self.timer.stop()
            self.wf.close()
        else:
            data = np.fromstring(data, np.int16)
            self.sample[0:1024] = data
            self.spec = np.fft.rfft(self.sample[0:1024])

        return (data, pyaudio.paContinue)

    def closeEvent(self, e):
        if os.path.exists('temp.wav'):
            os.remove('temp.wav')
        else:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
