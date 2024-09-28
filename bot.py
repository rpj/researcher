import argparse
import asyncio
import uuid
from pathlib import Path

import ircpy as irc

from lib.research import R2Config, reports_for_query

OUT_PATH = Path("./bot.out").resolve()
LINE_LENGTH_LIM = 400

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
    prefix="er?",
)


@bot.event
async def ready(nickname, channel):
    print(f"Logged in as {nickname}, in {channel}!")
    print(f"Report In Channel? {args.reportInChannel}")


@bot.event
async def message_received(msg, user, channel):
    try:
        if not len(msg) or not len(user):
            return
        comps = msg.split(" ")
        if comps[0].startswith("research!") and len(comps) > 3:
            query = " ".join(comps[1:])
            bot.send_message(
                f'## Generating report for user {user} with query "{query}"...'
            )
            [(repPath, repCost, r2Url, html_r2)] = await reports_for_query(
                name=str(uuid.uuid4()),
                query=query,
                r2config=r2config,
                outPath=OUT_PATH,
                appendSupplementary=False,
            )
            bot.send_message(f"## Report complete! Cost: {repCost}")
            if args.reportInChannel or comps[0].endswith("!loud"):
                with open(repPath, "r") as f:
                    for line in f:
                        split_lines = [line]
                        if len(line) > LINE_LENGTH_LIM:
                            split_lines = []
                            while len(line) > LINE_LENGTH_LIM:
                                split_lines.append(line[:LINE_LENGTH_LIM])
                                line = line[LINE_LENGTH_LIM:]
                            split_lines.append(line)
                        for sl in split_lines:
                            await asyncio.sleep(1)
                            print(f"[{len(sl)}]>> {sl}")
                            bot.send_message(sl)
            bot.send_message(f"## _ Report available at: {r2Url} or {html_r2} _")
    except Exception as e:
        bot.send_message(f"BOT ERROR: {e}")


bot.connect()
