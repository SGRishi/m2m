# M2M

M2M is a small tool for converting MIDI (or transcribed audio) between musical modes. It can download audio from YouTube, transcribe piano pieces with [Transkun](https://github.com/braindefender/transkun) and shift all notes to a new mode.

## Features

- Convert from major (Ionian) to natural minor (Aeolian), harmonic minor or any other church mode (Dorian, Phrygian, Lydian, Mixolydian, Locrian).
- Convert from minor back to major.
- Works with local MIDI files or audio/YouTube links (audio is transcribed to MIDI).
- Simple Flask web frontend with a faux "terminal" look.

## Installation

```bash
pip install -r requirements.txt
```

Transkun requires additional dependencies and a working `sox` installation. Refer to its documentation if transcription fails.

## Command line usage

Interactive mode:

```bash
python final.py
```

You will be prompted for a source (local file or YouTube URL), an output filename and the target mode.

Direct mode:

```bash
python final.py input_file output.mid
```

## Modes

The following target modes are available when starting from a major key:

- **Aeolian** (natural minor)
- **Harmonic minor**
- **Dorian**
- **Phrygian**
- **Lydian**
- **Mixolydian**
- **Locrian**

Optionally you can convert from minor back to **Major**.

## Web frontend

Run `python web_app.py` and open `http://localhost:5000` in a browser. The page resembles a green-on-black terminal. Upload a MIDI file or provide a YouTube link, choose the target mode and download the converted MIDI.


## Netlify deployment

The `index.html` page can be served directly from Netlify. A Netlify Function
called `convert` is provided to run the Python converter. The included
`netlify.toml` already points Netlify to the `netlify/functions` directory.
When deploying, just push the repository to Netlify and ensure that required
Python dependencies are installed (as listed in `requirements.txt`). The page
will POST conversion requests to `/.netlify/functions/convert`.
