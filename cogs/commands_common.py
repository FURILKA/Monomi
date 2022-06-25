from discord.ext import commands
from colors import color
import discord
import random
import datetime
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
    # **************************************************************************************************************************************************************
    # Показывает список розыгрышей на текущем сервере
    @commands.command()
    async def listdraw(self,ctx):
        try:
            command_name = 'listdraw'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Ищем розыгрышы на текущем сервере
            current_draws = []
            for channel_id in self.bot.draws:
                for draw in self.bot.draws[channel_id]:
                    if draw['guild_id']==ctx.guild.id:
                        current_draws.append(draw)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если ничего не нашлось - сообщаем об этом и выходим
            if current_draws == []:
                emoji_name = self.bot.emoji['sadclownpepe']
                emoji_id =''.join(i for i in emoji_name if i.isdigit())
                emoji_obj = self.bot.get_emoji(int(emoji_id))
                embed=discord.Embed(title='Грустно признавать, но...',color=color['gray'])
                embed_value = f'Ничего не нашлось\n'
                embed_value += f'В данный момент розыгрыши не проводятся\n'
                embed.add_field(name='Никакого праздника!',value=embed_value,inline=False)
                embed.set_thumbnail(url=str(emoji_obj.url))
                await ctx.send(content=ctx.author.mention,embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Что-то все же нашлось, сообщим об этом
            emoji_name = self.bot.emoji['CasinoChips']
            emoji_id =''.join(i for i in emoji_name if i.isdigit())
            emoji_obj = self.bot.get_emoji(int(emoji_id))
            embed=discord.Embed(title='Активные розыгрыши',color=color['green'])
            for draw in current_draws:
                # Получаем информацию о призах розыгрыша
                draw_id = draw['draw_id']
                author = draw['author_name']
                draw_date = datetime.datetime.strftime(draw['draw_date'],'%d.%m.%Y %H:%M')
                draw_players_count = draw['draw_players_count']
                result = self.bot.mysql.execute(f"SELECT * FROM draw_prizes WHERE draw_id = {str(draw_id)}")
                embed_value = ''
                players_count_now = len(self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)} AND is_active = 1"))
                if result == [] or result == ():
                    embed_value = f'ID розыгрыша: **#{str(draw_id)}**\n'
                    embed_value += f'Организатор: **{author}**\n'
                    if draw_players_count == 0:
                        embed_value += f'Количество участников: **Не ограничено**\n'
                    else:
                        embed_value += f'Количество участников: **{str(players_count_now)}\\{str(draw_players_count)}**\n'
                    embed_value += f'Объявление результатов: **{draw_date}**\n'
                    embed_value += f'Очень странно: розыгрыш есть, а призов нет'
                else:
                    if len(result) == 1:
                        prize_name = result[0]['prize_name']
                        embed_value = f'ID розыгрыша: **#{str(draw_id)}**\n'
                        embed_value += f'Организатор: **{author}**\n'
                        if draw_players_count == 0:
                            embed_value += f'Количество участников: **Не ограничено**\n'
                        else:
                            embed_value += f'Количество участников: **{str(players_count_now)}\\{str(draw_players_count)}**\n' 
                        embed_value += f'Объявление результатов: **{draw_date}**\n'
                        embed_value += f'Приз: **{prize_name}**\n'
                    else:
                        i = 1
                        embed_value  = f'ID розыгрыша: **#{str(draw_id)}**\n'
                        embed_value += f'Организатор: **{author}**\n'
                        if draw_players_count == 0:
                            embed_value += f'Количество участников: **Не ограничено**\n'
                        else:
                            embed_value += f'Количество участников: **{str(players_count_now)}\\{str(draw_players_count)}**\n'
                        embed_value += f'Объявление результатов: **{draw_date}**\n'
                        for row in result:
                            prize_name = row['prize_name']
                            embed_value += f'Приз №{str(i)}: **{prize_name}**\n'
                            i += 1
                embed.add_field(name=draw['draw_name'],value=embed_value,inline=False)
            embed.set_thumbnail(url=str(emoji_obj.url))
            embed.set_footer(text=f'Что бы принять участие используй команду: {self.bot.prefix}joindraw <#id>')
            await ctx.send(content=ctx.author.mention,embed=embed)
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
    # Принять участие в розыгрыше
    @commands.command()
    async def joindraw(self,ctx, draw_id=None):
        try:
            command_name = 'joindraw'
            command_info  = f'\nЧто бы принять участие в розыгрыше введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#ID розыгрыша>***\n'
            command_info += f'**<#ID розыгрыша>**: номер (ID), в котором вы хотите принять участие\n'
            command_info += f'Получение списка активных розыгрышей: **{self.bot.prefix}listdraw**\n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверим, что draw_id передан в команду
            if draw_id == None:
                msgtext  = f'Не указан ID розыгрыша, в котором вы хотите принять участие\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Не указан ID розыгрыша, в котором вы хотите принять участие')
                return
            draw_id = draw_id.replace('#','')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверим, что переданный ID это число
            if draw_id.isdigit()==False:
                msgtext  = f'Указан некорректный ID розыгрыша\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Указан некорректный ID розыгрыша')
                return
            draw_id = int(draw_id)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # ID передан корректно, поищем такой розыгрыш в списке доступных розыгрышей
            found_draw = None
            for channel_id in self.bot.draws:
                for draw in self.bot.draws[channel_id]:
                    if draw_id==draw['draw_id'] and ctx.guild.id == draw['guild_id']:
                        found_draw = draw.copy()
                        break
                if found_draw != None: break
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если мы не нашли розыгрыш с таким ID сообщим об этом пользователю
            if found_draw == None:
                msgtext  = f'Розыгрыш с указанным ID не найден\n'
                msgtext += f'Проверьте ID розыгрыша и повторите попытку\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Розыгрыш с указанным ID не найден')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверим - может быть пользователь УЖЕ является участником этого розыгрыша?
            draw_id = found_draw['draw_id']
            draw_name = found_draw['draw_name']
            sql_result = self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)} AND player_id = {str(member.id)} AND is_active = 1")
            if sql_result != () and sql_result != []:
                msgtext  = f'{ctx.author.mention} ты **уже** являешься участником данного розыгрыша\n'
                msgtext += f'Может быть ты хотел учавствовать в другом розыгрыше?\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Пользователь уже является участником розыгрыша')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверим - не достигнут ли предел количества участников розыгрыша?
            if found_draw['draw_players_count']>0:
                sql_result = self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)} AND is_active = 1")
                if len(sql_result)>=found_draw['draw_players_count']:
                    draw_players_count = found_draw['draw_players_count']
                    msgtext  = f'{ctx.author.mention} увы, но в розыгрыше уже принимает максимальное количество участников\n'
                    msgtext += f'Всего организатором заявлено не более {str(draw_players_count)} участников\n'
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=msgtext, inline=False)
                    await ctx.send(embed=embed)
                    self.bot.LLC.addlog('Достигнуто максимальное количество участников')
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            self.bot.mysql.execute(f"""
                INSERT INTO draw_players
                (
                    player_id,
                    player_name,
                    draw_id,
                    draw_name,
                    guild_id,
                    guild_name,
                    status
                )
                VALUES
                (
                    {str(ctx.author.id)},
                    '{ctx.author.name}',
                    {str(draw_id)},
                    '{draw_name}',
                    {str(ctx.guild.id)},
                    '{ctx.guild.name}',
                    'Учавствует в розыгрыше'
                )
            """)
            embed=discord.Embed(title='Новый участник розыгрыша',color=color['green'])
            embed_value = f'{ctx.author.mention} принимает участие, желаем удачи!\n'
            embed.add_field(name=found_draw['draw_name'],value=embed_value,inline=False)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.addlog(str(error),'error')
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(common(bot))