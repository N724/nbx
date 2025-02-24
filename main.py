import aiohttp
import json
import logging
from typing import Optional
from astrbot.api.all import AstrMessageEvent, CommandResult, Context, Plain
import astrbot.api.event.filter as filter
from astrbot.api.star import register, Star

logger = logging.getLogger("astrbot")

@register("maoyan_boxoffice", "Soulter", "猫眼实时票房插件", "1.0.0")
class MaoyanBoxOffice(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.api_url = "https://api.pearktrue.cn/api/maoyan/"

    async def fetch_data(self) -> Optional[dict]:
        """获取票房数据"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
                async with session.get(self.api_url) as resp:
                    if resp.status != 200:
                        logger.error(f"API请求失败: {resp.status}")
                        return None
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取数据异常: {str(e)}")
            return None

    def _format_boxoffice(self, amount: str) -> str:
        """格式化票房数据"""
        if '万' in amount:
            num = float(amount.replace('万', ''))
            if num >= 10000:
                return f"{num/10000:.2f}亿"
            return amount
        return amount

    @filter.command("票房排行")
    async def boxoffice_rank(self, event: AstrMessageEvent):
        '''获取实时票房排行榜'''
        # 发送等待提示
        yield CommandResult().message("🎬 正在抓取最新票房数据...")

        data = await self.fetch_data()
        if not data or data.get("code") != 200:
            yield CommandResult().error("📉 数据获取失败，请稍后重试~")
            return

        movies = json.loads(data["data"])[:5]  # 取前五名
        
        if not movies:
            yield CommandResult().message("🎥 今日影院静悄悄，暂无票房数据哦~")
            return

        # 构建消息内容
        msg = ["🐱【猫眼实时票房TOP5】🐱\n"]
        for movie in movies:
            formatted_box = self._format_boxoffice(movie["sumBoxDesc"])
            msg.append(
                f"🏆 第{movie['top']}名：{movie['movieName']}\n"
                f"💰 累计票房：{formatted_box}（{movie['boxRate']}）\n"
                f"🎫 排片占比：{movie['showCountRate']}\n"
                f"👥 上座率：{movie['avgSeatView']}\n"
                "🍿" + "━"*20
            )
        
        # 添加更新时间
        msg.append(f"\n⏰ 更新时间：{data['time'].split('.')[0]}")

        yield CommandResult().message("\n".join(msg)).use_t2i(False)
