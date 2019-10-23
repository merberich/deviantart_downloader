# -*- coding: utf-8 -*-

"""
@package da_downloader

Runnable script frontend for DeviantArt downloader tool.
"""

import sys
from explorer import *
import argparse
import pathlib
import asyncio as aio

def _build_parser(parser):
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
        dest = "error_file",
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

def _build_folder_list(api, source, error_stream):
    folders = []
    idx = 0
    while True:
        try:
            temp = api.list_folders(source, idx)
        except DAExplorerException as e:
            print("Failed to fetch gallery folders: ", file = error_stream)
            sys.exit()
        if temp == None:
            break
        folders += temp
        idx += 1
    return folders

def _list_all(api, error_stream):
    # Build list of folders for each source
    gallery_folders = _build_folder_list(api, Source.GALLERY, error_stream)
    collection_folders = _build_folder_list(api, Source.COLLECTION, error_stream)

    # Dump directly to command line
    print("Gallery folders:")
    for folder in gallery_folders:
        print("  " + folder.name)
    print("Collection folders:")
    for folder in collection_folders:
        print("  " + folder.name)

async def _download_group(api, deviations, output_directory):
    tasks = []
    for deviation in deviations:
        tasks.append(aio.create_task(
            api.download_deviation(deviation, output_directory)
        ))
    await aio.gather(*tasks)

def _download_folder(api, source, folder, error_stream, rebuild_cache):
    # Identify the output directory for this folder download
    local_out_dir = None
    if source == Source.GALLERY and folder == None:
        local_out_dir = output_directory.joinpath("GalleryAll")
    elif source == Source.GALLERY:
        local_out_dir = output_directory.joinpath("Gallery").joinpath(folder.name)
    elif source == Source.COLLECTION:
        local_out_dir = output_directory.joinpath("Collection").joinpath(folder.name)
    os.makedirs(local_out_dir, exist_ok = True)

    print("Downloading " + str(local_out_dir.absolute()) + ".", end="", flush=True)

    # Get the last cached deviation ID
    last_cached = ""
    cache_path = local_out_dir.joinpath("cache")
    if os.path.exists(cache_path):
        with open(local_out_dir.joinpath("cache"), "r") as cache:
            last_cached = cache.read()

    # Do the folder download
    idx = 0
    first_fetched = None
    while True:
        try:
            devs = api.list_deviations(source, folder, idx)
        except DAExplorerException as e:
            print(f"Failed to list deviations in folder {folder.name} index {idx}",
                file = error_stream)
            sys.exit()

        # Detect end of deviations in folder
        if devs == None:
            break

        # For caching
        if idx == 0:
            first_fetched = devs[0].deviationid

        # Download only files that aren't already cached
        hit_cache_end = False
        if not rebuild_cache and last_cached != "":
            for i, dev in enumerate(devs):
                if dev.deviationid == last_cached:
                    devs = devs[0:i]  # Slice down to non-cached stuff
                    hit_cache_end = True
        '''
        # End downloading if files are already cached
        # @todo revise this; still have to download the whole group if only one dev added
        if not rebuild_cache:
            if len(list(filter(lambda f: f.startswith(devs[0].deviationid), \
                os.listdir(local_out_dir)))):
                break
        '''

        # Download this group of deviations
        aio.get_event_loop().run_until_complete(_download_group(api, devs, local_out_dir))
        print(".", end="", flush=True)
        idx += 1

        if hit_cache_end:
            break;

    # Generate the new cache
    with open(local_out_dir.joinpath("cache"), "w") as cache:
        cache.write(first_fetched)
    print(" Done.")

def _download_folders(api, source, folders, error_stream, rebuild_cache):
    available_folders = set(_build_folder_list(api, source, error_stream))
    folders_to_download = set()
    if len(folders) == 0:  # download everything
        folders_to_download = available_folders
    else:
        desired_folders = set(folders)
        for folder in available_folders:
            if folder.name in desired_folders:
                folders_to_download.add(folder)

    for folder in folders_to_download:
        _download_folder(api, source, folder, error_stream, rebuild_cache)

if __name__ == "__main__":
    # Build argument parser ------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="DeviantArt downloader.")
    _build_parser(parser)

    # Retrieve options from parser -----------------------------------------------------------------
    args = parser.parse_args()

    # Error redirection first, since errors can happen anywhere with the API
    error_stream = sys.stdout
    if args.error_file:
        error_stream = open(args.error_file, "w+")

    # API arguments
    creds = None
    try:
        creds = Credentials().from_file(args.creds)
    except Exception as e:
        print("Error obtaining credentials: " + str(type(e)) + ": " + str(e), file = error_stream)
        sys.exit()
    username = args.user

    # Output directory selection
    output_directory = pathlib.Path(args.out_dir).joinpath(username)

    # Flag commands
    should_list = args.do_list
    should_rebuild = args.force_rebuild
    should_get_gallery_all = args.gallery_all

    # Download commands
    download_galleries = args.galleries
    download_collections = args.collections

    # Do everything as asked via CLI -----------------------------------------------------
    # Open the API
    try:
        api = DAExplorer(
            credentials = creds,
            target_user = username
        )
    except DAExplorerException as e:
        print("Failed to open API: " + str(e))
        sys.exit()

    # Either list available folders, or start download
    if should_list:
        _list_all(api, error_stream)
    else:
        # Handle --gallery-all
        if should_get_gallery_all:
            _download_folder(api, Source.GALLERY, None, error_stream, should_rebuild)

        # Handle --galleries
        if download_galleries != None:
            _download_folders(api, Source.GALLERY, download_galleries, error_stream, should_rebuild)

        # Handle --collections
        if download_collections != None:
            _download_folders(api, Source.COLLECTION, download_galleries,
                error_stream, should_rebuild)

    # Close out safely -----------------------------------------------------------------------------
    if error_stream != sys.stdout:
        error_stream.close()

    # @todo consider restructuring this into a class so that members can be shared
    # @todo refactor so that sys.exit() still exits safely (error stream redirection, etc)
    #       generally, more robust error handling here
    # @todo setuptools / requirements
    # @todo update README with full instructions for how to use
