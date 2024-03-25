from .moderating import client, has_perms
import asyncio
from . import report

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