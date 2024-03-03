import wave
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

#fname = '1PPS_at_antenna_input_SDRSharp_20240221_204831Z_162000000Hz_IQ.wav'
fname = '1PPS_at_ADC_Input_SDRSharp_20240221_213050Z_161864000Hz_IQ.wav'

#wav = wave.open(fname,mode='rb')

#numframes = wav.getnframes()
#frames = wav.readframes(numframes)

data, samplerate = sf.read(fname, dtype='float32')

print(len(data))
data_array = np.array(data)
left_data = data_array[:,0]
right_data = data_array[:,1]
mag_data = np.sqrt(left_data**2 + right_data**2)

pulse = np.ones(int(samplerate*.1))
pulse = mag_data[260578:720074]

#cor = np.correlate(mag_data,pulse)
xcor = signal.correlate(mag_data,pulse,mode='full')
pulse[0] = 100
pulse[1] = 100
print(pulse)

print(len(xcor))
print(samplerate)
print(len(data)/samplerate)

print(mag_data)

x = np.linspace(0, len(data), len(data))

fig, ax = plt.subplots()
ax.plot(xcor)
#ax.plot(x, mag_data)
plt.show()