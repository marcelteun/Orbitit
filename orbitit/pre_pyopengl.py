# 2021-12-19:
# work-around for PyOpenGL bug (see commit message)
import os
if not os.environ.get("PYOPENGL_PLATFORM", ""):
    print("Note: environment variable PYOPENGL_PLATFORM undefined")
    if os.environ.get("DESKTOP_SESSION", "").lower() == "i3" or\
            "wayland" in os.getenv("XDG_SESSION_TYPE", "").lower():
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
        print("Note: PYOPENGL_PLATFORM set to egl")
    else:
        print("If not working (e.g. invalid context) define PYOPENGL_PLATFORM")
