"""Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work."""
from __future__ import annotations

import io
import logging
import os
import traceback


def findCaller(stack_info=False, stacklevel=2):  # pragma: no cover
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    f = logging.currentframe()  # noqa: VNE001
    # On some versions of IronPython, currentframe() returns None if
    # IronPython isn't run with -X:Frames.
    if f is None:
        return "(unknown file)", 0, "(unknown function)", None
    while stacklevel > 0:
        next_f = f.f_back
        if next_f is None:
            ## We've got options here.
            ## If we want to use the last (deepest) frame:
            break
            ## If we want to mimic the warnings module:
            # return ("sys", 1, "(unknown function)", None) # noqa: ERA001
            ## If we want to be pedantic:  # noqa: ERA001
            # raise ValueError("call stack is not deep enough") # noqa: ERA001
        f = next_f  # noqa: VNE001
        if not _is_internal_frame(f):
            stacklevel -= 1
    co = f.f_code
    sinfo = None
    if stack_info:
        with io.StringIO() as sio:
            sio.write("Stack (most recent call last):\n")
            traceback.print_stack(f, file=sio)
            sinfo = sio.getvalue()
            if sinfo[-1] == "\n":
                sinfo = sinfo[:-1]
    return co.co_filename, f.f_lineno, co.co_name, sinfo


# The following is based on warnings._is_internal_frame. It makes sure that
# frames of the import mechanism are skipped when logging at module level and
# using a stacklevel value greater than one.
def _is_internal_frame(frame):  # pragma: no cover
    """Signal whether the frame is a CPython or logging module internal."""
    filename = os.path.normcase(frame.f_code.co_filename)
    return filename == logging._srcfile or ("importlib" in filename and "_bootstrap" in filename)
