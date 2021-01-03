import re
import subprocess
import numpy as np
import pyrubberband as pyrb
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from pydub.utils import make_chunks
from mutagen.mp3 import MP3
from mutagen.id3 import TKEY, TBPM
from easing_functions import QuadEaseIn


def lerp(from_val, to_val, t):
    return from_val * (1 - t) + to_val * t

def apply_effect(audio, effect, from_val, to_val):
    out = AudioSegment.silent(duration=0)
    chunks = make_chunks(audio, 100)
    ease_fn = QuadEaseIn()
    for i, chunk in enumerate(chunks):
        val = lerp(from_val, to_val, ease_fn.ease(i / len(chunks)))
        out += effect(chunk, val)
    return out

def change_tempo(audio, bpm, new_bpm):
    y = np.array(audio.get_array_of_samples())
    if audio.channels == 2:
        y = y.reshape((-1, 2))

    sample_rate = audio.frame_rate

    tempo_ratio = new_bpm / bpm
    y_fast = pyrb.time_stretch(y, sample_rate, tempo_ratio)

    channels = 2 if (y_fast.ndim == 2 and y_fast.shape[1] == 2) else 1
    y = np.int16(y_fast * 2 ** 15)

    new_seg = AudioSegment(y.tobytes(), frame_rate=sample_rate, sample_width=2, channels=channels)
    return new_seg


class Track:
    def __init__(self, filename, bpm=None, leading_silence_ms=None):
        self.filename = filename
        self.audio = AudioSegment.from_mp3(filename) - 6  # subtract some for headroom
        self.metadata = MP3(filename)
        if leading_silence_ms != None:
            self.leading_silence_ms = leading_silence_ms
        else:
            self.leading_silence_ms = self.get_leading_silence()
        if bpm != None:
            self.bpm = bpm
        else:
            self.bpm = self.get_bpm()
        self.key = self.get_key()
        self.title = self.metadata.tags.get('TIT2')
        self.artist = self.metadata.tags.get('TPE1')
        print(f"{self.artist} - {self.title} [{self.key}, {self.bpm}, +{self.leading_silence_ms}]")

    def beats(self, first, last):
        single_beat_ms = 60000.0 / self.bpm
        start_ms = self.leading_silence_ms + single_beat_ms * first
        end_ms = self.leading_silence_ms + single_beat_ms * last
        beats = self.audio[start_ms:end_ms]
        return beats

    def bars(self, first, last):
        single_bar_ms = (60000.0 / self.bpm) * 4
        start_ms = self.leading_silence_ms + single_bar_ms * first
        end_ms = self.leading_silence_ms + single_bar_ms * last
        beats = self.audio[int(start_ms):int(end_ms)]
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

