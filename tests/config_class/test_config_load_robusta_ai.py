from unittest.mock import patch

from mavrick.clients.robusta_client import RobustaModel, RobustaModelsResponse
from mavrick.config import Config
from mavrick.core.llm import ModelEntry


def _fake_existing_model_entry() -> ModelEntry:
    return ModelEntry(model="gpt-4o", base_url="http://foo")

ROBUSTA_TEST_MODELS = RobustaModelsResponse(
    models={
        "Robusta/test": RobustaModel(
            mavrick_args={},
            model="azure/gpt-4o",
            is_default=False,
        )
    }
)


@patch("mavrick.core.llm.ROBUSTA_AI", True)
def test_cli_not_loading_robusta_ai(*, monkeypatch):
    config = Config.load_from_file(None)
    assert "Robusta" not in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_TEST_MODELS)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_loads_robusta_ai_when_true(mock_cluster, mock_fetch, *, monkeypatch):
    config = Config.load_from_env()
    assert "Robusta/test" in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", None)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_TEST_MODELS)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_loads_robusta_ai_when_not_exists_and_not_other_models(
    mock_cluster, mock_fetch, *, monkeypatch
):
    monkeypatch.setattr("mavrick.core.llm.MODEL_LIST_FILE_LOCATION", "")
    config = Config.load_from_env()
    assert "Robusta/test" in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", False)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_not_loads_robusta_ai_when_false(mock_cluster, *, monkeypatch):
    config = Config.load_from_env()
    assert "Robusta" not in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_TEST_MODELS)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
@patch(
    "mavrick.core.llm.LLMModelRegistry._parse_models_file",
    return_value={"existing_model": _fake_existing_model_entry()},
)
def test_server_loads_robusta_ai_when_true_and_model_list_exists(
    mock_parse, mock_cluster, mock_fetch, *, monkeypatch
):
    config = Config.load_from_env()
    assert "existing_model" in config.llm_model_registry.models
    assert "Robusta/test" in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", False)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
@patch(
    "mavrick.core.llm.LLMModelRegistry._parse_models_file",
    return_value={"existing_model": _fake_existing_model_entry()},
)
def test_server_not_loads_robusta_ai_when_false_and_model_list_exists(
    mock_parse, mock_cluster, *, monkeypatch
):
    config = Config.load_from_env()
    assert "existing_model" in config.llm_model_registry.models
    assert "Robusta" not in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", None)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
@patch(
    "mavrick.core.llm.LLMModelRegistry._parse_models_file",
    return_value={"existing_model": _fake_existing_model_entry()},
)
def test_server_not_loads_robusta_ai_when_no_env_var_and_model_list_exists(
    mock_parse, mock_cluster, *, monkeypatch
):
    config = Config.load_from_env()
    assert "existing_model" in config.llm_model_registry.models
    assert "Robusta" not in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_TEST_MODELS)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_loads_robusta_ai_when_model_var_exists(
    mock_cluster, mock_fetch, *, monkeypatch
):
    monkeypatch.setenv("MODEL", "some_model")

    config = Config.load_from_env()
    assert "Robusta/test" in config.llm_model_registry.models


ROBUSTA_OPTED_OUT = RobustaModelsResponse(models={}, robusta_ai_disabled=True)


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_OPTED_OUT)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
@patch(
    "mavrick.core.llm.LLMModelRegistry._parse_models_file",
    return_value={"existing_model": _fake_existing_model_entry()},
)
def test_server_not_loads_robusta_ai_when_the_account_opted_out(
    mock_parse, mock_cluster, mock_fetch, *, monkeypatch
):
    """ROBUSTA_AI=true still cannot put an opted-out account on a Robusta-hosted
    model: the account setting wins, and the cluster's own models still load."""
    config = Config.load_from_env()
    assert "existing_model" in config.llm_model_registry.models
    assert "Robusta" not in config.llm_model_registry.models
    assert config.llm_model_registry.default_robusta_model is None
    assert config.llm_model_registry.robusta_ai_disabled


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_OPTED_OUT)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_serves_the_model_env_var_when_the_account_opted_out(
    mock_cluster, mock_fetch, *, monkeypatch
):
    monkeypatch.setenv("MODEL", "some_model")

    config = Config.load_from_env()
    assert "Robusta" not in config.llm_model_registry.models
    assert config.llm_model_registry.get_model_params().name == "some_model"


@patch("mavrick.core.llm.ROBUSTA_AI", None)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_not_loads_robusta_ai_when_model_var_exists_and_no_env_var(
    mock_cluster, *, monkeypatch
):
    monkeypatch.setenv("MODEL", "some_model")
    config = Config.load_from_env()
    assert "Robusta" not in config.llm_model_registry.models


@patch("mavrick.core.llm.ROBUSTA_AI", False)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_server_not_loads_robusta_ai_when_model_var_exists_and_false_env_var(
    mock_cluster, *, monkeypatch
):
    monkeypatch.setenv("MODEL", "some_model")
    config = Config.load_from_env()
    assert "Robusta" not in config.llm_model_registry.models


ROBUSTA_MAVRICK_ARGS_MODELS = RobustaModelsResponse(
    models={
        "Robusta/test": RobustaModel(
            mavrick_args={},
            model="azure/gpt-4o",
            is_default=False,
        ),
        "Robusta/sonnet-1m": RobustaModel(
            mavrick_args={"max_context_size": 1000000},
            model="claude-sonnet-4-20250514",
            is_default=False,
        ),
    }
)


@patch("mavrick.core.llm.ROBUSTA_AI", True)
@patch("mavrick.core.llm.fetch_robusta_models", return_value=ROBUSTA_MAVRICK_ARGS_MODELS)
@patch("mavrick.config.Config._Config__get_cluster_name", return_value="test")
def test_robusta_ai_config_get_llm_context_override(
    mock_parse, mock_cluster, *, monkeypatch
):
    """Test that relay mavrick_args fields are passed and used for max_context_size.
    Also makes sure the args are poped before getting to completion call llm"""
    config = Config.load_from_env()
    llm = config._get_llm("Robusta/sonnet-1m")
    assert llm.get_context_window_size() == 1000000
    assert llm.args.get("custom_args") is None
