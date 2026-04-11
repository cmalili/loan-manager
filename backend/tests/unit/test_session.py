from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


MODULE_NAME = "app.db.session"


def unload_session_module() -> None:
    sys.modules.pop(MODULE_NAME, None)


class SessionModuleTests(unittest.TestCase):
    def tearDown(self) -> None:
        unload_session_module()

    def test_import_raises_when_database_url_is_missing(self) -> None:
        unload_session_module()

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is not set"):
                importlib.import_module(MODULE_NAME)

    def test_get_db_yields_session_and_closes_it(self) -> None:
        unload_session_module()

        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}, clear=True):
            session_module = importlib.import_module(MODULE_NAME)

        fake_session = MagicMock()
        session_module.SessionLocal = MagicMock(return_value=fake_session)

        generator = session_module.get_db()
        session = next(generator)

        self.assertIs(session, fake_session)

        with self.assertRaises(StopIteration):
            next(generator)

        fake_session.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
