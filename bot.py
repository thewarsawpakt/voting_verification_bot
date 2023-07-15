"""
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 
"""

from discord.ext import commands, tasks
from discord import Intents, Member, Reaction
from ast import literal_eval
import time

bot = commands.Bot(command_prefix=".", intents=Intents.default())


with open("wal.log", "a+") as wal:
    if len(wal.readlines()) > 0:
        # replace current state with last entry in logfile
        verification_db = literal_eval(wal.readlines[-1])
    else:
        verification_db = {}


VERIFICATION_THRESHHOLD = 10
VERIFIED_ROLE_ID = 1128559850373271592
TOKEN = ""


@bot.event
async def on_reaction_add(reaction: Reaction, user: Member):
    if user.id == reaction.message.author.id or reaction.emoji.name != "white_check_mark":
        return

    if agreed := verification_db.get(user.id, False):
        verification_db[user.id] += 1
    else:
        verification_db[user.id] = 1

    # simple write-ahead log that allows us to recover state if the application crashes
    with open("wal.log", "a+") as wal:
        wal.write(f"{time.time()},{verification_db}")

@tasks.loop(minutes=60)
async def check_verified_count():
    # check every 60 minutes to see which users should be verified
    for (user_id, count) in enumerate(verification_db):
        if count >= VERIFICATION_THRESHHOLD:
            member = bot.get_guild(1001876487059816542).get_member(user_id)
            member.add_roles([VERIFIED_ROLE_ID], reason=f"Verified after {count} agreements")

bot.run(TOKEN)