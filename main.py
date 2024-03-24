from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
import disnake
from disnake.ext import commands
from multiprocessing import Queue, Process, freeze_support
import asyncio
from bs4 import BeautifulSoup


def drive_and_refresh(queue, url):
    try:
        start = time.time()
        chrome_options = Options()
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        html = driver.page_source
        queue.put(html)
        finish = time.time()
        timer = finish - start
        print(f'{timer} sec(s) for 1 link.')
        for _ in range(0, 200):
            start = time.time()
            driver.refresh()
            html = driver.page_source
            queue.put(html)
            finish = time.time()
            timer = finish-start
            print(f'{timer} sec(s) for 1 link.')
    except Exception as e:
        drive_and_refresh(queue, url)
    driver.quit()
    drive_and_refresh(queue, url)

def bot_and_my_loop(queue, url):

    TOKEN = 'Input Your TOKEN'
    CHANNEL_ID = 'Input Your Channel ID'
    SERVER_ID = 'Input Your Server ID'

    async def my_loop(queue, url, CHANNEL_ID):
        output = ''
        previous_output = ''
        previous_html = ''
        n = 0
        while True:
            if queue.empty():
                pass
            if bot.is_ready():
                print('Bot still online.')
            html = queue.get()
            soup = BeautifulSoup(html, 'html.parser')
            data = soup.find('div', class_='sizes-list')
            sizes = ''
            for button in data:
                size = button.get_text(strip=True)
                if 'unavailable' in button['class']:
                    sizes += f'{size} - 0\n'
                else:
                    sizes += f'{size} - few\n'
            data = soup.find('h1', class_="product-specs__title h1")
            name = soup.h1.text.strip()
            data = soup.find('div', class_='price-tag')
            discount_span = soup.find('span', class_='price-tag__discount')
            default_span = soup.find('span', class_='price-tag__default')
            if discount_span is not None:
                price = discount_span.get_text(strip=True)
            else:
                price = default_span.get_text(strip=True)
            data = soup.find('img', class_='mobile-swiper__image')
            img = data['src']
            output = name + url + price + sizes + img
            if output != previous_output:
                print('send to channel')
                channel = bot.get_channel(int(CHANNEL_ID))
                embed = disnake.Embed(
                    url=url,
                    title=name,
                    color=disnake.Color.purple()
                )
                embed.set_thumbnail(url=img)
                embed.set_footer(text="V-Solutions Beta")
                embed.add_field(name=f"Price: {price}", value="", inline=False)
                embed.add_field(name="Sizes:", value=f"{sizes}", inline=False)
                await channel.send(embed=embed)
            previous_output = output

    intents = disnake.Intents.all()
    bot = commands.Bot(command_prefix='/', intents=intents, test_guilds=[int(SERVER_ID)])

    @bot.event
    async def on_ready():
        await bot.loop.create_task(my_loop(queue, url, CHANNEL_ID))

    bot.run(TOKEN)

if __name__ == '__main__':
    freeze_support()
    url = 'https://street-beat.ru/d/krossovki-adidas-originals-b75571/'
    q = Queue()
    p1 = Process(target=bot_and_my_loop, args=(q, url))
    p2 = Process(target=drive_and_refresh, args=(q, url))
    p1.start()
    p2.start()