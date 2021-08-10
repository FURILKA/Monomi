from discord.ext import commands
from discord.ext.commands.core import command
from colors import color
import discord
# ==================================================================================================================================================================
class help(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    @commands.command()
    async def help(self,ctx,command_for_more_help=None):
        try:
            command_name = 'help'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Это простой (общий) вызов справки, без указания конкретной команды
            if command_for_more_help == None:
                self.mysql.connect()
                commands = {'user':[],'moderator':[],'admin':[],'owner':[]}
                embed=discord.Embed(title="Справка", description="Список доступных команд", color=color['green'])
                commands_result = self.mysql.execute('SELECT * FROM commands')
                for row in commands_result:
                    command_type = row['command_type']
                    if command_type not in commands:
                        commands[command_type]=[]
                    commands[command_type].append(row['command_name'])
                for command_type in commands:
                    if command_type == 'admin':
                        emoji = ':red_circle:'
                        type_name = 'Команды админа'
                    elif command_type == 'moderator':
                        emoji = ':green_circle:'
                        type_name = 'Команды модератора'
                    elif command_type == 'user':
                        emoji = ':white_circle:'
                        type_name = 'Команды для всех'
                    elif command_type == 'owner':
                        emoji = ':orange_circle:'
                        type_name = 'Команды владельца'
                    i = 1
                    field_value = ''
                    for command_name in commands[command_type]:
                        field_value += str(i)+ ') __[' + command_name + '](https://countrycode.org/)__' + '\n'
                        i+=1
                    field_value = field_value[0:-1]
                    embed.add_field(name=f'{emoji} {type_name}', value=field_value, inline=False)
                embed.set_footer(text=f'Для подробной справки введи {self.bot.prefix}help <имя_команды>')
                embed.set_thumbnail(url="https://emoji.discord.st/emojis/65033a38-b3bd-4aa5-8783-63fcfc07171d.gif")
                await ctx.send(embed=embed)
                self.mysql.disconnect()
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Это вызов справки по конкретной команде
            if command_for_more_help != None:
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
    bot.add_cog(help(bot))