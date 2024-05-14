import requests
import re
import urllib.parse
import os

from tqdm import tqdm
from faster_whisper import WhisperModel
from bs4 import BeautifulSoup
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def get_lesson_elements(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        title_rabbi_element = soup.find("div", class_="title-rabbi")
        title_lessons_element = soup.find("div", class_="title-lessons")
        video_iframe = soup.find("iframe", class_="lesson-player")

        if video_iframe:
            video_src = video_iframe["src"]
            video_id_match = re.search(r"ID=(\d+)", video_src)
            if video_id_match:
                video_id = video_id_match.group(1)
            else:
                video_id = None
        else:
            video_id = None

        if not (title_rabbi_element and title_lessons_element and video_id):
            raise ValueError("לא הצלחנו למצוא אחד או יותר מהאלמנטים בדף זה.")

        title_lessons_parts = title_lessons_element.text.strip().split(" | ")

        video_url = f"https://vod.wgnmedia.com/VOD/LIB.MP4/v{video_id}.mp4"

        lesson_elements = {
            "title_rabbi": title_rabbi_element.text.strip(),
            "title_lessons": title_lessons_parts[0].strip(),
            "title_lessons_year": title_lessons_parts[1].strip(),
            "video_id": video_id,
            "video_url": video_url,
        }

        return lesson_elements

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"שגיאה בהורדת הדף: {e}")

    except Exception as e:
        raise RuntimeError(f"שגיאה לא צפויה: {e}")


async def get_video_id(url: str) -> dict:
    """
    Get video ID and URL from the page URL.

    Args:
            url (str): The page URL containing the video.

    Returns:
            dict: A dictionary containing the video ID and URL.
    """
    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Error occurred during the request: {e}")

    all_html = res.text

    regex = r'"\/\/(vod\.wgnmedia\.com\/VOD.+?)\"'
    wgnmedia_url_match = re.search(regex, all_html)

    if not wgnmedia_url_match or not wgnmedia_url_match.group(1):
        raise Exception("wgnmedia url not found")

    video_url_obj = urllib.parse.urlparse(f"https:{wgnmedia_url_match.group(1)}")
    video_id = urllib.parse.parse_qs(video_url_obj.query).get("ID", [""])[0]

    if not video_id:
        raise Exception("ID not found")

    video_url = f"https://vod.wgnmedia.com/VOD/LIB.MP4/v{video_id}.mp4"

    return {"video_url": video_url, "video_id": video_id}


def download_file(url, filename):

    filename = clean_filename(filename)

    
    response = requests.get(url, stream=True, verify=False)

    
    if response.status_code == 200:
        
        total_size = int(response.headers.get("content-length", 0))

        
        file_path = os.path.join(os.getcwd(), filename)

        
        with open(file_path, "wb") as file, tqdm(
            desc=filename,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

        print(f"File '{filename}' downloaded successfully!")
    else:
        print(f"Error: Failed to download file. Status code: {response.status_code}")


def check_link(link: str) -> None:
    if link.startswith("https://beinenu.com/lessons/"):
        print("Link is valid")
        print(urllib.parse.unquote(link))
    else:
        raise ValueError("Error: Invalid link")


def convert_to_subtitles_time_format(seconds: int, type: str) -> str:
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    if type == "vtt":
        str_time = "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)
    else:
        str_time = "%02d:%02d:%02d,%03d" % (hours, minutes, seconds, milliseconds)
    return str_time


def write_segments_to_vtt(segments, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for segment in segments:
            start_time = convert_to_subtitles_time_format(segment.start, "vtt")
            end_time = convert_to_subtitles_time_format(segment.end, "vtt")
            f.write("%s --> %s\n%s\n\n" % (start_time, end_time, segment.text))
            print("[%s --> %s] %s" % (start_time, end_time, segment.text))


def write_segments_to_srt(segments, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        segment_count = 1
        for segment in segments:
            start_time = convert_to_subtitles_time_format(segment.start, "srt")
            end_time = convert_to_subtitles_time_format(segment.end, "srt")
            text = segment.text.strip()

            f.write(f"{segment_count}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
            segment_count += 1
            print(f"[{start_time} --> {end_time}] {text}")


def transcribe(directory: str, subtitles_format: str) -> None:
    
    #device="cpu"
    #compute_type="default"
    compute_type="float16"
    device = "cuda"
    
    

    assert subtitles_format in [
        "srt",
        "vvt",
    ], "subtitles_format יכול להיות רק 'srt' או 'vvt'"

    model_size = "large-v2"
    initial_prompt = "Hello, How is it going? Please, always use punctuation."
    model = WhisperModel(model_size, device, compute_type=compute_type)
    for filename in os.listdir(directory):
        if filename.endswith(".mp4"):
            audio_file_path = os.path.join(directory, filename)
            filename_without_extension = os.path.splitext(filename)[0]

            segments, info = model.transcribe(
                audio_file_path,
                beam_size=5,
                language="he",
                initial_prompt=initial_prompt,
            )

            if subtitles_format == "srt":
                output_file = f"{filename_without_extension}.srt"
                write_segments_to_srt(segments, output_file)
            else:
                output_file = f"{filename_without_extension}.vtt"
                write_segments_to_vtt(segments, output_file)

            print("Transcription saved to", output_file)


def clean_filename(filename: str):
    """
    Removes all invalid characters for filenames across different operating systems.
    Returns a cleaned version of the filename.
    """
    bad_chars = r'[<>:/\\|?*"]'
    cleaned = re.sub(bad_chars, '_', filename)
    return cleaned

class GoogleDriveUpload:
    def __init__(self) -> None:
        self.gauth = GoogleAuth()
        self.gauth.LoadCredentialsFile("mycreds.txt")
        self.drive = GoogleDrive(self.gauth)

    def local_server_auth_and_save(self):
        self.gauth.LocalWebserverAuth()
        self.gauth.SaveCredentialsFile("mycreds.txt")
        self.drive = GoogleDrive(self.gauth)


    def check_if_folder_name_exist(self, folder_name: str, parent_folder_id: str):
        q = f"title='{folder_name}' and '{parent_folder_id}' in parents"
        file_list = self.drive.ListFile({"q": q}).GetList()
        if len(file_list) > 0:
            return file_list
        else:
            return False

    def create_folder(self, name: str, parent_folder_id: str):
        file = self.drive.CreateFile({
            "title": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [{
                "id": parent_folder_id
            }]
        })
        file.Upload()

    def create_folder_if_not_exist(self, folder_name:str, parent_folder_id:str):

        folder_details = self.check_if_folder_name_exist(folder_name, parent_folder_id)

        if(folder_details):
            return folder_details
        else:
            self.create_folder(folder_name, parent_folder_id)
    

    def upload_file(self, local_file_path:str, parent_folder_id:str):
        
        file_name = os.path.basename(local_file_path)

        file = self.drive.CreateFile({
            'title': file_name,
            "parents": [{
                "id": parent_folder_id
            }]
        })

        file.SetContentFile(local_file_path)

        file.Upload()

    def upload_lesson_files_to_drive(self, rabbi_name, file_name, drive_folder_id):
        self.create_folder_if_not_exist(rabbi_name, drive_folder_id)
        self.upload_file(file_name, drive_folder_id)
    
