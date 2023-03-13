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
    # Проверка - является ли инициатор команды админом бота на сервере, где бы запущена команда
    async def isAdmin(self,ctx):
        try:
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, является ли пользователь админом сервера. Если является - больше ничего делать не нужно, если не является - будем смотреть дальше
            isAdmin = ctx.author.guild_permissions.administrator
            if isAdmin == True: return(True)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если админские роли заданы - проверяем, есть ли одна из этих ролей у пользователя, если есть - значит он админ, если нет - значит НЕ админ
            admin_roles = self.bot.roles[ctx.guild.id]['admin'] if ctx.guild.id in self.bot.roles else []
            if admin_roles != [] and admin_roles != ():
                for role in ctx.author.roles:
                    # Если найденная роль юзера является одной из ролью списка админов по данному серверу - значит инициатор команды админ
                    if str(role.id) in admin_roles:
                        isAdmin = True
                        return(isAdmin)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Роли на сервере заданы, но у пользователя их нет. Даём ему соответствующее оповещение и возвращаем False
            if isAdmin == False:
                self.LLC.addlog(f'Пользователь: "{ctx.author.name}" [id:{ctx.author.id}] не является админом сервера "{ctx.guild.name}"')
                msgtext  = 'У тебя нет прав для выполнения данной команды\n'
                msgtext += 'Данная команда доступна только для админов бота\n'
                msgtext += 'Админами бота являются пользователи с ролью:\n\n'
                for role_id in admin_roles:
                    role = ctx.guild.get_role(role_id)
                    if role != None:
                        if len(admin_roles) > 1:
                            msgtext += f'{str(1+admin_roles.index(role_id))}) {role.mention}\n'
                        else:
                            msgtext += f'{role.mention}\n'
                embed=discord.Embed(description='**Ошибка!**',color=color['red'])
                embed.add_field(name=f':x:', value=msgtext, inline=False)
                await ctx.send(embed=embed)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            return(isAdmin)
        except Exception as error:
            self.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # команда "adminrole": если переданы аргументы - устанавливает админские роли сервера, без аргументов - показывает текущие админские роли
    @commands.command()
    async def roleadmin(self,ctx,*args):
        try:
            command_name = 'roleadmin'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.isAdmin(ctx) == False: return
            admin_roles = self.bot.roles[guild.id]['admin'] if guild.id in self.bot.roles else []
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в БД отсутствует информация об админских ролях на этом сервере (возможно это новый сервер?)
            if args == () and admin_roles == []:
                msgtext  = f'Админские роли на данном сервере пока не установлены\nЭто означает, что любой может использовать админские команды\n'
                msgtext += f'Что бы установить роли введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<роли>***\n'
                msgtext += f'Роли указываются через @, можно указывать несколько ролей'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В БД есть инфа + в команде не заданы аргументы: сообщаем список текущих ролей данного сервера
            if args == ():
                msgtext = f'Cписок админских ролей **{guild.name}**:\n\n'
                for role_id in admin_roles:
                    role = ctx.guild.get_role(role_id)
                    if role != None:
                        if len(admin_roles) > 1:
                            msgtext += f'{str(1+admin_roles.index(role_id))}) {role.mention}\n'
                        else:
                            msgtext += f'{role.mention}\n'
                msgtext += f'\nЧто бы изменить роли введите команду в формате:\n**{self.bot.prefix}{command_name}** ***<одна, или несколько ролей>***\n'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В БД есть инфа + в команде заданы аргументы: изменяем админские роли на данном сервере
            if args != ():
                insert_values = ''
                roles = []
                # Собираем список новых админских ролей + подготавливаем строку для sql-запроса на инсерт новых данных о ролях в таблицу ролей
                for role_mention in args:
                    if len(role_mention) < 10 or role_mention[1] != '@':
                        msgtext = f'Роль "{role_mention}" указана в неправильном формате\nРоли указываются через @ (через "собаку")'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    role_id = int(role_mention[3:-1])
                    role = ctx.guild.get_role(role_id)
                    if role == None:
                        msgtext = f'Роль {role_mention} на сервере не найдена\nПроверь корректность указания роли'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    insert_values = insert_values + f",('{guild.id}','{guild.name}','{role.id}','{role.name}','{member.id}','{member.name}')"
                    roles.append(role_id)
                # Удаляем из таблицы информацию о старых ролях
                query = f"DELETE FROM roles_admin WHERE guild_id = '{guild.id}'"
                self.mysql.execute(query)
                # Записываем в таблицу информацию о новых ролях
                query =  "INSERT INTO roles_admin (guild_id,guild_name,role_id,role_name,author_id,author_name) VALUES " + insert_values[1:]
                self.mysql.execute(query)
                # Обновляем информацию о ролях на данном сервере в боте
                if guild.id not in self.bot.roles: self.bot.roles[guild.id]={}
                self.bot.roles[guild.id]['admin'] = roles
                msgtext = f'Админские роли **{guild.name}** успешно изменены!'
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
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # команда "welcomerole": если переданы аргументы - устанавливает приветственные роли сервера, без аргументов - показывает текущие приветственные роли
    @commands.command()
    async def rolewelcome(self,ctx,*args):
        try:
            command_name = 'rolewelcome'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.isAdmin(ctx) == False: return
            welcome_roles = self.bot.roles[guild.id]['welcome'] if guild.id in self.bot.roles else []
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в БД отсутствует информация об приветственных ролях на этом сервере (возможно это новый сервер?)
            if args == () and welcome_roles == []:
                msgtext  = f'Приветственные роли на данном сервере пока не установлены\n'
                msgtext += f'Что бы установить роли введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<роли>***\n'
                msgtext += f'Роли указываются через @, можно указывать несколько ролей'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В БД есть инфа + в команде не заданы аргументы: сообщаем список текущих приветственных ролей данного сервера
            if args == ():
                msgtext = f'Cписок приветственных ролей **{guild.name}**:\n\n'
                for role_id in welcome_roles:
                    role = ctx.guild.get_role(role_id)
                    if role != None:
                        if len(welcome_roles) > 1:
                            msgtext += f'{str(1+welcome_roles.index(role_id))}) {role.mention}\n'
                        else:
                            msgtext += f'{role.mention}\n'
                msgtext += f'\nЧто бы изменить роли введите команду в формате:\n**{self.bot.prefix}{command_name}** ***<одна, или несколько ролей>***\n'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # в команде заданы аргументы: изменяем админские роли на данном сервере
            if args != ():
                insert_values = ''
                roles = []
                # Собираем список новых ролей + подготавливаем строку для sql-запроса на инсерт новых данных о ролях в таблицу ролей
                for role_mention in args:
                    if len(role_mention) < 10 or role_mention[1] != '@':
                        msgtext = f'Роль "{role_mention}" указана в неправильном формате\nРоли указываются через @ (через "собаку")'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    role_id = int(role_mention[3:-1])
                    role = ctx.guild.get_role(role_id)
                    if role == None:
                        msgtext = f'Роль {role_mention} на сервере не найдена\nПроверь корректность указания роли'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    insert_values = insert_values + f",('{guild.id}','{guild.name}','{role.id}','{role.name}','{member.id}','{member.name}')"
                    roles.append(role_id)
                # Удаляем из таблицы информацию о старых ролях
                query = f"DELETE FROM roles_welcome WHERE guild_id = '{guild.id}'"
                self.mysql.execute(query)
                # Записываем в таблицу информацию о новых ролях
                query =  "INSERT INTO roles_welcome (guild_id,guild_name,role_id,role_name,author_id,author_name) VALUES " + insert_values[1:]
                self.mysql.execute(query)
                # Обновляем информацию о ролях на данном сервере в боте
                if guild.id not in self.bot.roles: self.bot.roles[guild.id]={}
                self.bot.roles[guild.id]['welcome'] = roles
                msgtext = f'Приветственные роли **{guild.name}** успешно изменены!'
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
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # команда "adminrole": если переданы аргументы - устанавливает админские роли сервера, без аргументов - показывает текущие админские роли
    @commands.command()
    async def roleamoderator(self,ctx,*args):
        try:
            command_name = 'roleamoderator'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.isAdmin(ctx) == False: return
            moderator_roles = self.bot.roles[guild.id]['admin'] if guild.id in self.bot.roles else []
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в БД отсутствует информация об админских ролях на этом сервере (возможно это новый сервер?)
            if args == () and moderator_roles == []:
                msgtext  = f'Модераторские роли на данном сервере пока не установлены\n'
                msgtext += f'Что бы установить роли введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<роли>***\n'
                msgtext += f'Роли указываются через @, можно указывать несколько ролей'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # В БД есть инфа + в команде не заданы аргументы: сообщаем список текущих ролей данного сервера
            if args == ():
                msgtext = f'Cписок модераторских ролей **{guild.name}**:\n\n'
                for role_id in moderator_roles:
                    role = ctx.guild.get_role(role_id)
                    if role != None:
                        if len(moderator_roles) > 1:
                            msgtext += f'{str(1+moderator_roles.index(role_id))}) {role.mention}\n'
                        else:
                            msgtext += f'{role.mention}\n'
                msgtext += f'\nЧто бы изменить роли введите команду в формате:\n**{self.bot.prefix}{command_name}** ***<одна, или несколько ролей>***\n'
                embed = discord.Embed(description = msgtext, color = color['gray'])
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # в команде заданы аргументы: изменяем админские роли на данном сервере
            if args != ():
                insert_values = ''
                roles = []
                # Собираем список новых ролей + подготавливаем строку для sql-запроса на инсерт новых данных о ролях в таблицу ролей
                for role_mention in args:
                    if len(role_mention) < 10 or role_mention[1] != '@':
                        msgtext = f'Роль "{role_mention}" указана в неправильном формате\nРоли указываются через @ (через "собаку")'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    role_id = int(role_mention[3:-1])
                    role = ctx.guild.get_role(role_id)
                    if role == None:
                        msgtext = f'Роль {role_mention} на сервере не найдена\nПроверь корректность указания роли'
                        embed = discord.Embed(description = msgtext, color = color['red'])
                        await ctx.send(embed=embed)
                        return
                    insert_values = insert_values + f",('{guild.id}','{guild.name}','{role.id}','{role.name}','{member.id}','{member.name}')"
                    roles.append(role_id)
                 # Удаляем из таблицы информацию о старых ролях
                query = f"DELETE FROM roles_moderator WHERE guild_id = '{guild.id}'"
                self.mysql.execute(query)
                # Записываем в таблицу информацию о новых ролях
                query = "INSERT INTO roles_moderator (guild_id,guild_name,role_id,role_name,author_id,author_name) VALUES " + insert_values[1:]
                self.mysql.execute(query)
                # Обновляем информацию о ролях на данном сервере в боте
                if guild.id not in self.bot.roles: self.bot.roles[guild.id]={}
                self.bot.roles[guild.id]['welcome'] = roles
                msgtext = f'Модераторские роли **{guild.name}** успешно изменены!'
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
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(admin(bot))