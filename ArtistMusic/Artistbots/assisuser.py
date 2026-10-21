# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Channel      : https://t.me/artistbots
# ==========================================================
#
# Plugin   : Assistant (userbot) join / leave
# Location : ArtistMusic/Artistbots/assisuser.py
#
#   /userbotjoin | /assistantjoin   - invite this group's assistant
#   /userbotleave                   - make the assistant leave this group
#   Also auto-approves the assistant's own join request in private groups.
#   (Prefixes: / and .  - group admins and sudoers only)
# ==========================================================

import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    ChatWriteForbidden,
    FloodWait,
    PeerIdInvalid,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import ChatJoinRequest, Message

from ArtistMusic import app, db

from ._common import esc, is_admin

PREFIXES = [".", "/"]
ACTIVE = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.RESTRICTED,
}


async def _assistant(chat_id: int):
    ub = await db.get_assistant(chat_id)
    me = ub.me or await ub.get_me()
    return ub, me


async def _in_chat(client, chat_id: int, user_id: int) -> bool:
    try:
        return (await client.get_chat_member(chat_id, user_id)).status in ACTIVE
    except Exception:
        return False


async def join_userbot(client, chat_id: int, chat_username: str | None = None) -> str:
    ub, me = await _assistant(chat_id)

    try:
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.BANNED:
            try:
                await client.unban_chat_member(chat_id, me.id)
            except ChatAdminRequired:
                return "<b>❌  ɪ ηєєᴅ υηʙᴧη ᴘєʀϻɪssɪση ᴛσ ᴧᴅᴅ ᴛʜє ᴧssɪsᴛᴧηᴛ.</b>"
        elif member.status in ACTIVE:
            return "<b>🤖  ᴧssɪsᴛᴧηᴛ ɪs ᴧʟʀєᴧᴅʏ ɪη ᴛʜє ᴄʜᴧᴛ.</b>"
    except UserNotParticipant:
        pass
    except PeerIdInvalid:
        # peer not cached yet - fall through and try to join anyway
        pass

    if chat_username:
        invite = chat_username if chat_username.startswith("@") else f"@{chat_username}"
    else:
        try:
            invite = (await client.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return "<b>❌  ɪ ηєєᴅ ɪηᴠɪᴛє-ʟɪηᴋ ᴘєʀϻɪssɪση (σʀ ᴧ ᴘυʙʟɪᴄ @username) ᴛσ ᴧᴅᴅ ᴛʜє ᴧssɪsᴛᴧηᴛ.</b>"

    try:
        await ub.join_chat(invite)
        return "<b>✅  ᴧssɪsᴛᴧηᴛ ᴊσɪηєᴅ sυᴄᴄєssғυʟʟʏ.</b>"
    except UserAlreadyParticipant:
        return "<b>🤖  ᴧssɪsᴛᴧηᴛ ɪs ᴧʟʀєᴧᴅʏ ᴧ ᴘᴧʀᴛɪᴄɪᴘᴧηᴛ.</b>"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await ub.join_chat(invite)
            return "<b>✅  ᴧssɪsᴛᴧηᴛ ᴊσɪηєᴅ sυᴄᴄєssғυʟʟʏ.</b>"
        except Exception as ex:
            return f"<b>❌  ғᴧɪʟєᴅ ᴛσ ᴧᴅᴅ ᴧssɪsᴛᴧηᴛ ᴧғᴛєʀ ᴡᴧɪᴛ:</b> <code>{esc(str(ex))}</code>"
    except Exception as e:
        return f"<b>❌  ғᴧɪʟєᴅ ᴛσ ᴧᴅᴅ ᴧssɪsᴛᴧηᴛ:</b> <code>{esc(str(e))}</code>"


@app.on_chat_join_request()
async def approve_assistant_request(client, req: ChatJoinRequest):
    """When the assistant requests to join a private group, approve it."""
    try:
        _, me = await _assistant(req.chat.id)
        if req.from_user.id != me.id:
            return
        if await _in_chat(client, req.chat.id, me.id):
            return
        try:
            await client.approve_chat_join_request(req.chat.id, me.id)
        except UserAlreadyParticipant:
            return
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await client.approve_chat_join_request(req.chat.id, me.id)
        try:
            await client.send_message(req.chat.id, "<b>✅  ᴧssɪsᴛᴧηᴛ ʜᴧs ʙєєη ᴧᴘᴘʀσᴠєᴅ ᴧηᴅ ᴊσɪηєᴅ ᴛʜє ᴄʜᴧᴛ.</b>")
        except ChatWriteForbidden:
            pass
    except Exception:
        return


@app.on_message(
    filters.command(["userbotjoin", "assistantjoin"], prefixes=PREFIXES)
    & filters.group
    & ~app.bl_users
)
async def join_group(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("<blockquote>🚫  <b>σηʟʏ ᴧᴅϻɪηs ᴄᴧη υsє ᴛʜɪs ᴄσϻϻᴧηᴅ.</b></blockquote>")

    status = await message.reply_text("<blockquote><b>⏳  ᴘʟєᴧsє ᴡᴧɪᴛ, ɪηᴠɪᴛɪηɢ ᴧssɪsᴛᴧηᴛ...</b></blockquote>")
    try:
        me = await client.get_chat_member(message.chat.id, app.id)
        if me.status != ChatMemberStatus.ADMINISTRATOR:
            return await status.edit_text("<blockquote><b>❌  ɪ ηєєᴅ ᴛσ ʙє ᴧᴅϻɪη ᴛσ ɪηᴠɪᴛє ᴛʜє ᴧssɪsᴛᴧηᴛ.</b></blockquote>")
    except ChatAdminRequired:
        return await status.edit_text("<blockquote><b>❌  ɪ ᴄᴧη'ᴛ ᴄʜєᴄᴋ ϻʏ ᴧᴅϻɪη sᴛᴧᴛυs ɪη ᴛʜɪs ᴄʜᴧᴛ.</b></blockquote>")
    except Exception as e:
        return await status.edit_text(f"<blockquote><b>❌  ғᴧɪʟєᴅ ᴛσ ᴠєʀɪғʏ ᴘєʀϻɪssɪσηs:</b> <code>{esc(str(e))}</code></blockquote>")

    reply = await join_userbot(client, message.chat.id, message.chat.username)
    try:
        await status.edit_text(reply)
    except ChatWriteForbidden:
        pass


@app.on_message(filters.command("userbotleave", prefixes=PREFIXES) & filters.group & ~app.bl_users)
async def leave_one(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("<blockquote>🚫  <b>σηʟʏ ᴧᴅϻɪηs ᴄᴧη υsє ᴛʜɪs ᴄσϻϻᴧηᴅ.</b></blockquote>")

    chat_id = message.chat.id
    try:
        ub, me = await _assistant(chat_id)
        try:
            member = await ub.get_chat_member(chat_id, me.id)
        except UserNotParticipant:
            return await message.reply_text("<blockquote><b>🤖  ᴧssɪsᴛᴧηᴛ ɪs ησᴛ ᴄυʀʀєηᴛʟʏ ɪη ᴛʜɪs ᴄʜᴧᴛ.</b></blockquote>")
        if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
            return await message.reply_text("<blockquote><b>🤖  ᴧssɪsᴛᴧηᴛ ɪs ησᴛ ᴄυʀʀєηᴛʟʏ ɪη ᴛʜɪs ᴄʜᴧᴛ.</b></blockquote>")

        await ub.leave_chat(chat_id)
        try:
            await client.send_message(chat_id, "<b>✅  ᴧssɪsᴛᴧηᴛ ʜᴧs ʟєғᴛ ᴛʜɪs ᴄʜᴧᴛ.</b>")
        except ChatWriteForbidden:
            pass
    except ChannelPrivate:
        await message.reply_text("<blockquote><b>❌  ᴛʜɪs ᴄʜᴧᴛ ɪs ησᴛ ᴧᴄᴄєssɪʙʟє σʀ ʜᴧs ʙєєη ᴅєʟєᴛєᴅ.</b></blockquote>")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text("<blockquote><b>ғʟσσᴅ ᴡᴧɪᴛ ʜɪᴛ - ᴘʟєᴧsє ᴛʀʏ ᴛʜє ᴄσϻϻᴧηᴅ ᴧɢᴧɪη.</b></blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote><b>❌  ғᴧɪʟєᴅ ᴛσ ʀєϻσᴠє ᴧssɪsᴛᴧηᴛ:</b> <code>{esc(str(e))}</code></blockquote>")
