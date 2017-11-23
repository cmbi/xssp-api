#!/usr/bin/python

import sys
import os
import logging


logging.basicConfig(level=logging.INFO)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from xssp_api.controllers.blast import create_databank

from xssp_api.default_settings import (HG_HSSP_DATABANK, HSSP_STO_DATABANK,
                                       HG_HSSP_ROOT, HSSP_STO_ROOT)


create_databank(HG_HSSP_ROOT, HG_HSSP_DATABANK)
create_databank(HSSP_STO_ROOT, HSSP_STO_DATABANK)
