import pytest


class TestBase:
    @pytest.fixture(autouse=True)
    def _setup(self, cleanup: None) -> None: ...
