import asyncio
import os
from datetime import datetime, timedelta

import aiocache
import aiohttp
from aiohttp import web
import aiohttp_jinja2
from gidgethub import aiohttp as gh_aiohttp
import jinja2

from .queries import get_merged_prs

SPRINT_FIRST_DATE = "2019-09-09"
SECONDS_TO_INVALIDATE = 60 * 10

@aiocache.cached(ttl=SECONDS_TO_INVALIDATE)
async def merged_prs():
    print("Making new check")
    async with aiohttp.ClientSession() as session:
        oauth_token = os.environ.get("GH_AUTH")
        gh = gh_aiohttp.GitHubAPI(session, "leaderboard", oauth_token=oauth_token)
        prs = await get_merged_prs(gh, since=SPRINT_FIRST_DATE)
    return prs


async def handle_get(request, name="home"):
    prs = await merged_prs()
    context = {"ranking": prs}
    response = aiohttp_jinja2.render_template("index.html", request, context=context)
    return response


if __name__ == "__main__":  # pragma: no cover
    app = web.Application()

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), "templates"))
    )
    app["static_root_url"] = os.path.join(os.getcwd(), "static")
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    app.add_routes(
        [
            web.get("/", handle_get, name="home"),
            web.static("/static", os.path.join(os.getcwd(), "static")),
        ]
    )
    web.run_app(app, port=port)
