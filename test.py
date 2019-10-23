from midi_reader import midi_reader as mr
from wave_reader import wave_reader as wr
from utils import play_audio,npToBytes

midi_file_path = "path/filename.midi"
wave_file_path = "path/filename.wav"

def read_midi(midi_path):
	mreader = mr(midi_path)
	mreader.normal()
	events = mreader.get_events()
	return events

def read_wav(wave_path):
	wreader = wr(wave_path)
	return wreader

midi_events = read_midi(midi_file_path)
wave_data = read_wav(wave_file_path)

for event in midi_events:
	start = event.start_time
	end = event.end_time
	label = event.note    #pitch label -> event.note
	data = wave_data.cut(start,end) #data[0] and data[1] are left channel and right channel
