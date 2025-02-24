import aiohttp
import json
import logging
from astrbot.api.all import AstrMessageEvent, CommandResult, Context, Plain
from astrbot.api.event.filter import filter
from astrbot.api.star import register, Star

logger = logging.getLogger("astrbot")

@register("astrbot_plugin_maoyan", "Soulter", "", "", "")
class Main(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.PLUGIN_NAME = "astrbot_plugin_maoyan"
        self.api_url = "https://api.pearktrue.cn/api/maoyan/"

    @filter.command("实时票房")
    async def get_real_time_box_office(self, message: AstrMessageEvent):
        '''获取猫眼电影实时票房排行'''
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url) as resp:
                if resp.status != 200:
                    return CommandResult().error("请求失败，无法获取实时票房信息")
                data = await resp.json()

        if data["code"] == 200:
            response_msg = "📊【猫眼电影实时票房排行】\n"
            for movie in data["data"][:5]:  # 这里只展示前五名
                response_msg += f"""🏆【{movie['top']}】{movie['movieName']}\n上映信息: {movie['releaseInfo']}\n总票房: {movie['sumBoxDesc']}\n票房占比: {movie['boxRate']}\n排场次数: {movie['showCount']}次\n排片占比: {movie['showCountRate']}\n场均人次: {movie['avgShowView']}\n上座率: {movie['avgSeatView']}\n\n"""
            
            return CommandResult().message(response_msg)
        else:
            return CommandResult().error(f"获取失败: {data['msg']}")

