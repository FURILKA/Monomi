from discord.ext import commands
from colors import color
import discord

# ==================================================================================================================================================================
class admin(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    # Загрузка информации об ролях из mySQL БД бота по 'guild_id', role_type = тип загружаемых ролей (в данном случае 'admin' или 'moderator')
    def GetRolesByGuildID(self,guild_id,role_type):
        # Загружаем из базы (таблица "roles_admin") список админских ролей по всем серверам
        try:
            self.LLC.addlog(f'Загружаем список ролей "{role_type}"')
            self.mysql.connect()
            result = self.mysql.execute(f"SELECT role_id FROM roles_{role_type} WHERE guild_id = '{str(guild_id)}'")
            if result == [] or result == ():
                self.LLC.addlog(f'Таблица "roles_{role_type}" пуста, роли не найдены')
                roles = []
            else:
                roles = [row['role_id'] for row in result]
            self.mysql.disconnect()
            return(roles)
        except Exception as error:
            self.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    # Проверка - является ли пользователем админом или модератором на своём сервере
    async def IsAdminOrModerator(self,ctx):
        try:
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # По-умолчанию считаем, что инициатор команды не админ и не модератор, а дальше посмотрим
            IsAdminOrModerator = False
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если на сервере не заданы ни админские, ни модераторские роли - значит пользователь И админ И модератор :)
            admin_roles = self.GetRolesByGuildID(ctx.guild.id,'admin')
            moderator_roles = self.GetRolesByGuildID(ctx.guild.id,'moderator')
            if admin_roles == [] and moderator_roles == []:
                IsAdminOrModerator = True
                return(IsAdminOrModerator)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если админские роли заданы - проверяем, есть ли одна из этих ролей у пользователя
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
            self.mysql.connect()
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
                    self.mysql.disconnect()
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
                self.mysql.disconnect()
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
                self.mysql.disconnect()
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
                self.mysql.disconnect()
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
                self.mysql.disconnect()
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext = f'Что-то пошло не так, я не могу выполнить команду\n'
            msgtext += f'Проверь корректность указания названий ролей'
            embed = discord.Embed(description = msgtext, color = color['red'])
            await ctx.send(embed=embed)
            self.bot.LLC.addlog(str(error),'error')
            self.mysql.disconnect()
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(admin(bot))