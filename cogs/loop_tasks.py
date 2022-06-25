from asyncio.tasks import sleep
from discord.ext import commands
from discord.ext import tasks
from twitchAPI.twitch import Twitch
from colors import color
from googleapiclient.discovery import build
import random
import requests
import discord
import datetime
import asyncio
import urllib.request
import os
import datetime
# ==================================================================================================================================================================
class loop_tasks(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
        self.twich_check_streamers_online.start()
        self.youtube_check_new_videos.start()
        self.clear_messages_by_tymer.start()
    # **************************************************************************************************************************************************************
    # Получение информации об начале трансляции стримов
    @tasks.loop(minutes=1)
    async def twich_check_streamers_online(self):
        try:
            if self.bot.IsOnlineNow == False: return
            result = self.bot.mysql.execute('SELECT * FROM twitch_streamers')
            if result == [] or result == () : return
            for row in result:
                row_id     = row['id']
                user_name  = row['twitch_user_name']
                user_id    = row['twitch_user_id']
                guild_id   = row['guild_id']
                channel_id = row['channel_id']
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Получаем информацию о пользователе по его id
                url = f'https://api.twitch.tv/helix/users?id={user_id}'
                headers = {
                    'Authorization':f'Bearer ' + self.bot.twitch_creds['token'],
                    'Client-Id': self.bot.twitch_creds['client']}
                user_info = requests.get(url=url,headers=headers).json()['data'][0]
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Получаем информацию о стриме пользователя по его id
                url = f'https://api.twitch.tv/helix/streams?user_id={user_id}'
                headers = {
                    'Authorization':f'Bearer ' + self.bot.twitch_creds['token'],
                    'Client-Id': self.bot.twitch_creds['client']}
                stream_info = requests.get(url=url,headers=headers).json()
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Поле "дата" отсутствует в словаре с информацией о стриме
                if not 'data' in stream_info:
                    self.bot.LLC.addlog(f'Некорректная информация о стриме пользователя с id'+row['twitch_user_id'],'error')
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Стрим выключен, в базе помечен как оффлайн
                if stream_info['data'] == [] and row['twitch_user_status'] == 'offline':
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Стрим выключен, но в базе помечен как онлайн
                if stream_info['data'] == [] and row['twitch_user_status'] == 'online':
                    channel = self.bot.get_channel(channel_id)
                    if channel == None :
                        self.bot.LLC.addlog(f'Канал дискорд не найден: channel == none','twitch')
                        return
                    self.bot.LLC.addlog(f'Стрим пользователя "{user_name}" [id:{user_id}] закончился','twitch')
                    query = f"UPDATE twitch_streamers SET twitch_user_status = 'offline', twitch_user_date = NOW() WHERE id = {row_id}"
                    self.bot.mysql.execute(query)
                    msgtext = f'Трансляция **{user_name}** закончилась!\nСпасибо, что были с нами!\nЖдём на следующих стримах!'
                    await channel.send(content=msgtext)
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Стрим включен, в базе помечен как онлайн
                if stream_info['data'][0]['type'] == 'live' and row['twitch_user_status'] == 'online':
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Стрим включен, в базе помечен как оффлайн
                channel = self.bot.get_channel(channel_id)
                if channel == None:
                    self.bot.LLC.addlog(f'Канал дискорд не найден: channel == none','twitch')
                    return               
                if stream_info['data'][0]['type'] ==  'live' and row['twitch_user_status'] == 'offline':
                    user_name = stream_info['data'][0]['user_name']
                    thumbnail_url = stream_info['data'][0]['thumbnail_url']
                    thumbnail_url = thumbnail_url.replace('{width}','500').replace('{height}','300')
                    self.bot.LLC.addlog(f'Стрим пользователя "{user_name}" [id:{user_id}] онлайн!','twitch')
                    query = f"UPDATE twitch_streamers SET twitch_user_status = 'online', twitch_user_date = NOW() WHERE id = {row_id}"
                    self.bot.mysql.execute(query)
                    embed=discord.Embed(
                        title=user_info['display_name'],
                        description="Стрим онлайн!",
                        color=color['green'],
                        url=f'https://www.twitch.tv/{user_name}')
                    filename = str(random.randint(100000000000,999999999999))+'.jpg'
                    filepath = os.getcwd().replace('\\','/')+'/images/temp/'+filename
                    urllib.request.urlretrieve(thumbnail_url,filepath)
                    file = discord.File(filepath, filename=filename)
                    embed.set_image(url="attachment://"+filename)
                    embed.add_field(
                        name='Игра',
                        value=stream_info['data'][0]['game_name'],
                        inline=False)
                    embed.set_thumbnail(url=user_info['profile_image_url'])
                    msgtext = f'@here\nКто-то внезапно начал трансляцию на твиче!\n⭐ https://www.twitch.tv/{user_name} ⭐\nПрисоединяйтесь, не пропустите!'
                    await channel.send(file=file, embed=embed,content=msgtext)
                    await asyncio.sleep(10)
                    os.remove(filepath)
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @tasks.loop(minutes=1)
    async def youtube_check_new_videos(self):
        try:
            if self.bot.IsOnlineNow == False: return
            # Получаем список записей, по которым истек срок (в часах) с момента последней проверки свежих видео
            # Для этого к полю "check_delay" таблицы "youtube_videos" прибавляем кол-во часов из поля "check_delay"
            # Если текущая дата/время больше, чем получившийся результат - значит период проверки прошел и нужно проверять повторно
            query = """
                SELECT 
                    id,
                    check_delay,
                    youtube_channel_name,
                    youtube_playlist_id,
                    youtube_last_video_date,
                    channel_id 
                FROM 
                    youtube_videos
                WHERE 
                    NOW() > DATE_ADD(check_date, INTERVAL check_delay HOUR)
            """
            result = self.bot.mysql.execute(query)
            if result == [] or result == (): return
            # У нас есть по меньшей мери 1 запись, по которой нужно проверить наличие свежих видео. Сделаем это.
            self.bot.LLC.addlog('Поиск новых видео на Youtube','youtube')
            youtube_api = build('youtube', 'v3', developerKey=self.bot.youtube_api_key)
            for row in result:
                row_id = row['id']
                check_delay = row['check_delay']
                channel_id = row['channel_id']
                channel = self.bot.get_channel(channel_id)
                if channel == None:
                    self.bot.LLC.addlog('Не удалось получить канал дискорд: continue == none','error')
                    continue
                youtube_channel_name = row['youtube_channel_name']
                youtube_playlist_id = row['youtube_playlist_id']
                youtube_last_video_date = row['youtube_last_video_date']
                response_videos = youtube_api.playlistItems().list(playlistId=youtube_playlist_id, part='snippet,contentDetails,status',maxResults=2).execute()
                most_video_date = ''
                self.bot.LLC.addlog(f'Истек срок проверки = {check_delay}ч канала "{youtube_channel_name}", ищем новые видео','youtube')
                for video in response_videos['items']:
                    video_published = datetime.datetime.strptime(video['snippet']['publishedAt'],'%Y-%m-%dT%H:%M:%SZ')
                    video_title = video['snippet']['title']
                    if video_published > youtube_last_video_date:
                        self.bot.LLC.addlog(f'Найдено новое видео Youtube: [{youtube_channel_name}] "{video_title}"','youtube')
                        if most_video_date == '': most_video_date = video_published
                        if most_video_date < video_published : most_video_date = video_published
                        video_url = 'https://www.youtube.com/watch?v='+video['contentDetails']['videoId']
                        msgtext = f'@here На канале **{youtube_channel_name}** новое видео\n**{video_title}**\n{video_url}'
                        await channel.send(content=msgtext)
                if most_video_date != '' : 
                    query = f"""
                        UPDATE 
                            youtube_videos 
                        SET 
                            youtube_last_video_date = '{most_video_date}',
                            check_date = NOW()
                        WHERE
                            id = {row_id}
                    """
                    self.bot.mysql.execute(query)
                else:
                    query = f"""
                        UPDATE 
                            youtube_videos 
                        SET 
                            check_date = NOW()
                        WHERE
                            id = {row_id}
                    """
                    self.bot.mysql.execute(query)
                    self.bot.LLC.addlog(f'На канале "{youtube_channel_name}" новые видео отсутствуют','youtube')
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @tasks.loop(seconds=10)
    async def clear_messages_by_tymer(self):
        try:
            for channel_id in self.bot.channels_clearbytimer:
                channel = self.bot.get_channel(channel_id)
                if channel != None:
                    msg_to_delete_cnt = 0
                    guild_name = self.bot.channels_clearbytimer[channel_id]['guild_name']
                    channel_name = self.bot.channels_clearbytimer[channel_id]['channel_name']
                    interval = self.bot.channels_clearbytimer[channel_id]['interval']
                    messages = await channel.history(limit=200,oldest_first=False).flatten()
                    for message in messages:
                        if message.pinned == False:
                            diff = (datetime.datetime.utcnow()-message.created_at)
                            diff_minutes = (diff.days * 24 * 60) + (diff.seconds/60)
                            if diff_minutes >= interval:
                                msg_to_delete_cnt = msg_to_delete_cnt + 1
                                await message.delete()
                    if msg_to_delete_cnt > 0:
                        self.bot.LLC.addlog(f'На сервере "{guild_name}" в канале "{channel_name}" по таймеру = "{str(interval)}" удалено {str(msg_to_delete_cnt)} сообщений')
                else:
                    self.bot.LLC.addlog(f'Не удалось открыть канал {str(channel_id)}','warning')
                    self.bot.channels_clearbytimer.pop(channel_id)
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @tasks.loop(seconds=5)
    async def draw_check(self):
        try:
            self.bot.LLC.addlog('start -> draw_check')
            for channel_id in self.bot.draws:
                channel = self.bot.get_channel(channel_id)
                if channel == None: continue
                if self.bot.draws[channel_id] == []: continue
                for draw in self.bot.draws[channel_id]:
                    if draw['draw_date'] < datetime.datetime.now():
                        await channel.send(content='@here дамы и господа, минуточку внимания!')
                        async with channel.typing():
                            await asyncio.sleep(3)
                        await channel.send(content='спасибо за внимание!')
                    continue
            self.bot.LLC.addlog('end -> draw_check')
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(loop_tasks(bot))