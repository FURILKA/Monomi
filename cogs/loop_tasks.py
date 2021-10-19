from asyncio.tasks import sleep
from discord.ext import commands
from discord.ext import tasks
from twitchAPI.twitch import Twitch
from colors import color
from googleapiclient.discovery import build
import requests
import discord
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
    # **************************************************************************************************************************************************************
    # Получение информации об начале трансляции стримов
    @tasks.loop(seconds=60)
    async def twich_check_streamers_online(self):
        try:
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
                    self.bot.LLC.addlog(f'Стрим пользователя "{user_name}" [id:{user_id}] закончился')
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
                if stream_info['data'][0]['type'] ==  'live' and row['twitch_user_status'] == 'offline':
                    user_name = stream_info['data'][0]['user_name']
                    thumbnail_url = stream_info['data'][0]['thumbnail_url']
                    thumbnail_url = thumbnail_url.replace('{width}','500').replace('{height}','300')
                    self.bot.LLC.addlog(f'Стрим пользователя "{user_name}" [id:{user_id}] онлайн!')
                    query = f"UPDATE twitch_streamers SET twitch_user_status = 'online', twitch_user_date = NOW() WHERE id = {row_id}"
                    self.bot.mysql.execute(query)
                    channel = self.bot.get_channel(channel_id)
                    embed=discord.Embed(
                        title=user_info['display_name'],
                        description="Стрим онлайн!",
                        color=color['green'],
                        url=f'https://www.twitch.tv/{user_name}'
                        )
                    embed.add_field(
                        name='Игра',
                        value=stream_info['data'][0]['game_name'],
                        inline=False)
                    embed.set_thumbnail(url=user_info['profile_image_url'])
                    embed.set_image(url=thumbnail_url)
                    msgtext = f'@here\nКто-то внезапно начал трансляцию на твиче!\n⭐ https://www.twitch.tv/{user_name} ⭐\nПрисоеденяйтесь, не пропустите!'
                    await channel.send(embed=embed,content=msgtext)
                    continue
                # -------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @tasks.loop(seconds=10)
    async def youtube_check_new_videos(self):
        try:
            result = self.bot.mysql.execute("SELECT * FROM youtube_videos")
            if result == [] or result == (): return
            youtube_api = build('youtube', 'v3', developerKey=self.bot.youtube_api_key)
            for row in result:
                row_id = row['id']
                youtube_channel_name = row['youtube_channel_name']
                youtube_playlist_id = row['youtube_playlist_id']
                youtube_last_video_date = row['youtube_last_video_date']
                response_videos = youtube_api.playlistItems().list(playlistId=youtube_playlist_id, part='snippet,contentDetails,status',maxResults=2).execute()
                channel = self.bot.get_channel(row['channel_id'])
                most_video_date = ''
                if channel == None: continue
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
                if most_video_date != '' : self.bot.mysql.execute(f"UPDATE youtube_videos SET youtube_last_video_date = '{most_video_date}' WHERE id = {row_id}")
        except Exception as error:
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(loop_tasks(bot))