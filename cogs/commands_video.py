from googleapiclient.discovery import build
from discord.ext import commands
from colors import color
from twitchAPI.twitch import Twitch
import twitchAPI
import discord

# ==================================================================================================================================================================
class video(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    # Проверка - является ли пользователем админом или модератором на своём сервере
    async def IsAdminOrModerator(self,ctx):
        try:
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, является ли пользователь админом сервера. Если является - больше ничего делать не нужно, если не является - будем смотреть дальше
            IsAdminOrModerator = ctx.author.guild_permissions.administrator
            if IsAdminOrModerator == True: return(True)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если админские роли заданы - проверяем, есть ли одна из этих ролей у пользователя
            admin_roles = self.bot.roles[ctx.guild.id]['admin'] if ctx.guild.id in self.bot.roles else []
            moderator_roles = self.bot.roles[ctx.guild.id]['moderator'] if ctx.guild.id in self.bot.roles else []
            for role in ctx.author.roles:
                # Проверяем - есть ли у пользователя одна из админских ролей?
                if admin_roles != []:
                    if str(role.id) in admin_roles:
                        IsAdminOrModerator = True
                        return(IsAdminOrModerator)
                # Проверяем - есть ли у пользователя одна из модераторских
                if moderator_roles != []:
                    if str(role.id) in moderator_roles:
                        IsAdminOrModerator = True
                        return(IsAdminOrModerator)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Роли на сервере заданы, но у пользователя их нет. Даём ему соответствующее оповещение и возвращаем False
            if moderator_roles == False:
                self.LLC.addlog(f'Пользователь: "{ctx.author.name}" [id:{ctx.author.id}] не является админом сервера "{ctx.guild.name}"')
                msgtext  = 'У тебя нет прав для выполнения данной команды\n'
                msgtext += 'Данная команда доступна только для модераторов\n'
                msgtext += 'Модераторами являются пользователи с ролью:\n\n'
                for role_id in moderator_roles:
                    role = ctx.guild.get_role(int(role_id))
                    if role != None:
                        if len(moderator_roles) > 1:
                            msgtext += f'{str(1+moderator_roles.index(role_id))}) {role.mention}\n'
                        else:
                            msgtext += f'{role.mention}\n'
                embed = discord.Embed(description = msgtext, color = color['red'])
                await ctx.send(embed=embed)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            return(IsAdminOrModerator)
        except Exception as error:
            self.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    @commands.command()
    async def twitchcheckadd(self,ctx,channel_for_check = None,*,twich_user_name = None):
        try:
            command_name = 'twitchcheckadd'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            self.LLC.addlog(f'{self.bot.prefix}{command_name}" {channel_for_check=} {twich_user_name=}')
            if await self.IsAdminOrModerator(ctx) == False: return
            result = self.mysql.execute(f"SELECT message,channel_id FROM text_welcome WHERE guild_id='{guild.id}'")
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что в команду передано канал для оповещений И имя пользователя twitch
            if twich_user_name == None or channel_for_check == None:
                msgtext = ''
                if twich_user_name == None: msgtext += f'Имя стримера twitch не указано!\n'
                if channel_for_check == None: msgtext += f'Ссылка на канал для оповещений о стримах не указана!\n'
                msgtext += f'Что бы следить за каналом стримера twitch введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что канал передан корректно (в виде <#канал>)
            if channel_for_check[0:2] != '<#' and channel_for_check[-1] != '>':
                msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                msgtext += f'Что бы следить за каналом стримера twitch введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Получаем информацию о пользователе twitch по переданному в функцию "twich_user_name", если не получилось - сообщаем об ошибке
            twitch = Twitch(self.bot.twitch_creds['client'], self.bot.twitch_creds['secret'])
            twitch.authenticate_app([])
            try:
                user_info = twitch.get_users(logins=twich_user_name)
            except twitchAPI.types.TwitchAPIException as error:
                msgtext  = f'Пользователь twitch с ником "{twich_user_name}" не найден!\n'
                msgtext += f'Что бы следить за каналом стримера twitch введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # мы должны получить ответ в формате {'data': [<данные>]}, проверяем, что формат именно такой, если нет - сообщаем об ошибке
            if not 'data' in user_info:
                msgtext  = f'Некорректный ответ от api twitch!\n'
                msgtext += f'{user_info=}\n'
                msgtext += f'Если ошибка повторится - обратитесь к разработчику бота\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что указанный пользователь twitch найден, если он не найден (список user_info['data'] пуст) сообщаем об ошибке
            if user_info['data'] == []:
                msgtext  = f'Пользователь twitch с ником "{twich_user_name}" не найден!\n'
                msgtext += f'Что бы следить за каналом стримера twitch введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Инфа по пользователю есть - получаем его ID
            twitch_user_id = user_info['data'][0]['id']
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, есть ли такой пользователь с таким каналом на текущем сервере в базе данных
            channel = guild.get_channel(int(channel_for_check.replace('<#','').replace('>','')))
            result = self.bot.mysql.execute(f"""
                SELECT *
                FROM twitch_streamers
                WHERE 
                    guild_id = {guild.id}
                AND
                    channel_id = {channel.id}
                AND
                    twitch_user_id = {twitch_user_id}
                """)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если результат НЕ пустой - значит мы уже мониторим этого пользователя твич в заданном канале текущего сервера, сообщаем об ошибке
            if result != [] and result != ():
                msgtext  = f'Трансляции twitch "{twich_user_name}" уже отслеживаются в канале {channel_for_check}\n'
                msgtext += f'Что бы следить за каналом стримера twitch введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Результат пустой. Добавляем запись мониторинга трансляций в таблицу
            query = f"""
                INSERT INTO twitch_streamers
                    (guild_id,guild_name,channel_id,channel_name,twitch_user_id,twitch_user_name,twitch_user_status,twitch_user_date)
                VALUES
                    ({guild.id},'{guild.name}',{channel.id},'{channel.name}','{twitch_user_id}','{twich_user_name}','offline',NOW())
            """
            self.bot.mysql.execute(query)
            self.bot.LLC.addlog(f'Пользователь twitch "{twich_user_name}" добавлен для мониторинга на сервере "{guild.name}" в канале "{channel.name}"')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Сообщаем пользователю о том, что всё получилось
            embed=discord.Embed(color=color['green'])
            msgtext = f'-'*60
            embed.add_field(name=f':white_check_mark: Отслеживание стримов twitch добавлено!', value=msgtext, inline=False)
            embed.add_field(name=f':arrow_down: Имя пользователя twitch', value=f'{twich_user_name} [twitch_id:{twitch_user_id}]'+'\n'+'-'*60, inline=False)
            embed.add_field(name=f':arrow_down: Канал для отслеживания',  value=f'{channel.mention}'+'\n'+'-'*60, inline=False)
            msgtext =  f'Что бы следить за каналом twitch введите команду:\n'
            msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <имя_стримера>***\n'
            msgtext += f'Канал указывается как ссылка на канал (через #)\n'
            embed.add_field(name=':speech_left:  Справка',value=msgtext, inline=False)
            await ctx.send(embed=embed)
            return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    @commands.command()
    async def youtubecheckadd(self,ctx,channel_for_check = None,check_delay = None,youtube_channel_id = None):
        try:
            command_name = 'youtubecheckadd'
            msginfo  = f'\nЧто бы следить за каналом Youtube введите команду в формате:\n'
            msginfo += f'**{self.bot.prefix}{command_name}** ***<#канал> <периодичность> <ID_канала>***\n'
            msginfo += f'**<#канал>**: ссылка (через #) на discord-канал для отслеживания\n'
            msginfo += f'**<периодичность>**: периодичность (в часах) проверки новых видео, минимум: 1\n'
            msginfo += f'**<ID_канала>**: строка с ID канала Youtube\n'
            msginfo += f'ID канала можно получить из ссылки на канал Youtube:\n'
            msginfo += f'Пример: youtube.com/channel/**UCuP9elPARI_aLK4TOQrnfYQ**\n'
            msginfo += f'Канал указывается как ссылка на канал через # (через решетку)\n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            self.LLC.addlog(f'{self.bot.prefix}{command_name}" {channel_for_check=} {youtube_channel_id=}')
            if await self.IsAdminOrModerator(ctx) == False: return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если на задан ID канала Youtube или ссылка на канал для отслеживания - сообщаем об ошибке и выходим
            if channel_for_check == None or check_delay == None or youtube_channel_id == None:
                msgtext = ''
                self.bot.LLC.addlog('<#канал>, <периодичность> или <ID_канала> не заданы!')
                msgtext += f'<#канал> <периодичность> или <ID\_канала> не заданы!\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+msginfo, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что периодичность проверки задана корректно
            if check_delay.isdigit() == False or int(check_delay)<1 or int(check_delay)>168:
                msgtext = ''
                self.bot.LLC.addlog(f'Период проверки указан некоректно: check_delay = "{check_delay}"')
                if check_delay.isdigit() == False:  msgtext = f'Период проверки указан некоректно!\n'
                if int(check_delay)<1:   msgtext = f'Период проверки не может быть меньше одного часа!\n'
                if int(check_delay)>168: msgtext = f'Период проверки не может быть реже 1 раза в неделю!\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+msginfo, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что канал передан корректно (в виде <#канал>)
            if channel_for_check[0:2] != '<#' and channel_for_check[-1] != '>':
                msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+msginfo, inline=False)
                await ctx.send(embed=embed)
                return
            channel = guild.get_channel(int(channel_for_check.replace('<#','').replace('>','')))
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Пытаемся найти Youtube-канал по его ID и получить ID плейлиста добавленных видео из канала, делаем запрос к API Youtube
            youtube_api = build('youtube', 'v3', developerKey=self.bot.youtube_api_key)
            response_channels = youtube_api.channels().list(id=youtube_channel_id, part='snippet,contentDetails',maxResults=50).execute()
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в результате запроса ничего не нашлось - сообщаем пользователю об ошибке
            if response_channels['pageInfo']['totalResults'] == 0:
                self.bot.LLC.addlog(f'Канал Youtube c ID "{youtube_channel_id}" не найден')
                msgtext = f'Канал Youtube с указанным ID не найден!\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+msginfo, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, может быть отслеживание этого канала Youtube на этом сервере уже есть? Тогда сообщим об ошибке и выйдем из функции
            youtube_channel_name = response_channels['items'][0]['snippet']['title']
            youtube_channel_url = 'https://www.youtube.com/channel/'+youtube_channel_id
            youtube_playlist_id = response_channels['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            query = f"""
                SELECT *
                FROM youtube_videos
                WHERE
                    youtube_channel_id = '{youtube_channel_id}'
                    AND
                    guild_id = {guild.id}
            """
            result = self.bot.mysql.execute(query)
            # Если результат НЕ пустой - значит такая запись уже есть
            if result != [] and result != ():
                self.bot.LLC.addlog(f'Канал Youtube "**{youtube_channel_name}**" уже отслеживается в {channel.mention}')
                msgtext  = f'Видео на канале уже отслеживаются на данном сервере!\n'
                msgtext += f'Имя канала Youtube: "**{youtube_channel_name}**"\n'
                msgtext += f'Канал отслеживания: {channel.mention}\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+msginfo, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Отслеживание данного канала Youtube на данном сервере Discord отсутствует, добавляем новую запись в таблицу для отслеживания
            #response_playlistItems = youtube_api.playlistItems().list(playlistId=channel_uploads_playlist_id, part='snippet,contentDetails',maxResults=50).execute()
            query = f"""
                INSERT INTO 
                    youtube_videos
                        (
                            check_delay,
                            guild_id,
                            guild_name,
                            channel_id,
                            channel_name,
                            youtube_channel_name,
                            youtube_channel_url,
                            youtube_channel_id,
                            youtube_playlist_id,
                            author_id,
                            author_name
                        )
                VALUES 
                        (
                            {int(check_delay)},
                            {guild.id},
                            '{guild.name}',
                            {channel.id},
                            '{channel.name}',
                            '{youtube_channel_name}',
                            '{youtube_channel_url}',
                            '{youtube_channel_id}',
                            '{youtube_playlist_id}',
                            {ctx.author.id},
                            '{ctx.author.name}'
                        )
            """
            self.bot.mysql.execute(query)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Сообщаем об успехе
            embed=discord.Embed(color=color['green'])
            msgtext = f'-'*60
            embed.add_field(name=f':white_check_mark: Отслеживание новых видео Youtube добавлено!', value=msgtext, inline=False)
            embed.add_field(name=f':arrow_down: Имя канала Youtube', value=f'__{youtube_channel_name}__ \nid: {youtube_channel_id}'+'\n'+'-'*60, inline=False)
            embed.add_field(name=f':arrow_down: Канал для отслеживания',  value=f'{channel.mention}'+'\n'+'-'*60, inline=False)
            embed.add_field(name=':speech_left: Справка',value=msginfo, inline=False)
            await ctx.send(embed=embed)
            return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext+msginfo, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
            return
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(video(bot))