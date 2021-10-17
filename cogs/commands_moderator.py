from discord.ext import commands
from colors import color
from twitchAPI.twitch import Twitch
import twitchAPI
import discord
import requests

# ==================================================================================================================================================================
class admin(commands.Cog):
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
            self.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @commands.command()
    async def textwelcome(self,ctx,channel_welcome=None,*,new_text_welcome=None):
        try:
            command_name = 'textwelcome'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.IsAdminOrModerator(ctx) == False: return
            result = self.mysql.execute(f"SELECT message,channel_id FROM text_welcome WHERE guild_id='{guild.id}'")
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в команду передан канал - проверяем, что канал 1) указан в нормальном формате (через #) 2) канал существует на сервере
            if channel_welcome != None:
                if channel_welcome[0:2] != '<#' and channel_welcome[-1] != '>':
                    msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                    msgtext += f'Что бы установить сообщение введите команду в формате:\n'
                    msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <текст сообщения>***\n'
                    msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                    msgtext += f'Сообщение может содержать смайлы, эмодзи, ссылки, пинги и так далее'
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                    await ctx.send(embed=embed)
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В команде указан только 1 параметр из 2 (должно быть либо 0 либо 2)
            if (new_text_welcome == None and channel_welcome != None) or (new_text_welcome != None and channel_welcome == None):
                msgtext  = f'Не указан канал __или__ текст сообщения, нужно указать __оба__ параметра\n'
                msgtext += f'Что бы установить сообщение введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <текст сообщения>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                msgtext += f'Сообщение может содержать смайлы, эмодзи, ссылки, пинги и так далее'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Параметры не указаны и в базе пусто, приветственное сообщение пока не задано
            if new_text_welcome == None and channel_welcome == None and (result == [] or result == ()):
                msgtext  = f'В настоящий момент приветственное сообщение не установлено\n'
                msgtext += f'Что бы установить сообщение введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <текст сообщения>***\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                msgtext += f'Сообщение может содержать смайлы, эмодзи, ссылки, пинги и так далее'
                embed=discord.Embed(color=color['blue'])
                embed.add_field(name=f':page_facing_up:  Информация', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Параметры не указаны, а в базе есть инфа о приветственном сообщении - показываем инфу о нём
            if new_text_welcome == None and channel_welcome == None and result != [] and result != ():
                old_text_welcome = result[0]['message']
                old_channel_id = int(result[0]['channel_id'])
                channel = guild.get_channel(old_channel_id)
                embed=discord.Embed(color=color['blue'])
                msgtext = f'Текущее приветственное сообщение **{guild.name}**:'+'\n'+'-'*60
                embed.add_field(name=f':page_facing_up:   Информация', value=msgtext, inline=False)
                embed.add_field(name=f':arrow_down:  Канал, на котором появится сообщение', value=guild.get_channel(old_channel_id).mention+'\n'+'-'*60, inline=False)
                embed.add_field(name=f':arrow_down:  Текст приветственного сообщения', value='<@пинг_новичка> '+old_text_welcome+'\n'+'-'*60, inline=False)
                msgtext  = f'Что бы изменить сообщение введите команду:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<#канал> <текст сообщения>***\n'
                msgtext += f'Канал указывается как ссылка на канал через #\n'
                msgtext += f'Сообщение может иметь эмодзи, ссылки/пинги'
                embed.add_field(name=':speech_left:  Справка',value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Оба параметра заданы - меняем информацию о приветственном сообщении в базе данных
            if new_text_welcome != None and channel_welcome != None:
                channel_id = int(channel_welcome.replace('<#','').replace('>',''))
                channel = guild.get_channel(channel_id)
                values = f"'{str(guild.id)}','{guild.name}','{channel.id}','{channel.name}','{new_text_welcome}','{str(member.id)}','{member.name}'"
                self.mysql.execute(f"DELETE FROM text_welcome WHERE guild_id = '{guild.id}'")
                self.mysql.execute(f"INSERT INTO text_welcome(guild_id,guild_name,channel_id,channel_name,message,author_id,author_name) VALUES ({values})")
                msgtext = f'Приветственное сообщение успешно изменено!'
                embed = discord.Embed(description = msgtext, color = color['green'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            msgtext += f'Проверь корректность указания названий ролей'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.addlog(str(error),'error')
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
                    ({guild.id},'{guild.name}',{channel.id},'{channel.name}','{twitch_user_id}',{twich_user_name},'offline',NOW())
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
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(admin(bot))