import datetime
import json

import discord
import mysql.connector
from discord.ext import commands
import random
import sqlite3 as sl
from discord.ext.commands import BucketType

with open('config/config.json', 'r') as cjson:
    config = json.load(cjson)

bot = commands.Bot(command_prefix=['!', '/'])
bot.remove_command('help')

con = sl.connect(config["dbFile"])

cursor_lite = con.cursor()
cursor_lite.execute("""CREATE TABLE IF NOT EXISTS vouchers (
                            name text,
                            date timestamp
                        )""")
con.commit()

png = config["img"]


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=config["status"]))
    print("Bot enabled")


@bot.event
async def on_command_error(error, ctx):
    return


@bot.command(name='voucher')
@commands.cooldown(1, 3, BucketType.guild)
async def voucher(ctx, nick=None):
    await ctx.message.delete()
    if ctx.channel.id != 742072898503573566:
        return
    if nick is None:
        ret_str = config["commandUsage"]
        embed = discord.Embed(title=config["title"], color=0x1ae0a8)
        embed.set_thumbnail(url=png)
        embed.set_footer(text="⠀⠀₪⠀⠀" + ctx.message.author.display_name)
        embed.add_field(name=config["correctUsage"], value=ret_str)
        await ctx.send(embed=embed)
    else:
        cnx = mysql.connector.connect(user=config["user"],
                                      password=config["password"],
                                      database=config["db"],
                                      host=config["ip"])
        cursor = cnx.cursor()
        cursor.execute('SELECT UUID FROM `Players` WHERE UUID = %s', (nick,))
        user_exists = cursor.fetchall()
        if user_exists:
            sqlite_cursor = con.cursor()
            sql = "SELECT date FROM `vouchers` WHERE name='%s'" % nick
            in_db = sqlite_cursor.execute(sql)
            if in_db.fetchone() is None:
                sql = "INSERT INTO `vouchers` (name, date) values(?, ?)"
                data = [
                    (nick, datetime.datetime.now())
                ]
                with con:
                    sqlite_cursor.executemany(sql, data)
                    con.commit()
                    take_reward(nick, cursor, cnx)
                    ret_str = config["takeVoucher"]
                    embed = discord.Embed(title=config["title"], color=0x1ae0a8)
                    embed.set_thumbnail(url=png)
                    embed.set_footer(text="⠀⠀₪⠀⠀" + ctx.message.author.display_name)
                    embed.add_field(name=config["takeOnGames"], value=ret_str)
                    await ctx.send(embed=embed)
            else:
                sql = "SELECT date FROM `vouchers` WHERE name='%s'" % nick
                date = str(sqlite_cursor.execute(sql).fetchall()[0]) \
                    .replace("(", "") \
                    .replace(")", "") \
                    .replace(",", "").replace("'", "")
                compare_date = datetime.datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(
                    days=7)
                if compare_date < datetime.datetime.now():
                    sql = 'INSERT INTO `vouchers` (name, date) values(?, ?)'
                    data = [
                        (nick, datetime.datetime.now()),
                    ]
                    with con:
                        sqlite_cursor.executemany(sql, data)
                        con.commit()
                        take_reward(nick, cursor, cnx)
                        ret_str = config["takeVoucher"]
                        embed = discord.Embed(title=config["title"], color=0x1ae0a8)
                        embed.set_thumbnail(url=png)
                        embed.set_footer(text="⠀⠀₪⠀⠀" + ctx.message.author.display_name)
                        embed.add_field(name=config["takeOnGames"], value=ret_str)
                        await ctx.send(embed=embed)
                else:
                    if compare_date.minute < 10:
                        minutes = "0" + str(compare_date.minute)
                    else:
                        minutes = str(compare_date.minute)
                    ret_str = str("⏱ **" + str(compare_date.day) + "."
                                  + str(compare_date.month) + "** o godzinie **"
                                  + str(compare_date.hour) + ":"
                                  + minutes + "**")
                    embed = discord.Embed(title=config["title"], color=0x1ae0a8)
                    embed.set_thumbnail(url=png)
                    embed.set_footer(text="⠀⠀₪⠀⠀" + ctx.message.author.display_name)
                    embed.add_field(name=config["nextVoucher"], value=ret_str)
                    await ctx.send(embed=embed)
        else:
            ret_str = config["joinServer"]
            embed = discord.Embed(title=config["title"], color=0x1ae0a8)
            embed.set_thumbnail(
                url=png)
            embed.set_footer(text="⠀⠀₪⠀⠀" + ctx.message.author.display_name)
            embed.add_field(name=config["notInDB"], value=ret_str)
            await ctx.send(embed=embed)
        cnx.close()


def take_reward(nick, cursor, cnx):
    sql = "UPDATE Players SET REWARD = '%s' WHERE UUID = '%s'" % (str(random.randint(1, 5)), nick)
    cursor.execute(sql)
    cnx.commit()


bot.run(config["token"])
