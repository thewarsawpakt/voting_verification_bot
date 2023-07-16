from discord.ext import commands, tasks
from discord import Intents, Member, Reaction, Activity, ActivityType, Status, RawReactionActionEvent
from ast import literal_eval
import os

bot = commands.Bot(command_prefix=".", intents=Intents.default())


with open("wal.log", "a+") as wal:
    if len(wal.readlines()) > 0:
        # replace current state with last entry in logfile
        verification_db = literal_eval(wal.readlines[-1])
    else:
        verification_db = {}


VERIFIED_ROLE_ID = os.environ.get("VERIFIED_ROLE_ID")
VERIFICATION_CHANNEL_ID = os.environ.get("VERIFICATION_CHANNEL_ID")
GUILD_ID = os.environ.get("GUILD_ID")
BOT_COUNT = os.environ.get("BOT_COUNT")

# calculate the verification threshhold as a function of guild size
verification_threshold = lambda _: (bot.get_guild(GUILD_ID).member_count - BOT_COUNT) // 5
env = lambda v: os.environ.get(v, None)


@bot.event
async def on_ready():
    await bot.change_presence(activity=Activity(name="your verification requests.", type=ActivityType.listening), status=Status.idle)

@bot.event
async def on_raw_reaction_add(reaction: RawReactionActionEvent):
    if reaction.emoji.name != "✅" or reaction.channel_id != VERIFICATION_CHANNEL_ID or reaction.member.id == reaction.message_author_id:
        return

    if agreed := verification_db.get(reaction.member, False):
        verification_db[reaction.message_author_id] += 1
    else:
        verification_db[reaction.message_author_id] = 1

    # simple write-ahead log that allows us to recover state if the application crashes
    with open("./wal.log", "a+") as wal:
        wal.write(f"{verification_db}\n")


@tasks.loop(minutes=60)
async def check_verified_count():
    # check every 60 minutes to see which users should be verified
    for (user_id, count) in enumerate(verification_db):
        if count >= verification_threshold():
            member = bot.get_guild(GUILD_ID).get_member(user_id)
            member.add_roles([VERIFIED_ROLE_ID], reason=f"Verified after {count} agreements")

bot.run(os.environ.get("TOKEN"))