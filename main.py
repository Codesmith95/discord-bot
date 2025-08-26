import os
import discord
from discord.ext import commands
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# -------- Load environment variables safely --------
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("POLL_CHANNEL_ID", "0"))
VOTE_THRESHOLD = int(os.getenv("VOTE_THRESHOLD", "2"))
OWNER_ID = [int(os.getenv("OWNER_ID_1", "0")), int(os.getenv("OWNER_ID_2", "1"))]
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# -------- Intents and Bot --------
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
poll_message = None

# -------- Post poll safely --------
async def post_poll(channel):
    if channel is None:
        print("❌ Poll channel not found! Check POLL_CHANNEL_ID")
        return None
    try:
        await channel.purge(limit=100)
        msg = await channel.send("React 👍 to vote for server start!")
        await msg.add_reaction("👍")
        print(f"✅ Poll posted with ID {msg.id}")
        return msg
    except Exception as e:
        print(f"❌ Failed to post poll: {e}")
        return None

# -------- Notify owner via email --------
async def notify_owner():
    message = Mail(
        from_email=os.getenv("EMAIL"),
        to_emails=os.getenv("TO_EMAIL"),
        subject='Server Start Vote Passed!',
        plain_text_content='Enough votes have been reached!'
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
        print("📧 Email sent via SendGrid!")
    except Exception as e:
        print(f"❌ Failed to send email via SendGrid: {e}")


# -------- Bot Events --------
@bot.event
async def on_ready():
    global poll_message
    print(f"✅ Logged in as {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Poll channel not found! Check POLL_CHANNEL_ID")
        return

    # Check for existing poll
    async for msg in channel.history(limit=50):
        if "React 👍 to vote for server start!" in msg.content:
            poll_message = msg
            print(f"ℹ️ Found existing poll with ID {poll_message.id}")
            break

    # If no existing poll, post new one
    if poll_message is None:
        poll_message = await post_poll(channel)
        print("ℹ️ Posted a fresh poll on startup.")

@bot.event
async def on_reaction_add(reaction, user):
    global poll_message
    if user.bot or poll_message is None:
        return
    if reaction.message.id == poll_message.id and str(reaction.emoji) == "👍":
        if reaction.count >= VOTE_THRESHOLD:
            await notify_owner()

# -------- Commands --------
@bot.command()
async def resetpoll(ctx):
    global poll_message
    if ctx.author.id in OWNER_ID:
        await ctx.send("❌ You don’t have permission to do this.")
        return
    poll_message = await post_poll(ctx.channel)
    if poll_message:
        await ctx.send("✅ Poll has been reset for the next round!")

# -------- Run Bot --------
bot.run(TOKEN)
