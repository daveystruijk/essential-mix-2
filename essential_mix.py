import time
from pydub import AudioSegment, effects, scipy_effects
from pydub.playback import play
from track import Track, change_tempo, apply_effect

BPM = 128
KEY_NOTATION = 'openkey'
LIBRARY_DIR = "/Users/daveystruijk/Drive/Music"
mix = AudioSegment.silent(duration=0)

not_alone = Track(f"{LIBRARY_DIR}/Techno - Melodic/Time - Not Alone.mp3", bpm=120.0)
in_the_wild = Track(f"{LIBRARY_DIR}/Techno - Melodic/Dee Montero feat. Meliha - In The Wild.mp3")

# mix += not_alone.bars(0, 32)
not_alone_sync = apply_effect(change_tempo(not_alone.bars(160, 160+32), not_alone.bpm, in_the_wild.bpm), scipy_effects.high_pass_filter, 0.1, 10000)
in_the_wild_sync = apply_effect(in_the_wild.bars(16, 16+32), scipy_effects.high_pass_filter, 10000, 0.1)
mix += not_alone_sync.overlay(in_the_wild_sync)
mix += in_the_wild.bars(48, 64)
#output = sound1.overlay()

#mix = effects.normalize(mix)
play(mix)
mix.export("./output.wav", format="wav")

while True:
    time.sleep(1)

