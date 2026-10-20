import pytest

from foodbot.config import Config


@pytest.fixture
def cfg(tmp_path):
    data = tmp_path / "data"
    (data / "photos").mkdir(parents=True)
    return Config(discord_token="t", channel_id=1, claude_model="sonnet", data_dir=data)
