import os
import re
 
from ncatbot.utils import get_log
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import (
    GroupMessage,
    PrivateMessage,
    BaseMessage,
    Image,
    At,
    MessageChain)

from .utils import get_top50_id, get_image

bot = CompatibleEnrollment  # 兼容回调函数注册器
_log = get_log(__name__)

proxy_url = 'http://pixivproxy.cyou'  

class PixivTool(BasePlugin):
    name = "PixivTool"  # 插件名称
    version = "0.0.1"  # 插件版本
    author = "Damverva"  # 插件作者
    info = "集成了一些pixiv功能"  # 插件描述
    # dependencies = {}  # 插件依赖，格式: {"插件名": "版本要求"}
    
    get_top_flag: bool = False # 是否正在获取
    
    async def on_load(self):
        _log.info("PixivTool loaded successfully.")
    
    
    @bot.group_event()
    async def parser(self, msg: GroupMessage):
        cmd: str = msg.message
        cmd: list[str] = cmd.split(' ')
        _log.info(f"cmd: {cmd}")
        match cmd[0]:
            # parser /pixiv and it's sub-commands
            case "/pixiv":
                await self.match_pixiv(cmd[1:], msg)
            
            # the another name of /pixiv get
            case "/pid":
                await self.parser_get(cmd[1:], msg)
        # parse the second word
    
    async def match_pixiv(self, cmd: list[str], msg: GroupMessage):
        if len(cmd) < 1:
            await msg.reply("请指定操作类型")
            return
        match cmd[0]:
            case "get":
                await self.parser_get(cmd[1:], msg)
            case "top":
                await self.parser_top(cmd[1:], msg)
        return
        
    
    async def parser_get(self, cmd: list[str], msg: GroupMessage):
        
        if len(cmd) < 1:
            await msg.reply("请指定图片ID")
            return
        
        cmd = cmd[0]
        # match pid like 12345678 or 12345678-1 or 12345678_p1
        if re.match(r"^\d*(-)?\d$", cmd) != None:
            pid: str = cmd    
        elif re.match(r"^\d*(_p)?\d$", cmd) != None:
            pid: str = cmd.split("_")[0] + "-" + cmd.split("p")[1]
        
        # if pid can't match, return
        else:
            await msg.reply("图片ID必须为数字")
            return
        
        await msg.reply("正在获取图片，请稍后....")
        
        _log.info(f'{proxy_url}/{pid}')
        
        image = await get_image(f'{proxy_url}/{pid}')
        
        # check image is valid
        if image is None:
            await msg.reply("图片获取失败")
            return
        
        await self.api.post_group_msg(
            group_id = msg.group_id,
            image = image,
            at = msg.sender.user_id,
        )
        
    async def parser_top(self, cmd: list[str], msg: GroupMessage):
        
        if len(cmd) < 1:
            await msg.reply("请指定图片数量")
            return
        
        cmd = cmd[0]
        if not cmd.isdigit():
            await msg.reply("图片数量必须为数字")
            return
        
        # 避免重复获取，造成服务器负担
        if self.get_top_flag:
            await msg.reply("正在获取，请稍后再试")
            return
        self.get_top_flag = True
        
        count = int(cmd)
        if count > 50:
            await msg.reply("太多啦，要溢出来了~")
            self.get_top_flag = False
            return
        
        top50: list[str] = await get_top50_id()
        if top50 is None:
            await msg.reply("获取失败")
            self.get_top_flag = False
            return
        
        await self.api.post_group_msg(
            group_id=msg.group_id,
            text="以下是今日Pixiv榜单图片：",
        )
        
        message = MessageChain(f"0-{count if count < 10 else 9}")
        is_dirty = True
        for count, i in enumerate(top50[:count]):
            
            # if message is dirty, send it
            is_dirty = True
            
            # append image to message
            img = await get_image(f"{proxy_url}/{i}")
            if img is None:
                message += MessageChain(f"获取图片[{i}]失败\n")
            else:
                message += MessageChain(img)
            
            # send message every 10 images
            if count % 10 == 9:
                await self.api.post_group_msg(
                    group_id=msg.group_id,
                    rtf=message,)
                message = MessageChain(f"{(count+1)}-{count+10 if count+10 < 49 else 49}\n")
                is_dirty = False
            
        # send the last message
        if is_dirty:
            await self.api.post_group_msg(
                group_id=msg.group_id,
                rtf=message,)
        
        self.get_top_flag = False
        return