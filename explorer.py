# -*- coding: utf-8 -*-

"""
@package explorer

Module for abstracting functionality from DeviantArt. Wraps the DeviantArt API and improves
performance when fetching resources.
"""

import os
from enum import Enum, auto
import json

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
    def __init__(self):
        # @todo
        pass

class DAExplorer():
    """API object for searching and downloading Deviations via DeviantArt."""

    MAX_ITEMS_PER_REQUEST = 20

    def __init__(self):
        # @todo define class fields
        pass

    def open(self, credentials, target_user):
        """
        Open an API handle for the explorer.
        :param credentials: Credentials to use in this session.
        :param target_user: str for user to explore in this session.
        """
        # @todo define me
        pass

    def close(self):
        """Close the active API session, if any."""
        # @todo define me
        pass

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
        :param deviation Deviation object to download. Must be generated from this API.
        :param full_path path-like object (exclusing file name) in which to store result.
        """
        # @todo this
        pass
