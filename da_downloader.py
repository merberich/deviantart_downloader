# -*- coding: utf-8 -*-

"""
@package da_downloader

Runnable script frontend for DeviantArt downloader tool.
"""

import sys
from explorer import *
from frontend import *

if __name__ == "__main__":
    downloader = DAFrontend()
    downloader.run(sys.argv[1:])  # Ensure to omit the script call itself

    # @todo consider using a different naming scheme for Deviations saved (easier identification):
    #       <GUID>__<upload_date>__<sanitized_title> ?
    #       <GUID>__<upload_date> ?
    #       <upload_date>__<GUID> ?
    #       <upload_date>__<GUID>__<sanitized_title> ?
    # @todo update README with full instructions for how to use
