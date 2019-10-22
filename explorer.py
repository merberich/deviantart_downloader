# -*- coding: utf-8 -*-

"""Module for abstracting functionality from DeviantArt. Wraps the DeviantArt API and improves
performance when fetching resources."""

import os
from enum import Enum, auto
import json

class DAExplorerException(Exception):
    pass

class Credentials():
    def __init__(self):
        client_id = None
        client_secret = None

    def from_file(self, full_path):
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
        with open(full_path, "w") as file:
            out = {
                "client_id": str(self.client_id),
                "client_secret": str(self.client_secret)
            }
            json.dump(out, file, indent="  ")
        return self

class Source(Enum):
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
    def __init__(self):
        # @todo define class fields
        pass

    def open(self, credentials, target_user):
        # @todo define me
        pass

    def list_folders(self, source, page_idx):
        # @note source can be either Gallery or Collections
        # @todo define me
        pass

    def list_deviations(self, source, folder, page_idx):
        # @note source can be either Gallery or Collections
        # @todo define me
        pass

    async def download_deviation(self, deviation):
        # @todo this
        pass
