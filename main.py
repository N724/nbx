import aiohttp
import json
import logging
from typing import Optional
from astrbot.api.all import AstrMessageEvent, CommandResult, Context, Plain
import astrbot.api.event.filter as filter
from astrbot.api.star import register, Star

logger = logging.getLogger("astrbot")

@register("weather_query", "Soulter", "多版本天气查询插件", "1.0.0")
class WeatherQuery(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.api_url = "https://xiaoapi.cn/API/zs_tq.php"
        self.timeout = aiohttp.ClientTimeout(total=15)  # 15秒超时

    async def fetch_weather(self, city: str, source: str = "baidu", num: Optional[str] = None, n: Optional[str] = None) -> Optional[dict]:
        """获取天气数据（包含增强的错误处理）"""
        try:
            params = {
                "type": source,
                "msg": city,
                "num": num,
                "n": n
            }
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.api_url, params=params) as resp:
                    # 记录原始响应文本
                    raw_text = await resp.text()
                    logger.debug(f"API原始响应: {raw_text[:200]}...")  # 截断前200字符

                    # 先检查HTTP状态码
                    if resp.status != 200:
                        logger.error(f"API请求失败 HTTP {resp.status}")
                        return None
                    
                    # 尝试解析JSON
                    try:
                        data = await resp.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {str(e)}")
                        return None
                    
                    return data

        except aiohttp.ClientError as e:
            logger.error(f"网络请求异常: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"未知异常: {str(e)}", exc_info=True)
            return None

    @filter.command("天气查询")
    async def query_weather(self, event: AstrMessageEvent):
        '''获取指定城市的天气信息'''
        try:
            # 解析用户输入
            args = event.get_args()
            if not args:
                yield CommandResult().message("🌍 请告诉我你想查询哪个城市的天气哦~ 例如：天气查询 北京")
                return

            city = args[0]
            source = args[1] if len(args) > 1 else "baidu"  # 默认使用百度天气

            # 发送等待提示
            yield CommandResult().message(f"⏳ 正在从{source}获取{city}的天气数据，请稍等...")

            # 获取数据
            data = await self.fetch_weather(city, source)
            if not data:
                yield CommandResult().error("📡 连接天气数据中心失败，请稍后重试~")
                return

            # 检查状态码
            if data.get("code") != 200:
                logger.error(f"API返回错误状态码: {data.get('msg')}")
                yield CommandResult().error(f"📉 天气数据获取失败：{data.get('msg', '未知错误')}")
                return

            # 构建消息内容
            msg = [
                f"🌤️【{data.get('name', '未知地区')} 天气信息】🌤️\n",
                data.get("data", "暂无详细天气数据"),
                "\n\n💡 生活指数：" if "shzs" in data else "",
                data.get("shzs", "暂无生活指数信息"),
                f"\n\n🔗 数据来源：{source}天气"
            ]

            # 发送结果
            yield CommandResult().message("".join(msg)).use_t2i(False)

        except Exception as e:
            logger.error(f"处理指令异常: {str(e)}", exc_info=True)
            yield CommandResult().error("🌦️ 系统开小差了，请稍后再试~")
