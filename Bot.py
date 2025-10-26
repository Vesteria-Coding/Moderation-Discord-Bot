import os
import asyncio
import discord
import requests
import time as t
import aiofiles as asyncfile
from dotenv import load_dotenv
from discord import app_commands, Interaction, Embed

# Setup Credentials
load_dotenv()
MOD_API = os.getenv("MOD_API")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PASTEBIN_KEY = os.getenv("PASTEBIN_KEY")
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID'))

# Setup
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
banned_words = []

def create_pastebin(context , key):
    paste_data = {"api_dev_key": key, "api_option": "paste", "api_paste_code": context, "api_paste_name": "Big Message Removed", "api_paste_private": "1", "api_paste_expire_date": "N"}
    response = requests.post("https://pastebin.com/api/api_post.php", data=paste_data)
    return response.text

@client.event
async def on_ready():
    if not os.path.exists('message_log.txt'):
        open('message_log.txt', 'w').close()
    if not os.path.exists('banned_words.txt'):
        open('banned_words.txt', 'w').close()
    with open('banned_words.txt', 'r') as file:
        for word in file.read().splitlines():
            if word:
                banned_words.append(word)
    print(f"Bot is ready. Logged in as {client.user} (ID: {client.user.id})")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    async with asyncfile.open('message_log.txt', 'a') as log:
        await log.write(f'Message From: {message.author}, {message.author.id} | {message.content} \n')
    if len(message.content) > 1000:
        await message.delete()
        if message.author.nick:
            author = message.author.nick
        else:
            author = message.author.display_name
        embed = discord.Embed(title='Big Message Deleted', color=discord.Color.dark_gold())
        embed.add_field(name=f'Message sent by: {author}', value=create_pastebin(message.content, PASTEBIN_KEY), inline=False)
        await message.channel.send(embed=embed)
    if any(bad_word in message.content.lower() for bad_word in banned_words):
        await message.reply("That word isn’t allowed here.", mention_author=True)
        await message.delete()
        return

# Commands
@tree.command(name="ping", description="sends ping of bot", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    latency = client.latency * 1000  # Convert to ms
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)

@tree.command(name="add_banned_word", description="Adds a banned word to the word list", guild=discord.Object(id=GUILD_ID))
async def add(interaction: discord.Interaction, word: str):
    await interaction.response.defer(thinking=True)
    if MOD_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.followup.send("You don't have permission to use this command.", ephemeral=True)
        return
    async with asyncfile.open('banned_words.txt', 'a') as file:
        await file.write(f'{word.lower()}\n')
        banned_words.append(word.lower())
    await interaction.followup.send(f'Added word **{word.lower()}** to the banned word list.', ephemeral=True)

client.run(BOT_TOKEN)
