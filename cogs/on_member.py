from discord.ext import commands
from colors import color
import discord
import os,sys
import asyncio
# ==================================================================================================================================================================
class on_member(commands.Cog):
    # **************************************************************************************************************************************************************
    def __init__(self,bot):
        self.bot = bot
        self.LLC = bot.LLC
        self.mysql = bot.mysql
    # **************************************************************************************************************************************************************
    @commands.Cog.listener()
    async def on_member_join(self,member):
        guild = member.guild
        self.bot.LLC.addlog(f'К серверу [{guild.name}] присоединяется новый участник: "{member.name}"[id:{member.id}]')
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        # Ждём 3 секунды перед тем, как давать роли и писать сообщения новому участнику сообщества, пусть у него там всё прогрузится и т.д.
        await asyncio.sleep(3)
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        # Получаем информацию о приветственном сообщение и дефолтных ролях для данного сервера
        self.mysql.connect()
        welcome_text_result = self.mysql.execute(f"SELECT * FROM text_welcome WHERE guild_id = '{str(guild.id)}'")
        welcome_role_result = self.mysql.execute(f"SELECT * FROM roles_welcome WHERE guild_id = '{str(guild.id)}'")
        self.mysql.disconnect()
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        # Если у сервера заданы приветственные роли - выдаём их
        if welcome_role_result != [] and welcome_role_result != ():
            for row in welcome_role_result:
                role_id = int(row['role_id'])
                role_name = row['role_name']
                role = guild.get_role(role_id)
                if role != None:
                    self.bot.LLC.addlog(f'Выдаём пользователю "{member.name}"[id:{member.id}] роль "{role.name}" на сервере [{guild.name}]')
                    await member.add_roles(role)
                else:
                    self.LLC.addlog(f'Роль "{role_name}" на сервере [{guild.name}] не найдена!','error')
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------
        if welcome_text_result != [] and welcome_text_result != ():
            welcome_text = welcome_text_result[0]['message']
            welcome_channel = int(welcome_text_result[0]['channel_id'])
            channel = member.guild.get_channel(welcome_channel)
            if channel != None:
                self.bot.LLC.addlog(f'Отправляем для "{member.name}" [id:{member.id}] сообщение на сервере [{guild.name}]')
                await channel.send(str(member.mention) + ' ' + welcome_text)
            else:
                channel_name = welcome_text_result[0]['channel_name']
                self.LLC.addlog(f'Канал "{channel_name}" [id:{str(welcome_channel)}] на сервере [{guild.name}] не найден!','error')
# ==================================================================================================================================================================
def setup(bot):
    bot.add_cog(on_member(bot))