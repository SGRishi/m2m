import base64
import io
import os
import tempfile
import cgi
import json
from typing import Dict
import pretty_midi
from final import (
    download_audio_from_url,
    audio_to_polyphonic_midi,
    infer_tonic_name,
    convert_to_mode,
    ensure_mid_extension,
)

def handler(event, context):
    try:
        content_type = event['headers'].get('content-type') or event['headers'].get('Content-Type')
        if not content_type:
            return {'statusCode': 400, 'body': 'Missing Content-Type'}
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body_bytes = base64.b64decode(body)
        else:
            body_bytes = body.encode()
        environ = {'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type, 'CONTENT_LENGTH': str(len(body_bytes))}
        fs = cgi.FieldStorage(fp=io.BytesIO(body_bytes), environ=environ, keep_blank_values=True)
        mode = fs.getfirst('mode', 'aeolian')
        outname = ensure_mid_extension(fs.getfirst('out', 'output.mid'))
        url = fs.getfirst('url', '').strip()
        file_item = fs['midi'] if 'midi' in fs else None
        if file_item is not None and file_item.filename:
            temp_mid = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
            temp_mid.write(file_item.file.read())
            temp_mid.close()
            src_mid = temp_mid.name
        elif url:
            audio_path = download_audio_from_url(url)
            temp_mid = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
            temp_mid.close()
            audio_to_polyphonic_midi(audio_path, temp_mid.name)
            src_mid = temp_mid.name
            os.remove(audio_path)
        else:
            return {'statusCode': 400, 'body': 'No input provided'}
        pm = pretty_midi.PrettyMIDI(src_mid)
        tonic_pc = pretty_midi.note_name_to_number(infer_tonic_name(pm)) % 12
        convert_to_mode(pm, tonic_pc, mode)
        out_path = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        out_path.close()
        pm.write(out_path.name)
        with open(out_path.name, 'rb') as f:
            out_data = f.read()
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{outname}"'
            },
            'isBase64Encoded': True,
            'body': base64.b64encode(out_data).decode()
        }
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}

