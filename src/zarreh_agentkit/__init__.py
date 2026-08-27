"""Shared substrate for agent services.

Every abstraction in this package was extracted after two independent services
demonstrated the same need — never designed up front. That extraction rule is
what keeps the public surface deliberately narrow.
"""

from zarreh_agentkit.cost import CostEntry, CostTrackingHandler
from zarreh_agentkit.observability import (
    build_tracing_callbacks,
    configure_logging,
    correlation_id,
    get_logger,
)
from zarreh_agentkit.settings import AgentSettings
from zarreh_agentkit.version import __version__

__all__ = [
    "AgentSettings",
    "CostEntry",
    "CostTrackingHandler",
    "__version__",
    "build_tracing_callbacks",
    "configure_logging",
    "correlation_id",
    "get_logger",
]
