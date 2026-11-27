# SPDX-License-Identifier: LGPL-2.1-or-later

import pytest

from kernelci import build


@pytest.mark.parametrize(
    "message, expected",
    [
        ("", ""),
        ("Subject\n\nBody", "Subject\n\nBody"),
        ("é" * 8192, "é" * 8192),
        ("a" * 16384 + "b", "a" * 16384),
        ("a" * 16383 + "é", "a" * 16383),
    ],
    ids=[
        "empty",
        "subject-and-body",
        "exact-limit",
        "over-limit",
        "split-utf8",
    ],
)
def test_git_commit_message(monkeypatch, message, expected):
    monkeypatch.setattr(build, "shell_cmd", lambda cmd: message + "\n")
    assert build.git_commit_message("repo", "HEAD") == expected
