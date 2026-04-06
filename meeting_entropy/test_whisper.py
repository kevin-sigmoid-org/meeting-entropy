import numpy as np, pyaudio
from faster_whisper import WhisperModel
from pathlib import Path

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=1, frames_per_buffer=1024)
print('Parle pendant 3 sec...')
frames = [stream.read(1024) for _ in range(46)]
stream.stop_stream(); stream.close(); p.terminate()

data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
print(f'Audio shape: {data.shape}, max: {np.max(np.abs(data)):.4f}')

model_dir = Path.home() / '.meeting-entropy' / 'models' / 'small'
print(f'Model path: {model_dir}')
print(f'Model exists: {model_dir.exists()}')
model = WhisperModel(str(model_dir), device='auto', compute_type='default')
segments, info = model.transcribe(data, language='fr', beam_size=5)
segments_list = list(segments)
print(f'Language: {info.language}, prob: {info.language_probability:.2f}')
print(f'Segments: {len(segments_list)}')
for s in segments_list:
    print(f'  [{s.start:.1f}-{s.end:.1f}] {s.text}')