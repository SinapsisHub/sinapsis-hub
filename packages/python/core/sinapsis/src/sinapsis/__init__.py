"""Public API for Sinapsis.

The :mod:`sinapsis` package defines the stable, user-facing API for the
Sinapsis ecosystem. Symbols exposed here and through public submodules are
intended to be the primary interface for users and downstream Sinapsis
packages.

The underlying implementation is provided by internal packages and may
change independently of this public API. In particular, implementation
details should not be imported directly from internal or core packages.

For example, prefer::

    from sinapsis import Agent, Template

over importing these classes from their implementation modules.

This separation allows the underlying implementation to evolve, including
future changes to the execution engine or its language/runtime, without
requiring changes to user-facing imports.
"""

# from sinapsis.agent import Agent
from sinapsis.data_transport import DataContainer
from sinapsis.logging import sinapsis_logger
from sinapsis.sentinels import SinapsisSentinel
from sinapsis.template import Template

__all__ = [
    # "Agent",
    "Template",
    "DataContainer",
    "sinapsis_logger",
    "SinapsisSentinel",
]
