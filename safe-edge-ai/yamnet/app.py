import os
os.environ['TFHUB_CACHE_DIR'] = '/app/tfhub_cache'

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import pyaudio
import csv
import scipy.signal
import sys

print("[INFO] Loading YAMNet model...")
model = hub.load('https://tfhub.dev/google/yamnet/1')

class_map_path = model.class_map_path().numpy()
class_names = []
with tf.io.gfile.GFile(class_map_path) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        class_names.append(row['display_name'])

# 오디오 설정
MIC_RATE = 44100
MODEL_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = MIC_RATE

DIGITAL_GAIN = 5.0 

p = pyaudio.PyAudio()

mic_index = None
target_name = "AB13X" 

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if target_name in info['name'] or 'USB' in info['name']:
        mic_index = i
        print(f"[INFO] Monitoring device connected: {info['name']} (Index: {mic_index})")
        break

if mic_index is None:
    print("[WARN] USB microphone not found. Using default device.")

try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=MIC_RATE,
                    input=True, input_device_index=mic_index,
                    frames_per_buffer=CHUNK)
except OSError:
    MIC_RATE = 48000
    CHUNK = 48000
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=MIC_RATE,
                    input=True, input_device_index=mic_index,
                    frames_per_buffer=CHUNK)

print(f"\n[INFO] Abnormal noise monitoring system running (Gain: x{DIGITAL_GAIN})")
print("[INFO] Waiting for acoustic events...\n")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        waveform = np.frombuffer(data, dtype=np.int16) / 32768.0
        
        waveform = waveform * DIGITAL_GAIN
        waveform = np.clip(waveform, -1.0, 1.0) 

        number_of_samples = round(len(waveform) * float(MODEL_RATE) / MIC_RATE)
        waveform_resampled = scipy.signal.resample(waveform, number_of_samples)
        
        scores, embeddings, spectrogram = model(waveform_resampled)
        prediction = np.mean(scores, axis=0)
        
        top_index = np.argmax(prediction)
        top_name = class_names[top_index]
        confidence = prediction[top_index]

        IGNORE_LIST = ['Silence', 'Speech', 'Inside, small room']

        if top_name in IGNORE_LIST:
            sys.stdout.write(".") 
            sys.stdout.flush()
        else:
            if confidence > 0.2:
                # 심플하게 이벤트와 신뢰도만 출력
                print(f"\n[DETECTED] Event: {top_name} | Confidence: {confidence*100:.1f}%")
            else:
                sys.stdout.write(".")
                sys.stdout.flush()

except KeyboardInterrupt:
    print("\n[INFO] System shutdown.")
    stream.stop_stream()
    stream.close()
    p.terminate()