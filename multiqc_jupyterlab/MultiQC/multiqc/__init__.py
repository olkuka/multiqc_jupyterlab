#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" __init__.py
~~~~~~~~~~~~~~~~~~~~
Initialises when multiqc module is loaded.

Makes the following available under the main multiqc namespace:
- load(), show(), get_samples()
- config
- config.logger
- __version__
"""

import logging
from .utils import config
from .multiqc import add, init, load, show, get_samples, get_modules

config.logger = logging.getLogger(__name__)

__version__ = config.version
