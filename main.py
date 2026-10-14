import os
import sys

import decky  # provided by Decky Loader at runtime

# Decky already adds py_modules to sys.path; keep a fallback for older loaders.
_PY_MODULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "py_modules")
if _PY_MODULES not in sys.path:
    sys.path.append(_PY_MODULES)

from sysmon.metrics import MetricsCollector  # noqa: E402
from sysmon.processes import ProcessSampler  # noqa: E402


class Plugin:
    async def _main(self):
        self.metrics = MetricsCollector()
        self.processes = ProcessSampler()
        decky.logger.info("System Monitor loaded")

    async def _unload(self):
        decky.logger.info("System Monitor unloaded")

    async def get_metrics(self) -> dict:
        try:
            return self.metrics.snapshot()
        except Exception:
            decky.logger.exception("get_metrics failed")
            raise

    async def get_processes(
        self,
        sort_key: str = "cpu",
        descending: bool = True,
        limit: int = 40,
        include_kernel: bool = False,
        group: bool = False,
    ) -> dict:
        try:
            return self.processes.sample(sort_key, descending, limit, include_kernel, group)
        except Exception:
            decky.logger.exception("get_processes failed")
            raise
