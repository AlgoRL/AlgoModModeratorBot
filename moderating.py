import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
import json
from report import Report

load_dotenv('../.env')
token = os.environ.get("MODERATOR_DISCORD_TOKEN")
if not token:
    print("Token is unreachable")
    exit()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="--", intents=intents)

# small change for testing :3

# on ready function
@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    try:
        synced = await client.tree.sync()
        print(f'Synced {len(synced)} commands(s)')
    except Exception as e:
        print(e)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your conversations..."))

immune_roles = [
    "algo",
    "developer",
    "moderator",
    "algomod helper",
    "ALG",
    "Mod",
    "mee6"
]

mod_roles = [
    "Mod",
    "Moderator",
    "ALG",
    "Developer",
    "Admin"
]

with open("banned_words.json", 'r') as f:
    banned_words = json.load(f)['banned_words']

def message_has_invite(message):
    if "https://discord" in message.content:
        return True
    return False

async def mod(message, response, ban=False, delete=True):
    await message.channel.send(response)
    if ban:
        print(f"Banning user: {message.author}\nMessage: {message.content}")
        await message.author.ban()
    else:
        member = message.guild.get_member(message.author.id)
        if member:
            print(f"Warning user: {message.author}\nMessage: {message.content}")
            report(member, message.content, reason="Use of banned phrase", sev=1, manual=False)
    if delete:
        await message.delete()

# @client.command()
# async def warn(ctx, member : discord.Member,*reason:str):
        
def report(user, content=None, sev=1, reason=None, manual=False):
    doc = Report(user, content, sev, reason, manual)
    print(f"Sending warning report:\nUser: {user}\nContent: {content}\nSeverity: {sev}\nReason: {reason}")
    doc.log()


# Usage:
# --warn {user -> discord.Member : optional} {sev -> int : optional} {*reason -> str : optional} 
    
# --warn only for reply warnings
# /warn for all other manual warnings
    
@client.command()
async def echo(ctx, *msg):
    await ctx.message.channel.send(' '.join(msg))
    return

@client.command()
async def ping(ctx):
    await ctx.message.channel.send("Pong!")
    return

async def has_perms(user : discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    if any(role.lower() in user_roles for role in mod_roles):
        return True
    return False

async def is_immune(user : discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    if any(role.lower() in user_roles for role in immune_roles):
        return True
    return False

# # idea -> add a private_view parameter that makes the log file ephemeral
# @client.tree.command(name="sendlog")
# @app_commands.describe(dontuse="placeholder")
# async def set(interaction: discord.Interaction, dontuse : str = None):
#     if not await has_perms(interaction.user):
#         await interaction.response.send_message("You don't have permission to do that!", ephemeral=True)
#         return
    
#     channel = interaction.channel
#     everyone_perms = channel.overwrites_for(channel.guild.default_role)
#     if everyone_perms.read_messages:
#         await interaction.response.send_message("Logs cannot be sent to public channels. (@everyone has read permissions in this channel.)", ephemeral=True)
#         return
    
#     if dontuse is not None:
#         await interaction.response.send_message("I said not to use that parameter smh", ephemeral=True)
    
#     try:
#         with open("reports_log.json", "rb") as f:
#             log_file = discord.File(f, filename="reports_log.json")
#             await interaction.channel.send(log_file)
#             return
#     except FileNotFoundError:
#         await interaction.channel.send()
        
#     return

def get_member_log(member: discord.Member):
    with open("reports_log.json", 'r') as f:
        data = json.load(f)
    user_data = data.get(str(member))
    return user_data

@client.command()
async def sendlog(ctx, member : discord.Member = None):
    if not await has_perms(ctx.message.author):
        await ctx.message.channel.send("You don't have permission to do that!")
        return
    everyone_perms = ctx.channel.overwrites_for(ctx.channel.guild.default_role)
    if everyone_perms.read_messages:
        await ctx.message.channel.send("Logs cannot be sent to public channels. (@everyone has read permissions in this channel.)")
        return
    if not member:
        try:
            with open("reports_log.json", "rb") as f:
                log_file = discord.File(f, filename="warnings_log.json")
                await ctx.send(file=log_file)
                return
        except FileNotFoundError:
            await ctx.send("JSON File not found for some reason (this error should never happen. if it does, ping @ruasi immediately)")
            return
    else:
        with open('log_cache.txt', 'w') as f:
            json.dump(get_member_log(member), f, indent=4)
        with open('log_cache.txt', 'rb') as f:   
            log_file = discord.File(f, filename=f"{member}_log_file.json")
        await ctx.send(file=log_file)
        return


# semantics:
# (reply) --warn not supposed to say that -> 
@client.command()
async def warn(ctx, *args):
    if not await has_perms(ctx.message.author):
        await ctx.message.channel.send("You don't have permission to do that!")
        return
    if args:
        first_arg = args[0]
        try:
            sev = int(first_arg)
            reason = ' '.join(args[1:])
        except ValueError:
            sev = 1
            reason = ' '.join(args)
    else:
        sev = 1
        reason = None

    # Reply auto-warn system
    # Use reply warns for warning users with a specific message
    if ctx.message.reference:
        replied_message = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        replied_author = replied_message.author
        await ctx.message.channel.send(f"<@{replied_author.id}> you have been warned. Reason: {reason}")
        report(user=replied_author, content=replied_message.content, sev=sev, reason=reason, manual=True)
    else:
        await ctx.message.channel.send("You can only use --warn in a message reply to the target user. Try /warn")
    await replied_message.delete()
    await ctx.message.delete()

@client.tree.command(name="warn")
@app_commands.describe(user = "Mention the user you are warning", reason = "Reason for warning", severity = "Severity of infraction (1-5) : Default = 1", content = "Content of message being warned (optional)")
async def set(interaction: discord.Interaction, user: discord.Member, reason: str = None, severity: int = 1, content: str = None):
    member = interaction.guild.get_member(interaction.user.id)
    if not await has_perms(member):
        await interaction.response.send_message("You don't have permission to do that!", ephemeral=True)
        return
    if not user:
        await interaction.response.send_message("Please specify the user you want to warn.", ephemeral=True)
        return
    if not 1 <= severity <= 5:
        await interaction.response.send_message("Severity must be between 1 and 5, 1 being a small infraction, 5 being serious.", ephemeral=True)
    if user.guild is None:
        await interaction.response.send_message("User not found in this server.", ephemeral=True)
    report(user=user, reason=reason, sev=severity, content=content, manual=True)
    await interaction.response.send_message(f"<@{user.id}> you have been warned by a moderator.\nReason: {reason}")
    return


@client.event
async def on_message(message):
    await client.process_commands(message)

    if message.author == client.user:
        return
    # message = message to be checked (checks every message)
    # don't moderate if message is a DM
    if not message.guild:
        return
    member = message.guild.get_member(message.author.id)
    if member:
        # do not moderate messages from immune users (see `immune_roles`)
        if await is_immune(member):
            print(f"[Log] You are immune! Member: {message.author}")
            return
        
        if any(word in message.content for word in banned_words):
            await mod(message, "you cant say that idiot", delete=True)
            return
        
        if message_has_invite(message):
            if message.channel.id == 814757332944814100:
                return
            await mod(message, "You cannot send Discord server invites in this channel.", delete=True)
            if message:
                await message.delete()
            return
        
        
client.run(token)
