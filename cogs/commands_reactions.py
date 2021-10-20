from discord.ext import commands
from colors import color
import discord
from discord.utils import get
from discord import File
import inspect

# ==================================================================================================================================================================
class reactions(commands.Cog):
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
            admin_roles = self.bot.roles[ctx.guild.id]['admin']
            moderator_roles = self.bot.roles[ctx.guild.id]['moderator']
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
    async def addreactmessage(self,ctx,react_trigger=None,*,react_message=None):
        try:
            command_name = 'addreactmessage'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.IsAdminOrModerator(ctx) == False: return
            reactions = self.bot.reactions[guild.id]['message'] if guild.id in self.bot.reactions else []
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что в команду переданы оба аргумента, если нет - сообщаем пользователю об этом
            if react_trigger == None or (react_message == None and ctx.message.attachments == []):
                msgtext  = f'`Триггер реакции или текст реакции не указаны!`\n'
                msgtext += f'Что бы создать реакцию введите команду в формате:\n'
                msgtext += f'**{self.bot.prefix}{command_name}** ***<триггер> <текст сообщения>***\n'
                msgtext += f'Что бы пингануть отправителя сообщения используй %user% в тексте\n'
                msgtext += f'Для триггера на часть сообщения используй % в начале и в конце\n'
                msgtext += f'Прим.: триггер "%иск%" сработает на сообщение "д__иск__орд"\n'
                msgtext += f'Прим.: триггер "иск" (без %) сработает только на "иск"\n'
                msgtext += f'Сообщение может содержать смайлы, эмодзи, ссылки, пинги и так далее'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Получаем аттач сообщения, если он есть
            react_attach = ctx.message.attachments[0].url if ctx.message.attachments != [] else ''
            if react_message == None: react_message = ''
            react_trigger = react_trigger.lower()
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Для данного сервера рекций нет, т.к. это первая, просто добавляем её без задней мысли
            if reactions == []:
                rid = 1
                values = f"'{str(guild.id)}','{guild.name}',{str(rid)},'{react_trigger}','{react_message}','{react_attach}',{str(member.id)},'{member.name}'"
                query = f"INSERT INTO reactions_message(guild_id,guild_name,reaction_id,react_trigger,react_value,react_attach,author_id,author_name) VALUES ({values})"
                self.mysql.execute(query)
                self.bot.reactions[guild.id] = {}
                self.bot.reactions[guild.id]['message'] = []
                self.bot.reactions[guild.id]['message'].append({'id':rid,'trigger': react_trigger.lower(),'value': react_message,'attach':react_attach})
                if react_message != '' and react_attach != '': react_message = react_message + '\n'+ react_attach
                if react_message == '' and react_attach != '': react_message = react_attach
                embed=discord.Embed(description='**<:success:878625363540983848> Реакция добавлена!**',color=color['green'])
                embed.add_field(name=f'ID', value=f'#{str(rid)}', inline=False)
                embed.add_field(name=f'Триггер', value=react_trigger, inline=False)
                embed.add_field(name=f'Реакция', value=react_message, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog(f'[{guild.name}] добавлена новая реакция: {react_trigger=} {rid=}')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем - нет ли на данном сервере реакции с таким триггером? Если есть - обновляем и пишем пользователю соответствующее сообщение
            for reaction in reactions:
                # Ищем реакцию с таким тригером в списке реакций
                if reaction['trigger'].lower() == react_trigger.lower():
                    rid = reaction['id']
                    query = f"""
                        UPDATE reactions_message 
                        SET
                            react_value = '{react_message}',
                            react_attach = '{react_attach}',
                            author_id = {ctx.author.id},
                            author_name = '{ctx.author.name}',
                            date_add = now()
                        WHERE guild_id = {str(guild.id)} AND react_trigger = '{react_trigger}'"""
                    self.mysql.execute(query)
                    self.bot.reactions[guild.id]['message'].remove(reaction)
                    self.bot.reactions[guild.id]['message'].append({'id':rid,'trigger': react_trigger.lower(),'value': react_message,'attach':react_attach})
                    if react_message != '' and react_attach != '': react_message = react_message + '\n'+ react_attach
                    if react_message == '' and react_attach != '': react_message = react_attach
                    embed=discord.Embed(description='**<:success:878625363540983848> Реакция обновлена!**',color=color['green'])
                    embed.add_field(name=f'ID', value=f'#{str(rid)}', inline=False)
                    embed.add_field(name=f'Триггер', value=react_trigger, inline=False)
                    embed.add_field(name=f'Реакция', value=react_message, inline=False)
                    self.bot.LLC.addlog(f'[{guild.name}] реакция обновлена: {react_trigger=} {rid=}')
                    await ctx.send(embed=embed)
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Реакции с таким триггером на сервере нет. Это новая реакция. Значит добавляем её к списку реакций и в таблицу реакция + сообщение пользователю
            rid = self.mysql.execute(f"SELECT MAX(rm.reaction_id)+1 AS 'new_id' FROM reactions_message rm WHERE rm.guild_id = '{str(guild.id)}'")[0]['new_id']
            values = f"'{str(guild.id)}','{guild.name}',{str(rid)},'{react_trigger}','{react_message}',{str(member.id)},'{member.name}'"
            self.bot.reactions[guild.id]['message'].append({'id':rid,'trigger': react_trigger.lower(),'value': react_message,'attach':react_attach})
            if react_message != '' and react_attach != '': react_message = react_message + '\n'+ react_attach
            if react_message == '' and react_attach != '': react_message = react_attach
            embed=discord.Embed(description='**<:success:878625363540983848> Реакция добавлена!**',color=color['green'])
            embed.add_field(name=f'ID', value=f'#{str(rid)}', inline=False)
            embed.add_field(name=f'Триггер', value=react_trigger, inline=False)
            embed.add_field(name=f'Реакция', value=react_message, inline=False)
            await ctx.send(embed=embed)
            self.mysql.execute(f"INSERT INTO reactions_message(guild_id,guild_name,reaction_id,react_trigger,react_value,author_id,author_name) VALUES ({values})")
            self.bot.LLC.addlog(f'[{guild.name}] добавлена новая реакция: {react_trigger=} {rid=}')
            return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'`{str(error)}`\n'
            msgtext += f'Что-то пошло не так, не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
    @commands.command()
    async def listreactmessage(self,ctx):
        try:
            command_name = 'addreactmessage'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            reactions = self.bot.reactions[guild.id]['message'] if guild.id in self.bot.reactions else []
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если на сервере нет ни одной реакции - сообщаем об этом пользователю
            if reactions == []:
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
                msgtext = f'В данный момент на сервере нет ни одной текстовой реакции'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Список реакций не найден', value=msgtext, inline=False)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # На сервере есть реакции, выводим их список
            if reactions != []:
                str_id = ''
                str_tr = ''
                for reaction in reactions:
                    str_id += '#' + str(reaction['id']) + '\n'
                    str_tr += reaction['trigger'] + '\n'
                str_id = str_id[0:-1]
                str_tr = str_tr[0:-1]
                embed=discord.Embed(description='**<:success:878625363540983848> Список существующих реакций:**',color=color['green'])
                embed.add_field(name=f'ID', value=str_id, inline=True)
                embed.add_field(name=f'Триггер', value=str_tr, inline=True)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'`{str(error)}`\n'
            msgtext += f'Что-то пошло не так, не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.addlog(str(error),'error')
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(reactions(bot))