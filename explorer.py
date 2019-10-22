# -*- coding: utf-8 -*-

"""
@package explorer

Module for abstracting functionality from DeviantArt. Wraps the DeviantArt API and improves
performance when fetching resources.
"""

import os
from enum import Enum, auto
import json
from pathlib import PurePath
import mimetypes
import aiohttp
import aiofiles

from urllib.parse import urlencode
from urllib.error import HTTPError
from sanction import Client

class DAExplorerException(Exception):
    pass

class Credentials():
    """Credentials for self-identifying for the DeviantArt API."""
    def __init__(self):
        client_id = None
        client_secret = None

    def from_file(self, full_path):
        """
        Populate this Credentials object with the contents of a valid JSON file.
        :param full_path: A path-like object to the credentials file.
        """
        with open(full_path) as file:
            creds = json.load(file)
            if not "client_id" in creds or not type(creds["client_id"]) is str:
                raise DAExplorerException(
                    "Credentials must be valid JSON with string value 'client_id'.")
            if not "client_secret" in creds or not type(creds["client_secret"]) is str:
                raise DAExplorerException(
                    "Credentials must be valid JSON with string value 'client_secret'.")
            self.client_id = creds["client_id"]
            self.client_secret = creds["client_secret"]
        return self

    def to_file(self, full_path):
        """
        Write the contents of this Credentials object to disk.
        :param full_path: A path-like object to the credentials file.
        """
        with open(full_path, "w") as file:
            out = {
                "client_id": str(self.client_id),
                "client_secret": str(self.client_secret)
            }
            json.dump(out, file, indent="  ")
        return self

class Source(Enum):
    """
    Source of a Folder within Deviantart.
    Users can have Folders organize their gallery or favorites.
    """
    GALLERY = 1
    COLLECTION = 2

class Folder():
    """Class representing one grouping of Deviations."""
    def __init__(self):
        self.folderid = ""
        self.name = ""

class Deviation():
    """Class representing one art piece on DeviantArt."""
    def __init__(self):
        self.deviationid = ""
        self.is_downloadable = False
        self.preview_src = ""

class DAExplorer():
    """API object for searching and downloading Deviations via DeviantArt."""

    MAX_ITEMS_PER_REQUEST = 20  # Defined by DeviantArt API

    def __init__(self, credentials, target_user):
        """
        Open an API handle for the explorer.
        :param credentials: Credentials to use in this session.
        :param target_user: str for user to explore in this session.
        """
        if not type(credentials) is Credentials:
            raise DAExplorerException("Argument 'credentials' must be type Credentials.")
        if not type(target_user) is str:
            raise DAExplorerException("Argument 'target_user' must be type str.")

        # Define all class members
        self.oauth = None
        self.user = target_user

        # @todo move away from sanction oauth2 library, make this (and callers) async
        self.oauth = Client(
            auth_endpoint = "https://www.deviantart.com/oauth2/authorize",
            token_endpoint = "https://www.deviantart.com/oauth2/token",
            resource_endpoint = "https://www.deviantart.com/api/v1/oauth2",
            client_id = credentials.client_id,
            client_secret = credentials.client_secret
        )
        try:
            self.oauth.request_token(grant_type = "client_credentials")
        except HTTPError as e:
            if e.code == 401:
                raise DAExplorerException("Unauthorized. Check credentials. " + str(e))
            else:
                raise DAExplorerException("Error authorizing: " + str(e))

    def _api(self, endpoint, get_data=dict(), post_data=dict()):
        """
        Helper method to make a DeviantArt API call.
        :param endpoint: The endpoint to make the API call to.
        :param get_data: dict - data send through GET
        :param post_data: dict - data send through POST
        """

        # @todo move away from sanction oauth2 library, make this (and callers) async

        if get_data:
            request_parameter = "{}?{}".format(endpoint, urlencode(get_data))
        else:
            request_parameter = endpoint
        try:
            encdata = urlencode(post_data, True).encode('utf-8')
            response = self.oauth.request(request_parameter, data=encdata)
            if "error" in response:
                raise DAExplorerException("DA API error: " + response["error_description"])
        except HTTPError as e:
            raise DAExplorerException("HTTP error with request: " + str(e))
        return response

    def _get_gallery_folders(self, page_idx):
        """
        Helper method to call DeviantArt API function "/gallery/folders".
        :param page_idx: int Index of the page to fetch, pagelen MAX_ITEMS_PER_REQUEST.
        :return dict Response from the API.
        """
        return self._api("/gallery/folders", get_data={
            "username": self.user,
            "offset": page_idx * DAExplorer.MAX_ITEMS_PER_REQUEST,
            "limit": DAExplorer.MAX_ITEMS_PER_REQUEST,
            "mature_content": True
        })

    def _get_collection_folders(self, page_idx):
        """
        Helper method to call DeviantArt API function "/collections/folders".
        :param page_idx: int Index of the page to fetch, pagelen MAX_ITEMS_PER_REQUEST.
        :return dict Response from the API.
        """
        return self._api("/collections/folders", get_data={
            "username": self.user,
            "offset": page_idx * DAExplorer.MAX_ITEMS_PER_REQUEST,
            "limit": DAExplorer.MAX_ITEMS_PER_REQUEST,
            "mature_content": True
        })

    def _get_gallery_all(self, page_idx):
        """
        Helper method to call DeviantArt API function "/gallery/all".
        :param page_idx: int Index of the page to fetch, pagelen MAX_ITEMS_PER_REQUEST.
        :return dict Response from the API.
        """
        return self._api("/gallery/all", get_data={
            "username": self.user,
            "offset": page_idx * DAExplorer.MAX_ITEMS_PER_REQUEST,
            "limit": DAExplorer.MAX_ITEMS_PER_REQUEST,
            "mature_content": True
        })

    def _get_gallery_folder(self, folderid, page_idx):
        """
        Helper method to call DeviantArt API function "/gallery/{folderid}".
        :param folderid: str GUID for the folder to index into.
        :param page_idx: int Index of the page to fetch, pagelen MAX_ITEMS_PER_REQUEST.
        :return dict Response from the API.
        """
        return self._api(f"/gallery/{folderid}", get_data={
            "username": self.user,
            "mode": "newest",
            "offset": page_idx * DAExplorer.MAX_ITEMS_PER_REQUEST,
            "limit": DAExplorer.MAX_ITEMS_PER_REQUEST,
            "mature_content": True
        })

    def _get_collection_folder(self, folderid, page_idx):
        """
        Helper method to call DeviantArt API function "/collections/{folderid}".
        :param folderid: str GUID for the folder to index into.
        :param page_idx: int Index of the page to fetch, pagelen MAX_ITEMS_PER_REQUEST.
        :return dict Response from the API.
        """
        return self._api(f"/collections/{folderid}", get_data={
            "username": self.user,
            "offset": page_idx * DAExplorer.MAX_ITEMS_PER_REQUEST,
            "limit": DAExplorer.MAX_ITEMS_PER_REQUEST,
            "mature_content": True
        })

    def _download_deviation(self, deviationid):
        """
        Helper method to call DeviantArt API function "/deviation/download/{deviationid}".
        :param deviationid: str GUID for the Deviation to identify.
        :return dict Response from the API.
        """
        return self._api(f"/deviation/download/{deviationid}")

    def list_folders(self, source, page_idx):
        """
        Fetch up to MAX_ITEMS_PER_REQUEST Folders for current user.
        :param source: Source in which to index Folders.
        :param page_idx: int Index of Folder set to fetch.
        :return List of Folders at current index (or None if index is out of bounds).
        """
        if not type(source) is Source:
            raise DAExplorerException("Argument 'source' must be type Source.");
        if not type(page_idx) is int:
            raise DAExplorerException("Argument 'page_idx' must be type int.")

        output = []
        response = None
        if source is Source.GALLERY:
            response = self._get_gallery_folders(page_idx)
        elif source is Source.COLLECTION:
            response = self._get_collection_folders(page_idx)

        # End condition: no more Folders to find
        if response == None or (not response["has_more"] and len(response["results"]) == 0):
            return None

        for folder_info in response["results"]:
            output.append(Folder())
            folder = output[-1]
            folder.folderid = folder_info["folderid"]
            folder.name = folder_info["name"]

        return output

    def list_deviations(self, source, folder, page_idx):
        """
        Fetch up to MAX_ITEMS_PER_REQUEST Deviations in specified Folder for current user.
        :param source: Source in which to index Folders.
        :param folder: Folder object to be indexed into. Must be generated from this API.
            If source is GALLERY and this parameter is None, this method will search
            'gallery/all'. If source is COLLECTION and this parameter is None, this method
            will return None.
        :param page_idx : int Index of Deviation set to fetch.
        :return List of Deviations at current index (or None if index is out of bounds).
        """
        if not type(source) is Source:
            raise DAExplorerException("Argument 'source' must be type Source.");
        if not type(folder) is Folder and folder != None:
            print(type(folder))
            print(type(folder) is None)
            raise DAExplorerException("Argument 'folder' must be type Folder or None.");
        if not type(page_idx) is int:
            raise DAExplorerException("Argument 'page_idx' must be type int.")

        output = []
        response = None
        if source is Source.GALLERY:
            if folder is None:
                response = self._get_gallery_all(page_idx)
            else:
                response = self._get_gallery_folder(folder.folderid, page_idx)
        elif source is Source.COLLECTION:
            if folder is None:
                return output
            else:
                response = self._get_collection_folder(folder.folderid, page_idx)

        # End condition: no more Deviations to find
        if response == None or (not response["has_more"] and len(response["results"]) == 0):
            return None

        for dev_info in response["results"]:
            output.append(Deviation())
            dev = output[-1]
            dev.deviationid = dev_info["deviationid"]
            dev.is_downloadable = dev_info["is_downloadable"]
            if "content" in dev_info:
                dev.preview_src = dev_info["content"]["src"]

        return output

    async def download_deviation(self, deviation, full_path):
        """
        Download the requested Deviation.
        :param deviation: Deviation object to download. Must be generated from this API.
        :param full_path: path-like object (excluding file name) in which to store result.
        """
        if not type(deviation) is Deviation:
            raise DAExplorerException("Argument 'deviation' must be type Deviation.")
        os.makedirs(PurePath(full_path), exist_ok = True)  # Ensure the output path exists
        try:
            url_targ = ""
            if deviation.is_downloadable:
                deviation_raw = self._download_deviation(deviation.deviationid)
                url_targ = deviation_raw["src"]
            elif deviation.preview_src:
                # Deviation can't be downloaded at highest resolution, so fetch the preview
                url_targ = deviation.preview_src
            else:
                # Deviation has no image content to be downloaded
                return
            async with aiohttp.ClientSession() as session:
                async with session.get(url_targ) as resp:
                    if resp.status == 200:  # HTTP success
                        extension = mimetypes.guess_extension(resp.content_type, strict = False)
                        if not extension:
                            # Do it the hackish way if mimetypes can't figure it out
                            extension = "." + url_targ.split("/")[-1].split(".")[1].split("?")[0]
                        f = await aiofiles.open(
                            PurePath(full_path).joinpath(str(deviation.deviationid) + extension),
                            mode='wb'
                        )
                        await f.write(await resp.read())
                        await f.close()
        except Exception as e:
            raise DAExplorerException("Error downloading deviation " + str(deviation.deviationid)
                + ": " + str(e))
