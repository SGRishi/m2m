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

The code targets **Python 3.10**. When deploying to Netlify,
the `runtime.txt` file specifying `3.10.8` ensures the correct
version is used.

Transkun requires additional dependencies and a working `sox` installation. Refer to its documentation if transcription fails.

## Command line usage

Interactive mode:

```bash
python final.py
```

You will be prompted for a source (local file or YouTube URL), an output filename and the target mode.

Direct mode (provide a target mode as a third argument):

```bash
python final.py input_file output.mid dorian
```

## Modes

The following target modes are available when starting from a major key:

- **Ionian** (no change)

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

The `index.html` page can be served directly from Netlify. A serverless
function called `convert` (written in Python) lives in `netlify/functions/`.
The included `netlify.toml` already points Netlify to this directory. Deploy
the repository and ensure the Python dependencies from `requirements.txt` are
installed. Conversion requests sent to `/.netlify/functions/convert` will
return the converted MIDI file.

Netlify now provides a Python runtime by default, so no extra build plugins are
required.
