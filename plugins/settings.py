import asyncio 
import logging
from database import db
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    await message.delete()
    await message.reply_text(
        "<b>change your settings as your wish</b>",
        reply_markup=main_buttons()
    )
    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
    user_id = query.from_user.id
    logger.info(f"Callback received: {query.data}")
    i, type = query.data.split("#")
    buttons = [[InlineKeyboardButton('↩ Back', callback_data="settings#main")]]

    if type == "main":
        logger.info("Showing main settings menu")
        await query.message.edit_text(
            "<b>change your settings as your wish</b>",
            reply_markup=main_buttons())
       
    elif type == "bots":
        buttons = [] 
        bots = await db.get_bots(user_id)
        if bots:
            for _bot in bots:
                buttons.append([InlineKeyboardButton(_bot['name'],
                                callback_data=f"settings#editbot_{_bot['id']}")])
        buttons.append([InlineKeyboardButton('✚ Add Bot ✚', 
                        callback_data="settings#addbot")])
        buttons.append([InlineKeyboardButton('✚ Add User Bot ✚', 
                        callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('↩ Back', 
                        callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>My Bots</b></u>\n\n<b>You can manage your bots in here</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type == "addbot":
        await query.message.delete()
        bot_added = await CLIENT.add_bot(bot, query)
        if bot_added != True:
            return
        await query.message.reply_text(
            "<b>Bot token successfully added to db</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type == "adduserbot":
        await query.message.delete()
        user_added = await CLIENT.add_session(bot, query)
        if user_added != True:
            return
        await query.message.reply_text(
            "<b>Session successfully added to db</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
      
    elif type.startswith("editbot"):
        bot_id = type.split('_')[1]
        bots = await db.get_bots(user_id)
        bot = next((b for b in bots if str(b['id']) == bot_id), None)
        if not bot:
            await query.message.edit_text("Bot not found", reply_markup=InlineKeyboardMarkup(buttons))
            return
        TEXT = Translation.BOT_DETAILS if bot['is_bot'] else Translation.USER_DETAILS
        buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removebot_{bot_id}")
                  ],
                  [InlineKeyboardButton('↩ Back', callback_data="settings#bots")]]
        await query.message.edit_text(
            TEXT.format(bot['name'], bot['id'], bot['username']),
            reply_markup=InlineKeyboardMarkup(buttons))
                                             
    elif type.startswith("removebot"):
        bot_id = type.split('_')[1]
        await db.remove_bot(user_id, bot_id)
        await query.message.edit_text(
            "<b>Successfully removed bot</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
                                             
    elif type == "channels":
        buttons = []
        channels = await db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}",
                            callback_data=f"settings#editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add Channel ✚', 
                        callback_data="settings#addchannel")])
        buttons.append([InlineKeyboardButton('↩ Back', 
                        callback_data="settings#main")])
        await query.message.edit_text( 
            "<b><u>My Channels</b></u>\n\n<b>You can manage your target chats in here</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
   
    elif type == " Sinh

    elif type == "filters":
        logger.info(f"Opening filters menu for user {user_id}")
        try:
            markup = await filters_buttons(user_id)
            logger.info(f"Filters markup generated: {markup}")
            await query.message.edit_text(
                "<b><u>💠 CUSTOM FILTERS 💠</b></u>\n\n**configure the type of messages which you want forward**",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error in filters menu: {e}")
            await query.message.edit_text(f"Error opening filters: {e}")
  
    elif type == "nextfilters":
        await query.edit_message_reply_markup( 
            reply_markup=await next_filters_buttons(user_id))
   
    elif type.startswith("updatefilter"):
        logger.info(f"Updating filter: {type}")
        _, key, value = type.split('-')
        if key in ['poll', 'text', 'audio', 'voice', 'video', 'photo', 'document', 'animation', 'sticker']:
            current_filters = (await get_configs(user_id))['filters']
            current_filters[key] = not current_filters[key]
            await db.update_configs(user_id, {'filters': current_filters})
        else:
            new_value = False if value == "True" else True
            await update_configs(user_id, key, new_value)
        
        if key in ['poll', 'protect']:
            await query.edit_message_reply_markup(
                reply_markup=await next_filters_buttons(user_id))
        else:
            await query.edit_message_reply_markup(
                reply_markup=await filters_buttons(user_id))
   
    elif type.startswith("file_size"):
        settings = await get_configs(user_id)
        size = settings.get('file_size', 0)
        i, limit = size_limit(settings['size_limit'])
        await query.message.edit_text(
           f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
           reply_markup=size_button(size))
  
    elif type.startswith("update_size"):
        size = int(query.data.split('-')[1])
        if 0 < size > 2000:
            return await query.answer("size limit exceeded", show_alert=True)
        await update_configs(user_id, 'file_size', size)
        i, limit = size_limit((await get_configs(user_id))['size_limit'])
        await query.message.edit_text(
           f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
           reply_markup=size_button(size))
  
    elif type.startswith('update_limit'):
        i, limit, size = type.split('-')
        limit, sts = size_limit(limit)
        await update_configs(user_id, 'size_limit', limit) 
        await query.message.edit_text(
           f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {sts} `{size} MB` will forward</b>',
           reply_markup=size_button(int(size)))
      
    elif type == "add_extension":
        await query.message.delete() 
        ext = await bot.ask(user_id, text="**please send your extensions (seperete by space)**")
        if ext.text == '/cancel':
           return await ext.reply_text(
                      "<b>process canceled</b>",
                      reply_markup=InlineKeyboardMarkup(buttons))
        extensions = ext.text.split(" ")
        extension = (await get_configs(user_id))['extension']
        if extension:
            for extn in extensions:
                extension.append(extn)
        else:
            extension = extensions
        await update_configs(user_id, 'extension', extension)
        await ext.reply_text(
            f"**successfully updated**",
            reply_markup=InlineKeyboardMarkup(buttons))
      
    elif type == "get_extension":
        extensions = (await get_configs(user_id))['extension']
        btn = extract_btn(extensions)
        btn.append([InlineKeyboardButton('✚ ADD ✚', 'settings#add_extension')])
        btn.append([InlineKeyboardButton('Remove all', 'settings#rmve_all_extension')])
        btn.append([InlineKeyboardButton('↩ Back', 'settings#main')])
        await query.message.edit_text(
            text='<b><u>EXTENSIONS</u></b>\n\n**Files with these extiontions will not forward**',
            reply_markup=InlineKeyboardMarkup(btn))
  
    elif type == "rmve_all_extension":
        await update_configs(user_id, 'extension', None)
        await query.message.edit_text(text="**successfully deleted**",
                                       reply_markup=InlineKeyboardMarkup(buttons))
    elif type == "add_keyword":
        await query.message.delete()
        ask = await bot.ask(user_id, text="**please send the keywords (seperete by space)**")
        if ask.text == '/cancel':
           return await ask.reply_text(
                      "<b>process canceled</b>",
                      reply_markup=InlineKeyboardMarkup(buttons))
        keywords = ask.text.split(" ")
        keyword = (await get_configs(user_id))['keywords']
        if keyword:
            for word in keywords:
                keyword.append(word)
        else:
            keyword = keywords
        await update_configs(user_id, 'keywords', keyword)
        await ask.reply_text(
            f"**successfully updated**",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type == "get_keyword":
        keywords = (await get_configs(user_id))['keywords']
        btn = extract_btn(keywords)
        btn.append([InlineKeyboardButton('✚ ADD ✚', 'settings#add_keyword')])
        btn.append([InlineKeyboardButton('Remove all', 'settings#rmve_all_keyword')])
        btn.append([InlineKeyboardButton('↩ Back', 'settings#main')])
        await query.message.edit_text(
            text='<b><u>KEYWORDS</u></b>\n\n**File with these keywords in file name will forwad**',
            reply_markup=InlineKeyboardMarkup(btn))
      
    elif type == "rmve_all_keyword":
        await update_configs(user_id, 'keywords', None)
        await query.message.edit_text(text="**successfully deleted**",
                                       reply_markup=InlineKeyboardMarkup(buttons))
    elif type.startswith("alert"):
        alert = type.split('_')[1]
        await query.answer(alert, show_alert=True)
      
def main_buttons():
    buttons = [[
        InlineKeyboardButton('🤖 Bᴏᴛs',
                    callback_data='settings#bots'),
        InlineKeyboardButton('🏷 Cʜᴀɴɴᴇʟs',
                    callback_data='settings#channels')
        ],[
        InlineKeyboardButton('🖋️ Cᴀᴘᴛɪᴏɴ',
                    callback_data='settings#caption'),
        InlineKeyboardButton('🗃 MᴏɴɢᴏDB',
                    callback_data='settings#database')
        ],[
        InlineKeyboardButton('🕵‍♀ Fɪʟᴛᴇʀs 🕵‍♀',
                    callback_data='settings#filters'),
        InlineKeyboardButton('⏹ Bᴜᴛᴛᴏɴ',
                    callback_data='settings#button')
        ],[
        InlineKeyboardButton('Exᴛʀᴀ Sᴇᴛᴛɪɴɢs 🧪',
                    callback_data='settings#nextfilters')
        ],[      
        InlineKeyboardButton('⫷ Bᴀᴄᴋ', callback_data='back')
        ]]
    return InlineKeyboardMarkup(buttons)

def size_limit(limit):
    if str(limit) == "None":
        return None, ""
    elif str(limit) == "True":
        return True, "more than"
    else:
        return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
        for data in datas:
            if i >= 5:
                i = 0
            if i == 0:
                btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
                i += 1
                continue
            elif i > 0:
                btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
                i += 1
    return btn 

def size_button(size):
    buttons = [[
        InlineKeyboardButton('+',
                     callback_data=f'settings#update_limit-True-{size}'),
        InlineKeyboardButton('=',
                     callback_data=f'settings#update_limit-None-{size}'),
        InlineKeyboardButton('-',
                     callback_data=f'settings#update_limit-False-{size}')
        ],[
        InlineKeyboardButton('+1',
                     callback_data=f'settings#update_size-{size + 1}'),
        InlineKeyboardButton('-1',
                     callback_data=f'settings#update_size-{size - 1}')
        ],[
        InlineKeyboardButton('+5',
                     callback_data=f'settings#update_size-{size + 5}'),
        InlineKeyboardButton('-5',
                     callback_data=f'settings#update_size-{size - 5}')
        ],[
        InlineKeyboardButton('+10',
                     callback_data=f'settings#update_size-{size + 10}'),
        InlineKeyboardButton('-10',
                     callback_data=f'settings#update_size-{size - 10}')
        ],[
        InlineKeyboardButton('+50',
                     callback_data=f'settings#update_size-{size + 50}'),
        InlineKeyboardButton('-50',
                     callback_data=f'settings#update_size-{size - 50}')
        ],[
        InlineKeyboardButton('+100',
                     callback_data=f'settings#update_size-{size + 100}'),
        InlineKeyboardButton('-100',
                     callback_data=f'settings#update_size-{size - 100}')
        ],[
        InlineKeyboardButton('↩ Back',
                     callback_data="settings#main")
    ]]
    return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
    logger.info(f"Generating filters buttons for user {user_id}")
    filter = await get_configs(user_id)
    filters = filter.get('filters', {})
    forward_tag = filter.get('forward_tag', False)
    skip_bot_messages = filter.get('skip_bot_messages', False)
    duplicate = filter.get('duplicate', True)
    
    buttons = [[
        InlineKeyboardButton('🏷️ Forward tag',
                     callback_data=f'settings#updatefilter-forward_tag-{forward_tag}'),
        InlineKeyboardButton('✅' if forward_tag else '❌',
                     callback_data=f'settings#updatefilter-forward_tag-{forward_tag}')
        ],[
        InlineKeyboardButton('🤖 Bot Messages',
                     callback_data=f'settings#updatefilter-skip_bot_messages-{skip_bot_messages}'),
        InlineKeyboardButton('✅' if not skip_bot_messages else '❌',
                     callback_data=f'settings#updatefilter-skip_bot_messages-{skip_bot_messages}')
        ],[
        InlineKeyboardButton('🖍️ Texts',
                     callback_data=f'settings#updatefilter-text-{filters.get("text", True)}'),
        InlineKeyboardButton('✅' if filters.get('text', True) else '❌',
                     callback_data=f'settings#updatefilter-text-{filters.get("text", True)}')
        ],[
        InlineKeyboardButton('📁 Documents',
                     callback_data=f'settings#updatefilter-document-{filters.get("document", True)}'),
        InlineKeyboardButton('✅' if filters.get('document', True) else '❌',
                     callback_data=f'settings#updatefilter-document-{filters.get("document", True)}')
        ],[
        InlineKeyboardButton('🎞️ Videos',
                     callback_data=f'settings#updatefilter-video-{filters.get("video", True)}'),
        InlineKeyboardButton('✅' if filters.get('video', True) else '❌',
                     callback_data=f'settings#updatefilter-video-{filters.get("video", True)}')
        ],[
        InlineKeyboardButton('📷 Photos',
                     callback_data=f'settings#updatefilter-photo-{filters.get("photo", True)}'),
        InlineKeyboardButton('✅' if filters.get('photo', True) else '❌',
                     callback_data=f'settings#updatefilter-photo-{filters.get("photo", True)}')
        ],[
        InlineKeyboardButton('🎧 Audios',
                     callback_data=f'settings#updatefilter-audio-{filters.get("audio", True)}'),
        InlineKeyboardButton('✅' if filters.get('audio', True) else '❌',
                     callback_data=f'settings#updatefilter-audio-{filters.get("audio", True)}')
        ],[
        InlineKeyboardButton('🎤 Voices',
                     callback_data=f'settings#updatefilter-voice-{filters.get("voice", True)}'),
        InlineKeyboardButton('✅' if filters.get('voice', True) else '❌',
                     callback_data=f'settings#updatefilter-voice-{filters.get("voice", True)}')
        ],[
        InlineKeyboardButton('🎭 Animations',
                     callback_data=f'settings#updatefilter-animation-{filters.get("animation", True)}'),
        InlineKeyboardButton('✅' if filters.get('animation', True) else '❌',
                     callback_data=f'settings#updatefilter-animation-{filters.get("animation", True)}')
        ],[
        InlineKeyboardButton('🃏 Stickers',
                     callback_data=f'settings#updatefilter-sticker-{filters.get("sticker", True)}'),
        InlineKeyboardButton('✅' if filters.get('sticker', True) else '❌',
                     callback_data=f'settings#updatefilter-sticker-{filters.get("sticker", True)}')
        ],[
        InlineKeyboardButton('▶️ Skip duplicate',
                     callback_data=f'settings#updatefilter-duplicate-{duplicate}'),
        InlineKeyboardButton('✅' if duplicate else '❌',
                     callback_data=f'settings#updatefilter-duplicate-{duplicate}')
        ],[
        InlineKeyboardButton('⫷ back',
                     callback_data="settings#main")
        ]]
    return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
    filter = await get_configs(user_id)
    filters = filter.get('filters', {})
    buttons = [[
        InlineKeyboardButton('📊 Poll',
                     callback_data=f'settings#updatefilter-poll-{filters.get("poll", True)}'),
        InlineKeyboardButton('✅' if filters.get('poll', True) else '❌',
                     callback_data=f'settings#updatefilter-poll-{filters.get("poll", True)}')
        ],[
        InlineKeyboardButton('🔒 Secure message',
                     callback_data=f'settings#updatefilter-protect-{filter.get("protect", False)}'),
        InlineKeyboardButton('✅' if filter.get('protect', False) else '❌',
                     callback_data=f'settings#updatefilter-protect-{filter.get("protect", False)}')
        ],[
        InlineKeyboardButton('🛑 size limit',
                     callback_data='settings#file_size')
        ],[
        InlineKeyboardButton('💾 Extension',
                     callback_data='settings#get_extension')
        ],[
        InlineKeyboardButton('♦️ keywords ♦️',
                     callback_data='settings#get_keyword')
        ],[
        InlineKeyboardButton('⫷ back', 
                     callback_data="settings#main")
        ]]
    return InlineKeyboardMarkup(buttons)
