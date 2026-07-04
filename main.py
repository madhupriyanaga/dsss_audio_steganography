#!/usr/bin/env python3
"""
DSSS Audio Steganography - Command Line Interface

Embed secret messages into audio files using Direct Sequence Spread Spectrum.

Usage:
    python main.py encode <input.wav> "<message>" [output.wav]
    python main.py decode <input.wav> <message_length>
    python main.py info <input.wav>

Examples:
    python main.py encode "song.wav" "Hello Alice."
    python main.py encode "song.wav" "Secret" "output.wav"
    python main.py decode "watermarked_song.wav" 12
    python main.py info "song.wav"
"""

import sys
import argparse
from pathlib import Path
import soundfile as sf

from dsss import DSSSteganography


# ==================== Configuration ====================

INPUT_FOLDER = Path("input")
OUTPUT_FOLDER = Path("output")


# ==================== CLI Commands ====================

def cmd_encode(args):
    """Encode a message into an audio file."""
    
    # Resolve input path
    input_path = resolve_input_path(args.input)
    if not input_path:
        return 1
    
    # Resolve output path
    if args.output:
        output_path = OUTPUT_FOLDER / args.output
    else:
        output_path = OUTPUT_FOLDER / f"watermarked_{input_path.name}"
    
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    # Load audio
    print(f"Loading: {input_path}")
    samples, samplerate = sf.read(str(input_path), dtype='float32')
    
    # Handle stereo
    if samples.ndim == 2:
        print(f"  Stereo detected - using first channel")
        audio = samples[:, 0]
    else:
        audio = samples
    
    print(f"  Sample rate: {samplerate} Hz")
    print(f"  Duration: {len(audio) / samplerate:.2f} seconds")
    
    # Encode
    message = args.message
    print(f"\nMessage: \"{message}\"")
    print(f"  Length: {len(message)} characters ({len(message) * 8} bits)")
    
    dsss = DSSSteganography(alpha=args.strength)
    
    # Check capacity
    capacity = dsss.get_capacity(len(audio))
    if len(message) > capacity:
        print(f"\nERROR: Message too long! Max capacity: {capacity} characters")
        return 1
    
    print(f"\nEncoding with DSSS (strength={args.strength})...")
    watermarked = dsss.encode(audio, message)
    
    # Save
    print(f"Saving: {output_path}")
    sf.write(str(output_path), watermarked, samplerate)
    
    # Verify
    print(f"\nVerifying...")
    decoded = dsss.decode(watermarked, len(message))
    
    if decoded == message:
        print(f"[OK] Message verified successfully!")
    else:
        print(f"[WARNING] Decoded message differs:")
        print(f"  Expected: \"{message}\"")
        print(f"  Got:      \"{decoded}\"")
    
    print(f"\nDone! Output: {output_path}")
    return 0


def cmd_decode(args):
    """Decode a message from a watermarked audio file."""
    
    # Resolve input path
    input_path = resolve_input_path(args.input)
    if not input_path:
        # Also check output folder for watermarked files
        output_path = OUTPUT_FOLDER / args.input
        if output_path.exists():
            input_path = output_path
        else:
            print(f"ERROR: File not found: {args.input}")
            return 1
    
    # Load audio
    print(f"Loading: {input_path}")
    samples, samplerate = sf.read(str(input_path), dtype='float32')
    
    if samples.ndim == 2:
        audio = samples[:, 0]
    else:
        audio = samples
    
    print(f"  Duration: {len(audio) / samplerate:.2f} seconds")
    
    # Decode
    message_length = args.length
    print(f"\nDecoding {message_length} characters...")
    
    dsss = DSSSteganography()
    decoded = dsss.decode(audio, message_length)
    
    print(f"\n{'='*40}")
    print(f"Decoded message: \"{decoded}\"")
    print(f"{'='*40}")
    
    return 0


def cmd_info(args):
    """Show information about an audio file and its capacity."""
    
    input_path = resolve_input_path(args.input)
    if not input_path:
        return 1
    
    # Load audio
    samples, samplerate = sf.read(str(input_path), dtype='float32')
    
    if samples.ndim == 2:
        audio = samples[:, 0]
        channels = "Stereo"
    else:
        audio = samples
        channels = "Mono"
    
    dsss = DSSSteganography()
    capacity = dsss.get_capacity(len(audio))
    
    print(f"File: {input_path.name}")
    print(f"{'='*40}")
    print(f"  Sample rate:    {samplerate} Hz")
    print(f"  Duration:       {len(audio) / samplerate:.2f} seconds")
    print(f"  Samples:        {len(audio):,}")
    print(f"  Channels:       {channels}")
    print(f"  Max capacity:   {capacity} characters")
    print(f"                  ({capacity * 8} bits)")
    
    return 0


def cmd_list(args):
    """List available audio files."""
    
    print("Available files:")
    print(f"\n  Input folder ({INPUT_FOLDER}):")
    
    if INPUT_FOLDER.exists():
        wav_files = list(INPUT_FOLDER.glob("*.wav"))
        if wav_files:
            for f in wav_files:
                print(f"    - {f.name}")
        else:
            print("    (no WAV files found)")
    else:
        print("    (folder does not exist)")
    
    print(f"\n  Output folder ({OUTPUT_FOLDER}):")
    
    if OUTPUT_FOLDER.exists():
        wav_files = list(OUTPUT_FOLDER.glob("*.wav"))
        if wav_files:
            for f in wav_files:
                print(f"    - {f.name}")
        else:
            print("    (no WAV files found)")
    else:
        print("    (folder does not exist)")
    
    return 0


# ==================== Helpers ====================

def resolve_input_path(filename: str) -> Path | None:
    """Resolve input file path (check input folder first, then current dir)."""
    
    # Check input folder
    input_path = INPUT_FOLDER / filename
    if input_path.exists():
        return input_path
    
    # Check current directory
    direct_path = Path(filename)
    if direct_path.exists():
        return direct_path
    
    # Check output folder (for decode)
    output_path = OUTPUT_FOLDER / filename
    if output_path.exists():
        return output_path
    
    print(f"ERROR: File not found: {filename}")
    print(f"  Checked: {input_path}")
    print(f"  Checked: {direct_path}")
    return None


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(
        description="DSSS Audio Steganography - Hide messages in audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py encode "song.wav" "Hello Alice."
  python main.py encode "song.wav" "Secret" --output "secret.wav"
  python main.py decode "watermarked_song.wav" 12
  python main.py info "song.wav"
  python main.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Encode command
    encode_parser = subparsers.add_parser("encode", help="Embed a message into audio")
    encode_parser.add_argument("input", help="Input WAV file (from input/ folder)")
    encode_parser.add_argument("message", help="Secret message to embed")
    encode_parser.add_argument("output", nargs="?", help="Output filename (optional)")
    encode_parser.add_argument("-s", "--strength", type=float, default=0.005,
                               help="Embedding strength (default: 0.005)")
    
    # Decode command
    decode_parser = subparsers.add_parser("decode", help="Extract message from audio")
    decode_parser.add_argument("input", help="Watermarked WAV file")
    decode_parser.add_argument("length", type=int, help="Message length in characters")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show audio file info and capacity")
    info_parser.add_argument("input", help="WAV file to analyze")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available audio files")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Create folders
    INPUT_FOLDER.mkdir(exist_ok=True)
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    # Run command
    if args.command == "encode":
        return cmd_encode(args)
    elif args.command == "decode":
        return cmd_decode(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "list":
        return cmd_list(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
