from kasa import Discover

PLUG_IP = "192.168.1.183"


async def get_plug():
    plug = await Discover.discover_single(PLUG_IP)

    if plug is None:
        raise RuntimeError(f"Could not find plug at {PLUG_IP}")

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