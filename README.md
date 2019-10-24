# deviantart_downloader

Command-line tool for browsing DeviantArt.

## Installation

- Install Python 3.7.5+
- Download this directory
- From a terminal instance within this directory, run `python -m pip install -r requirements.txt`

Since this tool operates over the DeviantArt API, it will also be necessary to generate access credentials for DeviantArt. To do so, follow the instructions under [Gaining OAuth 2.0 Credentials](https://www.deviantart.com/developers/authentication).

Create a "creds.json" file in the "creds" directory with the following contents in this directory:
```
{
  "client_id": "your-client-id-here",
  "client_secret": "your-client-secret-here"
}
```

The tool should now be ready to use.

## Examples

To list folders available for download:
`python da_downloader.py <username> -l`

To download everything for a specific user:
`python da_downloader.py <username> --gallery-all -g -c`

To download everything into a specific directory:
`python da_downloader.py <username> -o <output_path> --gallery-all -g -c`

To download only specific folders in the gallery:
`python da_downloader.py <username> -g <folder1> "<folder with spaces in name>"`

To download only specific folders in the favorites collections:
`python da_downloader.py <username> -c <folder1> <folder2>`

To specify a file in which to put error reports for this call:
`python da_downloader.py <username> -e <error_file_path> -g`

To specify a credentials file that isn't in this directory:
`python da_downloader.py <username> -a <path_to_credentials> -g`

## Full Usage

```
usage: da_downloader.py [-h] [-a CREDS] [-o OUT_DIR] [-e ERROR_FILE] [-l] [-f]
                        [-g [GALLERIES [GALLERIES ...]]] [--gallery-all]
                        [-c [COLLECTIONS [COLLECTIONS ...]]]
                        user

DeviantArt downloader.

positional arguments:
  user                  DeviantArt username to explore.

optional arguments:
  -h, --help            show this help message and exit
  -a CREDS, --auth_creds CREDS
                        DeviantArt client credentials file path. The
                        credentials file must be valid JSON containing string
                        attributes 'client_id' and 'client_secret'. To obtain
                        client authentication keys, see DeviantArt's developer
                        portal under "Gaining OAuth 20.0 Credentials" here:
                        https://www.deviantart.com/developers/authentication
  -o OUT_DIR, --output OUT_DIR
                        Output directory for download operations.
  -e ERROR_FILE, --error-output ERROR_FILE
                        Optional command to redirect error output to file.
                        Default behavior is to print errors to command line.
  -l, --list            List available folders for the user, by location.
                        Enabling this flag causes the download commands ('-g',
                        '--gallery-all', '-c') to be ignored.
  -f, --force-rebuild   Ignore cached folders and download all available
                        Deviations available again.
  -g [GALLERIES [GALLERIES ...]], --galleries [GALLERIES [GALLERIES ...]]
                        Download gallery folders (folder names with spaces
                        must be enclosed with quotations). If no folders are
                        suggested, download all folders available. Note that
                        if a folder has already been downloaded, only new
                        Deviations will be downloaded. Caching behavior can be
                        overridden with the '--force-rebuild' option.
  --gallery-all         Use this special flag to download the 'ALL' gallery
                        folder.
  -c [COLLECTIONS [COLLECTIONS ...]], --collections [COLLECTIONS [COLLECTIONS ...]]
                        Download favorites/collections folders (folder names
                        with spaces must be enclosed with quotations). If no
                        folders are suggested, download all folders available.
                        Note that if a folder has already been downloaded,
                        only new Deviations will be downloaded. Caching
                        behavior can be overridden with the '--force-rebuild'
                        option.
```

## Backlog / TODOs

- Version this project and display version number via terminal usage
