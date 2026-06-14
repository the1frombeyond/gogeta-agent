import os
from typing import Dict

from tools.mcp._state import logger, _ENV_VAR_PATTERN


def _interpolate_env_vars(value):
    if isinstance(value, str):
        def _replace(m):
            return os.environ.get(m.group(1), m.group(0))
        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(v) for v in value]
    return value


def _load_mcp_config() -> Dict[str, dict]:
    try:
        from gogeta_cli.config import load_config
        config = load_config()
        servers = config.get("mcp_servers")
        if not servers or not isinstance(servers, dict):
            return {}
        try:
            from gogeta_cli.env_loader import load_gogeta_dotenv
            load_gogeta_dotenv()
        except Exception:
            pass
        return {name: _interpolate_env_vars(cfg) for name, cfg in servers.items()}
    except Exception as exc:
        logger.debug("Failed to load MCP config: %s", exc)
        return {}
