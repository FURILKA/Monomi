from discord.ext import commands
from colors import color
import discord
import os,sys
import asyncio
# ==================================================================================================================================================================
class onmessage(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    @commands.Cog.listener()
    async def on_message(self,message):
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        # Проверка - является ли содержимое сообщения - или содержит ли - триггер для реакции
        async def check_for_reaction(message):
            try:
                guild = message.guild
                member = message.author
                msgtext = str(message.content).lower()
                reactions = self.bot.reactions[guild.id]['message'] if guild.id in self.bot.reactions else []
                # Если на данном сервере реакций нет - просто выходим
                if reactions == []: return
                for reaction in reactions:
                    trigger = reaction['trigger'].lower()
                    value = reaction['value'].replace(f'%user%',str(member.mention))
                    attach = reaction['attach']
                    partial_trigger_type = False
                    # Если первый и последний символ триггера == % значит это поиск частичного текста в сообщении
                    if trigger[0] == '%' and trigger[-1] == '%':
                        partial_trigger_type = True
                        trigger = trigger[1:-1]
                    # Если это "строгий" триггер - проверяем является ли сообщение триггером, если является - пишем реакцию
                    if partial_trigger_type == False:
                        if trigger == msgtext:
                            self.bot.LLC.addlog(f'[{guild.name}] сработала реакция: {trigger=}')
                            if value != '' and value != None:
                                await message.channel.send(value)
                            if attach != '' and attach != None:
                                await message.channel.send(attach)
                    # Если это "частичный" триггер то просто пытаемся найти первое вхождение, если оно есть - пишем реакцию
                    if partial_trigger_type == True:
                        if msgtext.find(trigger) >= 0:
                            self.bot.LLC.addlog(f'[{guild.name}] сработала реакция: trigger=%{trigger}%')
                            if value != '' and value != None:
                                await message.channel.send(value)
                            if attach != '' and attach != None:
                                await message.channel.send(attach)
            except Exception as error:
                self.LLC.addlog(str(error),'error')
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        try:
            if message.author == self.bot.user: return
            if message.author.bot == True: return
            await check_for_reaction(message)
        except Exception as error:
            self.LLC.addlog(str(error),'error')
    # **************************************************************************************************************************************************************
def setup(bot):
    bot.add_cog(onmessage(bot))