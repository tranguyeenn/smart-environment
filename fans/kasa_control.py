from kasa import SmartPlug

PLUG_IP = "192.168.1.169"


async def get_plug():
    plug = SmartPlug(PLUG_IP)
    await plug.update()
    return plug


async def get_state():
    plug = await get_plug()

    return {
        "name": plug.alias,
        "is_on": plug.is_on,
    }


async def turn_on():
    plug = await get_plug()
    await plug.turn_on()


async def turn_off():
    plug = await get_plug()
    await plug.turn_off()