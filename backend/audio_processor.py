import librosa
import soundfile as sf
import numpy as np
from scipy import signal

class AudioProcessor:
    """Handles audio processing like tempo adjustment and effects."""
    
    def __init__(self, audio_path, sr=22050):
        """
        Load audio file.
        
        Args:
            audio_path (str): Path to audio file
            sr (int): Sample rate
        """
        self.audio, self.sr = librosa.load(audio_path, sr=sr)
        self.original_audio = self.audio.copy()
    
    def adjust_tempo(self, tempo_factor):
        """
        Change tempo without affecting pitch.
        
        Args:
            tempo_factor (float): 0.5 = half speed, 1.0 = normal, 2.0 = double speed
        
        Returns:
            np.ndarray: Time-stretched audio
        """
        if tempo_factor == 1.0:
            return self.audio
        return librosa.effects.time_stretch(self.audio, rate=tempo_factor)
    
    def add_reverb(self, room_scale=0.5):
        """
        Add simple reverb effect using convolution.
        
        Args:
            room_scale (float): 0.0-1.0, higher = more reverb
        
        Returns:
            np.ndarray: Audio with reverb
        """
        if room_scale == 0.0:
            return self.audio
        
        # Create a simple impulse response
        impulse_length = int(self.sr * room_scale)
        impulse = np.zeros(impulse_length)
        impulse[0] = 1.0
        
        # Add decaying reflections
        for i in range(1, impulse_length):
            impulse[i] = impulse[i-1] * 0.97 * (1 - room_scale)
        
        # Convolve with audio
        wet = signal.fftconvolve(self.audio, impulse, mode='same')
        
        # Mix dry and wet signals
        mix = (self.audio * (1 - room_scale * 0.5)) + (wet * (room_scale * 0.5))
        return mix / np.max(np.abs(mix))  # Normalize
    
    def adjust_volume(self, gain_db):
        """
        Adjust volume in decibels.
        
        Args:
            gain_db (float): Gain in dB (-20 to +20)
        
        Returns:
            np.ndarray: Volume-adjusted audio
        """
        if gain_db == 0:
            return self.audio
        
        gain_linear = 10 ** (gain_db / 20)
        return np.clip(self.audio * gain_linear, -1, 1)
    
    def process(self, tempo=1.0, reverb=0.0, volume=0):
        """
        Apply all processing in sequence.
        
        Args:
            tempo (float): Tempo adjustment factor
            reverb (float): Reverb amount (0.0-1.0)
            volume (float): Volume adjustment in dB
        
        Returns:
            np.ndarray: Processed audio
        """
        audio = self.adjust_tempo(tempo)
        audio = librosa.to_mono(audio.reshape(1, -1)) if audio.ndim > 1 else audio
        
        # Temporarily replace self.audio for reverb processing
        original = self.audio
        self.audio = audio
        audio = self.add_reverb(reverb)
        audio = self.adjust_volume(volume)
        self.audio = original
        
        return audio