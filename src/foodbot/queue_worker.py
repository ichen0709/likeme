"""排隊與逐張處理：一個工作者、一次一張（架構文件第 4、7 節）。"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from . import claude_runner, messages, photos, schema
from .config import MAX_IMAGE_BYTES, QUEUE_MAX, Config
from .records import Record, Records
from .usage import Usage


class JobFailed(Exception):
    """處理失敗；訊息只給終端機看。"""


@dataclass
class Job:
    user_id: int
    uploader: str
    when: datetime  # 本機時間，照片被傳上來的時間
    hint: str  # 上傳者的附帶文字（未清洗，由防護 2 處理）
    size: int
    download: Callable[[], Awaitable[bytes]]
    set_text: Callable[[str], Awaitable[None]]  # 編輯「處理中」那則回覆
    finished: Callable[[], Awaitable[None]]  # 這張結束後通知 bot（用來移除 ⏳）
    counted: bool = False  # 是否已計入 usage.json


class Worker:
    def __init__(self, cfg: Config, usage: Usage, records: Records):
        self._cfg = cfg
        self._usage = usage
        self._records = records
        self._queue: asyncio.Queue[Job] = asyncio.Queue()
        self._waiting: list[Job] = []
        self._current: Job | None = None

    # ---- 給 bot 收件時判斷用 ----
    def ahead(self) -> int:
        return len(self._waiting) + (1 if self._current else 0)

    def free_slots(self) -> int:
        return max(0, QUEUE_MAX - len(self._waiting))

    def _not_yet_counted(self) -> list[Job]:
        jobs = list(self._waiting)
        if self._current and not self._current.counted:
            jobs.append(self._current)
        return jobs

    def queued_total(self) -> int:
        return len(self._not_yet_counted())

    def queued_user(self, user_id: int) -> int:
        return sum(1 for j in self._not_yet_counted() if j.user_id == user_id)

    def submit(self, job: Job) -> None:
        self._waiting.append(job)
        self._queue.put_nowait(job)

    # ---- 工作者 ----
    async def run(self) -> None:
        while True:
            job = await self._queue.get()
            self._waiting.remove(job)
            self._current = job
            await self._refresh_waiting_texts()
            try:
                await self._process(job)
            except Exception as e:  # 任何一張失敗都不能讓工作者停下
                print(f"警告：一張照片處理失敗（{type(e).__name__}：{e}）")
                await self._safe_set_text(job, messages.FAILED)
            finally:
                self._current = None
                await self._safe(job.finished())

    async def _refresh_waiting_texts(self) -> None:
        for i, waiting in enumerate(self._waiting):
            await self._safe_set_text(waiting, messages.processing(i + 1))
        if self._current:
            await self._safe_set_text(self._current, messages.processing(0))

    @staticmethod
    async def _safe(coro: Awaitable) -> None:
        try:
            await coro
        except Exception as e:
            print(f"警告：Discord 操作失敗（{type(e).__name__}）")

    async def _safe_set_text(self, job: Job, text: str) -> None:
        await self._safe(job.set_text(text))

    async def _process(self, job: Job) -> None:
        if job.size > MAX_IMAGE_BYTES:
            raise JobFailed("圖片超過 10 MB")
        data = await job.download()
        if len(data) > MAX_IMAGE_BYTES:
            raise JobFailed("圖片超過 10 MB")
        ext = photos.sniff_image(data)
        if ext is None:
            raise JobFailed("內容不是支援的圖片格式")

        self._usage.increment(job.user_id)  # 先加再跑：失敗、逾時也算一張
        job.counted = True

        raw = await claude_runner.analyze(self._cfg, data, ext, job.hint)
        analysis = schema.validate(raw)

        photo_path = await asyncio.to_thread(
            photos.save_photo, self._cfg.photos_dir, job.when, analysis.name, data, ext)
        uid = str(job.user_id)
        before = await asyncio.to_thread(self._records.daily_total, uid, job.when.date())
        meal = analysis.kcal if analysis.is_food else 0.0
        day_total = before + meal
        record = Record(
            when=job.when,
            uploader=job.uploader,
            user_id=uid,
            description=analysis.name if analysis.is_food else "不是食物",
            ingredients=messages.ingredients_text(analysis),
            weight_g=analysis.weight_g,
            kcal=analysis.kcal,
            day_total=day_total,
            photo_path=str(photo_path),
        )
        await asyncio.to_thread(self._records.append, record)
        await job.set_text(messages.result(job.user_id, analysis, day_total))
