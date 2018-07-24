import logging

from aiohttp import ClientError
from aiohttp.web import Application
from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))


async def get_case(case_id: str, app: Application):
    async with app.http_session_pool.get(f"{app['CASE_URL']}/cases/{case_id}", auth=app["CASE_AUTH"]) as response:
        try:
            response.raise_for_status()
        except ClientError as ex:
            logger.error("Error retrieving case", case_id=case_id, url=str(response.url), status_code=response.status)
            raise ex
        else:
            logger.debug("Successfully retrieved case", case_id=case_id, url=str(response.url))
        return await response.json()


async def post_case_event(case_id: str, category: str, description: str, app: Application):
    async with app.http_session_pool.post(
        f"{app['CASE_URL']}/cases/{case_id}/events",
        auth=app["CASE_AUTH"],
        json={'description': description, 'category': category, 'createdBy': 'RESPONDENT_HOME'}
    ) as response:
        try:
            response.raise_for_status()
        except ClientError as ex:
            logger.error("Error posting case event", case_id=case_id, url=str(response.url), status_code=response.status)
            raise ex
        else:
            logger.debug("Successfully posted case event", case_id=case_id, url=str(response.url))
        return await response.json()
