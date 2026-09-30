from http import HTTPStatus
from unittest import mock

from mavrick.version import check_version, fetch_mavrick_info


def test_version_check_matches_latest(responses):
    fetch_mavrick_info.cache_clear()
    with mock.patch("mavrick.version.get_version", return_value="1.0.0"):
        responses.add(
            responses.GET,
            "https://api.robusta.dev/api/mavrick/get_info",
            json={"latest_version": "1.0.0"},
        )
        result = check_version()
        assert result.is_latest
        assert result.current_version == "1.0.0"
        assert result.latest_version == "1.0.0"
        assert result.update_message is None


def test_version_check_matches_latest_on_dev(responses):
    fetch_mavrick_info.cache_clear()
    with mock.patch("mavrick.version.get_version", return_value="dev-1.0.0"):
        responses.add(
            responses.GET,
            "https://api.robusta.dev/api/mavrick/get_info",
            json={"latest_version": "1.0.0"},
        )
        result = check_version()
        assert result.is_latest
        assert result.current_version == "dev-1.0.0"
        assert result.latest_version == "1.0.0"
        assert result.update_message is None


def test_version_check_outdated(responses):
    fetch_mavrick_info.cache_clear()
    with mock.patch("mavrick.version.get_version", return_value="0.9.0"):
        responses.add(
            responses.GET,
            "https://api.robusta.dev/api/mavrick/get_info",
            json={"latest_version": "1.0.0"},
        )
        result = check_version()
        assert not result.is_latest
        assert result.current_version == "0.9.0"
        assert result.latest_version == "1.0.0"
        assert "Update available: 1.0.0 (current: 0.9.0)" in result.update_message


def test_version_check_failed_fetch(responses):
    fetch_mavrick_info.cache_clear()
    responses.add(
        responses.GET,
        "https://api.robusta.dev/api/mavrick/get_info",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    with mock.patch("mavrick.version.get_version", return_value="1.0.0"):
        result = check_version()
        assert result.is_latest  # Assumes latest on failure
        assert result.current_version == "1.0.0"
        assert result.latest_version is None
        assert result.update_message is None
