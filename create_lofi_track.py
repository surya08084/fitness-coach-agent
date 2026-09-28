import math
import wave
import struct
import numpy as np

def generate_lofi_audio(filename="scratch/lofi_beat.wav", duration_sec=35.0, sample_rate=44100):
    num_samples = int(duration_sec * sample_rate)
    audio = np.zeros(num_samples, dtype=np.float32)
    
    bpm = 84
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    
    # Time array
    t_full = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # 1. Chords: Cmaj7 - Am7 - Dm7 - G7
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [293.66, 349.23, 440.00, 523.25],  # Dm7
        [196.00, 246.94, 293.66, 349.23],  # G7
    ]
    
    chord_len_samples = int(bar_dur * sample_rate)
    
    for i in range(num_samples):
        t = t_full[i]
        bar_idx = int(t / bar_dur)
        chord = chords[bar_idx % len(chords)]
        
        # Position within bar
        t_in_bar = t % bar_dur
        
        # Strum / chord trigger on beat 1 and 3
        chord_val = 0.0
        for freq in chord:
            # Vibrato / Tremolo LFO
            lfo = 1.0 + 0.15 * math.sin(2 * math.pi * 5.0 * t)
            # Soft organ/epiano tone (fundamental + gentle 2nd harmonic)
            note = (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)) * lfo
            # Envelope: decay across 2 beats
            env = math.exp(-1.5 * (t_in_bar % (beat_dur * 2)))
            chord_val += note * env
            
        audio[i] += chord_val * 0.12

    # 2. Drums: Kick, Snare, Hi-Hat
    rng = np.random.RandomState(42)
    for sample_i in range(num_samples):
        t = t_full[sample_i]
        beat_pos = (t % bar_dur) / beat_dur
        
        # Kick on 0 and 2.5
        dist_kick1 = min(abs(beat_pos - 0), abs(beat_pos - 4))
        dist_kick2 = abs(beat_pos - 2.5)
        kick_trig = min(dist_kick1, dist_kick2)
        if kick_trig < 0.2:
            dt = kick_trig * beat_dur
            freq_env = 110 * math.exp(-30 * dt) + 45
            amp_env = math.exp(-15 * dt)
            audio[sample_i] += 0.45 * math.sin(2 * math.pi * freq_env * dt) * amp_env
            
        # Snare on 1 and 3
        dist_snare = min(abs(beat_pos - 1.0), abs(beat_pos - 3.0))
        if dist_snare < 0.15:
            dt = dist_snare * beat_dur
            noise = rng.uniform(-1, 1)
            tone = math.sin(2 * math.pi * 180 * dt)
            env = math.exp(-22 * dt)
            audio[sample_i] += 0.25 * (noise * 0.7 + tone * 0.3) * env

        # Hi-hat every 0.5 beats (8th notes)
        hat_pos = (beat_pos % 0.5)
        if hat_pos < 0.08:
            dt = hat_pos * beat_dur
            noise = rng.uniform(-1, 1)
            env = math.exp(-60 * dt)
            audio[sample_i] += 0.08 * noise * env

    # Low-pass filter smoothing (Lo-fi warmth)
    smoothed = np.zeros_like(audio)
    alpha = 0.25
    for i in range(1, num_samples):
        smoothed[i] = alpha * audio[i] + (1 - alpha) * smoothed[i - 1]

    # Normalize to -1..1
    max_val = np.max(np.abs(smoothed))
    if max_val > 0:
        smoothed = smoothed / max_val * 0.85

    # Write WAV file
    int_data = (smoothed * 32767).astype(np.int16)
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_data.tobytes())

    print(f"Generated lo-fi beat track: {filename} ({duration_sec}s)")

if __name__ == "__main__":
    import os
    os.makedirs("scratch", exist_ok=True)
    generate_lofi_audio()
