import abc

class StorageBackend(abc.ABC):
    name: str
    @abc.abstractmethod
    async def store_file(self, file_path: str, desired_name: str) -> str:
        ...

class TelegramStorage(StorageBackend):
    name = "telegram"
    def __init__(self, bot, dump_channel_id: int):
        self.bot = bot
        self.dump_channel_id = dump_channel_id

    async def store_file(self, file_path: str, desired_name: str) -> str:
        sent = await self.bot.send_document(
            chat_id=self.dump_channel_id,
            document=open(file_path, "rb"),
            file_name=desired_name
        )
        return f"tg://file_id/{sent.document.file_id}"

class MegaStorage(StorageBackend):
    name = "mega"
    async def store_file(self, file_path: str, desired_name: str) -> str:
        raise NotImplementedError("Integrate official Mega API/SDK here.")

def build_backends(bot, settings):
    mapping = {}
    for backend_name in settings.STORAGE_BACKENDS:
        if backend_name == "telegram":
            mapping[backend_name] = TelegramStorage(bot, settings.DUMP_CHANNEL_ID)
        elif backend_name == "mega":
            mapping[backend_name] = MegaStorage()
    return mapping