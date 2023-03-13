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
                embed=discord.Embed(title="Справка", description="Список доступных команд:", color=color['green'])
                commands_by_category = {}
                # Собираем словарь "commands_by_category", где ключем будет поле "name" таблицы "commands_types", а значением имя команды из таблицы "commands"
                for command_row in self.bot.commands_list:
                    command_name = command_row['command_name']
                    command_type = command_row['command_type']
                    command_category_name = ''
                    for command_type_row in self.bot.commands_type:
                        type_name = command_type_row['type']
                        if command_type == type_name:
                            command_category_name = command_type_row['name']
                            break
                    if command_category_name == '':
                        command_category_name == ':interrobang: Без категории'
                    if command_category_name not in commands_by_category:
                        commands_by_category[command_category_name] = []
                    commands_by_category[command_category_name].append(command_name)
                # Словарь собран, формируем сообщение
                for command_category in commands_by_category:
                    commands_list = commands_by_category[command_category]
                    field_value = ''
                    for command_name in commands_list:
                        field_value += command_name + '\n'
                    embed.add_field(name=f'{command_category}',value=field_value,inline=True)
                # Текст сообщения сформирован, добавляем подпись, гифку и отправляем
                embed.set_footer(text=f'Для подробной справки введи {self.bot.prefix}help <имя_команды>')
                embed.set_thumbnail(url=ctx.guild.icon_url)
                await ctx.send(embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Это вызов справки по конкретной команде, ищем команду в списке команд, выводим по ней подробную справку, выходим из функции
            if command_for_more_help != None:
                self.bot.LLC.addlog(f'Запрошена дополнительная справка по команде "{command_for_more_help}"')
                command_for_more_help = command_for_more_help.lower()
                for command_row in self.bot.commands_list:
                    command_name = command_row['command_name']
                    if command_name == command_for_more_help:
                        command_help = '\n'+command_row['command_help']
                        command_help = command_help.replace('<prefix>',self.bot.prefix)
                        embed=discord.Embed(color=color['green'])
                        embed.add_field(name=f':page_facing_up: Информация по команде "**{command_name}**"',value=command_help,inline=True)
                        embed.set_footer(text=f'Для получения справки введи {self.bot.prefix}help')
                        await ctx.send(embed=embed)
                        return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если дошли сюда, значит была запрошена доп. справка по команде, но в списке команд указанной команды нет, сообщим об ошибке
            self.bot.LLC.addlog(f'Команда "**{command_for_more_help}**" не найдена!')
            msgtext  = f'Команда "**{command_for_more_help}**" не найдена!`\n'
            msgtext += f'Проверьте корректность указания команды'
            embed=discord.Embed(color=color['red'])
            embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext = f'Что-то пошло не так, я не могу выполнить команду\n'
            msgtext += f'Проверь корректность указания названий ролей'
            embed = discord.Embed(description = msgtext, color = color['red'])
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(help(bot))