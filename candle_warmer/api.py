import asyncio

from fastapi import APIRouter

from candle_warmer.kasa_control import get_state, turn_off, turn_on

router = APIRouter(prefix="/api/candle-warmer", tags=["Candle Warmer"])

TIMER_MINUTES = 120
timer_task: asyncio.Task | None = None


def _cancel_timer() -> None:
    global timer_task

    if timer_task is not None and not timer_task.done():
        timer_task.cancel()
    timer_task = None


async def do_on() -> None:
    await turn_on()


async def do_off() -> None:
    _cancel_timer()
    await turn_off()


async def do_on_timer() -> dict:
    global timer_task

    _cancel_timer()
    await turn_on()

    async def delayed_off():
        global timer_task
        try:
            await asyncio.sleep(TIMER_MINUTES * 60)
            await turn_off()
        except asyncio.CancelledError:
            pass
        finally:
            timer_task = None

    timer_task = asyncio.create_task(delayed_off())

    return {
        "status": "on",
        "timer_minutes": TIMER_MINUTES,
    }


@router.get("/state")
async def candle_state():
    return await get_state()


@router.post("/on")
async def candle_on():
    await do_on()
    return {"status": "on"}


@router.post("/off")
async def candle_off():
    await do_off()
    return {"status": "off"}


@router.post("/on-timer")
async def candle_on_timer():
    return await do_on_timer()
