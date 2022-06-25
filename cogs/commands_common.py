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
                msgtext += f'Может быть ты имеешь ввиду другой розыгрыш?\n'
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
    # **************************************************************************************************************************************************************
    # Отказаться от участия в розыгрыше
    @commands.command()
    async def leavedraw(self,ctx, draw_id=None):
        try:
            command_name = 'leavedraw'
            command_info  = f'\nЧто бы отказаться от участия в розыгрыше введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#ID розыгрыша>***\n'
            command_info += f'**<#ID розыгрыша>**: номер (ID), от участия в котором вы отказываетесь\n'
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
            # Проверим - может является ли пользователь участником розыгрыша?
            draw_id = found_draw['draw_id']
            draw_name = found_draw['draw_name']
            sql_result = self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)} AND player_id = {str(member.id)} AND is_active = 1")
            if sql_result == () or sql_result == []:
                msgtext  = f'{ctx.author.mention} ты не являешься участником данного розыгрыша\n'
                msgtext += f'Может быть ты имеешь ввиду другой розыгрыш?\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Пользователь не является участником розыгрыша')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Пометим участника в таблице как отказавшегося и напишем ему сообщение
            sql_result = self.bot.mysql.execute(f"""
                UPDATE draw_players 
                SET is_active = 0, status = 'Отказался от участия'
                WHERE draw_id = {str(draw_id)} AND player_id = {str(member.id)} AND is_active = 1
                """)
            embed=discord.Embed(title='Участник покинул розыгрыш',color=color['green'])
            embed_value = f'{ctx.author.mention} отказывается от участия\n'
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
    # **************************************************************************************************************************************************************
    @commands.command()
    async def infodraw(self,ctx, draw_id=None):
        try:
            command_name = 'infodraw'
            command_info  = f'\nЧто бы получить информацию о розыгрыше введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#ID розыгрыша>***\n'
            command_info += f'**<#ID розыгрыша>**: номер (ID) розыгрыша, который вас интересует\n'
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
            # Получим общий список участников и проверим, является ли пользователь участником
            sql_result_players = self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)} AND is_active = 1")
            is_member_join_draw = False
            if sql_result_players == [] or sql_result_players == ():
                players_count_now = 0
            else:
                players_count_now = len(sql_result_players)
                for player in sql_result_players:
                    if player['player_id'] == ctx.author.id:
                        is_member_join_draw = True
                        break
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Получим список призов
            prizes = []
            sql_result_prizes = self.bot.mysql.execute(f"SELECT prize_name FROM draw_prizes WHERE draw_id = {str(draw_id)} AND is_active = 1")
            for prize in sql_result_prizes:
                prizes.append(prize['prize_name'])
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Сообщим пользователю информацию об розыгрыше
            draw_name = found_draw['draw_name']
            draw_date = datetime.datetime.strftime(found_draw['draw_date'],'%d.%m.%Y %H:%M')
            draw_channel = '<#'+str(found_draw['draw_channel_id'])+'>'
            draw_players_count = found_draw['draw_players_count']
            dray_prizes_count = found_draw['dray_prizes_count']
            draw_name = found_draw['draw_name']
            draw_author = found_draw['author_name']
            emoji_name = self.bot.emoji['CasinoChips']
            emoji_id =''.join(i for i in emoji_name if i.isdigit())
            emoji_obj = self.bot.get_emoji(int(emoji_id))
            embed=discord.Embed(title='Информация о розыгрыше',color=color['green'])
            embed_value = f'ID розыгрыша: **#{str(draw_id)}**\n'
            embed_value += f'Организатор: **{draw_author}**\n'
            embed_value += f'Дата окончания: **{draw_date}**\n'
            embed_value += f'Канал: **{draw_channel}**\n'
            if int(draw_players_count)==0:
                embed_value += f'Макс. участников: **Не ограничено**\n'
            else:
                embed_value += f'Макс. участников: **{draw_players_count}**\n'
            embed_value += f'Приняло участие: **{str(players_count_now)}**\n'
            if int(dray_prizes_count) == 1:
                draw_prize_name = prizes[0]
                embed_value += f'Количество призов: **1**\n'
                embed_value += f'\nПриз: **{draw_prize_name}**\n'
            elif int(dray_prizes_count) == 0:
                embed_value += f'Количество призов: **0**\n'
                embed_value += f'\nПризов нет, странно\n'
            else:
                embed_value += f'Количество призов: **{int(dray_prizes_count)}**\n\n'
                for i in range(int(dray_prizes_count)):
                    draw_prize_name = prizes[i]
                    embed_value += f'Приз №{str(i+1)}: **{draw_prize_name}**\n'
            if is_member_join_draw == True:
                embed_value += f'__Ты являешься участником розыгрыша__\n'
            else:
                embed_value += f'__Ты **не** являешься участником розыгрыша__\n'
            embed.add_field(name='"'+draw_name+'"',value=embed_value,inline=True)
            embed_value = ''
            for player in sql_result_players:
                embed_value += player['player_name'] + '\n'
            if embed_value == '': embed_value = 'Пока нет'
            embed.add_field(name='Список участников',value=embed_value,inline=True)
            embed.set_thumbnail(url=str(emoji_obj.url))
            if is_member_join_draw == False: embed.set_footer(text=f'Что бы принять участие в розыгрыше используй команду: {self.bot.prefix}joindraw <#id>')
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
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(common(bot))