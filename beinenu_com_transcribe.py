import requests
import re
import urllib.parse
import os

from tqdm import tqdm
from faster_whisper import WhisperModel




def srt_file_to_txt_file(path: str):
    r"[\d:,]+ --> [\d:,]+"
    pass

# ניקוד עברי
"[\u0591-\u05C7]"