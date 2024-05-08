import requests
import re
import urllib.parse
import os

from tqdm import tqdm
from faster_whisper import WhisperModel
from bs4 import BeautifulSoup

def get_lesson_elements(url):
	try:
		response = requests.get(url)
		response.raise_for_status()

		soup = BeautifulSoup(response.content, "html.parser")

		title_rabbi_element = soup.find("div", class_="title-rabbi")
		title_lessons_element = soup.find("div", class_="title-lessons")
		video_iframe = soup.find("iframe", class_="lesson-player")

		if video_iframe:
			video_src = video_iframe['src']
			video_id_match = re.search(r'ID=(\d+)', video_src)
			if video_id_match:
				video_id = video_id_match.group(1)
			else:
				video_id = None
		else:
			video_id = None

		if not (title_rabbi_element and title_lessons_element and video_id):
			raise ValueError("לא הצלחנו למצוא אחד או יותר מהאלמנטים בדף זה.")

		title_lessons_parts = title_lessons_element.text.strip().split(' | ')

		video_url = f"https://vod.wgnmedia.com/VOD/LIB.MP4/v{video_id}.mp4"

		lesson_elements = {
			'title_rabbi': title_rabbi_element.text.strip(),
			'title_lessons': title_lessons_parts[0].strip(),
			'title_lessons_year': title_lessons_parts[1].strip(),
			'video_id': video_id,
			'video_url': video_url
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

	return {
		"video_url": video_url, 
		"video_id": video_id
		}

async def main(video_url):
	try:
		video_info = await get_video_id(video_url)
		print(f"Video ID: {video_info['video_id']}")
		print(f"Video URL: {video_info['video_url']}")
	except Exception as e:
		print(f"Error: {e}")

def download_file(url, filename):
	# Send a GET request to the URL
	response = requests.get(url, stream=True, verify=False)

	# Check if the request was successful
	if response.status_code == 200:
		# Get the total file size
		total_size = int(response.headers.get('content-length', 0))

		# Create a new file in the current directory
		file_path = os.path.join(os.getcwd(), filename)
		
		# Write the file content to the new file
		with open(file_path, 'wb') as file, tqdm(
				desc=filename,
				total=total_size,
				unit='iB',
				unit_scale=True,
				unit_divisor=1024
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

def convert_to_subtitles_time_format(seconds):
	hours = int(seconds // 3600)
	seconds %= 3600
	minutes = int(seconds // 60)
	seconds %= 60
	milliseconds = int((seconds - int(seconds)) * 1000)
	str_time = "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)
	return str_time

def write_segments_to_vtt(segments, file_path):
	with open(file_path, 'w', encoding='utf-8') as f:
		f.write("WEBVTT\n\n")
		for segment in segments:
			start_time = convert_to_subtitles_time_format(segment.start)
			end_time = convert_to_subtitles_time_format(segment.end)
			f.write("%s --> %s\n%s\n\n" % (start_time, end_time, segment.text))
			print("[%s --> %s] %s" % (start_time, end_time, segment.text))

def write_segments_to_srt(segments, file_path):
	with open(file_path, 'w', encoding='utf-8') as f:
		segment_count = 1
		for segment in segments:
			start_time = convert_to_subtitles_time_format(segment.start)
			end_time = convert_to_subtitles_time_format(segment.end)
			text = segment.text.strip()

			f.write(f"{segment_count}\n")
			f.write(f"{start_time} --> {end_time}\n")
			f.write(f"{text}\n\n")
			segment_count += 1
			print(f"[{start_time} --> {end_time}] {text}")


def transcribe(directory: str, subtitles_format: str) -> None:

	assert subtitles_format in ['srt', 'vvt'], "subtitles_format יכול להיות רק 'srt' או 'vvt'"

	model_size = "large-v2"
	initial_prompt="Hello, How is it going? Please, always use punctuation."
	model = WhisperModel(model_size, device="cuda", compute_type="float16")
	for filename in os.listdir(directory):
		if filename.endswith(".mp4"):
			audio_file_path = os.path.join(directory, filename)
			filename_without_extension = os.path.splitext(filename)[0]

			segments, info = model.transcribe(audio_file_path, beam_size=5, language='he', initial_prompt=initial_prompt)

			if(subtitles_format == 'srt'):
				output_file = f"{filename_without_extension}.srt"
				write_segments_to_srt(segments, output_file)
			else:
				output_file = f"{filename_without_extension}.vtt"
				write_segments_to_vtt(segments, output_file)
			
			print("Transcription saved to", output_file)
