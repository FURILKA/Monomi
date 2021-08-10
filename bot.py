from logger import LocalLogCollector
from discord.ext import commands
from configurator import configurator
from mysqlconnector import mySQLConnector
import discord
import os
# ==================================================================================================================================================================
#pycatalog = os.environ['PythonFilesCatalog']
config = configurator(os.path.dirname(os.path.realpath(__file__))+"\config\config.ini")
prefix = config.get(section='bot',setting='prefix')
token  = config.get(section='bot',setting='token')
owners = config.get(section='bot',setting='owners')
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=prefix,intents=intents)
bot.remove_command('help')
bot.prefix = prefix
bot.LLC = LocalLogCollector()
bot.owners = owners.split(';')
bot.mysql = mySQLConnector(
    host=config.get(section='mySQL',setting='host'),
    user=config.get(section='mySQL',setting='user'),
    pwrd=config.get(section='mySQL',setting='pass'),
    base=config.get(section='mySQL',setting='base'),
    LocalLogCollector = bot.LLC)
# ==================================================================================================================================================================
def load_cogs(reload=False):
    bot.LLC.addlog('Загружаем коги')
    for filename in os.listdir(os.path.dirname(os.path.realpath(__file__))+'/cogs'):
        if filename.endswith('.py'):
            fn = f'cogs.{filename[:-3]}'
            if reload==True:
                bot.unload_extension(fn)
            bot.load_extension(fn)
    bot.LLC.addlog('Коги загружены')
# ==================================================================================================================================================================
def get_emoji(emoji_name):
    bot.mysql.connect()
    result = bot.mysql.execute(f"SELECT emoji_url FROM emojis WHERE emoji_name = '{emoji_name}'")
    emoji_url = ''
    if result != [] and result != []:
        emoji_url = result[0]['emoji_url']
    bot.mysql.disconnect()
    return(emoji_url)
# ==================================================================================================================================================================
bot.get_emoji = get_emoji
bot.LLC.addlog('Запускаем бота')
load_cogs()
bot.run(token)