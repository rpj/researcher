import argparse
import asyncio
import json
import time
import uuid
from collections import defaultdict
from pathlib import Path

import ircpy as irc

from lib.research import R2Config, reports_for_query

OUT_PATH = Path("./bot.out").resolve()
LINE_LENGTH_LIM = 400
TRIGGER = "research!"
RT_STATS = defaultdict(int)
RT_STATS["reportTypes"] = defaultdict(int)
STARTUP_TIME = time.time()

parser = argparse.ArgumentParser(description="An IRC bot that can do some research")
parser.add_argument("--nickname")
parser.add_argument("--server")
parser.add_argument("--channel")
parser.add_argument("--r2endpoint")
parser.add_argument("--r2bucket")
parser.add_argument("--r2domain")
parser.add_argument("--reportInChannel", action=argparse.BooleanOptionalAction)
args = parser.parse_args()
r2config = R2Config(
    endpoint=args.r2endpoint, bucket=args.r2bucket, domain=args.r2domain
)
args = parser.parse_args()

bot = irc.Bot(
    nickname=args.nickname,
    server=args.server,
    channel=args.channel,
    prefix="er?",  # TODO: fix crappy handling of this in the lib...
)


async def _throttled_send(lines, sleep_time_secs=1):
    for l in lines:
        await asyncio.sleep(sleep_time_secs)
        bot.send_message(l)


@bot.event
async def ready(nickname, channel):
    print(f"Logged in as {nickname}, in {channel}!")
    print(f"Report In Channel? {args.reportInChannel}")
    bot.send_message("Ready to research!")


@bot.event
async def message_received(msg, user, channel):
    try:
        if not len(msg) or not len(user):
            return

        [trigger, *queryComps] = msg.split(" ")

        if trigger.startswith(TRIGGER) and len(queryComps) == 0:
            cmd = trigger[len(TRIGGER) :]
            if cmd == "ping":
                bot.send_message("Pong!")
            if cmd == "stats":
                await _throttled_send(
                    json.dumps(
                        {**RT_STATS, "uptime": time.time() - STARTUP_TIME}, indent=2
                    ).split("\n")[1:-1]
                )
            return

        if trigger.startswith(TRIGGER) and len(queryComps) > 0:
            query = " ".join(queryComps)
            report_type = "research"
            type_idx = trigger.find("!type")
            if type_idx != -1:
                [_t, report_type] = trigger[type_idx:].split("=")

            msg = f'Generating {report_type} report for user {user} with query "{query}"...'
            bot.send_message(msg)
            print(msg)
            [(repPath, repCost, elapsed, r2Url, html_r2, supl_url, supl_html_url)] = (
                await reports_for_query(
                    name=str(uuid.uuid4()),
                    query=query,
                    r2config=r2config,
                    outPath=OUT_PATH,
                    reportTypes=[report_type],
                )
            )
            RT_STATS["costs"] += repCost
            RT_STATS["processingTime"] += elapsed
            RT_STATS["queries"] += 1
            RT_STATS["reportTypes"][report_type] += 1

            bot.send_message(
                f'Report for {user}\'s query "{query}" (~{round(elapsed)}s): {html_r2}'
            )

            loud = trigger.endswith("!loud")

            if args.reportInChannel:
                with open(repPath, "r") as f:
                    for line in f:
                        split_lines = [line]
                        if len(line) > LINE_LENGTH_LIM:
                            split_lines = []
                            while len(line) > LINE_LENGTH_LIM:
                                split_lines.append(line[:LINE_LENGTH_LIM])
                                line = line[LINE_LENGTH_LIM:]
                            split_lines.append(line)
                        await _throttled_send(split_lines)

            if loud:
                bot.send_message(
                    f"Markdown available at {r2Url}; supplementary available at {supl_url} or {supl_html_url}; cost {repCost}"
                )
    except Exception as e:
        bot.send_message(f"BOT ERROR: {e}")


bot.connect()
