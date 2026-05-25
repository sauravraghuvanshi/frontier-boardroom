"""App Insights + structlog. Agent 365 hooks emit custom events for token spend."""

from __future__ import annotations

import logging
import os

import structlog

_configured = False


def configure_telemetry(connection_string: str = "") -> None:
    global _configured
    if _configured:
        return
    _configured = True

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    conn = connection_string or os.environ.get("APPINSIGHTS_CONNECTION_STRING", "")
    if conn:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor

            configure_azure_monitor(connection_string=conn)
        except Exception as e:  # noqa: BLE001
            logging.warning("App Insights init failed: %s", e)


def get_logger(name: str = "frontier") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def agent_event(role: str, event: str, **fields) -> None:
    """Emit an Agent 365 observability event."""
    get_logger("agent365").info(event, role=role, **fields)
