from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kasa_control import get_state, turn_on, turn_off
import asyncio

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

TIMER_MINUTES = 120

@app.get("/")
async def home(request: Request):
    state = await get_state()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"state": state,
                 "timer_minutes": TIMER_MINUTES,
        },
    )


@app.post("/on")
async def on():
    await turn_on()
    return RedirectResponse("/", status_code=303)

@app.post("/off")
async def off():
    await turn_off()
    return RedirectResponse("/", status_code=303)

@app.post("/on-timer")
async def on_timer():
    await turn_on()

    async def delayed_off():
        await asyncio.sleep(TIMER_MINUTES * 60)
        await turn_off()

    asyncio.create_task(delayed_off())

    return RedirectResponse("/", status_code=303)