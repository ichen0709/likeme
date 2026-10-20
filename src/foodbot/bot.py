"""Discord 收訊息、回覆、編輯訊息（架構文件第 3.2、4 節）。"""

import discord

from . import messages
from .config import MAX_IMAGES_PER_MESSAGE, Config
from .queue_worker import Job, Worker
from .records import Records
from .usage import Usage

RECEIVED_EMOJI = "⏳"
_NO_MENTIONS = discord.AllowedMentions.none()


class _Ticket:
    """同一則訊息的幾張照片都結束後，才移除 ⏳。"""

    def __init__(self, message: discord.Message, bot_user: discord.abc.User, count: int):
        self._message, self._bot_user, self._remaining = message, bot_user, count

    async def finish_one(self) -> None:
        self._remaining -= 1
        if self._remaining == 0:
            try:
                await self._message.remove_reaction(RECEIVED_EMOJI, self._bot_user)
            except discord.HTTPException as e:
                print(f"警告：移除 {RECEIVED_EMOJI} 失敗（{type(e).__name__}）")


class FoodBot(discord.Client):
    def __init__(self, cfg: Config):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=_NO_MENTIONS)
        self._cfg = cfg
        self._usage = Usage(cfg)
        self._worker = Worker(cfg, self._usage, Records(cfg))

    async def setup_hook(self) -> None:
        self._worker_task = self.loop.create_task(self._worker.run())

    async def on_ready(self) -> None:
        print(f"agent 已上線，只聽頻道 {self._cfg.channel_id}。")

    async def on_message(self, message: discord.Message) -> None:
        # 收件檢查：頻道對、不是 bot、有圖片附件
        if message.channel.id != self._cfg.channel_id or message.author.bot:
            return
        images = [a for a in message.attachments
                  if a.content_type and a.content_type.startswith("image/")]
        if not images:
            return

        notes: list[str] = []
        if len(images) > MAX_IMAGES_PER_MESSAGE:
            images = images[:MAX_IMAGES_PER_MESSAGE]
            notes.append(messages.TOO_MANY_IMAGES)

        uid = message.author.id
        allowed, total_full = self._usage.remaining(
            uid, self._worker.queued_total(), self._worker.queued_user(uid))
        if allowed <= 0:
            await message.reply(messages.TOTAL_LIMIT if total_full else messages.USER_LIMIT,
                                mention_author=False)
            return
        if allowed < len(images):
            images = images[:allowed]
            notes.append(messages.partial_quota(allowed))

        free = self._worker.free_slots()
        if free <= 0:
            await message.reply(messages.QUEUE_FULL, mention_author=False)
            return
        if free < len(images):
            images = images[:free]
            notes.append(messages.QUEUE_FULL)

        try:
            await message.add_reaction(RECEIVED_EMOJI)
        except discord.HTTPException as e:
            print(f"警告：加 {RECEIVED_EMOJI} 失敗（{type(e).__name__}），請確認 bot 有「新增反應」權限。")

        ticket = _Ticket(message, self.user, len(images))
        local_time = message.created_at.astimezone().replace(tzinfo=None)
        for attachment in images:
            reply = await message.reply(messages.processing(self._worker.ahead()),
                                        mention_author=False)
            self._worker.submit(Job(
                user_id=uid,
                uploader=message.author.display_name,
                when=local_time,
                hint=message.content,
                size=attachment.size,
                download=attachment.read,
                set_text=self._editor(reply, uid),
                finished=ticket.finish_one,
            ))
        if notes:
            await message.reply("\n".join(notes), mention_author=False)

    @staticmethod
    def _editor(reply: discord.Message, user_id: int):
        mentions = discord.AllowedMentions(everyone=False, roles=False,
                                           users=[discord.Object(id=user_id)])

        async def set_text(text: str) -> None:
            await reply.edit(content=text, allowed_mentions=mentions)

        return set_text
