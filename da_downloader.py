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
