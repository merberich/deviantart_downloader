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
    parser.add_argument("-a", "--auth_creds",
        dest = "creds",
        type = str,
        default = "creds.json",
        help = """
            DeviantArt client credentials file path. The credentials file must be valid
            JSON containing string attributes 'client_id' and 'client_secret'. To
            obtain client authentication keys, see DeviantArt's developer portal under
            "Gaining OAuth 20.0 Credentials" here:
            https://www.deviantart.com/developers/authentication
            """
    )
    parser.add_argument("-o", "--output",
        dest = "out_dir",
        type = str,
        default = ".",
        help = "Output directory for download operations."
    )
    parser.add_argument("-e", "--error-output",
        dest = "error_dir",
        type = str,
        default = None,
        help = """
            Optional command to redirect error output to file. Default behavior is to print errors to command line.
            """
    )
    parser.add_argument("-l", "--list",
        dest = "do_list",
        action = "store_true",
        help = """
            List available folders for the user, by location. Enabling this flag causes the download
            commands ('-g', '--gallery-all', '-c') to be ignored.
            """
    )
    parser.add_argument("-f", "--force-rebuild",
        dest = "force_rebuild",
        action = "store_true",
        help = "Ignore cached folders and download all available Deviations available again."
    )
    parser.add_argument("-g", "--galleries",
        dest = "galleries",
        type = str,
        nargs = "*",
        help = """
            Download gallery folders (folder names with spaces must be enclosed
            with quotations). If no folders are suggested, download all folders
            available. Note that if a folder has already been downloaded, only new
            Deviations will be downloaded. Caching behavior can be overridden with the
            '--force-rebuild' option.
            """
    )
    parser.add_argument("--gallery-all",
        dest = "gallery_all",
        action = "store_true",
        help = "Use this special flag to download the 'ALL' gallery folder."
    )
    parser.add_argument("-c", "--collections",
        dest = "collections",
        type = str,
        nargs = "*",
        help = """
            Download favorites/collections folders (folder names with spaces must be
            enclosed with quotations). If no folders are suggested, download all folders
            available. Note that if a folder has already been downloaded, only new
            Deviations will be downloaded. Caching behavior can be overridden with the
            '--force-rebuild' option.
        """
    )

    # Retrieve options from parser
    args = parser.parse_args()
    try:
        creds = Credentials().from_file(args.creds)
    except Exception as e:
        print("Error obtaining credentials: " + str(type(e)) + ": " + str(e))
        sys.exit()
    user = args.user
    # @todo remaining optional arguments:
    # - output directory
    # - error redirection
    # - list command
    # - rebuild cache command
    # - download galleries
    # - gallery-all command
    # - download collections

    # Open the API
    api = DAExplorer(
        credentials = creds,
        target_user = user
    )

    # Perform requested actions
    # @todo Everything, performant. Don't forget to write a cache algo.
