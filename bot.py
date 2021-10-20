from logger import LocalLogCollector
from discord.ext import commands
from configurator import configurator
from mysqlconnector import mySQLConnector
import discord
import requests
import os
# ==================================================================================================================================================================
config = configurator(os.path.dirname(os.path.realpath(__file__))+"\config\config.ini")
prefix = config.get(section='bot',setting='prefix')
token  = config.get(section='bot',setting='token')
owners = config.get(section='bot',setting='owners')
twitch_id = config.get(section='twitch',setting='bot_client_id')
twitch_secret = config.get(section='twitch',setting='bot_client_secret')
youtube_api_key = config.get(section='youtube',setting='api_key')
intents = discord.Intents.default()
intents.members = True
url = 'https://id.twitch.tv/oauth2/token'
params = {
    'client_id': twitch_id,
    'client_secret': twitch_secret,
    'grant_type':'client_credentials'}
req = requests.post(url=url,params=params)
twitch_token = req.json()['access_token']
bot = commands.Bot(command_prefix=prefix,intents=intents)
bot.twitch_creds = {
    'client': twitch_id,
    'secret': twitch_secret,
    'token' : twitch_token
    }
bot.youtube_api_key = youtube_api_key
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
# Список когов бота в порядке, в котором они должны быть загружены при запуске бота
cogs_list = [
    'commands_admin.py',
    'commands_common.py',
    'commands_help.py',
    'commands_moderator.py',
    'commands_owner.py',
    'commands_reactions.py',
    'commands_video.py',
    'commands_debug.py',
    'on_errors.py',
    'on_member.py',
    'on_message.py',
    'on_ready.py',
    'loop_tasks.py'
]
# Функция загрузки когов
def load_cogs(reload=False):
    bot.LLC.addlog('Загружаем коги')
    for filename in cogs_list:
        if filename.endswith('.py'):
            fn = f'cogs.{filename[:-3]}'
            if reload==True:
                bot.unload_extension(fn)
            bot.LLC.addlog(f'Загружаем: "{fn}"')
            bot.load_extension(fn)
    bot.LLC.addlog('Коги загружены')
# ==================================================================================================================================================================
#bot.get_emoji = get_emoji
bot.LLC.addlog('Запускаем бота')
load_cogs()
bot.IsOnlineNow = False
bot.run(token)