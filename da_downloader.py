# -*- coding: utf-8 -*-

"""
@package da_downloader

Runnable script frontend for DeviantArt downloader tool.
"""

import sys
from explorer import *
import argparse

if __name__ == "__main__":
    # Build argument parser
    parser = argparse.ArgumentParser(description="DeviantArt downloader.")
    parser.add_argument("user",
        type = str,
        help = "DeviantArt username to explore.",
    )
    parser.add_argument("-c", "--creds",
        dest = "creds",
        type = str,
        default = "creds.json",
        help = "DeviantArt client credentials file path."
    )
    # @todo optional arguments:
    # - output directory
    # - force rebuild of cache
    # - select target folders
    # - download or just identify

    # Retrieve options from parser
    args = parser.parse_args()
    try:
        creds = Credentials().from_file(args.creds)
    except Exception as e:
        print("Error obtaining credentials: " + str(type(e)) + ": " + str(e))
        sys.exit()
    user = args.user
    # @todo remaining optional arguments

    # Open the API
    api = DAExplorer(
        credentials = creds,
        target_user = user
    )

    # Perform requested actions
    # @todo remaining functions
