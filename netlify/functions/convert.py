"""Minimal Netlify function returning a dummy MIDI file."""

import base64

# Base64 of a very small MIDI file generated with ``mido``.  Returning the
# bytes directly avoids any dependency on external libraries.
DUMMY_MIDI_B64 = (
    "TVRoZAAAAAYAAQABAeBNVHJrAAAAEADADACQQECDYIBAQAD/LwA="
)


def handler(event, context):
    """Handle a request from ``/.netlify/functions/convert``.

    This implementation simply reads the ``mode`` query parameter (for
    demonstration) and returns the tiny MIDI above.  The response includes a
    CORS header so that ``fetch`` from the browser succeeds.
    """

    # Access query parameters; default to 'aeolian' if missing.
    params = event.get("queryStringParameters") or {}
    mode = params.get("mode", "aeolian")

    # The mode is unused in this dummy implementation but reading it proves the
    # function received the query string correctly, which helps diagnose 404
    # errors coming from misconfigured routing.
    _ = mode

    return {
        "statusCode": 200,
        # CORS header allows browser fetches from the same origin.
        "headers": {
            "Content-Type": "audio/midi",
            "Access-Control-Allow-Origin": "*",
        },
        # The body is base64-encoded MIDI data.
        "isBase64Encoded": True,
        "body": DUMMY_MIDI_B64,
    }

