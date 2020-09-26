# ---------------------------------- common startup site handling -----------------------------------
import inspect
import os
import site
import sys


def common_startup():
    # Add site-packages to sys.path
    package_dir = os.path.dirname(os.path.dirname(os.path.dirname(inspect.getfile(inspect.currentframe()))))  # my god

    if package_dir not in sys.path:
        site.addsitedir(package_dir)


common_startup()

# ---------------------------------- !common startup site handling -----------------------------------
