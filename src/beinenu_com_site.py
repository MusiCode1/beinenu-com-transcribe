import urllib.parse
import requests
import re

from bs4 import BeautifulSoup, Tag


def get_lesson_elements(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        title_rabbi_element = soup.find("div", class_="title-rabbi")
        title_lessons_element = soup.find("div", class_="title-lessons")
        video_iframe = soup.find("iframe", class_="lesson-player")

        if video_iframe and isinstance(video_iframe, Tag):
            video_src = video_iframe["src"]

            if isinstance(video_src, list):
                video_src = video_src[0]

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
            "title_lessons_year": title_lessons_parts[1].replace('"', "").strip(),
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

def check_lesson_link(link: str) -> None:
    if link.startswith("https://beinenu.com/lessons/"):
        print("Link is valid")
        print(urllib.parse.unquote(link))
    else:
        raise ValueError("Error: Invalid link")
