"""Unit tests for Windows Explorer context menu service."""

import sys
import pytest

from vietzip.services.context_menu_service import (
    is_context_menu_registered,
    register_context_menu,
    unregister_context_menu,
)


@pytest.mark.skipif(sys.platform != "win32", reason="Chỉ chạy trên Windows")
def test_context_menu_register_and_unregister():
    # Kiểm tra đăng ký thành công
    ok, msg = register_context_menu()
    assert ok is True
    assert is_context_menu_registered() is True

    # Kiểm tra gỡ bỏ thành công
    ok_unreg, msg_unreg = unregister_context_menu()
    assert ok_unreg is True
    assert is_context_menu_registered() is False
