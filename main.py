import decky  # noqa: F401  (provided by Decky Loader at runtime)


class Plugin:
    async def _main(self):
        decky.logger.info("System Monitor loaded")

    async def _unload(self):
        decky.logger.info("System Monitor unloaded")
