import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kasa_control import get_state, turn_off, turn_on

app = FastAPI(
    title="Smart Fan",
    description="Fan control dashboard",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

TIMER_MINUTES = 120
timer_task: asyncio.Task | None = None


@app.get("/")
async def home(request: Request):
    state = await get_state()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state,
            "timer_minutes": TIMER_MINUTES,
            "timer_running": timer_task is not None and not timer_task.done(),
        },
    )


@app.post("/on")
async def on():
    global timer_task

    if timer_task is not None and not timer_task.done():
        timer_task.cancel()
        timer_task = None

    await turn_on()

    return RedirectResponse(url="/", status_code=303)


@app.post("/off")
async def off():
    global timer_task

    if timer_task is not None and not timer_task.done():
        timer_task.cancel()
        timer_task = None

    await turn_off()

    return RedirectResponse(url="/", status_code=303)


@app.post("/on-timer")
async def on_timer():
    global timer_task

    if timer_task is not None and not timer_task.done():
        timer_task.cancel()

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

    return RedirectResponse(url="/", status_code=303)


@app.get("/health")
async def health():
    return {"status": "ok"}