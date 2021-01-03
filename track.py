import re
import subprocess
import numpy as np
import pyrubberband as pyrb
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from mutagen.mp3 import MP3
from mutagen.id3 import TKEY, TBPM


class Track:
    def __init__(self, filename, leading_silence_ms=None):
        self.filename = filename
        self.audio = AudioSegment.from_mp3(filename)
        self.metadata = MP3(filename)
        if leading_silence_ms != None:
            self.leading_silence_ms = leading_silence_ms
        else:
            self.leading_silence_ms = self.get_leading_silence()
        self.key = self.get_key()
        self.bpm = self.get_bpm()
        self.title = self.metadata.tags.get('TIT2')
        self.artist = self.metadata.tags.get('TPE1')
        print(f"{self.artist} - {self.title} [{self.key}, {self.bpm}, +{self.leading_silence_ms}]")

    def beats(self, first, last):
        single_beat_ms = 60000.0 / self.bpm
        start_ms = self.leading_silence_ms + single_beat_ms * first
        end_ms = self.leading_silence_ms + single_beat_ms * last
        beats = self.audio[start_ms:end_ms]
        return beats

    def get_leading_silence(self):
        return detect_leading_silence(self.audio)

    def get_key(self):
        key = self.metadata.tags.get('TKEY')
        pattern = re.compile("^[0-9]{1,2}[md]$")
        if (key != None and pattern.match(key.text[0])):
            return key.text[0]
        print("Detecting key...")
        new_key = subprocess.check_output(["keyfinder-cli", "-n", "openkey", self.filename]).strip().decode()
        self.metadata.tags.add(TKEY(encoding=3, text=new_key))
        self.metadata.save()
        return new_key

    def get_bpm(self):
        bpm = self.metadata.tags.get('TBPM')
        if (bpm != None):
            return float(bpm.text[0])
        print("Detecting bpm...")
        subprocess.check_output(["bpm-tag", self.filename])
        self.metadata = MP3(self.filename)  # re-read id3 data
        new_bpm = self.metadata.tags.get('TBPM')
        return float(new_bpm.text[0])

    def change_tempo(self, audiosegment, tempo, new_tempo):
        y = np.array(audiosegment.get_array_of_samples())
        if audiosegment.channels == 2:
            y = y.reshape((-1, 2))

        sample_rate = audiosegment.frame_rate

        tempo_ratio = new_tempo / tempo
        print(tempo_ratio)
        y_fast = pyrb.time_stretch(y, sample_rate, tempo_ratio)

        channels = 2 if (y_fast.ndim == 2 and y_fast.shape[1] == 2) else 1
        y = np.int16(y_fast * 2 ** 15)

        new_seg = AudioSegment(y.tobytes(), frame_rate=sample_rate, sample_width=2, channels=channels)

        return new_seg
