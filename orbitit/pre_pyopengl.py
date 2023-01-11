# 2021-12-19:
"""work-around for PyOpenGL bug (see commit message)"""
import logging
import os
if not os.environ.get("PYOPENGL_PLATFORM", ""):
    logging.info("Note: environment variable PYOPENGL_PLATFORM undefined")
    if os.environ.get("DESKTOP_SESSION", "").lower() == "i3" or\
            "wayland" in os.getenv("XDG_SESSION_TYPE", "").lower():
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
        logging.info("Note: PYOPENGL_PLATFORM set to egl")
    else:
        logging.info("If not working (e.g. invalid context) define PYOPENGL_PLATFORM")
