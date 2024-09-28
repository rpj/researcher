import argparse
import asyncio
import uuid
from pathlib import Path

import ircpy as irc

from lib.research import reports_for_query

OUT_PATH = Path("./bot.out").resolve()
LINE_LENGTH_LIM = 400

parser = argparse.ArgumentParser(description="An IRC bot that can do some research")
parser.add_argument("--nickname")
parser.add_argument("--server")
parser.add_argument("--channel")
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


@bot.event
async def message_received(msg, user, channel):
    if not len(msg) or not len(user):
        return
    comps = msg.split(" ")
    if comps[0] == "research!" and len(comps) > 3:
        query = " ".join(comps[1:])
        msg = f'Generating report for user {user} with query "{query}"...'
        bot.send_message(f"## {msg}")
        print(msg)
        try:
            [(repPath, repCost)] = await reports_for_query(
                name=str(uuid.uuid4()),
                query=query,
                outPath=OUT_PATH,
                appendSupplementary=False,
            )
            bot.send_message(f"## Report complete! Cost: {repCost}")
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
            bot.send_message(f"_Report can be found at {repPath.stem}_")
        except Exception as e:
            print(e)


bot.connect()
