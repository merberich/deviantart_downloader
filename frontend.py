# -*- coding: utf-8 -*-

"""
@package frontend

Module for representing functionality exposed in the downloader logic.
"""

import sys
from explorer import *
import argparse
import pathlib
import asyncio as aio

class DAFrontend():
    def __init__(self):
        # Define class members
        self.parser = argparse.ArgumentParser(description = "DeviantArt downloader.")
        self._build_parser()

        self.api = None
        self.error_stream = sys.stdout
        self.creds = None
        self.user = None
        self.out_dir = None
        self.flag_list = False
        self.flag_rebuild = False
        self.flag_gal_all = False
        self.down_gal = None
        self.down_col = None

    def _build_parser(self):
        """Helper method: generate parser commands."""

        self.parser.add_argument("user",
            type = str,
            help = "DeviantArt username to explore.",
        )
        self.parser.add_argument("-a", "--auth_creds",
            dest = "creds",
            type = str,
            default = ".\creds\creds.json",
            help = """
                DeviantArt client credentials file path. The credentials file must be valid
                JSON containing string attributes 'client_id' and 'client_secret'. To
                obtain client authentication keys, see DeviantArt's developer portal under
                "Gaining OAuth 20.0 Credentials" here:
                https://www.deviantart.com/developers/authentication
                """
        )
        self.parser.add_argument("-o", "--output",
            dest = "out_dir",
            type = str,
            default = ".",
            help = "Output directory for download operations."
        )
        self.parser.add_argument("-e", "--error-output",
            dest = "error_file",
            type = str,
            default = None,
            help = """
                Optional command to redirect error output to file. Default behavior is to print errors to command line.
                """
        )
        self.parser.add_argument("-l", "--list",
            dest = "do_list",
            action = "store_true",
            help = """
                List available folders for the user, by location. Enabling this flag causes the download
                commands ('-g', '--gallery-all', '-c') to be ignored.
                """
        )
        self.parser.add_argument("-f", "--force-rebuild",
            dest = "force_rebuild",
            action = "store_true",
            help = "Ignore cached folders and download all available Deviations available again."
        )
        self.parser.add_argument("-g", "--galleries",
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
        self.parser.add_argument("--gallery-all",
            dest = "gallery_all",
            action = "store_true",
            help = "Use this special flag to download the 'ALL' gallery folder."
        )
        self.parser.add_argument("-c", "--collections",
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

    def _populate_args(self, raw_args):
        """
        Helper method: parse passed arguments and populate class members.
        :param raw_args: str Arguments for this application.
        """
        args = self.parser.parse_args(raw_args)

        # Error redirection first, since it affects all options following
        if args.error_file:
            self.error_stream = open(args.error_file, "w+")

        # API arguments
        try:
            self.creds = Credentials().from_file(args.creds)
        except Exception as e:
            print("Error obtaining credentials: " + str(type(e)) + ": " + str(e),
                file = error_stream)
            sys.exit()
        self.user = args.user

        # Output directory selection
        self.out_dir = pathlib.Path(args.out_dir).joinpath(self.user)

        # Flag commands
        self.flag_list = args.do_list
        self.flag_rebuild = args.force_rebuild
        self.flag_gal_all = args.gallery_all

        # Download commands
        self.down_gal = args.galleries
        self.down_col = args.collections

    def _build_folder_list(self, source):
        """
        Helper method: construct list of folders available for the given source.
        :param source: Source for the folders.
        :return list of Folders within the designated Source.
        """
        folders = []
        idx = 0
        while True:
            # Multiple attempts for fetching the Folder list for this page
            retry_count = 0
            MAX_RETRIES = 3
            last_except = None
            temp = None
            while retry_count < MAX_RETRIES:
                try:
                    temp = self.api.list_folders(source, idx)
                    break
                except Exception as e:
                    last_except = e
                    retry_count += 1
                if retry_count == MAX_RETRIES:
                    print("Failed to fetch gallery folders: " + str(type(last_except))
                        + ": " + str(last_except), file = self.error_stream)
                    raise Exception("Too many retries.")

            # Detect end of Folder list
            if temp == None:
                break

            # Append and continue through list
            folders += temp
            idx += 1
        return folders

    def _list_folders(self):
        """Helper method: display available folders for each source."""
        # Build list of folders for each source
        gallery_folders = self._build_folder_list(Source.GALLERY)
        collection_folders = self._build_folder_list(Source.COLLECTION)

        # Dump directly to command line
        print("Gallery folders:")
        for folder in gallery_folders:
            print("  " + folder.name)
        print("Collection folders:")
        for folder in collection_folders:
            print("  " + folder.name)

    async def _download_with_error(self, deviation, out_dir):
        """
        Helper method: error-handled API download of one Deviation.
        :param deviation: Deviation to download.
        :param out_dir: path-like to the directory where output should be placed.
        """
        try:
            await self.api.download_deviation(deviation, out_dir)
        except Exception as e:
            print("Failed to download deviation " + deviation.deviationid + ": "
                + str(type(e)) + ": " + str(e), file = self.error_stream)

    async def _download_group(self, deviations, out_dir):
        """
        Helper method: batch download a group of Deviations asynchronously (better performance).
        :param deviations: list of Deviations to download.
        :param out_dir: path-like to the directory where output should be placed.
        """
        tasks = []
        for deviation in deviations:
            tasks.append(aio.create_task(
                self._download_with_error(deviation, out_dir)
            ))
        await aio.gather(*tasks)

    def _download_folder(self, source, folder):
        """
        Helper method to handle downloading all Deviations within a specified Folder.
        If source == Source.GALLERY and folder == None, download Gallery-ALL.
        :param source: Source for the folder to download.
        :param folder: Folder to download.
        """
        # Identify the output directory for this folder download
        local_out_dir = None
        if source == Source.GALLERY and folder == None:
            local_out_dir = self.out_dir.joinpath("GalleryAll")
        elif source == Source.GALLERY:
            local_out_dir = self.out_dir.joinpath("Gallery").joinpath(folder.name)
        elif source == Source.COLLECTION:
            local_out_dir = self.out_dir.joinpath("Collection").joinpath(folder.name)
        # @note the download operation will create the directory if it doesn't already exist

        print("Downloading " + str(local_out_dir.absolute()) + ".", end="", flush=True)

        # Get the last cached deviation ID
        last_cached = ""
        cache_path = local_out_dir.joinpath("cache")
        if os.path.exists(cache_path):
            with open(local_out_dir.joinpath("cache"), "r") as cache:
                last_cached = cache.read()

        # Do the folder download
        idx = 0
        first_fetched_deviationid = None
        while True:
            # Multiple attempts for fetching the Deviation list for this page
            retry_count = 0
            MAX_RETRIES = 3
            last_except = None
            devs = None
            while retry_count < MAX_RETRIES:
                try:
                    devs = self.api.list_deviations(source, folder, idx)
                    break
                except Exception as e:
                    last_except = e
                    retry_count += 1
                if retry_count == MAX_RETRIES:
                    print("Failed: " + str(type(last_except)) + ": " + str(last_except))
                    print(f"Failed to list deviations in folder '{folder.name}' index '{idx}': "
                        + str(type(last_except)) + ": " + str(last_except),
                        file = self.error_stream)
                    return

            # Detect end of Deviation list
            if devs == None:
                break

            # For caching
            if idx == 0:
                first_fetched_deviationid = devs[0].deviationid

            # Download only files that aren't already cached
            hit_cache_end = False
            if not self.flag_rebuild and last_cached != "":
                for i, dev in enumerate(devs):
                    if dev.deviationid == last_cached:
                        devs = devs[0:i]  # Slice down to non-cached stuff
                        hit_cache_end = True

            # Download this group of deviations
            aio.get_event_loop().run_until_complete(self._download_group(devs, local_out_dir))
            print(".", end="", flush=True)
            idx += 1

            if hit_cache_end:
                break;

        # Generate the new cache
        with open(local_out_dir.joinpath("cache"), "w") as cache:
            cache.write(first_fetched_deviationid)
        print("Done.")

    def _download_folders(self, source, folder_names):
        """
        Helper method to download multiple folders' worth of Deviations.
        If folder_names is empty, download all folders.
        :param source: Source for the folders to download.
        :param folder_names: list of str identifying the folders in the source to download.
        """
        # Generate list of folders to target
        available_folders = set(self._build_folder_list(source))
        folders_to_download = set()
        if len(folder_names) == 0:
            # Download everything!
            folders_to_download = available_folders
        else:
            # Download only user-specified folders
            desired_folders = set(folder_names)
            for folder in available_folders:
                if folder.name in desired_folders:
                    folders_to_download.add(folder)

        # Do the downloads
        for folder in folders_to_download:
            self._download_folder(source, folder)

    def _safe_close(self):
        """Helper method: ensure all open resource handles are closed before exit."""
        if self.error_stream != sys.stdout:
            self.error_stream.close()

    def run(self, args):
        self._populate_args(args)

        try:
            # Open the API for use
            try:
                self.api = DAExplorer(
                    credentials = self.creds,
                    target_user = self.user
                )
            except DAExplorerException as e:
                print("Failed to open API: " + str(e))
                return

            # Application functions
            if self.flag_list:
                # Ignore other commands; only list available folders
                self._list_folders()
            else:
                # Do downloads as requested

                # Handle --gallery-all first
                if self.flag_gal_all:
                    self._download_folder(Source.GALLERY, None)

                # Handle --galleries
                if self.down_gal != None:
                    self._download_folders(Source.GALLERY, self.down_gal)

                # Handle --collections
                if self.down_col != None:
                    self._download_folders(Source.COLLECTION, self.down_col)
        except Exception as e:
            print("Error: " + str(type(e)) + ": " + str(e),
                file = self.error_stream)
            print("Please report this to a maintainer!", file = self.error_stream)
            return
        finally:
            self._safe_close()
