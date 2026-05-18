from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import json

app = FastAPI()

# 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 换成智谱的完全免费模型 glm-4-flash
API_KEY = "0c353a5e3afe49829058b5c171424e25.ZSVDzFWxjBDc7NFL"  # 👈 贴在这里
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
MODEL_NAME = "glm-4-flash"
# ==========================================
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 定义前端传过来的数据格式
class DiaryInput(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "小阳的后台服务器运行正常，API 接口已就绪！"}

# 核心接口：接收日记，调用大模型，返回属性增减
@app.post("/api/settle")
def settle_attributes(diary: DiaryInput):
    # 核心系统提示词（Prompt Engineering）
    system_prompt = """
    你现在是《大学人生模拟器》的后台属性结算引擎。
    玩家会输入他今天做的事情，你需要根据常理，判断这些事情对玩家属性的增减（增减幅度在 -15 到 +15 之间）。
    
    【⚠️ 核心属性定义（必须严格遵守）】：
    1. 体力 (stamina)：代表玩家当天的“剩余精力”。跑步、熬夜、上课、打工等消耗体能的行为，体力必须是负数（扣分）！只有睡觉、吃饭、休息、摸鱼才能恢复体力（加分）。
    2. 智力 (intelligence)：代表学识。看书、上课、复习会加分；纯打游戏、发呆会扣分或不变。
    3. 心情 (mood)：娱乐、美食、社交顺利加分；吵架、挂科、被骂扣分。

    必须严格输出纯 JSON 格式，不要任何 Markdown 标记（如 ```json），不要解释。
    JSON 必须包含以下键：
    - "stamina_delta": 整数，体力变化
    - "intelligence_delta": 整数，智力变化
    - "mood_delta": 整数，心情变化
    - "summary": 字符串，用一句幽默且符合 RPG 风格的旁白总结玩家的一天（限20字内）
    """
    
    try:
        # 调用大模型
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": diary.text}
            ],
            # 强制要求返回 JSON 格式（大部分新模型支持）
            response_format={"type": "json_object"} 
        )
        
        # 获取大模型的文本回复
        result_str = response.choices[0].message.content
        
        # 将字符串解析为真正的 JSON (Python 字典)
        result_json = json.loads(result_str)
        return result_json
        
    except Exception as e:
        # 容错处理：如果大模型抽风了，返回一个保底数据，防止前端崩溃
        print(f"API调用报错: {e}")
        return {
            "stamina_delta": 0, 
            "intelligence_delta": 0, 
            "mood_delta": 0, 
            "summary": "服务器开小差了，当前行动未生效..."
        }