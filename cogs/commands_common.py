from discord.ext import commands
from colors import color
import discord
import random
# ==================================================================================================================================================================
class common(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    # Бросок кубиков с 6 гранями, по-умолчанию бросаем 2d6, но можно задать конкретное кол-во кубиков и граней
    @commands.command(aliases = ['ролл'])
    async def diceroll(self,ctx,roll=None):
        try:
            command_name = 'addreactmessage'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            # -----------------------------------------------------------------------------------------------------------------------------------------------------
            # в словарь "d" собираем все доступные эмодзи-кости, для наглядности без цикла, у нас будет кубик с 6 гранями
            d = {
                1: self.bot.emoji['dice1'],
                2: self.bot.emoji['dice2'],
                3: self.bot.emoji['dice3'],
                4: self.bot.emoji['dice4'],
                5: self.bot.emoji['dice5'],
                6: self.bot.emoji['dice6']}     
            # -----------------------------------------------------------------------------------------------------------------------------------------------------
            # Инициатор команды не задал количество костей и макс кол-во граней, поэтому кидаем 2d6
            if roll == None:
                r1 = random.randint(1,6)
                r2 = random.randint(1,6)
                summ = r1+r2
                roll_text = d[r1] + ' + ' + d[r2] + ' = ' + str(summ)
                embed=discord.Embed(title='Бросаем 2d6',color=color['green'])
                embed.add_field(name=f'Результат:', value=f'{roll_text}', inline=False)
                await ctx.send(embed=embed,content=f'---> {ctx.author.display_name}')
                return
            # -----------------------------------------------------------------------------------------------------------------------------------------------------
            # Если задано определенное кол-во костей или ограничения по граням - проверяем, что всё задано корректно
            if roll != None:
                # параметр "ролл" должен быть из 3х символов, второй должен быть "d", первый - цифра от 1 до 6, третий - цифра от 2 до 6
                if (
                    len(roll)!=3 or                 # Проверяем, что аргумент состоит из 3х символов
                    roll.lower()[1] != 'd' or       # Второй символ должен быть = "d"
                    roll[0].isdigit() == False or   # Первый должен быть числом
                    roll[2].isdigit() == False or   # Третий тоже должен быть числом
                    int(roll[0])<1 or               # Первый не должен быть меньше 1
                    int(roll[0])>6 or               # Но не должен быть больше 6
                    int(roll[2])<2 or               # Третий тоже не должен быть меньше 2
                    int(roll[2])>6                  # И тоже не должен быть больше 6
                ):
                    # Если одно из условий не соблюдено - пишем ошибку и выходим из функции
                    msgtext = f'Так-так, кажется ты что-то напутал ಠ_ಠ\n'
                    msgtext += f'У меня есть только 6 кубиков с 6 гранями на каждом\n'
                    msgtext += f'Кубика с __одной__ гранью у меня нет, даже не проси!\n'
                    msgtext += f'Что бы бросить 1 кубик с 6 гранями укажи "1d6" в команде\n'
                    msgtext += f'Что бы бросить 5 кубиков с 3 гранями укажи "5d3" в команде\n'
                    msgtext += f'Можешь ничего не указывать, тогда я брошу стандартные 2d6\n'
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                    await ctx.send(embed=embed)
                    return
                else:
                    dices = int(roll[0])
                    faces = int(roll[2])
                    roll_text = ''
                    roll_summ = 0
                    for i in range(dices):
                        roll_result = random.randint(1,faces)
                        roll_text += d[roll_result] + ' + '
                        roll_summ += roll_result
                    roll_text = roll_text[0:-2] + ' = ' + str(roll_summ)
                    embed=discord.Embed(title=f'Бросаем {str(dices)}d{str(faces)}',color=color['green'])
                    embed.add_field(name=f'Результат:', value=f'{roll_text}', inline=False)
                    await ctx.send(embed=embed,content=f'---> {ctx.author.display_name}')
            # -----------------------------------------------------------------------------------------------------------------------------------------------------      
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
    bot.add_cog(common(bot))