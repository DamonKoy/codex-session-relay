from __future__ import annotations

import ctypes
import getpass
import sys
from typing import Optional

from .errors import RelayError


SECURITY_FRAMEWORK = "/System/Library/Frameworks/Security.framework/Security"
CORE_FOUNDATION = (
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)


def _frameworks():
    if sys.platform != "darwin":
        raise RelayError("v0.1.0 的安全凭证存储仅支持 macOS Keychain")
    return ctypes.CDLL(SECURITY_FRAMEWORK), ctypes.CDLL(CORE_FOUNDATION)


def read_secret(service_name: str, account: Optional[str] = None) -> Optional[str]:
    security, core = _frameworks()
    service = service_name.encode("utf-8")
    account_bytes = (account or getpass.getuser()).encode("utf-8")
    length = ctypes.c_uint32()
    data = ctypes.c_void_p()
    item = ctypes.c_void_p()
    security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    status = security.SecKeychainFindGenericPassword(
        None,
        len(service),
        service,
        len(account_bytes),
        account_bytes,
        ctypes.byref(length),
        ctypes.byref(data),
        ctypes.byref(item),
    )
    try:
        if status == -25300:
            return None
        if status != 0:
            raise RelayError("读取 macOS Keychain 失败，OSStatus=%s" % status)
        return ctypes.string_at(data, length.value).decode("utf-8")
    finally:
        if data:
            security.SecKeychainItemFreeContent(None, data)
        if item:
            core.CFRelease(item)


def write_secret(service_name: str, secret: str, account: Optional[str] = None) -> None:
    if not secret:
        raise RelayError("API Key 不能为空")
    security, core = _frameworks()
    service = service_name.encode("utf-8")
    account_bytes = (account or getpass.getuser()).encode("utf-8")
    password = secret.encode("utf-8")
    length = ctypes.c_uint32()
    data = ctypes.c_void_p()
    item = ctypes.c_void_p()
    security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    status = security.SecKeychainFindGenericPassword(
        None,
        len(service),
        service,
        len(account_bytes),
        account_bytes,
        ctypes.byref(length),
        ctypes.byref(data),
        ctypes.byref(item),
    )
    buffer = ctypes.create_string_buffer(password)
    if status == 0:
        security.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
        status = security.SecKeychainItemModifyAttributesAndData(
            item, None, len(password), ctypes.cast(buffer, ctypes.c_void_p)
        )
    elif status == -25300:
        security.SecKeychainAddGenericPassword.restype = ctypes.c_int32
        status = security.SecKeychainAddGenericPassword(
            None,
            len(service),
            service,
            len(account_bytes),
            account_bytes,
            len(password),
            ctypes.cast(buffer, ctypes.c_void_p),
            None,
        )
    if data:
        security.SecKeychainItemFreeContent(None, data)
    if item:
        core.CFRelease(item)
    if status != 0:
        raise RelayError("写入 macOS Keychain 失败，OSStatus=%s" % status)

