import time
from pydub import AudioSegment
from pydub.playback import play
from track import Track

BPM = 128
KEY_NOTATION = 'openkey'
LIBRARY_DIR = "/Users/daveystruijk/Drive/Music"
mix = AudioSegment.silent(duration=0)

not_alone = Track(f"{LIBRARY_DIR}/Techno - Melodic/Time - Not Alone.mp3")
in_the_wild = Track(f"{LIBRARY_DIR}/Techno - Melodic/Dee Montero feat. Meliha - In The Wild.mp3")

# output = sound1.overlay(sound2, position=5000)

mix += not_alone.beats(0, 4)
mix += not_alone.beats(0, 4)
mix += not_alone.beats(0, 4)
mix += not_alone.beats(0, 4)
mix += not_alone.beats(0, 4)
mix += not_alone.beats(0, 4)

play(mix)

while True:
    time.sleep(1)

