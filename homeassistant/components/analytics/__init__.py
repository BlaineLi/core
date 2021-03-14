"""Send instance and usage analytics."""
import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .analytics import Analytics
from .const import ATTR_HUUID, ATTR_PREFERENCES, DOMAIN, INTERVAL


async def async_setup(hass: HomeAssistant, _):
    """Set up the analytics integration."""
    uuid = await hass.helpers.instance_id.async_get()
    analytics = Analytics(hass, uuid)

    await analytics.load_preferences()
    await analytics.send_analytics()

    async_track_time_interval(hass, analytics.send_analytics, INTERVAL)
    websocket_api.async_register_command(hass, websocket_analytics_preferences)
    websocket_api.async_register_command(hass, websocket_analytics_preferences_update)

    hass.data[DOMAIN] = analytics
    return True


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({vol.Required("type"): "analytics"})
async def websocket_analytics_preferences(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Return analytics preferences."""
    analytics: Analytics = hass.data[DOMAIN]
    connection.send_result(
        msg["id"],
        {ATTR_PREFERENCES: analytics.preferences, ATTR_HUUID: analytics.huuid},
    )


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "analytics/preferences",
        vol.Required("preferences"): cv.ensure_list,
    }
)
async def websocket_analytics_preferences_update(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Update analytics preferences."""
    preferences = msg[ATTR_PREFERENCES]
    analytics: Analytics = hass.data[DOMAIN]

    await analytics.save_preferences(preferences)
    await analytics.send_analytics()

    connection.send_result(msg["id"])
