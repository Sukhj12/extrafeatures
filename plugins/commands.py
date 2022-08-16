import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming & ~filters.edited)
async def start(client, message):
    if message.chat.type in ['group', 'supergroup']:
        buttons = [
            [
                InlineKeyboardButton('🔰 𝑂𝑊𝑁𝐸𝑅 🔰', url='https://t.me/Sukhmankaler')
            ],
            [
                InlineKeyboardButton('⭕ 𝐻𝐸𝐿𝑃 ⭕', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ]
            ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('✔️ 𝐴𝐷𝐷 𝑀𝐸 𝑇𝑂 𝑌𝑂𝑈𝑅 𝐺𝑅𝑂𝑈𝑃 ✔️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔰 𝐶𝐻𝐴𝑁𝑁𝐸𝐿 🔰', url='https://t.me/NewLatestMovieDirect'),
            InlineKeyboardButton('📛 𝑂𝑊𝑁𝐸𝑅 📛', url='https://t.me/Sukhmankaler')
            ],[
            InlineKeyboardButton('♂️ 𝐻𝐸𝐿𝑃 ♂️', callback_data='help'),
            InlineKeyboardButton('⚕️ 𝑀𝑌 𝐺𝑅𝑂𝑈𝑃 ⚕️', url='https://t.me/+7FcPo53Z7VZkZDM9'),   
            InlineKeyboardButton('♻️ 𝐴𝐵𝑂𝑈𝑇 ♻️', callback_data='about')
        ]]
        reply1 = await message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_video(
            video=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Forcesub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 𝐽𝑂𝐼𝑁 𝑈𝑃𝐷𝐴𝑇𝐸 𝐶𝐻𝐴𝑁𝑁𝐸𝐿", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
            	kk, file_id = message.command[1].split("_", 1)
            	pre = 'checksubp' if kk == 'filep' else 'checksub' 
            	btn.append([InlineKeyboardButton(" 🔄 Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(" 🔄 Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="markdown"
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('✔️ 𝐴𝐷𝐷 𝑀𝐸 𝑇𝑂 𝑌𝑂𝑈𝑅 𝐺𝑅𝑂𝑈𝑃 ✔️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔰 𝐶𝐻𝐴𝑁𝑁𝐸𝐿 🔰', url='https://t.me/NewLatestMovieDirect'),
            InlineKeyboardButton('📛 𝑂𝑊𝑁𝐸𝑅 📛', url='https://t.me/Sukhmankaler')
            ],[
            InlineKeyboardButton('♂️ 𝐻𝐸𝐿𝑃 ♂️', callback_data='help'),
            InlineKeyboardButton('⚕️ 𝑀𝑌 𝐺𝑅𝑂𝑈𝑃 ⚕️', url='https://t.me/+7FcPo53Z7VZkZDM9'),   
            InlineKeyboardButton('♻️ 𝐴𝐵𝑂𝑈𝑇 ♻️', callback_data='about')
        
import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming & ~filters.edited)
async def start(client, message):
    if message.chat.type in ['group', 'supergroup']:
        buttons = [
            [
                InlineKeyboardButton('🔰 𝑂𝑊𝑁𝐸𝑅 🔰', url='https://t.me/Sukhmankaler')
            ],
            [
                InlineKeyboardButton('⭕ 𝐻𝐸𝐿𝑃 ⭕', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ]
            ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('✔️ 𝐴𝐷𝐷 𝑀𝐸 𝑇𝑂 𝑌𝑂𝑈𝑅 𝐺𝑅𝑂𝑈𝑃 ✔️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔰 𝐶𝐻𝐴𝑁𝑁𝐸𝐿 🔰', url='https://t.me/NewLatestMovieDirect'),
            InlineKeyboardButton('📛 𝑂𝑊𝑁𝐸𝑅 📛', url='https://t.me/Sukhmankaler')
            ],[
            InlineKeyboardButton('♂️ 𝐻𝐸𝐿𝑃 ♂️', callback_data='help'),
            InlineKeyboardButton('⚕️ 𝑀𝑌 𝐺𝑅𝑂𝑈𝑃 ⚕️', url='https://t.me/+7FcPo53Z7VZkZDM9'),   
            InlineKeyboardButton('♻️ 𝐴𝐵𝑂𝑈𝑇 ♻️', callback_data='about')
        ]]
        reply1 = await message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_video(
            video=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Forcesub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 𝐽𝑂𝐼𝑁 𝑈𝑃𝐷𝐴𝑇𝐸 𝐶𝐻𝐴𝑁𝑁𝐸𝐿", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
            	kk, file_id = message.command[1].split("_", 1)
            	pre = 'checksubp' if kk == 'filep' else 'checksub' 
            	btn.append([InlineKeyboardButton(" 🔄 Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(" 🔄 Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="markdown"
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('✔️ 𝐴𝐷𝐷 𝑀𝐸 𝑇𝑂 𝑌𝑂𝑈𝑅 𝐺𝑅𝑂𝑈𝑃 ✔️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔰 𝐶𝐻𝐴𝑁𝑁𝐸𝐿 🔰', url='https://t.me/NewLatestMovieDirect'),
            InlineKeyboardButton('📛 𝑂𝑊𝑁𝐸𝑅 📛', url='https://t.me/Sukhmankaler')
            ],[
            InlineKeyboardButton('♂️ 𝐻𝐸𝐿𝑃 ♂️', callback_data='help'),
            InlineKeyboardButton('⚕️ 𝑀𝑌 𝐺𝑅𝑂𝑈𝑃 ⚕️', url='https://t.me/+7FcPo53Z7VZkZDM9'),   
            InlineKeyboardButton('♻️ 𝐴𝐵𝑂𝑈𝑇 ♻️', callback_data='about')
        ]]
        reply1 = await message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_video(
            Video=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("Please wait")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
