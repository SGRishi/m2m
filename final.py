#!/usr/bin/env python3
"""
combined_audio2midi_and_mode_convert.py

This script prompts for either a YouTube link or a local audio/MIDI file (or accepts two args),
supports downloading via yt-dlp (with fallback if MP3 conversion fails),
transcribes polyphonic piano audio to MIDI via Transkun if needed,
then converts between major and minor modes (natural or harmonic minor).

Usage:
    # Interactive mode (no args): choose source type, then prompts
    python combined_audio2midi_and_mode_convert.py

    # Direct mode (two args): input_file_or_URL output.mid
    python combined_audio2midi_and_mode_convert.py input_file_or_url output.mid

If the output filename lacks a .mid extension, it will be appended automatically.

Requirements:
    pip install pretty_midi transkun yt-dlp
"""
import sys
import os
import glob
import tempfile
import subprocess
from collections import Counter
import pretty_midi

# Supported local file extensions
AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
ALL_INPUT_EXTS = AUDIO_EXTS.union({'.mid'})


def infer_tonic_name(pm: pretty_midi.PrettyMIDI) -> str:
    pitches = [note.pitch for inst in pm.instruments for note in inst.notes]
    if not pitches:
        raise ValueError("No notes found in this MIDI to infer a tonic from.")
    pcs = [p % 12 for p in pitches]
    tonic_pc = Counter(pcs).most_common(1)[0][0]
    same_pc = sorted(p for p in pitches if p % 12 == tonic_pc)
    median_pitch = same_pc[len(same_pc) // 2]
    return pretty_midi.note_number_to_name(median_pitch)


def download_audio_from_url(url: str) -> str:
    """Download best audio via yt-dlp with MP3 conversion fallback"""
    tmp_dir = tempfile.mkdtemp()
    # Try MP3 extraction
    try:
        subprocess.run([
            'yt-dlp', url, '-f', 'bestaudio',
            '--extract-audio', '--audio-format', 'mp3',
            '-o', os.path.join(tmp_dir, 'audio.%(ext)s')
        ], check=True)
        for f in os.listdir(tmp_dir):
            if f.lower().endswith('.mp3'):
                return os.path.join(tmp_dir, f)
        raise FileNotFoundError()
    except Exception:
        # Fallback raw audio
        subprocess.run([
            'yt-dlp', url, '-f', 'bestaudio',
            '-o', os.path.join(tmp_dir, 'audio.%(ext)s')
        ], check=True)
        files = os.listdir(tmp_dir)
        if not files:
            print("Error: no audio downloaded.")
            sys.exit(1)
        return os.path.join(tmp_dir, files[0])


def audio_to_polyphonic_midi(input_audio: str, output_midi: str) -> None:
    subprocess.run(['transkun', input_audio, output_midi], check=True)


def choose_input_file() -> str:
    files = [f for f in glob.glob("*") if os.path.splitext(f)[1].lower() in ALL_INPUT_EXTS]
    if not files:
        print("No audio or MIDI found.")
        sys.exit(1)
    print("Available files:")
    for i,f in enumerate(files,1): print(f" {i}: {f}")
    choice = input(f"Select 1-{len(files)}: ")
    try:
        idx = int(choice)
        return files[idx-1]
    except Exception:
        print("Invalid selection.")
        sys.exit(1)


def ensure_mid_extension(path: str) -> str:
    base, ext = os.path.splitext(path)
    return path if ext.lower()=='.mid' else f"{path}.mid"


def choose_conversion() -> str:
    print("Choose conversion:")
    print(" 1: Major → Natural minor")
    print(" 2: Major → Harmonic minor")
    print(" 3: Minor → Major")
    c = input("Enter 1,2 or 3: ")
    if c not in {'1','2','3'}:
        print("Invalid choice.")
        sys.exit(1)
    return c


def main():
    # Input and output
    if len(sys.argv)==3:
        inp, outp = sys.argv[1], sys.argv[2]
    else:
        print("-- Source Selection --")
        print("1: YouTube URL")
        print("2: Local file")
        sel = input("Enter 1 or 2: ")
        if sel=='1':
            inp = input("YouTube URL: ").strip()
        elif sel=='2':
            inp = choose_input_file()
        else:
            print("Invalid source.")
            sys.exit(1)
        outp = input("Output MIDI filename (no .mid needed): ")
    outp = ensure_mid_extension(outp)

    # Download if URL
    audio_temp = None
    midi_temp = None
    if inp.startswith(('http://','https://')):
        print(f"Fetching audio: {inp}")
        audio_temp = download_audio_from_url(inp)
        inp = audio_temp

    # Transcription needed?
    ext = os.path.splitext(inp)[1].lower()
    is_audio = ext in AUDIO_EXTS
    if is_audio:
        tmpm = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        midi_temp = tmpm.name; tmpm.close()
        print(f"Transcribing {inp} → {midi_temp}")
        audio_to_polyphonic_midi(inp, midi_temp)
        midi_src = midi_temp
    else:
        midi_src = inp

    # Load MIDI
    pm = pretty_midi.PrettyMIDI(midi_src)
    tonic_name = infer_tonic_name(pm)
    tonic_pc = pretty_midi.note_name_to_number(tonic_name) % 12

    # Conversion choice
    conv = choose_conversion()
    if conv=='1':
        to_lower={4,9,11}
        for inst in pm.instruments:
            for note in inst.notes:
                if (note.pitch-tonic_pc)%12 in to_lower:
                    note.pitch-=1
        desc = 'natural minor'
    elif conv=='2':
        to_lower={4,9}
        for inst in pm.instruments:
            for note in inst.notes:
                if (note.pitch-tonic_pc)%12 in to_lower:
                    note.pitch-=1
        desc = 'harmonic minor'
    else:  # '3'
        to_raise={3,8,10}
        for inst in pm.instruments:
            for note in inst.notes:
                if (note.pitch-tonic_pc)%12 in to_raise:
                    note.pitch+=1
        desc = 'major'

    # Write and cleanup
    pm.write(outp)
    print(f"Detected tonic {tonic_name}; converted to {desc} saved as {outp}")
    for tmp in (audio_temp,midi_temp):
        if tmp and os.path.exists(tmp): os.remove(tmp)

if __name__=='__main__':
    main()

