"""
RinBot v1.4.3
feita por rin
"""

# Imports
import discord
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.checks import *
from program import db_manager

# Bloco de comandos 'moderation'
class Moderation(commands.Cog, name='moderation'):
    def __init__(self, bot):
        self.bot = bot
    
    # Manipula a lista de usuários na classe 'admins' da bot
    @commands.hybrid_command(
        name="admins",
        description="Manipula a lista de administradores")
    @app_commands.describe(action="A ação a ser feita")
    @app_commands.describe(user="O usuário a ser manipulado")
    @app_commands.choices(
        action=[
            Choice(name='adicionar', value=0),
            Choice(name='remover', value=1)])
    @not_blacklisted()
    @is_owner()
    async def admins(self, ctx: Context, action: Choice[int], user: discord.User = None) -> None:
        # Adiciona uma pessoa a classe admin
        if action.value == 0 and user is not None:
            user_id = user.id
            if await db_manager.is_admin(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** já está na lista de admins.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.add_user_to_admins(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** foi adicionado(a) com sucesso a lista de admins.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Remove uma pessoa da classe admins
        elif action.value == 1 and user is not None:
            user_id = user.id
            if not await db_manager.is_admin(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** não está na lista de admins.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.remove_user_from_admins(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** foi removido(a) com sucesso da lista de admins.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Ação inválida / usuário inválido
        else:
            embed = discord.Embed(
                title="Erro",
                description=f"Ação inválida ou usuário inválido",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Manipula a lista negra (quem não deve usar a bot) da bot
    @commands.hybrid_command(
        name="blacklist",
        description="Manipula a lista de usuários bloqueados")
    @app_commands.describe(action="A ação a ser feita")
    @app_commands.describe(user="O usuário a ser manipulado")
    @app_commands.choices(
        action=[
            Choice(name='mostrar', value=0),
            Choice(name='adicionar', value=1),
            Choice(name='remover', value=2)])
    @not_blacklisted()
    @is_admin()
    async def blacklist(self, ctx: Context, action: Choice[int], user: discord.User = None) -> None:
        # Mostra os usuários que estão na lista negra
        if action.value == 0:
            blacklisted_users = await db_manager.get_blacklisted_users()
            if len(blacklisted_users) == 0:
                embed = discord.Embed(
                    description="Não tem nenhum usuário na lista negra! Lesgo", color=0x9C84EF)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(title="Usuários bloqueados:", color=0x9C84EF)
            users = []
            for bluser in blacklisted_users:
                user = self.bot.get_user(int(bluser[0])) or await self.bot.fetch_user(
                    int(bluser[0]))
                users.append(f" • {user.mention} ({user}) - Blacklisted <t:{bluser[1]}>")
            embed.description = "\n".join(users)
            await ctx.send(embed=embed)
        
        # Adiciona um usuário na lista negra
        elif action.value == 1 and user is not None:
            user_id = user.id
            if await db_manager.is_blacklisted(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** já está na lista negra.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            total = await db_manager.add_user_to_blacklist(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** foi adicionado(a) com sucesso a lista negra",
                color=0x9C84EF)
            embed.set_footer(
                text=f"Tem {total} {'usuário(a)' if total == 1 else 'usuários(as)'} na lista negra.")
            await ctx.send(embed=embed)
        
        # Remove um usuário da list anegra
        elif action.value == 2 and user is not None:
            user_id = user.id
            if not await db_manager.is_blacklisted(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** não está na lista negra.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            total = await db_manager.remove_user_from_blacklist(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** foi removido(a) com sucesso da lista negra",
                color=0x9C84EF)
            embed.set_footer(
                text=f"Tem {total} {'usuário(a)' if total == 1 else 'usuários(as)'} na lista negra.")
            await ctx.send(embed=embed)
        
        # Ação inválida / usuário inválido
        else:
            embed = discord.Embed(
                title="Erro",
                description=f"Ação inválida ou usuário inválido",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Manipula / visualiza avisos dentro da base de dados
    @commands.hybrid_command(
        name='avisos',
        description='Manipula os avisos de um usuário')
    @app_commands.describe(action='A ação a ser feita')
    @app_commands.describe(user='O usuário a ser manipulado')
    @app_commands.describe(warn='O aviso em si')
    @app_commands.choices(
        action=[
            Choice(name='mostrar', value=0),
            Choice(name='adicionar', value=1),
            Choice(name='remover', value=2)])
    @not_blacklisted()
    @is_admin()
    async def warning(self, ctx: Context, action: Choice[int], user: discord.User = None, warn: str = None, warn_id: int = None) -> None:
        # Mostra os avisos de um usuário
        if action.value == 0 and user is not None:
            warnings_list = await db_manager.get_warnings(user.id, ctx.guild.id)
            embed = discord.Embed(title=f"Avisos de {user}", color=0x9C84EF)
            description = " ❌ Erro de leitura :c"
            if len(warnings_list) == 0:
                description = "Este usuário não tem avisos, YAY!"
            else:
                for warning in warnings_list:
                    description += f" • Avisado(a) por <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - ID do aviso #{warning[5]}\n"
            embed.description = description
            await ctx.send(embed=embed)
        
        # Adiciona um aviso a um usuário
        elif action.value == 1 and user != None and warn != None and warn != 0:
            member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(
                user.id)
            total = await db_manager.add_warn(
                user.id, ctx.guild.id, ctx.author.id, warn)
            embed = discord.Embed(
                description=f"**{member}** foi avisado(a) por **{ctx.author}**!\nAvisos totais do usuário: {total}",
                color=0x9C84EF,)
            embed.add_field(name="Aviso:", value=warn)
            await ctx.send(embed=embed)
            try:
                await member.send(
                    f"Você foi avisado(a) por **{ctx.author}** em **{ctx.guild.name}**!\nRazão: {warn}")
            except:
                await ctx.send(
                    f"{member.mention}, você foi avisado(a) por **{ctx.author}**!\nRazão: {warn}")
        
        # Remove o aviso de um usuário
        elif action.value == 2 and user is not None and warn_id is not None:
            member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(
                user.id)
            total = await db_manager.remove_warn(warn_id, user.id, ctx.guild.id)
            embed = discord.Embed(
                description=f"Removi o aviso **#{warn_id}** de **{member}**!\nAvisos totais do usuário: {total}",
                color=0x9C84EF,)
            await ctx.send(embed=embed)
        
        # Ação inválida / usuário inválido
        else:
            embed = discord.Embed(
                title="Erro",
                description=f"Ação inválida ou usuário inválido",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Apaga um determinado número de mensagens do canal
    @commands.hybrid_command(
        name='sensurar',
        description='Deleta um número de mensagens')
    
    # Verifica se a bot tem permissões de guilda pra manipular mensagens
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    
    @app_commands.describe(amount="O número de mensagens a serem deletadas")
    @not_blacklisted()
    @is_admin()
    async def sensor(self, ctx: Context, amount: int) -> None:
        embed = discord.Embed(
            description=f"Olha a sensura! {ctx.author} decidiu limpar {amount} mensagens!",
            color=0x9C84EF)
        await ctx.send(embed=embed)
        await ctx.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{ctx.author}** limpou **{amount}** mensagens!",
            color=0x9C84EF)
        await ctx.channel.send(embed=embed)
        embed = discord.Embed(
            description=f"Você limpou **{amount}** mensagens de **{ctx.channel.name}** em **{ctx.guild.name}**!",
            color=0x9C84EF)
        await ctx.author.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Moderation(bot))