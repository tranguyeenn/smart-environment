from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from candle_warmer.api import (
    TIMER_MINUTES as CANDLE_TIMER_MINUTES,
    do_off as candle_do_off,
    do_on as candle_do_on,
    do_on_timer as candle_do_on_timer,
    router as candle_router,
)
from candle_warmer.kasa_control import get_state as get_candle_state
from fans.api import (
    TIMER_MINUTES as FAN_TIMER_MINUTES,
    do_off as fan_do_off,
    do_on as fan_do_on,
    do_on_timer as fan_do_on_timer,
    router as fan_router,
    timer_running as fan_timer_running,
)
from fans.kasa_control import get_state as get_fan_state

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Smart Environment API",
    description="Control smart environment devices.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount(
    "/fan-static",
    StaticFiles(directory=str(BASE_DIR / "fans" / "static")),
    name="fan-static",
)
app.mount(
    "/candle-static",
    StaticFiles(directory=str(BASE_DIR / "candle_warmer" / "static")),
    name="candle-static",
)

root_templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
fan_templates = Jinja2Templates(directory=str(BASE_DIR / "fans" / "templates"))
candle_templates = Jinja2Templates(
    directory=str(BASE_DIR / "candle_warmer" / "templates")
)

app.include_router(fan_router)
app.include_router(candle_router)


@app.get("/")
async def home(request: Request):
    return root_templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/fan")
async def fan_ui(request: Request):
    state = await get_fan_state()

    return fan_templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state,
            "timer_minutes": FAN_TIMER_MINUTES,
            "timer_running": fan_timer_running(),
        },
    )


@app.post("/fan/on")
async def fan_ui_on():
    await fan_do_on()
    return RedirectResponse(url="/fan", status_code=303)


@app.post("/fan/off")
async def fan_ui_off():
    await fan_do_off()
    return RedirectResponse(url="/fan", status_code=303)


@app.post("/fan/on-timer")
async def fan_ui_on_timer():
    await fan_do_on_timer()
    return RedirectResponse(url="/fan", status_code=303)


@app.get("/candle-warmer")
async def candle_warmer_ui(request: Request):
    state = await get_candle_state()

    return candle_templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "state": state,
            "timer_minutes": CANDLE_TIMER_MINUTES,
        },
    )


@app.post("/candle-warmer/on")
async def candle_warmer_ui_on():
    await candle_do_on()
    return RedirectResponse(url="/candle-warmer", status_code=303)


@app.post("/candle-warmer/off")
async def candle_warmer_ui_off():
    await candle_do_off()
    return RedirectResponse(url="/candle-warmer", status_code=303)


@app.post("/candle-warmer/on-timer")
async def candle_warmer_ui_on_timer():
    await candle_do_on_timer()
    return RedirectResponse(url="/candle-warmer", status_code=303)
