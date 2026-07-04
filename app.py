"""
DSSS Audio Steganography - Gradio UI
Run: python app.py
"""

import gradio as gr
from pathlib import Path
import soundfile as sf
import numpy as np
from difflib import SequenceMatcher
from dsss import DSSSteganography

OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(exist_ok=True)
dsss = DSSSteganography()

def load_audio(file_path):
    """Load audio file as mono float32."""
    samples, sr = sf.read(str(file_path), dtype='float32')
    return samples[:, 0] if samples.ndim == 2 else samples, sr

def save_audio(path, audio, sr):
    """Save audio as 16-bit WAV."""
    sf.write(str(path), (audio * 32767).astype(np.int16), sr, subtype='PCM_16')

def get_match_html(original, decoded):
    """Generate color-coded match indicator."""
    if not original or not decoded:
        return ""
    
    # Use SequenceMatcher for proper string similarity
    pct = SequenceMatcher(None, original, decoded).ratio() * 100
    
    # Color levels based on match percentage
    if pct == 100:
        bg, icon, txt = "#4CAF50", "✓", "PERFECT MATCH"
    elif pct >= 80:
        bg, icon, txt = "#8BC34A", "✓", "Good Match"
    elif pct >= 60:
        bg, icon, txt = "#FFEB3B", "!", "Partial Match"
    elif pct >= 40:
        bg, icon, txt = "#FF9800", "!", "Low Match"
    else:
        bg, icon, txt = "#F44336", "✗", "Mismatch"
    
    color = "#000" if bg == "#FFEB3B" else "#fff"
    return f'<div style="text-align:center;padding:15px;"><div style="display:inline-flex;align-items:center;background:{bg};color:{color};padding:12px 25px;border-radius:8px;font-size:1.3em;font-weight:bold;box-shadow:0 2px 6px rgba(0,0,0,0.15);"><span style="font-size:1.4em;margin-right:8px;">{icon}</span>{txt} ({pct:.0f}%)</div></div>'

def check_inputs(audio_file, message):
    """Update status and button state."""
    if audio_file is None:
        return "🟡 Audio: Waiting...", "🟡 Message: Waiting...", gr.update(interactive=False)
    
    try:
        audio, sr = load_audio(audio_file)
        cap = dsss.get_capacity(len(audio))
        audio_ok = f"✅ Audio: {len(audio)/sr:.1f}s, max {cap} chars"
    except Exception as e:
        return f"❌ Audio: {e}", "🟡 Message: Waiting...", gr.update(interactive=False)
    
    msg = message.strip() if message else ""
    msg_ok = f"✅ Message: {len(msg)} chars" if msg else "🟡 Message: Waiting..."
    
    return audio_ok, msg_ok, gr.update(interactive=bool(msg))

def encode_and_decode(audio_file, message):
    """Encode message into audio, decode to verify, return results."""
    if not audio_file or not message or not message.strip():
        return gr.update(), gr.update(), "", "", "", None, None
    
    try:
        audio, sr = load_audio(audio_file)
        msg = message.strip()
        
        # Encode & decode
        watermarked = dsss.encode(audio, msg)
        decoded = dsss.decode(watermarked, len(msg))
        
        # Save files
        name = Path(audio_file).stem
        orig_path = OUTPUT_FOLDER / f"original_{name}.wav"
        wm_path = OUTPUT_FOLDER / f"watermarked_{name}.wav"
        save_audio(orig_path, audio, sr)
        save_audio(wm_path, watermarked, sr)
        
        return (
            gr.update(visible=False), gr.update(visible=True),
            msg, decoded, get_match_html(msg, decoded),
            str(orig_path), str(wm_path)
        )
    except Exception as e:
        return gr.update(), gr.update(), "", "", f"❌ Error: {e}", None, None

def reset():
    """Reset to initial state."""
    return (
        gr.update(visible=True), gr.update(visible=False),
        None, "", "🟡 Audio: Waiting...", "🟡 Message: Waiting...",
        gr.update(interactive=False)
    )

# ==================== UI ====================

with gr.Blocks(title="DSSS Audio Steganography") as app:
    gr.Markdown("# 🎵 DSSS Audio Steganography\n**Hide secret messages in audio using Direct Sequence Spread Spectrum**")
    
    # Page 1: Encode
    with gr.Group(visible=True) as page1:
        gr.Markdown("## 🔐 Encode Your Message")
        audio_status = gr.Markdown("🟡 Audio: Waiting...")
        msg_status = gr.Markdown("🟡 Message: Waiting...")
        gr.Markdown("---")
        input_audio = gr.Audio(label="📁 Upload WAV file", type="filepath", sources=["upload"])
        input_msg = gr.Textbox(label="💬 Secret Message", placeholder="Type your message...", lines=2)
        gr.Markdown("---")
        btn_encode = gr.Button("🔐 Encrypt & Continue →", variant="primary", size="lg", interactive=False)
    
    # Page 2: Results
    with gr.Group(visible=False) as page2:
        gr.Markdown("## ✅ Results & Verification")
        match_html = gr.HTML()
        gr.Markdown("---")
        with gr.Row():
            orig_text = gr.Textbox(label="📝 Original (edit to test)", lines=2, interactive=True)
            dec_text = gr.Textbox(label="🔓 Decoded", lines=2, interactive=False)
        gr.Markdown("---")
        gr.Markdown("### 🎵 Audio (playable & downloadable)")
        with gr.Row():
            orig_audio = gr.Audio(label="🎧 Original", type="filepath", interactive=False)
            wm_audio = gr.Audio(label="🎧 Watermarked", type="filepath", interactive=False)
        gr.Markdown("---")
        btn_reset = gr.Button("← Start Over", variant="secondary")
    
    # Events
    input_audio.change(check_inputs, [input_audio, input_msg], [audio_status, msg_status, btn_encode])
    input_msg.change(check_inputs, [input_audio, input_msg], [audio_status, msg_status, btn_encode])
    btn_encode.click(
        encode_and_decode, 
        [input_audio, input_msg], 
        [page1, page2, orig_text, dec_text, match_html, orig_audio, wm_audio]
    ).then(
        lambda o, d: get_match_html(o.strip() if o else "", d),
        [orig_text, dec_text],
        [match_html]
    )
    orig_text.change(lambda o, d: get_match_html(o.strip() if o else "", d), [orig_text, dec_text], [match_html])
    btn_reset.click(reset, outputs=[page1, page2, input_audio, input_msg, audio_status, msg_status, btn_encode])
    
    gr.Markdown("---\n**How it works:** DSSS spreads your message across thousands of audio samples!")

if __name__ == "__main__":
    app.launch(theme=gr.themes.Soft(), inbrowser=True)
