import logging
import subprocess
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    def run_python_script(call):
        subprocess.Popen(["python3", "/config/custom_components\my_python_script\python_script.py"])

    hass.services.async_register("my_python_script", "run", run_python_script)
    return True
