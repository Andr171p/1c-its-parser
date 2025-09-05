import logging

from playwright.async_api import Browser

from .constants import URL
from .settings import Credentials
from .utils import get_current_page

logger = logging.getLogger(__name__)


async def authenticate(browser: Browser, credentials: Credentials) -> Browser:
    """Аутентифицируется на сайте 1c.its.ru"""
    page = await get_current_page(browser)
    await page.goto(URL)
    await page.fill("#username", credentials.username)
    await page.fill("#password", credentials.password)
    await page.click("#loginButton")
    await page.wait_for_load_state("networkidle")
    if page.url != f"{URL}/login":
        logger.info("Successfully authenticated!")
    else:
        logger.warning("Error occurred while authentication!")
    return browser
