from flask import Flask, request, send_file
import tempfile
import os
import pretty_midi
from final import (
    download_audio_from_url,
    audio_to_polyphonic_midi,
    infer_tonic_name,
    convert_to_mode,
    ensure_mid_extension,
)

app = Flask(__name__)

HTML_PAGE = open('index.html', 'r').read()

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/convert', methods=['POST'])
def convert():
    mode = request.form.get('mode', 'aeolian')
    outname = ensure_mid_extension(request.form.get('out', 'output.mid'))
    url = request.form.get('url', '').strip()
    midi_file = request.files.get('midi')
    if midi_file and midi_file.filename:
        tmp_mid = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        midi_file.save(tmp_mid.name)
        src_mid = tmp_mid.name
    elif url:
        audio_path = download_audio_from_url(url)
        tmp_mid = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        audio_to_polyphonic_midi(audio_path, tmp_mid.name)
        src_mid = tmp_mid.name
        os.remove(audio_path)
    else:
        return 'No input provided', 400

    pm = pretty_midi.PrettyMIDI(src_mid)
    tonic_pc = pretty_midi.note_name_to_number(infer_tonic_name(pm)) % 12
    convert_to_mode(pm, tonic_pc, mode)
    out_path = tempfile.NamedTemporaryFile(suffix='.mid', delete=False).name
    pm.write(out_path)
    return send_file(out_path, as_attachment=True, download_name=outname)

# Netlify expects the serverless function under '/.netlify/functions/convert'.
# When running this Flask app locally, the HTML still posts to that path, so we
# provide an alias that reuses the same logic.
@app.route('/.netlify/functions/convert', methods=['POST'])
def convert_netlify():
    return convert()

if __name__ == '__main__':
    app.run()
