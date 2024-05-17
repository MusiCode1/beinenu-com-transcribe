import logging
from beinenu_com_transcribe import (
    transcribe
)

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)


transcribe('שיעור.mp4', 'srt', "תמלול.srt")