import requests
import os
import re

from tqdm import tqdm

def clean_filename(filename: str):
    """
    Removes all invalid characters for filenames across different operating systems.
    Returns a cleaned version of the filename.
    """
    bad_chars = r'[<>:/\\|?*"\']'
    cleaned = re.sub(bad_chars, "", filename)
    return cleaned




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


