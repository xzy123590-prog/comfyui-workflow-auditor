"""Single-file reads, with no-follow handles and bounded allocation."""
import os
import stat
from contextlib import contextmanager
from pathlib import PurePath
from .diagnostics import Rejected
from .limits import DEFAULT_MAX_BYTES, MAX_BYTES, validate_limit


def is_link_or_reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & 0x400)


def validate_path(path):
    if type(path) is not str or not path or "\0" in path:
        raise Rejected("INPUT_NOT_REGULAR_FILE")
    normalized = path.replace("/", "\\")
    if normalized.startswith(("\\\\?\\", "\\\\.\\", "\\??\\")):
        raise Rejected("INPUT_DEVICE_PATH")
    if normalized.startswith("\\\\"):
        raise Rejected("INPUT_UNC_PATH")
    # Reject ambiguous drive-relative paths and Windows alternate data streams.
    if os.name == "nt":
        drive, tail = os.path.splitdrive(path)
        if ":" in tail or (drive and not tail.startswith(("/", "\\"))):
            raise Rejected("INPUT_DEVICE_PATH")
        for part in tail.replace("/", "\\").split("\\"):
            stem = part.split(".")[0].upper().rstrip(" ")
            if stem in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} or (
                len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[3].isdigit()
            ):
                raise Rejected("INPUT_DEVICE_PATH")
            if part not in {"", ".", ".."} and part.endswith((" ", ".")):
                raise Rejected("INPUT_DEVICE_PATH")
    if ".." in PurePath(path).parts:
        raise Rejected("INPUT_NOT_REGULAR_FILE")


@contextmanager
def _windows_fd(path):
    # ctypes and msvcrt are standard-library modules. OPEN_REPARSE_POINT
    # opens the link itself. Directory handles deny write/delete sharing,
    # pinning already-verified ancestors until the final read completes.
    import ctypes
    import msvcrt
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                       wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    attributes = kernel.GetFileInformationByHandleEx
    attributes.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                           wintypes.DWORD]
    attributes.restype = wintypes.BOOL

    class TagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    handles = []
    fd = None
    try:
        parts = PurePath(path).parts
        prefixes = []
        current = ""
        for part in parts:
            current = os.path.join(current, part)
            prefixes.append(current)
        if not os.path.isabs(path):
            prefixes.insert(0, ".")
        for index, prefix in enumerate(prefixes):
            final = index == len(prefixes) - 1
            handle = create(prefix, 0x80000000 if final else 0x80, 1,
                            None, 3, 0x00200000 | 0x02000000, None)
            if handle == ctypes.c_void_p(-1).value:
                error = ctypes.get_last_error()
                if error in (2, 3):
                    raise Rejected("INPUT_NOT_FOUND")
                raise Rejected("INPUT_NOT_REGULAR_FILE", "NOT_CHECKED")
            handles.append(handle)
            tag = TagInfo()
            if not attributes(handle, 9, ctypes.byref(tag), ctypes.sizeof(tag)):
                raise Rejected("INPUT_NOT_REGULAR_FILE", "NOT_CHECKED")
            if tag.attributes & 0x400:
                raise Rejected("INPUT_LINK_OR_REPARSE_POINT")
            if bool(tag.attributes & 0x10) == final:
                raise Rejected("INPUT_NOT_REGULAR_FILE")
        fd = msvcrt.open_osfhandle(handles[-1], os.O_RDONLY | os.O_BINARY)
        handles.pop()
        yield fd
    finally:
        if fd is not None:
            os.close(fd)
        for handle in reversed(handles):
            close(handle)


@contextmanager
def _posix_fd(path):
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Rejected("INPUT_NOT_REGULAR_FILE", "NOT_CHECKED")
    descriptors = []
    try:
        parts = PurePath(path).parts
        root = "/" if os.path.isabs(path) else "."
        base = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(base)
        components = list(parts[1:] if os.path.isabs(path) else parts)
        if not components:
            raise Rejected("INPUT_NOT_REGULAR_FILE")
        for index, part in enumerate(components):
            info = os.stat(part, dir_fd=base, follow_symlinks=False)
            if is_link_or_reparse(info):
                raise Rejected("INPUT_LINK_OR_REPARSE_POINT")
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if index < len(components) - 1:
                flags |= os.O_DIRECTORY
            base = os.open(part, flags, dir_fd=base)
            descriptors.append(base)
        yield base
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def read_input(path, max_bytes=DEFAULT_MAX_BYTES):
    validate_limit(max_bytes, MAX_BYTES)
    validate_path(path)
    try:
        opener = _windows_fd if os.name == "nt" else _posix_fd
        with opener(path) as fd:
            before = os.fstat(fd)
            if is_link_or_reparse(before):
                raise Rejected("INPUT_LINK_OR_REPARSE_POINT")
            if not stat.S_ISREG(before.st_mode):
                raise Rejected("INPUT_NOT_REGULAR_FILE")
            if before.st_size > max_bytes:
                raise Rejected("INPUT_TOO_LARGE")
            chunks = []
            remaining = max_bytes + 1
            while remaining:
                chunk = os.read(fd, min(remaining, 65536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            if len(data) > max_bytes:
                raise Rejected("INPUT_TOO_LARGE")
            after = os.fstat(fd)
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise Rejected("INPUT_NOT_REGULAR_FILE", "NOT_CHECKED")
            return data
    except FileNotFoundError:
        raise Rejected("INPUT_NOT_FOUND") from None
    except (OSError, ValueError):
        raise Rejected("INPUT_NOT_REGULAR_FILE", "NOT_CHECKED") from None
