# Import necessary libraries
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import json
from report import Report
from datetime import date
import asyncio

# Load environment variables
load_dotenv('../.env')
token = os.environ.get("MODERATOR_DISCORD_TOKEN")
if not token:
    print("Token is unreachable")
    exit()

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot
client = commands.Bot(command_prefix="--", intents=intents)

# Define immune and moderator roles
immune_roles = ["algo", "developer", "moderator", "algomod helper", "ALG", "Mod", "mee6"]
mod_roles = ["Mod", "Moderator", "ALG", "Developer", "Admin"]

# Load banned words from file
with open("banned_words.json", 'r') as f:
    banned_words = json.load(f)['banned_words']

# Check if a message contains an invite link
def message_has_invite(message):
    return "https://discord" in message.content

# Function to handle moderation actions
async def mod(message, response, ban=False, kick=False, delete=True):
    sent_message = await message.channel.send(response)
    if ban:
        print(f"Banning user: {message.author}\nMessage: {message.content}")
        await message.author.ban()
    elif kick:
        print(f"Kicking user: {message.author}\nMessage: {message.content}")
        await message.author.kick()
    async def delete_message():
        await asyncio.sleep(10)
        await sent_message.delete()
    if delete:
        await message.delete()
    asyncio.create_task(delete_message())

# Function to send warning report
def report(user, content=None, sev=1, reason=None, manual=False):
    doc = Report(user, content, sev, reason, manual)
    print(f"Sending warning report:\nUser: {user}\nContent: {content}\nSeverity: {sev}\nReason: {reason}")
    doc.log()

# Command to echo a message
@client.command()
async def echo(ctx, *msg):
    await ctx.message.channel.send(' '.join(msg))

# Command to ping
@client.command()
async def ping(ctx):
    await ctx.message.channel.send("Pong!")

# Check if user has moderator permissions
async def has_perms(user: discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    return any(role.lower() in user_roles for role in mod_roles)

# Check if user is immune
async def is_immune(user: discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    return any(role.lower() in user_roles for role in immune_roles)

# Function to retrieve log data for a member
def get_member_log(member: discord.Member):
    try:
        with open("reports_log.json", 'r') as f:
            data = json.load(f)
        user_data = data.get(str(member))
        return user_data
    except FileNotFoundError:
        print("Log file not found.")
        return None


# Command to send log file
@client.command()
async def sendlog(ctx, member: discord.Member = None):
    if not await has_perms(ctx.message.author):
        await ctx.message.channel.send("You don't have permission to do that!")
        return
    everyone_perms = ctx.channel.overwrites_for(ctx.channel.guild.default_role)
    if everyone_perms.read_messages:
        await ctx.message.channel.send("Logs cannot be sent to public channels. (@everyone has read permissions in this channel.)")
        return
    try:
        if not member:
            with open("reports_log.json", "rb") as f:
                log_file = discord.File(f, filename="warnings_log.json")
                await ctx.send(file=log_file)
        else:
            with open('log_cache.txt', 'w') as f:
                json.dump(get_member_log(member), f, indent=4)
            with open('log_cache.txt', 'rb') as f:   
                log_file = discord.File(f, filename=f"{member}_log_file.json")
            await ctx.send(file=log_file)
    except FileNotFoundError:
        await ctx.send("JSON File not found. Please contact the bot administrator.")

# Command to warn users
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

    if ctx.message.reference:
        replied_message = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        replied_author = replied_message.author
        await ctx.message.channel.send(f"<@{replied_author.id}> you have been warned. Reason: {reason}")
        report(user=replied_author, content=replied_message.content, sev=sev, reason=reason, manual=True)
    else:
        await ctx.message.channel.send("You can only use --warn in a message reply to the target user. Try /warn")
    await asyncio.sleep(5)
    await ctx.message.delete()

# Start bot
client.run(token)
