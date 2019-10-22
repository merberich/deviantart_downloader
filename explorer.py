# -*- coding: utf-8 -*-

"""
@package explorer

Module for abstracting functionality from DeviantArt. Wraps the DeviantArt API and improves
performance when fetching resources.
"""

import deviantart
import os
from enum import Enum, auto
import json
from pathlib import PurePath
import mimetypes
import aiohttp
import aiofiles

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
    def __init__(self):
        # @todo
        pass

class Deviation():
    """Class representing one art piece on DeviantArt."""
    def __init__(self):
        self.deviationid = ""
        self.is_downloadable = False
        self.preview_src = ""

class DAExplorer():
    """API object for searching and downloading Deviations via DeviantArt."""

    MAX_ITEMS_PER_REQUEST = 20

    def __init__(self, credentials, target_user):
        """
        Open an API handle for the explorer.
        :param credentials: Credentials to use in this session.
        :param target_user: str for user to explore in this session.
        """
        self.api = None
        self.user = target_user
        # @todo other fields as necessary

        self.api = deviantart.Api(
            client_id = credentials.client_id,
            client_secret = credentials.client_secret,
            redirect_uri = ""
        )

    def list_folders(self, source, page_idx):
        """
        Fetch up to MAX_ITEMS_PER_REQUEST Folders for current user.
        :param source: Source in which to index Folders.
        :param page_idx: int Index of Folder set to fetch.
        :return List of Folders at current index, or None if index is out of bounds.
        """
        # @todo define me
        pass

    def list_deviations(self, source, folder, page_idx):
        """
        Fetch up to MAX_ITEMS_PER_REQUEST Deviations in specified Folder for current user.
        :param source: Source in which to index Folders.
        :param folder: Folder object to be indexed into. Must be generated from this API.
        :param page_idx : int Index of Deviation set to fetch.
        :return List of Deviations at current index, or None if index is out of bounds.
        """
        # @todo define me
        pass

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
                deviation_raw = self.api.download_deviation(deviation.deviationid)
                url_targ = deviation_raw["src"]
            else:
                # Deviation can't be downloaded at highest resolution, so fetch the preview
                url_targ = deviation.preview_src
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
