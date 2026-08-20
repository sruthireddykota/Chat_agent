
from app.utils.logger import get_logger

logger= get_logger()

_CONFIGURED= False


def congfigure_observability():
    global _CONFIGURED
    if _CONFIGURED:
        return True

    from azure.monitor.opentelemetry import configure_azure_monitor
    from agent_framework.observability import create_resource, enable_instrumentation

    from app.config.settings import settings
    if settings.APPLICATION_INSIGHTS_CONNECTION_STR:
        configure_azure_monitor(
            connection_string=settings.APPLICATION_INSIGHTS_CONNECTION_STR,
            resource=create_resource(service_name="Agent Platform"),
            logger_name="app",
            disable_logging=False,
            enable_live_metrics=True,
            instrumentation_options={"azure_sdk": {"enabled": False}},
        )

        enable_instrumentation(enable_sensitive_data=False)
        _CONFIGURED=True
        logger.info("[Observability] Azure Monitor + Agent Framework instrumentation enabled")
        return True
    return False
