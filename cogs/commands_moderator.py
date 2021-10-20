import asyncio
from discord.ext import commands
from colors import color
from twitchAPI.twitch import Twitch
import twitchAPI
import discord
import requests

# ==================================================================================================================================================================
class moderator(commands.Cog):
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
    # Удаление <N> последних сообщений в #Канале (опционально: только сообщения <пользователя>)
    @commands.command()
    async def clear(self,ctx,msg_count=None,user=None):
        try:
            command_name = 'clear'
            command_info  = f'\nЧто бы удалить сообщения введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<N> [пользователь]***\n'
            command_info += f'**<N>**: количество последних сообщений в канале (от 1 до 100)\n'
            command_info += f'**[пользователь]**: чьи сообщения будут удалены (опционально)\n'
            command_info += f'Пользователь указывается как ID (прим.: FURILKA#5953) или пинг \n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            self.LLC.addlog(f'{self.bot.prefix}{command_name}" {msg_count=} {user=}')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # msg_count должно быть числом от 1 до 100 включительно, если передано что-то не так (или ничего не передано) сообщаем об ошибке
            if msg_count == None or msg_count.isdigit()==False or int(msg_count)<1 or int(msg_count)>100:
                msgtext = f'Количество сообщений для удаления указано некорректно!\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Количество сообщений для удаления указано некорректно!')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В команде задано кол-во сообщений для удаления и НЕ задан пользователь, чьи сообщения удалять: удаляем последние N сообщений в канале
            if msg_count != None and user == None:
                await ctx.message.delete()
                await ctx.channel.purge(limit=int(msg_count))
                embed=discord.Embed(color=color['green'],description=':broom: Сообщения удалены!')
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(2)
                await msg.delete()
                self.LLC.addlog(f'В канале "{ctx.channel.name}" [{guild.name}] удалено {msg_count} последних сообщений')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В команде задано И кол-во сообщений И пользователь, по которому сообщения нужно почистить
            if msg_count != None and user != None:
                member = guild.get_member_named(user)
                # Такого пользователя на сервере нет, возможно его задали не как имя пользователя, а как пинг? попробуем получить объект пользователя из пинга
                if member == None:
                    if user[0:2] == '<@' and user[-1] == '>':
                        user_id = int(user.replace('<@','').replace('>',''))
                        member = guild.get_member(user_id)
                if member == None:
                    # Такого пользователя на сервере нет, сообщаем об ошибке и выходим
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=f'Пользователь "{user}" не найден!', inline=False)
                    msg = await ctx.send(embed=embed)
                    self.LLC.addlog(f'Пользователь "{user}" не найден!')
                    await asyncio.sleep(2)
                    await msg.delete()
                    return
                else:
                    messages = await ctx.channel.history(limit=200,oldest_first=False).flatten()
                    deleted_count = 0
                    for msg in messages:
                        if msg.author == member:
                            deleted_count += 1
                            await msg.delete()
                            if deleted_count == int(msg_count): break
                    if deleted_count == 0:
                        # Если ничего не удалили - сообщим об ошибке
                        embed=discord.Embed(color=color['red'])
                        embed.add_field(
                            name=f':x: Ошибка',
                            value=f'Сообщения пользователя {member.name} в каналей не найдены!',
                            inline=False)
                        self.LLC.addlog(f'Сообщения пользователя {member.name} в каналей не найдены!')
                    else:
                        # Если сообщения удалось найти и удалить - сообщим о результатах
                        embed=discord.Embed(color=color['green'])
                        embed.add_field(
                            name=self.bot.emoji['success']+' Успех',
                            value=f'Удалено **{deleted_count}** сообщений пользователя "{member.name}" в текущем канале',
                            inline=False)
                        self.LLC.addlog(f'Удалено {deleted_count} сообщений пользователя "{member.name}" в текущем канале')
                    # Отправляем сообщение, ждём пару секунд, удаляем отправленное сообщение и выходим
                    msg = await ctx.send(embed=embed)
                    await asyncio.sleep(4)
                    await msg.delete()
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            if await self.IsAdminOrModerator(ctx) == False: return
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
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(moderator(bot))