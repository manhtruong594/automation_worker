from __future__ import annotations

import importlib.util
import io
import pathlib
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


SCRIPT_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "get_workai_token.py"
SPEC = importlib.util.spec_from_file_location("get_workai_token", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TokenSanitizationTests(unittest.TestCase):
    def test_removes_supported_prefixes(self) -> None:
        self.assertEqual(MODULE.sanitize_token(" Bearer abc "), ("abc", True))
        self.assertEqual(MODULE.sanitize_token("sessionToken=xyz"), ("xyz", True))

    def test_rejects_empty_or_control_characters(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.sanitize_token("   ")
        with self.assertRaises(ValueError):
            MODULE.sanitize_token("abc\ndef")
        with self.assertRaises(ValueError):
            MODULE.sanitize_token("abc def")


class CommandTests(unittest.TestCase):
    def test_success_does_not_print_token(self) -> None:
        secret = "top-secret-token"
        output = io.StringIO()
        errors = io.StringIO()
        valid = MODULE.VerificationResult(True, "Token hợp lệ.", MODULE.EXIT_OK)

        with (
            mock.patch.object(MODULE, "read_supplied_token", return_value=secret),
            mock.patch.object(
                MODULE,
                "read_user_environment",
                return_value={name: None for name in MODULE.TOKEN_VARIABLES},
            ),
            mock.patch.object(MODULE, "verify_token", return_value=valid),
            mock.patch.object(MODULE, "persist_exclusive_token") as persist,
            redirect_stdout(output),
            redirect_stderr(errors),
        ):
            exit_code = MODULE.run(["--type", "bearer"])

        self.assertEqual(exit_code, MODULE.EXIT_OK)
        persist.assert_called_once_with("WORKAI_TOKEN", secret)
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn(secret, errors.getvalue())

    def test_failed_verification_does_not_persist(self) -> None:
        rejected = MODULE.VerificationResult(False, "Token bị từ chối.", MODULE.EXIT_REJECTED)
        with (
            mock.patch.object(MODULE, "read_supplied_token", return_value="secret"),
            mock.patch.object(
                MODULE,
                "read_user_environment",
                return_value={name: None for name in MODULE.TOKEN_VARIABLES},
            ),
            mock.patch.object(MODULE, "verify_token", return_value=rejected),
            mock.patch.object(MODULE, "persist_exclusive_token") as persist,
            redirect_stderr(io.StringIO()),
        ):
            exit_code = MODULE.run(["--type", "session"])

        self.assertEqual(exit_code, MODULE.EXIT_REJECTED)
        persist.assert_not_called()

    def test_existing_different_credential_requires_replace(self) -> None:
        with (
            mock.patch.object(MODULE, "read_supplied_token", return_value="new-secret"),
            mock.patch.object(
                MODULE,
                "read_user_environment",
                return_value={"WORKAI_TOKEN": "old-secret", "WORKAI_SESSION_TOKEN": None},
            ),
            mock.patch.object(MODULE, "verify_token") as verify,
            mock.patch.object(MODULE, "persist_exclusive_token") as persist,
            redirect_stderr(io.StringIO()),
        ):
            exit_code = MODULE.run(["--type", "bearer"])

        self.assertEqual(exit_code, MODULE.EXIT_REPLACE_REQUIRED)
        verify.assert_not_called()
        persist.assert_not_called()


if __name__ == "__main__":
    unittest.main()
