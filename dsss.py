"""
DSSS (Direct Sequence Spread Spectrum) Audio Steganography

This module provides a class-based implementation of the DSSS algorithm
for embedding and extracting hidden messages in audio files.

Reference:
    Nugraha, Rizky M. "Implementation of Direct Sequence Spread Spectrum 
    Steganography on Audio Data." ICEEI 2011.
"""

import numpy as np
from scipy.signal import convolve
from scipy.signal.windows import hann


class DSSSteganography:
    """
    Direct Sequence Spread Spectrum (DSSS) Audio Steganography.
    
    This class implements the DSSS technique for hiding secret messages
    in audio signals. The message is spread across the audio using a
    spreading sequence, making it imperceptible to human listeners.
    
    Attributes:
        alpha (float): Embedding strength (default: 0.005 = 0.5%)
        min_segment_length (int): Minimum samples per bit (default: 8192)
        smoothing_window (int): Hann window size for smooth transitions (default: 256)
    
    Example:
        >>> dsss = DSSSteganography()
        >>> watermarked = dsss.encode(audio_data, "Hello World")
        >>> decoded = dsss.decode(watermarked, message_length=11)
        >>> print(decoded)  # "Hello World"
    """
    
    def __init__(self, alpha: float = 0.005, min_segment_length: int = 8192, 
                 smoothing_window: int = 256):
        """
        Initialize the DSSS steganography encoder/decoder.
        
        Args:
            alpha: Embedding strength (0.001 to 0.01 recommended).
                   Higher = more robust but more audible.
            min_segment_length: Minimum audio samples per embedded bit.
            smoothing_window: Hann window size for smoothing bit transitions.
        """
        self.alpha = alpha
        self.min_segment_length = min_segment_length
        self.smoothing_window = smoothing_window
    
    # ==================== Public Methods ====================
    
    def encode(self, audio: np.ndarray, message: str) -> np.ndarray:
        """
        Encode a secret message into an audio signal.
        
        Args:
            audio: Input audio signal as 1D numpy array (mono).
                   Values should be in range [-1.0, 1.0].
            message: Text message to embed.
        
        Returns:
            Watermarked audio signal (same shape as input).
        
        Raises:
            ValueError: If audio is too short to embed the message.
        """
        bits = self._text_to_bits(message)
        return self._encode_bits(audio, bits)
    
    def decode(self, audio: np.ndarray, message_length: int) -> str:
        """
        Decode a secret message from a watermarked audio signal.
        
        Args:
            audio: Watermarked audio signal as 1D numpy array.
            message_length: Number of characters in the original message.
        
        Returns:
            Decoded text message.
        """
        bit_length = message_length * 8  # 8 bits per character
        bits = self._decode_bits(audio, bit_length)
        return self._bits_to_text(bits)
    
    def encode_bits(self, audio: np.ndarray, bits: list) -> np.ndarray:
        """
        Encode raw bits into an audio signal.
        
        Args:
            audio: Input audio signal as 1D numpy array.
            bits: List of bits [0, 1, 1, 0, ...] to embed.
        
        Returns:
            Watermarked audio signal.
        """
        return self._encode_bits(audio, bits)
    
    def decode_bits(self, audio: np.ndarray, bit_length: int) -> list:
        """
        Decode raw bits from a watermarked audio signal.
        
        Args:
            audio: Watermarked audio signal.
            bit_length: Number of bits to extract.
        
        Returns:
            List of decoded bits [0, 1, 1, 0, ...].
        """
        return self._decode_bits(audio, bit_length)
    
    def get_capacity(self, audio_length: int) -> int:
        """
        Calculate the maximum number of characters that can be embedded.
        
        Args:
            audio_length: Number of samples in the audio.
        
        Returns:
            Maximum message length in characters.
        """
        L = self.min_segment_length
        nframe = np.floor(audio_length / L)
        N = int(nframe - np.mod(nframe, 8))
        return N // 8  # 8 bits per character
    
    # ==================== Text Conversion ====================
    
    @staticmethod
    def _text_to_bits(text: str) -> list:
        """Convert text string to list of bits (8 bits per character)."""
        bits = []
        for char in text:
            char_bits = [int(b) for b in format(ord(char), '08b')]
            bits.extend(char_bits)
        return bits
    
    @staticmethod
    def _bits_to_text(bits: list) -> str:
        """Convert list of bits back to text string."""
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) == 8:
                char_code = int(''.join(str(b) for b in byte), 2)
                if 0 < char_code < 128:  # Valid ASCII
                    chars.append(chr(char_code))
        return ''.join(chars)
    
    # ==================== Core Algorithm ====================
    
    def _mixer(self, L: int, bits: list) -> np.ndarray:
        """
        Create smoothed watermark signal from bits.
        
        Uses Hann window convolution to create smooth transitions
        between bit segments, avoiding audible clicks.
        
        Args:
            L: Segment length (samples per bit).
            bits: List of bits to convert.
        
        Returns:
            Smoothed signal array in range [-1, +1].
        """
        K = self.smoothing_window
        
        # Adjust K if segment is too short
        if 2 * K > L:
            K = int(np.floor(L / 4) - np.mod(np.floor(L / 4), 4))
        else:
            K = int(K - np.mod(K, 4))
        
        N = len(bits)
        encbit = np.asarray(bits)
        
        # Create rectangular signal: each bit repeated L times
        m_sig = np.transpose(np.ones((L, 1)) * encbit)
        m_sig = m_sig.reshape((N * L))
        
        # Convolve with Hann window to smooth transitions
        c = convolve(m_sig, hann(K))
        
        # Trim edges and normalize
        wnorm_left = int(K / 2)
        wnorm_right = int(len(c) - K / 2 + 1)
        wnorm = c[wnorm_left:wnorm_right] / np.max(np.abs(c))
        
        # Scale to range [-1, +1]
        return wnorm * 2 - 1
    
    def _encode_bits(self, audio: np.ndarray, bits: list) -> np.ndarray:
        """
        Core encoding algorithm: embed bits into audio using DSSS.
        
        Algorithm:
        1. Divide audio into N segments of L samples each
        2. Generate spreading sequence (pseudo-noise)
        3. Create smoothed watermark signal from bits
        4. Add watermark to audio: output = audio + (watermark × α)
        """
        L_min = self.min_segment_length
        
        # Calculate segment parameters
        L2 = np.floor(len(audio) / len(bits))
        L = int(max(L_min, L2))
        nframe = np.floor(len(audio) / L)
        N = int(nframe - np.mod(nframe, 8))  # Multiple of 8
        
        # Validate audio length
        min_samples = L_min * 8
        if N == 0 or len(audio) < min_samples:
            raise ValueError(
                f"Audio too short! Need at least {min_samples} samples "
                f"(~{min_samples/48000:.1f}s at 48kHz), got {len(audio)}."
            )
        
        # Prepare bits (pad or truncate to N)
        prepared_bits = bits[:N] if len(bits) > N else (bits + [0] * N)[:N]
        
        # Generate spreading sequence (PN sequence - simplified as all 1s)
        spreading_seq = np.ones((L,))
        full_spreading = np.tile(spreading_seq, N)
        
        # Create smoothed watermark signal
        watermark = self._mixer(L, prepared_bits)
        
        # Embed: add scaled watermark to audio
        watermarked = audio[:N * L] + watermark * full_spreading * self.alpha
        
        # Append unchanged tail
        return np.concatenate((watermarked, audio[N * L:]))
    
    def _decode_bits(self, audio: np.ndarray, bit_length: int) -> list:
        """
        Core decoding algorithm: extract bits from watermarked audio.
        
        Algorithm:
        1. Divide audio into segments (same as encoding)
        2. Correlate each segment with spreading sequence
        3. Threshold: correlation > 0 → bit=1, else bit=0
        """
        L_min = self.min_segment_length
        
        # Calculate segment parameters (must match encoding)
        L2 = np.floor(len(audio) / bit_length)
        L = int(max(L_min, L2))
        nframe = np.floor(len(audio) / L)
        N = int(nframe - np.mod(nframe, 8))
        
        # Reshape audio into segments (L samples × N segments)
        segments = audio[:N * L].reshape(N, L).T
        
        # Generate same spreading sequence
        spreading_seq = np.ones((L,))
        
        # Correlate: dot product with spreading sequence
        correlation = np.dot(spreading_seq, segments) / L
        
        # Threshold to recover bits
        decoded = (correlation > 0).astype(int)
        
        return decoded[:bit_length].tolist()


# ==================== Convenience Functions ====================

def encode_message(audio: np.ndarray, message: str, alpha: float = 0.005) -> np.ndarray:
    """
    Convenience function to encode a message into audio.
    
    Args:
        audio: Input audio signal (1D numpy array).
        message: Text message to embed.
        alpha: Embedding strength (default: 0.005).
    
    Returns:
        Watermarked audio signal.
    """
    dsss = DSSSteganography(alpha=alpha)
    return dsss.encode(audio, message)


def decode_message(audio: np.ndarray, message_length: int) -> str:
    """
    Convenience function to decode a message from audio.
    
    Args:
        audio: Watermarked audio signal.
        message_length: Number of characters in the message.
    
    Returns:
        Decoded text message.
    """
    dsss = DSSSteganography()
    return dsss.decode(audio, message_length)
