from mavrick.config import Config


def test_create_alertmanager_source_forwards_basic_auth_credentials() -> None:
    config = Config(
        alertmanager_url="https://alertmanager.example.com",
        alertmanager_username="mavrick",
        alertmanager_password="secret-password",
    )

    source = config.create_alertmanager_source()

    assert source.username == "mavrick"
    assert source.password == "secret-password"
