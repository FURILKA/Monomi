from discord.ext import commands
from colors import color
import discord
import os,sys
import asyncio
from discord_components import DiscordComponents
# ==================================================================================================================================================================
class owner(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
        if hasattr(self.bot,'channels_clearbytimer')==False: self.bot.channels_clearbytimer = {}
        if hasattr(self.bot,'draws')==False: self.bot.draws = {}
    # **************************************************************************************************************************************************************
    @commands.Cog.listener()
    async def on_ready(self):
        # **********************************************************************************************************************************************************
        # Загрузка информации о существующих ролях
        def load_roles():
            try:
                # создаём словарь "roles", ключем в нём будут ID серверов, значением будет словарь с названиями ролей и списками ID ролей
                roles = {}
                dict_empty_roles = {}
                roles_types = ['admin','moderator','welcome'] # <--- если появятся новые типы ролей - добавлять их сюда
                # собираем словарь с ключем = именам всех типов ролей и значений из пустых списков
                for role_type in roles_types:
                    dict_empty_roles[role_type]=[]
                # перебираем все типы ролей
                for role_type in roles_types:
                    # делаем запрос в БД и получаем все роли данного типа по всем серверам
                    result_roles = self.mysql.execute('SELECT * FROM roles_' + role_type)
                    # перебираем все роли
                    for role in result_roles:
                        guild_id = int(role['guild_id'])
                        role_id  = int(role['role_id'])
                        # если в словаре пока нет такого сервера - добавляем его с пустым словарем "dict_empty_roles"
                        if guild_id not in roles: roles[guild_id] = dict_empty_roles
                        # добавляем для этого сервера для этой роли ID роли к общему списку ID по этой роли
                        roles[guild_id][role_type].append(role_id)
                self.bot.roles = roles
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        # Загрузка реакций
        def load_reactions():
            try:
                # создаём словарь "reactions", ключем в нём будут ID серверов, значением будет словарь с типами реакций и списками из ID реакции + триггер + значение
                reactions = {}
                dict_empty_reactions = {}
                reactions_types = ['message','emoji'] # <--- если появятся новые типы реакций - добавлять их сюда
                # собираем словарь с ключем = именам всех типов реакций и значений из пустых списков
                for reaction_type in reactions_types:
                    dict_empty_reactions[reaction_type]=[]
                # Собираем пустой словарь реакций, заполняем его id серверов и типами реакций
                for table_reaction_type in reactions_types:
                    result_guilds = self.mysql.execute(f'SELECT rm.guild_id FROM reactions_{table_reaction_type} rm GROUP BY rm.guild_id')
                    for row in result_guilds:
                        guild_id = int(row['guild_id'])
                        if guild_id not in reactions:
                            reactions[guild_id] = {}
                            for reaction_type in reactions_types:
                                reactions[guild_id][reaction_type]=[]
                # заполняем итоговый словарь реакций
                result_reactions = {}
                for reaction_type in reactions_types:
                    # делаем запрос в БД и получаем все реакции данного типа по всем серверам
                    result_reactions[reaction_type] = self.mysql.execute('SELECT * FROM reactions_' + reaction_type)
                    # перебираем все найденные реакции
                    if result_reactions[reaction_type] != [] and result_reactions[reaction_type] != ():
                        r = {}
                        for reaction in result_reactions[reaction_type]:
                            reaction_dict = {
                                'id':reaction['reaction_id'],
                                'trigger':  reaction['react_trigger'],
                                'value': reaction['react_value'],
                            }
                            guild_id = int(reaction['guild_id'])
                            if 'react_attach' in reaction:
                                reaction_dict['attach'] = reaction['react_attach']
                            else:
                                reaction_dict['attach'] = ''
                            reactions[guild_id][reaction_type].append(reaction_dict)
                            result_dict = reactions.copy()
                # словарь реакций готов, записываем его в бота
                self.bot.reactions = result_dict
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        # Загрузка эмодзи
        def load_emoji():
            try:
                result = self.bot.mysql.execute(f"SELECT emoji_name, emoji_text FROM emojis")
                emojis = {}
                for row in result:
                    emoji_name = row['emoji_name']
                    emoji_text = row['emoji_text']
                    emojis[emoji_name] = emoji_text
                self.bot.emoji = emojis
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        # Загрузка команд
        def load_commands():
            try:
                self.bot.commands_type = self.bot.mysql.execute(f"SELECT * FROM commands_types ORDER BY type_order ASC")
                self.bot.commands_list = self.bot.mysql.execute(f"SELECT * FROM commands ORDER BY command_type ASC, command_order ASC")
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        # Загрузка каналов для очистки по таймеру
        def load_clearbytimer():
            try:
                sqlresult = self.bot.mysql.execute(f"SELECT * FROM channels_clearbytimer")
                if sqlresult != [] and sqlresult != ():
                    for row in sqlresult:
                        channel_id = row['channel_id']
                        guild_name = row['guild_name']
                        channel_name = row['channel_name']
                        interval  = row['interval']
                        self.bot.channels_clearbytimer[channel_id]={'guild_name':guild_name,'channel_name':channel_name,'interval':interval}
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        # Загрузка розыгрышей
        def load_draws():
            try:
                sqlresult = self.bot.mysql.execute(f"SELECT * FROM draw_byguild WHERE is_active = 1")
                if sqlresult != [] and sqlresult != ():
                    for row in sqlresult:
                        draw_channel_id = row['draw_channel_id']
                        if draw_channel_id not in self.bot.draws: self.bot.draws[draw_channel_id]=[]
                        self.bot.draws[draw_channel_id].append({
                            'draw_id': row['draw_id'],
                            'draw_name': row['draw_name'],
                            'guild_id': row['guild_id'],
                            'guild_name': row['guild_name'],
                            'draw_date': row['draw_date'],
                            'draw_channel_id': row['draw_channel_id'],
                            'draw_channel_name': row['draw_channel_name'],
                            'draw_players_count': row['draw_players_count'],
                            'dray_prizes_count': row['dray_prizes_count'],
                            'author_id': row['author_id'],
                            'author_name': row['author_name'],
                            'status': row['status'],
                        })
            except Exception as error:
                self.LLC.adderrorlog()
        # **********************************************************************************************************************************************************
        self.bot.LLC.addlog('Загрузка компонент')
        DiscordComponents(self.bot)
        self.bot.LLC.addlog('Загрузка команд')
        load_commands()
        self.bot.LLC.addlog('Загрузка групп')
        load_roles()
        self.bot.LLC.addlog('Загрузка реакций')
        load_reactions()
        self.bot.LLC.addlog('Загрузка эмодзи')
        load_emoji()
        self.bot.LLC.addlog('Загрузка каналов очистки по таймеру')
        load_clearbytimer()
        self.bot.LLC.addlog('Загрузка информации о розыгрышах')
        load_draws()
        self.bot.LLC.addlog('Бот запущен и готов к работе')
        self.bot.IsOnlineNow = True
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(owner(bot))