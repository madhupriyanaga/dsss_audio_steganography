# DSSS Audio Steganography

Hide secret messages in audio files using Direct Sequence Spread Spectrum.

```
██████╗ ███████╗███████╗███████╗
██╔══██╗██╔════╝██╔════╝██╔════╝
██║  ██║███████╗███████╗███████╗
██║  ██║╚════██║╚════██║╚════██║
██████╔╝███████║███████║███████║
╚═════╝ ╚══════╝╚══════╝╚══════╝
Audio Steganography Tool
```

---

## Quick Start

### 1. Setup

```bash
cd DSSS-Audio-Steganography
pip install -r requirements.txt
```

### 2. Add Your Audio

Place your WAV files in the `input/` folder.

### 3. Run the App

**Option A: Web UI (Recommended)**
```bash
python app.py
```
Opens at: http://127.0.0.1:7860

**Option B: Command Line**
```bash
python main.py encode "song.wav" "Hello Alice."
python main.py decode "watermarked_song.wav" 12
```

---

## Web UI Features

| Tab | Features |
|-----|----------|
| 🔒 **Encode** | Upload/select audio → Enter message → Encode → Play both audios |
| 🔓 **Decode** | Select watermarked file → Enter original message → Compare → ✅ Match |

**Run:** `python app.py` → http://127.0.0.1:7860

---

## Installation

### Requirements
- Python 3.8+
- Dependencies: numpy, scipy, soundfile, gradio

### Install
```bash
pip install -r requirements.txt
```

### Project Structure
```
DSSS-Audio-Steganography/
├── app.py               # Web UI (Gradio)
├── main.py              # Command-line interface
├── dsss.py              # DSSS algorithm (class-based)
├── requirements.txt     # Dependencies
├── README.md            # This file
├── input/               # Put your WAV files here
└── output/              # Watermarked files saved here
```

---

## Usage Guide

### Web UI (Recommended)

```bash
python app.py
```

Opens a browser at http://127.0.0.1:7860 with:

**🔒 Encode Tab:**
1. Upload a WAV file OR select from `input/` folder
2. Enter your secret message
3. Click **Encode Message**
4. Listen to original vs watermarked audio
5. File saved to `output/` folder

**🔓 Decode Tab:**
1. Select watermarked file from `output/` folder
2. Enter the original message (for comparison)
3. Click **Decode & Compare**
4. See decoded message and ✅ match status

### CLI Commands

| Command | Description |
|---------|-------------|
| `encode` | Embed a secret message into audio |
| `decode` | Extract a message from watermarked audio |
| `info` | Show audio file info and embedding capacity |
| `list` | List available audio files |

### Encode Examples

```bash
# Basic usage
python main.py encode "song.wav" "Hello Alice."

# With custom output filename
python main.py encode "song.wav" "Secret" --output "my_secret.wav"

# With custom embedding strength (0.001-0.01)
python main.py encode "song.wav" "Hidden" --strength 0.008
```

### Decode Examples

```bash
# Decode from output folder
python main.py decode "watermarked_song.wav" 12

# Decode with known message length
python main.py decode "my_secret.wav" 6
```

### Info & List

```bash
# Check capacity of an audio file
python main.py info "song.wav"

# List all available files
python main.py list
```

### Python API

```python
from dsss import DSSSteganography
import soundfile as sf

# Load audio
audio, sr = sf.read("input/song.wav", dtype='float32')
if audio.ndim == 2:
    audio = audio[:, 0]  # Use first channel if stereo

# Encode
dsss = DSSSteganography(alpha=0.005)
watermarked = dsss.encode(audio, "Hello World")
sf.write("output/watermarked.wav", watermarked, sr)

# Decode
decoded = dsss.decode(watermarked, message_length=11)
print(decoded)  # "Hello World"
```

---

## Table of Contents
1. [Overview](#overview)
2. [Algorithm Explanation (Theory)](#algorithm-explanation-theory)
3. [Code Walkthrough](#code-walkthrough)
4. [Project Structure](#project-structure)
5. [Usage](#usage)

---

## Overview

**DSSS (Direct Sequence Spread Spectrum)** is a watermarking technique that hides secret data in audio by:
- **Spreading** each bit across thousands of audio samples
- **Adding** the spread signal at very low amplitude (imperceptible)
- **Recovering** the bits by correlating with the same spreading pattern

### Why DSSS Works
- The watermark energy is spread across many samples → **hard to detect**
- Low amplitude (0.5% of signal) → **inaudible to humans**
- Correlation-based decoding → **robust to some noise**

---

## Algorithm Explanation (Theory)

### ENCODING (Embedding the Message)

#### Step 1: Convert Text to Binary
```
"Hi" → H=72, i=105 → [01001000, 01101001] → [0,1,0,0,1,0,0,0,0,1,1,0,1,0,0,1]
```
Each character becomes 8 bits (ASCII).

#### Step 2: Divide Audio into Segments
```
Audio: [s₀, s₁, s₂, ..., sₙ]  (millions of samples)
                ↓
Divide into N segments, each of length L samples:

Segment 0: [s₀,    s₁,    ..., s_{L-1}  ]  ← embed bit 0
Segment 1: [s_L,   s_{L+1}, ..., s_{2L-1}]  ← embed bit 1
Segment 2: [s_{2L}, ..., s_{3L-1}        ]  ← embed bit 2
...
```

**Key parameters:**
- `L` = 8192 samples minimum (ensures enough "spreading")
- `N` = number of bits we can embed = floor(audio_length / L)

#### Step 3: Generate Spreading Sequence
```
r = [1, 1, 1, ..., 1]  (L ones)
```
This is a simplified **pseudo-noise (PN) sequence**. In advanced DSSS, this would be a random-looking pattern known only to encoder/decoder.

#### Step 4: Create Watermark Signal
For each bit `b` (either 0 or 1):
```
If bit = 1:  watermark_segment = +1 × r = [+1, +1, +1, ...]
If bit = 0:  watermark_segment = -1 × r = [-1, -1, -1, ...]
```

The `mixer()` function smooths transitions between segments to avoid audible "clicks":
```
Before: [+1,+1,+1,+1,-1,-1,-1,-1]  ← abrupt transition (clicks)
After:  [+1,+1,+1,+0.5,0,-0.5,-1,-1]  ← smooth transition (inaudible)
```

#### Step 5: Embed into Audio
```
watermarked_audio = original_audio + (watermark_signal × α)

where α = 0.005 (0.5% amplitude - imperceptible)
```

**Visual:**
```
Original:    ~~~~∿∿∿∿~~~~∿∿∿∿~~~~
Watermark:   +++++++-------+++++  (scaled by 0.005)
Result:      ~~~~∿∿∿∿~~~~∿∿∿∿~~~~  (looks/sounds the same!)
```

---

### DECODING (Extracting the Message)

#### Step 1: Divide Watermarked Audio into Segments
Same segmentation as encoding (L samples per segment).

#### Step 2: Correlate Each Segment with Spreading Sequence
```
For segment i:
    correlation = sum(segment[i] × r) / L
    
    = sum([s₀×1 + s₁×1 + ... + s_{L-1}×1]) / L
    = average of all samples in segment
```

#### Step 3: Threshold to Recover Bits
```
If correlation > 0:  bit = 1
If correlation ≤ 0:  bit = 0
```

**Why this works:**
- If bit=1 was embedded: we added positive values → average is positive
- If bit=0 was embedded: we added negative values → average is negative
- The original audio's contribution averages out (random positive/negative values cancel)

#### Step 4: Convert Bits Back to Text
```
[0,1,0,0,1,0,0,0, 0,1,1,0,1,0,0,1] → [72, 105] → "Hi"
```

---

## Code Walkthrough

### Text ↔ Binary Conversion

```python
def text_to_bits(text: str) -> list:
    """Convert text string to list of bits."""
    bits = []
    for char in text:
        # ord('H') = 72 → format(72, '08b') = '01001000'
        # Then convert string '01001000' to list [0,1,0,0,1,0,0,0]
        char_bits = [int(b) for b in format(ord(char), '08b')]
        bits.extend(char_bits)
    return bits
# Example: text_to_bits("Hi") → [0,1,0,0,1,0,0,0, 0,1,1,0,1,0,0,1]


def bits_to_text(bits: list) -> str:
    """Convert list of bits back to text string."""
    chars = []
    for i in range(0, len(bits), 8):      # Process 8 bits at a time
        byte = bits[i:i+8]                 # Get one byte (8 bits)
        if len(byte) == 8:
            # [0,1,0,0,1,0,0,0] → '01001000' → 72 → 'H'
            char_code = int(''.join(str(b) for b in byte), 2)
            if 0 < char_code < 128:        # Valid ASCII only
                chars.append(chr(char_code))
    return ''.join(chars)
# Example: bits_to_text([0,1,0,0,1,0,0,0, 0,1,1,0,1,0,0,1]) → "Hi"
```

---

### Mixer Function (Smooth Transitions)

```python
def mixer(L, bits, lower=0, upper=1, K=256):
    """
    Mix watermark bits with smooth transitions to avoid audible clicks.
    
    Args:
        L: Segment length (samples per bit)
        bits: List of bits to embed [0,1,1,0,...]
        lower, upper: Output range (e.g., -1 to +1)
        K: Smoothing window size (256 samples)
    
    Returns:
        Smoothed watermark signal
    """
    # Adjust K if segment is too short
    if 2 * K > L:
        K = int(np.floor(L / 4) - np.mod(np.floor(L / 4), 4))
    else:
        K = int(K - np.mod(K, 4))
    
    N = len(bits)
    encbit = np.asarray(bits)

    # Create rectangular signal: each bit repeated L times
    # bits=[1,0] → [[1,1,1,...,1], [0,0,0,...,0]] → [1,1,1,...,1,0,0,0,...,0]
    m_sig = np.transpose(np.ones((L, 1)) * encbit)
    m_sig = m_sig.reshape((N * L))
    
    # Convolve with Hann window to smooth transitions
    # Hann window is bell-shaped: gradual rise and fall
    c = convolve(m_sig, hann(K))
    
    # Trim edges (convolution adds K/2 samples on each side)
    wnorm_left = int(K / 2)
    wnorm_right = int(len(c) - K / 2 + 1)
    wnorm = c[wnorm_left:wnorm_right] / np.max(np.abs(c))
    
    # Scale to desired range (e.g., -1 to +1)
    w_sig = wnorm * (upper - lower) + lower
    return w_sig
```

**What the mixer does visually:**
```
Input bits:  [1, 1, 0, 0, 1]
Before mixer: ████████████________████
              ↑ abrupt edges cause clicks
              
After mixer:  ▄▄██████████▄▄__▄▄████
              ↑ smooth transitions = silent
```

---

### DSSS Encode (Embedding)

```python
def dsss_encode(data: np.ndarray, message: list) -> np.ndarray:
    """
    Encode a watermark message into audio using DSSS.
    
    Args:
        data: Input audio signal (1D numpy array of floats, e.g., [-1.0, 0.5, ...])
        message: List of bits [0, 1, 1, 0, ...] to embed
    
    Returns:
        Watermarked audio signal (same length as input)
    """
    
    # === STEP 1: Calculate segment parameters ===
    
    L_min = 8 * 1024  # = 8192 samples minimum per bit
                      # At 48kHz, this is ~0.17 seconds per bit
    
    # Calculate ideal segment length based on audio length and message length
    L2 = np.floor(len(data) / len(message))  # If we spread evenly
    
    # Use the larger of minimum or calculated length
    L = int(max(L_min, L2))
    
    # Calculate how many segments fit in the audio
    nframe = np.floor(len(data) / L)
    
    # Round down to multiple of 8 (for clean byte boundaries)
    N = int(nframe - np.mod(nframe, 8))
    
    # Example: 8 million samples, 96-bit message
    # L = max(8192, 8000000/96) = max(8192, 83333) = 83333
    # N = floor(8000000/83333) = 96, rounded to multiple of 8 = 96
    
    
    # === STEP 2: Validate audio length ===
    
    min_samples_needed = L_min * 8  # Need at least 8 segments
    if N == 0 or len(data) < min_samples_needed:
        raise ValueError(f"Audio too short!")
    
    
    # === STEP 3: Set embedding strength ===
    
    alpha = 0.005  # 0.5% of audio amplitude
                   # Higher = more robust but more audible
                   # Lower = less audible but easier to lose
    
    
    # === STEP 4: Prepare watermark bits ===
    
    # Pad or truncate message to exactly N bits
    bits = message[:N] if len(message) > N else (message + [0] * N)[:N]
    # Example: message=[1,0,1], N=8 → bits=[1,0,1,0,0,0,0,0]
    
    
    # === STEP 5: Generate spreading sequence ===
    
    r = np.ones((L,))    # Simple spreading sequence: all 1s
                         # Length L (one segment worth)
    
    pr = np.tile(r, N)   # Repeat N times for all segments
                         # Total length: N * L samples
    
    
    # === STEP 6: Create smoothed watermark signal ===
    
    mix = mixer(L, bits, -1, 1, 256)
    # Converts bits [1,0,1,...] to smooth signal [-1...+1...−1...]
    # with gradual transitions between bits
    
    
    # === STEP 7: Embed watermark into audio ===
    
    stego = data[:N * L] + mix * pr * alpha
    #       ↑               ↑    ↑   ↑
    #       original        │    │   └── scale down (0.5%)
    #       audio           │    └────── spreading sequence (all 1s)
    #                       └─────────── smoothed bit signal (-1 or +1)
    
    # Numerical example for one sample:
    # original = 0.3, mix = 0.8 (representing bit=1), pr = 1, alpha = 0.005
    # stego = 0.3 + 0.8 * 1 * 0.005 = 0.3 + 0.004 = 0.304
    #                                              ↑ barely changed!
    
    
    # === STEP 8: Append unmodified tail ===
    
    return np.concatenate((stego, data[N * L:]))
    # Any remaining samples that don't fit in a full segment
    # are left unchanged
```

---

### DSSS Decode (Extraction)

```python
def dsss_decode(data_with_watermark: np.ndarray, watermark_length: int) -> list:
    """
    Decode a watermark from a watermarked audio signal.
    
    Args:
        data_with_watermark: Watermarked audio signal
        watermark_length: Number of bits to extract (must know this!)
    
    Returns:
        List of decoded bits [0, 1, 1, 0, ...]
    """
    
    # === STEP 1: Calculate segment parameters (same as encode) ===
    
    L_min = 8 * 1024
    L2 = np.floor(len(data_with_watermark) / watermark_length)
    L = int(max(L_min, L2))
    nframe = np.floor(len(data_with_watermark) / L)
    N = int(nframe - np.mod(nframe, 8))
    
    # CRITICAL: These must match what was used during encoding!
    
    
    # === STEP 2: Reshape audio into segments ===
    
    xsig = data_with_watermark[:N * L].reshape(N, L).T
    #                                  ↑
    # Reshape 1D array into 2D matrix:
    # From: [s0, s1, s2, ..., s_{N*L-1}]
    # To:   [[seg0], [seg1], ..., [segN-1]]  (N columns, L rows each)
    #
    # .T transposes so each COLUMN is one segment
    # Shape: (L, N) - L samples × N segments
    
    
    # === STEP 3: Generate same spreading sequence ===
    
    r = np.ones((L,))  # Must match encoder's sequence!
    
    
    # === STEP 4: Correlate each segment with spreading sequence ===
    
    c = np.dot(r, xsig) / L
    #   ↑
    # Matrix multiplication: r (1×L) dot xsig (L×N) = result (1×N)
    #
    # For each segment j:
    #   c[j] = (r[0]*xsig[0,j] + r[1]*xsig[1,j] + ... + r[L-1]*xsig[L-1,j]) / L
    #        = sum of all samples in segment j / L
    #        = average of segment j
    #
    # Since r is all 1s, this simplifies to just averaging each segment
    
    
    # === STEP 5: Threshold to get bits ===
    
    decoded_bits = (c > 0).astype(int)
    #               ↑
    # If average > 0: embedded bit was 1 (we added positive values)
    # If average ≤ 0: embedded bit was 0 (we added negative values)
    #
    # The original audio averages to ~0 (music is roughly symmetric)
    # So the watermark tips the average positive or negative
    
    
    # === STEP 6: Return requested number of bits ===
    
    return decoded_bits[:watermark_length].tolist()
```

---

## Project Structure

### Files

| File | Description |
|------|-------------|
| `app.py` | Web UI (Gradio) - recommended for demos |
| `main.py` | Command-line interface |
| `dsss.py` | DSSS algorithm implementation (class-based) |
| `requirements.txt` | Python dependencies |
| `README.md` | Documentation |

### Folders

```
DSSS-Audio-Steganography/
├── app.py                 ← Web UI (python app.py)
├── main.py                ← CLI (python main.py)
├── dsss.py                ← Algorithm class
├── requirements.txt
├── README.md
├── input/                 ← Put your WAV files here
│   ├── song1.wav
│   └── ...
└── output/                ← Watermarked files saved here (auto-created)
    ├── watermarked_song1.wav
    └── ...
```

---

## DSSSteganography Class

The core algorithm is encapsulated in the `DSSSteganography` class in `dsss.py`:

```python
class DSSSteganography:
    def __init__(self, alpha=0.005, min_segment_length=8192, smoothing_window=256):
        ...
    
    def encode(self, audio, message) -> np.ndarray:
        """Embed text message into audio."""
    
    def decode(self, audio, message_length) -> str:
        """Extract text message from watermarked audio."""
    
    def get_capacity(self, audio_length) -> int:
        """Calculate max characters that can be embedded."""
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.005 | Embedding strength (0.5%). Higher = more robust but audible |
| `min_segment_length` | 8192 | Minimum samples per bit |
| `smoothing_window` | 256 | Hann window size for smooth transitions |

---

## CLI Usage Examples

### Basic Command
```bash
python main.py <command> [arguments]
```

### Encode (Embed Message)
```bash
# Basic
python main.py encode "Little Miracle.wav" "Hello Alice."

# With custom output
python main.py encode "song.wav" "Copyright 2026" --output "protected.wav"

# With stronger embedding
python main.py encode "music.wav" "Secret" --strength 0.01
```

### Decode (Extract Message)
```bash
python main.py decode "watermarked_song.wav" 12
```

### Output
```
Loading: input\song.wav
  Sample rate: 48000 Hz
  Duration: 180.00 seconds

Message: "Hello Alice."
  Length: 12 characters (96 bits)

Encoding with DSSS (strength=0.005)...
Saving: output\watermarked_song.wav

Verifying...
[OK] Message verified successfully!

Done! Output: output\watermarked_song.wav
```

---

## Algorithm Correctness Notes

This implementation is a **simplified but functional** DSSS:

| Aspect | This Implementation | Full DSSS |
|--------|---------------------|-----------|
| Spreading sequence | All 1s (simple) | Pseudo-random PN sequence |
| Security | Low (easy to detect) | High (need the PN seed) |
| Robustness | Basic | Better with PN sequences |
| Functionality | ✅ Works correctly | More features |

The core mathematical principle (spread + correlate) is correct. For production use, you'd want to add a proper pseudo-random spreading sequence with a secret key.

---

## Quick Reference

### Run Options

| Method | Command | URL |
|--------|---------|-----|
| **Web UI** | `python app.py` | http://127.0.0.1:7860 |
| **CLI** | `python main.py <command>` | — |

### CLI Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `encode` | `python main.py encode "file.wav" "message"` | Embed message |
| `decode` | `python main.py decode "file.wav" 10` | Extract message (10 chars) |
| `info` | `python main.py info "file.wav"` | Show capacity |
| `list` | `python main.py list` | List files |

### DSSSteganography Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `encode(audio, message)` | Embed text | `dsss.encode(audio, "Hi")` |
| `decode(audio, length)` | Extract text | `dsss.decode(audio, 2)` |
| `get_capacity(samples)` | Max chars | `dsss.get_capacity(len(audio))` |
| `encode_bits(audio, bits)` | Embed raw bits | `dsss.encode_bits(audio, [0,1,1])` |
| `decode_bits(audio, length)` | Extract raw bits | `dsss.decode_bits(audio, 24)` |

### Internal Functions

| Function | Purpose |
|----------|---------|
| `_text_to_bits()` | Convert text → bits |
| `_bits_to_text()` | Convert bits → text |
| `_mixer()` | Smooth bit transitions |
| `_encode_bits()` | Core encoding algorithm |
| `_decode_bits()` | Core decoding algorithm |
