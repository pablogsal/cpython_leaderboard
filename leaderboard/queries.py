import asyncio
import collections
import re

import aiohttp
from aiohttp import web
import cachetools
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio

MISS_ISLIGNTON_USERNAME = "miss-islington"
VALID_USERS = {
    MISS_ISLIGNTON_USERNAME,
    "pablogsal",
    "tiran",
    "ezio-melotti",
    "1st1",
    "DinoV",
    "JulienPalard",
    "ambv",
    "applio",
    "benjaminp",
    "brettcannon",
    "emilyemorehouse",
    "encukou",
    "ericsnowcurrently",
    "ezio-melotti",
    "gpshead",
    "gvanrossum",
    "jaraco",
    "larryhastings",
    "lisroach",
    "matrixise",
    "markshannon",
    "mdickinson",
    "ned-deily",
    "vsajip",
    "willingc",
    "zooba",
    "voidspace",
    "zware",
    "holdenweb",
    "scoder",
    "Yhg1s",
    "pganssle",
}

AUTOMERGE_REGEXP = re.compile(
    r"Automerge-Triggered-By: @([a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})"
)


def is_pr_valid(pr):
    if pr["user"]["login"] == MISS_ISLIGNTON_USERNAME:
        return False
    if pr["user"]["login"] == pr["merged_by"]["login"]:
        return False
    if pr["merged_by"]["login"] not in VALID_USERS:
        return False
    return True


async def get_merged_prs(gh_api, *, since, core_devs=None):
    query = f"search/issues?q=is:merged+is:pr+repo:python/cpython+base:master+merged:>{since}"
    futures = []
    prs = []
    async for pr in gh_api.getiter(query):
        futures.append(asyncio.create_task(gh_api.getitem(pr["pull_request"]["url"])))
    for future in futures:
        await future
        prs.append(future.result())
    return await categorize_prs(gh_api, prs)


async def categorize_prs(gh_api, prs):
    prs_merged = collections.Counter()
    for pr in prs:
        if not is_pr_valid(pr):
            continue
        author = pr["merged_by"]["login"]
        if author == MISS_ISLIGNTON_USERNAME:
            label_registers = AUTOMERGE_REGEXP.findall(pr["body"])
            if not label_registers:
                continue
            *_, author = label_registers
        if author not in VALID_USERS:
            continue
        prs_merged[author] += 1
    return prs_merged
