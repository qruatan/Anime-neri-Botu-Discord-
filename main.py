import discord
from discord.ext import tasks, commands
import aiohttp
import os
from dotenv import load_dotenv
from datetime import time, timezone

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# AYARLAR
TARGET_CHANNEL_ID = 1467576625364205745 # Öneri kanalının ID'si
TARGET_ROLE_ID = 1467577041829494838 # Etiketlenecek rolün ID'si (Örn: @AnimeSeverler)

intents = discord.Intents.default()
intents.message_content = True  # Komutları okuması için bu satır ŞART
bot = commands.Bot(command_prefix='!', intents=intents)

# Her gün saat 18:00'da çalışacak (UTC)
scheduled_time = time(hour=15, minute=0, tzinfo=timezone.utc)

async def get_recommendation():
    url = "https://api.jikan.moe/v4/random/anime"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['data']
            return None

@tasks.loop(time=scheduled_time)
async def daily_recommendation():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        anime = await get_recommendation()
        if anime:
            # Rol etiketleme formatı: <@&ROL_ID>
            mention_text = f"<@&{TARGET_ROLE_ID}> Yeni bir öneri vaktı! 🌸"
            
            embed = discord.Embed(
                title=f"🎬 {anime['title']}",
                description=anime.get('synopsis', 'Açıklama bulunamadı.')[:400] + "...",
                url=anime.get('url'),
                color=discord.Color.gold()
            )
            embed.set_image(url=anime['images']['jpg']['large_image_url'])
            embed.add_field(name="⭐ Puan", value=anime.get('score', 'N/A'), inline=True)
            embed.add_field(name="📺 Tür", value=anime.get('type', 'N/A'), inline=True)
            embed.set_footer(text="İyi seyirler dilerim!")
            
            # Mesajı hem etiketle hem de embed ile gönder
            await channel.send(content=mention_text, embed=embed)

@bot.command(name="test")
async def test_rec(ctx):
    """Sadece deneme amaçlı: Botun öneri yapmasını manuel tetikler."""
    print("Test komutu algılandı, öneri gönderiliyor...")
    await daily_recommendation()
    await ctx.send("✅ Test önerisi başarıyla gönderildi!")

@bot.event
async def on_ready():
    print(f'{bot.user} aktif! Hedef Kanal ID: {TARGET_CHANNEL_ID}')
    if not daily_recommendation.is_running():
        daily_recommendation.start()

bot.run(TOKEN)