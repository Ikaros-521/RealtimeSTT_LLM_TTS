from zhipuai import ZhipuAI
import requests
import traceback
import os, sys, logging

from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger
from utils.audio_player import AUDIO_PLAYER

if getattr(sys, 'frozen', False):
    # 当前是打包后的可执行文件
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
    file_relative_path = os.path.dirname(os.path.abspath(bundle_dir))
else:
    # 当前是源代码
    file_relative_path = os.path.dirname(os.path.abspath(__file__))
    
common = Common()

# 配置文件路径
config_path = os.path.join(file_relative_path, 'config.json')

# 日志文件路径
file_path = "./log/log-" + common.get_bj_time(1) + ".txt"
Configure_logger(file_path)

# 获取 httpx 库的日志记录器
httpx_logger = logging.getLogger("httpx")
# 设置 httpx 日志记录器的级别为 WARNING
httpx_logger.setLevel(logging.WARNING)

# 获取特定库的日志记录器
watchfiles_logger = logging.getLogger("watchfiles")
# 设置日志级别为WARNING或更高，以屏蔽INFO级别的日志消息
watchfiles_logger.setLevel(logging.WARNING)

logging.debug("配置文件路径=" + str(config_path))

# 实例化配置类
config = Config(config_path)

audio_player =  AUDIO_PLAYER(config.get("audio_player"))

# 实例化
client = ZhipuAI(api_key="") # 请填写您自己的APIKey

tmp_content = ""

def contains_chinese_punctuation(s):
    # 定义中文标点符号集合
    chinese_punctuation = "。、，；！？"
    # 检查字符串中是否有中文标点符号
    for char in s:
        if char in chinese_punctuation:
            return True
    return False



def gpt_sovits_api(data):
    try:
        logging.debug(f"data={data}")

        if data["type"] == "api":
            try:
                data_json = {
                    "refer_wav_path": data["ref_audio_path"],
                    "prompt_text": data["prompt_text"],
                    "prompt_language": data["prompt_language"],
                    "text": data["content"],
                    "text_language": data["language"]
                }

                response = requests.post(data["api_ip_port"], json=data_json, timeout=60)
                response.raise_for_status()  # 抛出HTTP错误

                file_name = 'gpt_sovits_' + common.get_bj_time(4) + '.wav'
                voice_tmp_path = common.get_new_audio_path(config.get("play_audio", "out_path"), file_name)

                with open(voice_tmp_path, 'wb') as f:
                    f.write(response.content)

                return voice_tmp_path
            except requests.RequestException as e:
                logging.error(traceback.format_exc())
                logging.error(f'gpt_sovits请求失败: {e}')
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(f'gpt_sovits未知错误: {e}')
        elif data["type"] == "webtts":
            try:
                params = {
                    key: value
                    for key, value in data["webtts"].items()
                    if value != ""
                    if key != "api_ip_port"
                }

                params["text"] = data["content"]

                response = requests.get(data["webtts"]["api_ip_port"], params=params, timeout=60)
                response.raise_for_status()  # 抛出HTTP错误

                file_name = 'gpt_sovits_' + common.get_bj_time(4) + '.wav'
                voice_tmp_path = common.get_new_audio_path(config.get("play_audio", "out_path"), file_name)

                with open(voice_tmp_path, 'wb') as f:
                    f.write(response.content)

                return voice_tmp_path
            except requests.RequestException as e:
                logging.error(traceback.format_exc())
                logging.error(f'gpt_sovits请求失败: {e}')
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(f'gpt_sovits未知错误: {e}')
    except Exception as e:
        logging.error(traceback.format_exc())

    
    return None

response = client.chat.completions.create(
    model="glm-3-turbo",  # 填写需要调用的模型名称
    messages=[
        {"role": "system", "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"},
        {"role": "user", "content": "你好"},
    ],
    stream=True,
)

for chunk in response:
    tmp_content += chunk.choices[0].delta.content
    if contains_chinese_punctuation(tmp_content):
        logging.info(tmp_content)
        # 进行tts合成
        data = {
            "type": config.get("gpt_sovits", "type"),
            "ws_ip_port": config.get("gpt_sovits", "ws_ip_port"),
            "api_ip_port": config.get("gpt_sovits", "api_ip_port"),
            "ref_audio_path": config.get("gpt_sovits", "ref_audio_path"),
            "prompt_text": config.get("gpt_sovits", "prompt_text"),
            "prompt_language": config.get("gpt_sovits", "prompt_language"),
            "language": config.get("gpt_sovits", "language"),
            "cut": config.get("gpt_sovits", "cut"),
            "webtts": config.get("gpt_sovits", "webtts"),
            "content": tmp_content
        }
        voice_tmp_path = gpt_sovits_api(data)
        # print(voice_tmp_path)

        data_json = {
            "type": data["type"],
            "voice_path": voice_tmp_path,
            "content": data["content"],
            "random_speed": {
                "enable": False,
                "max": 1.3,
                "min": 0.8
            },
            "speed": 1
        }
        audio_player.play(data_json)

        # 清空
        tmp_content = ""

    # logging.info(chunk)
    if chunk.choices[0].finish_reason == "stop":
        logging.info("任务完成")