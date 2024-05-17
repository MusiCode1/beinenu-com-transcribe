import urllib.parse
import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile
from typing import Union, Literal


class GoogleDriveUpload:
    def __init__(self, gauth: GoogleAuth) -> None:
        self.gauth = gauth
        # self.gauth.LoadCredentialsFile("mycreds.txt")
        self.drive = GoogleDrive(self.gauth)

    def local_server_auth_and_save(self):
        self.gauth.LocalWebserverAuth()
        self.gauth.SaveCredentialsFile("mycreds.txt")
        self.drive = GoogleDrive(self.gauth)

    def check_if_folder_name_exist(
        self, folder_name: str, parent_folder_id: str
    ) -> Union[GoogleDriveFile, Literal[False]]:

        q = f"title='{folder_name}' and '{parent_folder_id}' in parents"
        file_list = self.drive.ListFile({"q": q}).GetList()
        if len(file_list) > 1:
            raise ValueError("יש יותר מתיקייה אחת מתאימה")
        if len(file_list) > 0:
            folder = file_list[0]
            return folder
        else:
            return False

    def create_folder(self, name: str, parent_folder_id: str):
        file = self.drive.CreateFile(
            {
                "title": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [{"id": parent_folder_id}],
            }
        )
        file.Upload()
        return file

    def create_folder_if_not_exist(
        self, folder_name: str, parent_folder_id: str
    ) -> GoogleDriveFile:

        folder_details = self.check_if_folder_name_exist(folder_name, parent_folder_id)

        if folder_details:
            return folder_details
        else:
            return self.create_folder(folder_name, parent_folder_id)

    def upload_file(self, local_file_path: str, parent_folder_id: str):

        parents = [{"id": parent_folder_id}]

        file_name = split_path_and_filename(local_file_path)

        file = self.drive.CreateFile({"title": file_name, "parents": parents})
        file.SetContentFile(local_file_path)
        file.Upload()
        return file


def split_path_and_filename(path_or_filename):
    if os.path.isabs(path_or_filename):
        filename = os.path.split(path_or_filename)
    else:
        filename = path_or_filename

    return filename

def convert_google_code(code: str):
    parsed_url = urllib.parse.urlparse(code)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    code = query_params["code"][0]

    return code
