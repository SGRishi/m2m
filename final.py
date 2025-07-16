#!/usr/bin/env python3
"""
combined_audio2midi_and_mode_convert.py

This script prompts for either a YouTube link or a local audio/MIDI file (or accepts two args),
supports downloading via yt-dlp (with fallback if MP3 conversion fails),
transcribes polyphonic piano audio to MIDI via Transkun if needed,
then converts MIDI between various modes.

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

# Mapping of target modes relative to Ionian (major)
MODE_MAP = {
    'ionian':    {'lower': set(), 'raise': set()},
    'aeolian':    {'lower': {4, 9, 11}, 'raise': set()},
    'harmonic_minor': {'lower': {4, 9}, 'raise': set()},
    'dorian':     {'lower': {4, 11}, 'raise': set()},
    'phrygian':   {'lower': {2, 4, 9, 11}, 'raise': set()},
    'lydian':     {'lower': set(), 'raise': {5}},
    'mixolydian': {'lower': {11}, 'raise': set()},
    'locrian':    {'lower': {2, 4, 7, 9, 11}, 'raise': set()},
    'major':      {'lower': set(), 'raise': {3, 8, 10}},  # for minor → major
}


def convert_to_mode(pm: pretty_midi.PrettyMIDI, tonic_pc: int, mode: str) -> str:
    """Shift notes in-place to the given mode. Returns description."""
    info = MODE_MAP.get(mode)
    if info is None:
        raise ValueError(f"Unsupported mode: {mode}")
    to_lower = info.get('lower', set())
    to_raise = info.get('raise', set())
    for inst in pm.instruments:
        for note in inst.notes:
            pc = (note.pitch - tonic_pc) % 12
            if pc in to_lower:
                note.pitch -= 1
            elif pc in to_raise:
                note.pitch += 1
    return mode.replace('_', ' ')


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
    print("Choose target mode:")
    options = [
        ("1", "Major → Natural minor (Aeolian)"),
        ("2", "Major → Harmonic minor"),
        ("3", "Minor → Major"),
        ("4", "Major → Dorian"),
        ("5", "Major → Phrygian"),
        ("6", "Major → Lydian"),
        ("7", "Major → Mixolydian"),
        ("8", "Major → Locrian"),
        ("9", "No conversion (Ionian)"),
    ]
    for k, desc in options:
        print(f" {k}: {desc}")
    c = input("Enter choice: ")
    valid = {k for k, _ in options}
    if c not in valid:
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
    mode_lookup = {
        '1': 'aeolian',
        '2': 'harmonic_minor',
        '3': 'major',
        '4': 'dorian',
        '5': 'phrygian',
        '6': 'lydian',
        '7': 'mixolydian',
        '8': 'locrian',
        '9': 'ionian',
    }
    target_mode = mode_lookup[conv]
    desc = convert_to_mode(pm, tonic_pc, target_mode)

    # Write and cleanup
    pm.write(outp)
    print(f"Detected tonic {tonic_name}; converted to {desc} saved as {outp}")
    for tmp in (audio_temp,midi_temp):
        if tmp and os.path.exists(tmp): os.remove(tmp)

if __name__=='__main__':
    main()

