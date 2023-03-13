import asyncio
from discord.ext import commands
from colors import color
import discord
import datetime

from discord_components import Button,ButtonStyle,DiscordComponents
from discord.ext.forms import Form,ReactionForm
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
            self.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # Создание нового розыгрыша
    @commands.command()
    async def newdraw(self,ctx):
        try:
            command_name = 'newdraw'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.IsAdminOrModerator(ctx) == False: return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Задаем пользователю вопросы о новом розыгрыше
            message_begin = await ctx.send(content='Окей, создаём новый розыгрыш, ответь на несколько вопросов:')
            form = Form(ctx,'Создание нового розыгрыша')
            form.add_question('Укажите название нового розыгрыша','draw_name')
            form.add_question('Укажите дату окончания розыгрыша\nДата указывается формате "dd.mm.yyyy"','draw_end_date')
            form.add_question('Укажите время окончания розыгрыша\nВремя указывается в формате "hh:mm"','draw_end_time')
            form.add_question('В каком канале объявить результаты?\nКанал указывается через #','draw_channel')
            form.add_question('Количество участников?\nЧисло, от 0 (не ограничено) до 50','draw_players_count')
            form.add_question('Сколько будет разыгрываться призов?\nЧисло, не менее 1, но не более 10','draw_prize_count')
            form.set_timeout(60)
            result = await form.start()
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Получаем ответы на вопросы
            draw_name = result.draw_name
            draw_end_date = result.draw_end_date
            draw_end_time = result.draw_end_time
            draw_players_count = result.draw_players_count
            draw_channel = result.draw_channel
            draw_prize_count = result.draw_prize_count
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем их корректность
            input_errors = []
            # Проверяем дату розыгрыша
            try:
                end_date = datetime.datetime.strptime(draw_end_date, '%d.%m.%Y')
            except ValueError:
                input_errors.append('Дата указана некорректно')
            # Проверяем время розыгрыша
            try:
                datetime.datetime.strptime(draw_end_time, '%H:%M')
            except ValueError:
                input_errors.append('Указано некорректное время окончания розыгрыша')
            # Проверяем дату + время розыгрыша - не должны быть меньше текущей
            try:
                if datetime.datetime.strptime(draw_end_date + ' ' + draw_end_time, '%d.%m.%Y %H:%M')<datetime.datetime.now():
                    input_errors.append('Дата/время розыгрыша не могут быть меньше текущих')
                else:
                    draw_end_datetime = draw_end_date + ' ' + draw_end_time
            except ValueError:
                pass
            # Проверяем кол-во участников
            if draw_players_count.isdigit()==False:
                input_errors.append('Указано некорректное количество участников')
            else:
                if int(draw_players_count)<0 or int(draw_players_count)>50:
                    input_errors.append('Указано некорректное количество участников')
            # Проверяем количество призов
            if draw_prize_count.isdigit()==False:
                input_errors.append('Указано некорректное количество призов')
            else:
                if int(draw_prize_count)<1 or int(draw_prize_count)>10:
                    input_errors.append('Указано некорректное количество призов')
            # Проверяем канал розыгрыша
            if draw_channel[0:2] != '<#' and draw_channel[-1] != '>':
                input_errors.append('Указан некорректный канал объявления результатов')
            else:
                channel_id = draw_channel.replace('<#','').replace('>','')
                if channel_id.isdigit()==False:
                    input_errors.append('Указан некорректный канал объявления результатов')
                else:
                    channel_id = int(channel_id)
                    channel = self.bot.get_channel(channel_id)
                    if channel == None:
                        input_errors.append('Боту не удалось открыть указанный канал')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если есть ошибки - сообщаем о них пользователю и выходим
            if input_errors != []:
                emoji_name = self.bot.emoji['error']
                emoji_id =''.join(i for i in emoji_name if i.isdigit())
                emoji_obj = self.bot.get_emoji(int(emoji_id))
                embed=discord.Embed(title='Ошибка при создании розыгрыша',color=color['red'])
                embed_value = ''
                for error_name in input_errors:
                    embed_value += f'{error_name}\n'
                embed.add_field(name='Ну давай разберем по частям тобою написанное',value=embed_value,inline=False)
                embed.set_thumbnail(url=str(emoji_obj.url))
                embed.set_footer(text='Попробуй ещё раз и будь внимательнее :)')
                message = await ctx.send(content=ctx.author.mention,embed=embed)
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Уточняем информацию о призах
            prizes = []
            if int(draw_prize_count) == 1:
                message_prize = await ctx.send(content='Какой приз будем разыгрывать?')
                form = Form(ctx,'Выбор приза')
                form.add_question('Укажи наименование приза','draw_prize_name')
                form.set_timeout(60)
                result = await form.start()
                draw_prize_name = result.draw_prize_name
                prizes.append(draw_prize_name)
            else:
                message_prize = await ctx.send(content='Теперь давай определимся с призами, что мы будем разыгрывать?')
                form = Form(ctx,'Выбор призов')
                form.set_timeout(60)
                questions = []
                
                for i in range(int(draw_prize_count)):
                    question = f'Укажи наименование приза №{str(i+1)}'
                    questions.append(question)
                    form.add_question(question,f'draw_prize_name{str(i+1)}')
                result = await form.start()
                for i in range(int(draw_prize_count)):
                    prizes.append(getattr(result,f'draw_prize_name{str(i+1)}'))
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Выводим пользователю итоговую информацию и спрашиваем подтверждение
            components = [Button(style=ButtonStyle.green,label='Да'),Button(style=ButtonStyle.red, label='Нет')]
            embed_name = 'Мы создаём новый розыгрыш'
            embed_value  = f'Название розыгрыша: **{draw_name}**\n'
            embed_value += f'Дата окончания розыгрыша: **{draw_end_date}**\n'
            embed_value += f'Время окончания розыгрыша: **{draw_end_time}**\n'
            embed_value += f'Канал объявления результатов: **{draw_channel}**\n'
            if int(draw_players_count)==0:
                embed_value += f'Максимальное количество участников: **Не ограничено**\n'
            else:
                embed_value += f'Максимальное количество участников: **{draw_players_count}**\n'
            if int(draw_prize_count) == 1:
                embed_value += f'Количество призов: **1**\n'
                embed_value += f'\nПриз: **{draw_prize_name}**\n'
            else:
                embed_value += f'Количество призов: **{int(draw_prize_count)}**\n\n'
                for i in range(int(draw_prize_count)):
                    draw_prize_name = prizes[i]
                    embed_value += f'Приз №{str(i+1)}: **{draw_prize_name}**\n'
            embed=discord.Embed(title='Давай проверим введенные данные',color=color['green'])
            embed.add_field(name=embed_name,value=embed_value + '\nВсё верно?',inline=False)
            embed.set_footer(text='Подтвердите создания нового розыгрыша')
            message = await ctx.send(embed=embed,components=[components])
            response = await self.bot.wait_for('button_click')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Обрабатываем подтверждение
            if response.channel == ctx.channel and response.author == ctx.author:
                if response.component.label == 'Да':
                    # Если была нажата кнопка "Да"
                    # Убираем кнопки с подтверждения
                    await message.edit(embed=embed,components=[])
                    response.responded = True
                    # Записываем информацию о розыгрыше в базу данных
                    self.mysql.execute(f"""
                        INSERT INTO 
                            draw_byguild
                            (
                                draw_name,
                                guild_id,
                                guild_name,
                                draw_date,
                                draw_channel_id,
                                draw_channel_name,
                                draw_players_count,
                                dray_prizes_count,
                                author_id,
                                author_name,
                                status
                            ) 
                        VALUES 
                            (
                                '{draw_name}',
                                {str(ctx.guild.id)},
                                '{ctx.guild.name}',
                                STR_TO_DATE('{draw_end_datetime}','%d.%m.%Y %H:%i'),
                                {str(channel_id)},
                                '{channel.name}',
                                {str(draw_players_count)},
                                {str(draw_prize_count)},
                                {str(ctx.author.id)},
                                '{ctx.author.name}',
                                'Ожидание розыгрыша'
                            )
                        """)
                    # Получим ID созданной записи розыгрыша в базе данных
                    sql_result = self.mysql.execute(f"""
                        SELECT draw_id 
                        FROM draw_byguild 
                        WHERE guild_id = {str(ctx.guild.id)} 
                        ORDER BY date_add DESC 
                        LIMIT 1
                        """)
                    draw_id = sql_result[0]['draw_id']
                    # Записываем информацию о призах в базу данных
                    query = f'INSERT INTO draw_prizes (prize_name,draw_id,draw_name,guild_id,guild_name,status) VALUES '
                    values = []
                    for prize_name in prizes:
                        values.append(
                            f"('{prize_name}',{str(draw_id)},'{draw_name}',{str(ctx.guild.id)},'{ctx.guild.name}','Ожидание розыгрыша')"
                        )
                    query = query + ','.join(values)
                    self.mysql.execute(query)
                    # Записываем информацию о новом розыгрыше в параметр бота
                    if channel_id not in self.bot.draws:
                        self.bot.draws[channel_id]=[]
                    self.bot.draws[channel_id].append({
                            'draw_id': draw_id,
                            'draw_name': draw_name,
                            'guild_id': ctx.guild.id,
                            'guild_name': ctx.guild.name,
                            'draw_date': datetime.datetime.strptime(draw_end_datetime,'%d.%m.%Y %H:%M'),
                            'draw_channel_id': channel.id,
                            'draw_channel_name': channel.name,
                            'draw_players_count': draw_players_count,
                            'dray_prizes_count': draw_prize_count,
                            'author_id': ctx.author.id,
                            'author_name': ctx.author.name,
                            'status': 'Ожидание розыгрыша'
                        })
                    # Подготавливаем сообщение с подтверждением
                    emoji_name = self.bot.emoji['success']
                    emoji_id =''.join(i for i in emoji_name if i.isdigit())
                    emoji_obj = self.bot.get_emoji(int(emoji_id))
                    embed=discord.Embed(title='Розыгрыш успешно создан',color=color['green'])
                    embed.add_field(name='Детали розыгрыша',value=embed_value,inline=False)
                    embed.set_thumbnail(url=str(emoji_obj.url))
                    # Удаляем старое сообщение
                    await message.delete()
                    # Отправляемс ообщение с подтверждением
                    message = await ctx.send(content=ctx.author.mention,embed=embed)
                else:
                    # Если была нажата кнопка "Нет" выходим из функции
                    embed.color = color['gray']
                    await message.edit(embed=embed,components=[])
                    response.responded = True
                    message = await ctx.send(content=ctx.author.mention+' понял, понял, вычеркиваю!')
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # Удаление существующего розыгрыша
    @commands.command()
    async def deldraw(self,ctx, draw_id=None):
        try:
            command_name = 'deldraw'
            command_info  = f'\nДля удаления розыгрыша введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#ID розыгрыша>***\n'
            command_info += f'**<#ID розыгрыша>**: номер (ID) розыгрыша для удаления\n'
            command_info += f'Получение списка активных розыгрышей: **{self.bot.prefix}listdraw**\n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            if await self.IsAdminOrModerator(ctx) == False: return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверим, что draw_id передан в команду
            if draw_id == None:
                msgtext  = f'Не указан ID розыгрыша для удаления\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Не указан ID розыгрыша для удаления')
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
            # Розыгрыш найден, спросим у пользователя подтверждение
            prizes = []
            sql_result = self.bot.mysql.execute(f"SELECT * FROM draw_prizes WHERE draw_id = {str(draw_id)}")
            players_count_now = len(self.bot.mysql.execute(f"SELECT * FROM draw_players WHERE draw_id = {str(draw_id)}"))
            for row in sql_result:
                prizes.append(row['prize_name'])
            components = [Button(style=ButtonStyle.green,label='Да'),Button(style=ButtonStyle.red, label='Нет')]
            draw_name = found_draw['draw_name']
            draw_date = datetime.datetime.strftime(found_draw['draw_date'],'%d.%m.%Y %H:%M')
            draw_channel = '<#'+str(found_draw['draw_channel_id'])+'>'
            draw_players_count = found_draw['draw_players_count']
            dray_prizes_count = found_draw['dray_prizes_count']
            draw_name = found_draw['draw_name']
            embed_name = 'Ты собираешься отменить существующий розыгрыш'
            embed_value  = f'Название розыгрыша: **{draw_name}**\n'
            embed_value += f'Дата окончания розыгрыша: **{draw_date}**\n'
            embed_value += f'Канал объявления результатов: **{draw_channel}**\n'
            if int(draw_players_count)==0:
                embed_value += f'Максимальное количество участников: **Не ограничено**\n'
            else:
                embed_value += f'Максимальное количество участников: **{draw_players_count}**\n'
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
            embed=discord.Embed(title='Давай уточним',color=color['green'])
            embed.add_field(name=embed_name,value=embed_value + '\nВсё верно? Отменяем розыгрыш?',inline=False)
            embed.set_footer(text='Подтвердите создания нового розыгрыша')
            message = await ctx.send(embed=embed,components=[components])
            response = await self.bot.wait_for('button_click')
            if response.channel == ctx.channel and response.author == ctx.author:
                if response.component.label == 'Да':
                    # Если была нажата кнопка "Да"
                    # Убираем кнопки с подтверждения
                    await message.edit(embed=embed,components=[])
                    response.responded = True
                else:
                    await message.edit(embed=embed,components=[])
                    response.responded = True
                    await ctx.send(content=ctx.author.mention+' передумал, да ? Розыгрыш не был отменен')
                    return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Удалим розыгрыш из списка розыгрышей
            for channel_id in self.bot.draws:
                for draw in self.bot.draws[channel_id]:
                    if draw == found_draw:
                        self.bot.draws[channel_id].remove(found_draw)
                        break
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Удалим его из базы данных
            self.bot.mysql.execute(f"UPDATE draw_byguild SET status = 'Розыгрыш отменен', is_active = 0 WHERE draw_id = {str(draw_id)}")
            self.bot.mysql.execute(f"UPDATE draw_players SET status = 'Розыгрыш отменен', is_active = 0 WHERE draw_id = {str(draw_id)}")
            self.bot.mysql.execute(f"UPDATE draw_prizes SET status = 'Розыгрыш отменен', is_active = 0 WHERE draw_id = {str(draw_id)}")
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Сообщим пользователю о том, что всё получилось
            emoji_name = self.bot.emoji['success']
            emoji_id =''.join(i for i in emoji_name if i.isdigit())
            emoji_obj = self.bot.get_emoji(int(emoji_id))
            embed=discord.Embed(title='Розыгрыш отменен',color=color['green'])
            embed.add_field(name='Детали розыгрыша',value=embed_value,inline=False)
            embed.set_thumbnail(url=str(emoji_obj.url))
            # Удаляем старое сообщение
            await message.delete()
            # Отправляемс ообщение с подтверждением
            message = await ctx.send(content=ctx.author.mention,embed=embed)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
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
            self.bot.LLC.adderrorlog()
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
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # Удаление сообщений в канале если оно старше <N> минут
    @commands.command()
    async def addclearbytimer(self,ctx,channel_target=None,minutes_count=None):
        try:
            command_name = 'addclearbytimer'
            command_info  = f'\nДля настройки удаления сообщений введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#канал> <N минут>***\n'
            command_info += f'**<#канал>**: ссылка на канал (через # решетку)\n'
            command_info += f'**<N минут>**: через сколько минут сообщения будут удалены\n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            self.LLC.addlog(f'{self.bot.prefix}{command_name}" {channel_target=} {minutes_count=}')
            if await self.IsAdminOrModerator(ctx) == False: return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в команду передан канал - проверяем, что канал указан в нормальном формате (через #)
            if channel_target != None:
                if channel_target[0:2] != '<#' and channel_target[-1] != '>':
                    msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                    msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                    await ctx.send(embed=embed)
                    self.bot.LLC.addlog('Ссылка на канал указана некорректно, возможно опечатка?')
                    return
            channel_id = str(channel_target).replace('<#','').replace('>','')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что переданный ID канала в цифровом виде (а не просто написали "<#канал>")
            if channel_id.isdigit() == False:
                msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Ссылка на канал указана некорректно, возможно опечатка?')
                return   
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Пытаемся открыть канал на сервере, проверяем что он открылся
            channel_id = int(channel_id)
            channel = guild.get_channel(channel_id)
            if channel == None:
                msgtext  = f'Не удалось найти указанный канал на сервере!\n'
                msgtext += f'Проверьте:\n'
                msgtext += f'1) Корректность указания канала\n'
                msgtext += f'2) Права доступа бота к указанному каналу\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Не удалось найти указанный канал на сервере!')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # minutes_count должно быть числом от 1 до 1440 включительно, если передано что-то не так (или ничего не передано) сообщаем об ошибке
            if minutes_count == None or minutes_count.isdigit()==False or int(minutes_count)<1 or int(minutes_count)>1440:
                msgtext = f'Таймер для удаления сообщений указан некорректно!\nДолжно быть целое число от 1 до 1440\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Таймер для удаления сообщений указан некорректно!')
                return
            minutes_count = minutes_count
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Все, канал открыт, минуты указаны корректно - создаём/изменяем таймер удаления сообщений на канале
            values = f"'{str(guild.id)}','{guild.name}',{str(channel.id)},'{channel.name}','{minutes_count}',{str(member.id)},'{member.name}'"
            sqlresult = self.mysql.execute(f"SELECT * FROM channels_clearbytimer WHERE guild_id = {str(guild.id)} AND channel_id = {str(channel.id)}")
            if sqlresult == () or sqlresult == []:
                self.mysql.execute(f"INSERT INTO channels_clearbytimer(guild_id,guild_name,channel_id,channel_name,`interval`,author_id,author_name) VALUES ({values})")
                msgtext = f'Таймер удаления сообщений установлен!'
                self.bot.channels_clearbytimer[channel.id]={'guild_name':guild.name,'channel_name':channel.name,'interval':int(minutes_count)}
            else:
                last_timer = str(sqlresult[0]['interval'])
                self.mysql.execute(f"""
                    UPDATE 
                        channels_clearbytimer 
                    SET
                        channel_name='{channel.name}',`interval`={str(minutes_count)},date_add=CURRENT_TIMESTAMP(),author_id={str(member.id)},author_name='{member.name}'
                    WHERE
                         guild_id = {str(guild.id)} AND channel_id = {str(channel.id)}
                    """)
                msgtext  = f'Таймер удаления сообщений изменен!\n'
                msgtext += f'Прошлое значение таймера: {last_timer}\n'
                msgtext += f'Новое значение таймера: {str(minutes_count)}\n'
                self.bot.channels_clearbytimer[channel.id]={'guild_name':guild.name,'channel_name':channel.name,'interval':int(minutes_count)}
            embed = discord.Embed(description = msgtext, color = color['green'])
            await ctx.send(embed=embed)
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
        except Exception as error:
            msgtext  = f'Команда: **{self.bot.prefix}{command_name}**\n'
            msgtext += f'||{str(error)}||\n'
            msgtext += f'Что-то пошло не так, я не могу выполнить команду\n'
            embed=discord.Embed(description='**Ошибка!**',color=color['red'])
            embed.add_field(name=f':x:', value=msgtext, inline=False)
            await ctx.send(embed=embed)
            self.bot.LLC.adderrorlog()
    # **************************************************************************************************************************************************************
    # Удаление сообщений в канале если оно старше <N> минут
    @commands.command()
    async def delclearbytimer(self,ctx,channel_target=None):
        try:
            command_name = 'delclearbytimer'
            command_info  = f'\nДля отключения удаления сообщений введите команду в формате:\n'
            command_info += f'**{self.bot.prefix}{command_name}** ***<#канал>***\n'
            command_info += f'**<#канал>**: ссылка на канал (через # решетку)\n'
            guild = ctx.guild
            member = ctx.author
            self.LLC.addlog(f'Новая команда "{self.bot.prefix}{command_name}" [сервер: "{guild.name}", пользователь: "{member.name}"]')
            self.LLC.addlog(f'{self.bot.prefix}{command_name}" {channel_target=}')
            if await self.IsAdminOrModerator(ctx) == False: return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Если в команду передан канал - проверяем, что канал указан в нормальном формате (через #)
            if channel_target != None:
                if channel_target[0:2] != '<#' and channel_target[-1] != '>':
                    msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                    msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                    embed=discord.Embed(color=color['red'])
                    embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                    await ctx.send(embed=embed)
                    self.bot.LLC.addlog('Ссылка на канал указана некорректно, возможно опечатка?')
                    return
            channel_id = str(channel_target).replace('<#','').replace('>','')
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Проверяем, что переданный ID канала в цифровом виде (а не просто написали "<#канал>")
            if channel_id.isdigit() == False:
                msgtext  = f'Ссылка на канал указана некорректно, возможно опечатка?\n'
                msgtext += f'Канал указывается как ссылка на канал через # (через решетку)\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Ссылка на канал указана некорректно, возможно опечатка?')
                return   
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Пытаемся открыть канал на сервере, проверяем что он открылся
            channel_id = int(channel_id)
            channel = guild.get_channel(channel_id)
            if channel == None:
                msgtext  = f'Не удалось найти указанный канал на сервере!\n'
                msgtext += f'Проверьте:\n'
                msgtext += f'1) Корректность указания канала\n'
                msgtext += f'2) Права доступа бота к указанному каналу\n'
                embed=discord.Embed(color=color['red'])
                embed.add_field(name=f':x: Ошибка', value=msgtext+command_info, inline=False)
                await ctx.send(embed=embed)
                self.bot.LLC.addlog('Не удалось найти указанный канал на сервере!')
                return
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            # Все, канал открыт, минуты указаны корректно - создаём/изменяем таймер удаления сообщений на канале
            sqlresult = self.mysql.execute(f"SELECT * FROM channels_clearbytimer WHERE guild_id = {str(guild.id)} AND channel_id = {str(channel.id)}")
            if sqlresult == () or sqlresult == []:
                msgtext = f'Таймер удаления сообщений в канале не установлен'
                embed = discord.Embed(description = msgtext,color = color['red'])
                if channel.id in self.bot.channels_clearbytimer:
                    self.bot.channels_clearbytimer.pop(channel.id)
            else:
                self.mysql.execute(f'DELETE FROM channels_clearbytimer WHERE guild_id = {str(guild.id)} AND channel_id = {str(channel.id)}')
                msgtext = f'Таймер удаления сообщений в канале удален'
                if channel.id in self.bot.channels_clearbytimer:
                    self.bot.channels_clearbytimer.pop(channel.id)
                embed = discord.Embed(description = msgtext,color = color['green'])
            await ctx.send(embed=embed)
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
    bot.add_cog(moderator(bot))