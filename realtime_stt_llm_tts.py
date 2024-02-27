from RealtimeSTT import AudioToTextRecorder

from zhipuai import ZhipuAI

import logging, time, traceback, requests
from datetime import datetime

# 按键监听语音聊天板块
import keyboard
import threading
import signal
import os


from utils.chatgpt import Chatgpt

from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger
from utils.search_online import SEARCH_ONLINE
from utils.audio_player import AUDIO_PLAYER



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

def llm_and_tts(prompt):
    my_logger.info(f"【用户】：{prompt}")

    # 实例化
    client = ZhipuAI(api_key="") # 请填写您自己的APIKey

    response = client.chat.completions.create(
        model="glm-3-turbo",  # 填写需要调用的模型名称
        messages=[
            {"role": "system", "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的建议。"},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    tmp_content = ""

    for chunk in response:
        tmp_content += chunk.choices[0].delta.content
        if contains_chinese_punctuation(tmp_content):
            my_logger.info(f"【LLM】：{tmp_content}")
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

        # my_logger.info(chunk)
        if chunk.choices[0].finish_reason == "stop":
            my_logger.info("任务完成")
            return

def process_text(text):
    global recoding_to_content, recorder_content

    my_logger.info(f"【识别内容】：{text}")

    if input_type == "keyword":
        for drop_cmd in config.get("recorder", "drop_cmd"):
            if drop_cmd in text:
                my_logger.info(f'清空录音')

                recorder_content = ""

                return
                
        for start_cmd in config.get("recorder", "start_cmd"):
            if start_cmd in text:
                my_logger.info(f'开始记录录音')

                if not recoding_to_content:
                    recoding_to_content = True

                    return
            
        for stop_cmd in config.get("recorder", "stop_cmd"):
            if stop_cmd in text:
                my_logger.info("结束记录录音")

                if recorder_content == "":
                    return

                # logging.info(f"联网搜素内容：{recorder_content}")
                # data_list = search_online.google(recorder_content, 1)
                # logging.info(f"搜索结果：{data_list}")
                # summary_list = search_online.get_summary_list(data_list, 1)

                # summary_content = ""

                # for summary in summary_list:
                #     summary_content += summary

                # current_date = datetime.now().strftime("%Y年%m月%d日")
                # # prompt = f"""当前中国北京日期：{current_date}，请判断并提取内容中与"{summary_content}"有关的详细内容，必须保留细节，准确的时间线以及富有逻辑的排版！如果与时间、前因后果、上下文等有关内容不能忽略，不可以胡编乱造！"""

                # prompt = config.get("chatgpt", "prompt_template")
                # # 提前定义所有可能的关键字参数
                # format_args = {
                #     "current_date": current_date if current_date else "",
                #     "summary_content": summary_content if summary_content else "",
                #     "recorder_content": recorder_content if recorder_content else ""
                # }

                # # 一次性使用 .format 方法替换所有占位符
                # prompt = prompt.format(**format_args)

                # prompt = f'当前中国北京日期：{current_date}，根据以下数据进行总结并提供答案。如果问题与数据不相关，使用你的常规知识回答，不可以胡编乱造！。\n参考数据：{summary_content}\n问题：{recorder_content}'
                

                llm_and_tts(recorder_content)

                recorder_content = ""

                return
        
        for get_mouse_coordinate_cmd in config.get("recorder", "get_mouse_coordinate_cmd"):
            if get_mouse_coordinate_cmd in text:
                import pyautogui

                # 获取鼠标当前的 x 和 y 坐标
                x, y = pyautogui.position()
                my_logger.info(f'鼠标当前坐标：x={x}, y={y}')

                return

    if recoding_to_content == True:
        recorder_content += text
    else:
        if recorder_content == "":
            return 

"""
按键监听板块
"""

def on_key_press(event):
    global recoding_to_content, recorder_content

    # 按键CD
    current_time = time.time()
    if current_time - last_pressed < cooldown:
        return
    

    """
    触发按键部分的判断
    """
    trigger_key_lower = None
    stop_trigger_key_lower = None

    # trigger_key是字母, 整个小写
    if trigger_key.isalpha():
        trigger_key_lower = trigger_key.lower()

    # stop_trigger_key是字母, 整个小写
    if stop_trigger_key.isalpha():
        stop_trigger_key_lower = stop_trigger_key.lower()
    
    if trigger_key_lower:
        if event.name == trigger_key or event.name == trigger_key_lower:
            my_logger.info(f'检测到单击键盘 {event.name}，即将开始录音~')
            recoding_to_content = True
        elif event.name == stop_trigger_key or event.name == stop_trigger_key_lower:
            my_logger.info(f'检测到单击键盘 {event.name}，即将停止录音~')
            recoding_to_content = False

            llm_and_tts(recorder_content)

            recorder_content = ""

            return
        else:
            return
    else:
        if event.name == trigger_key:
            my_logger.info(f'检测到单击键盘 {event.name}，即将开始录音~')
            recoding_to_content = True
        elif event.name == stop_trigger_key:
            my_logger.info(f'检测到单击键盘 {event.name}，即将停止录音~')
            recoding_to_content = False
            
            llm_and_tts(recorder_content)

            recorder_content = ""

            return
        else:
            return



# 按键监听
def key_listener():
    # 注册按键按下事件的回调函数
    keyboard.on_press(on_key_press)

    try:
        # 进入监听状态，等待按键按下
        keyboard.wait()
    except KeyboardInterrupt:
        os._exit(0)




# 退出程序
def exit_handler(signum, frame):
    print("Received signal:", signum)


if __name__ == '__main__':
    input_type = "keyboard"

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    common = Common()

    # 日志文件路径
    log_path = "./log/log-" + common.get_bj_time(1) + ".txt"
    Configure_logger(log_path)

    my_logger = logging.getLogger("my_logger")
    my_logger.setLevel(logging.INFO)

    # 获取 httpx 库的日志记录器
    httpx_logger = logging.getLogger("httpx")
    # 设置 httpx 日志记录器的级别为 WARNING
    httpx_logger.setLevel(logging.WARNING)

    # 获取 faster_whisper 库的日志记录器
    faster_whisper_logger = logging.getLogger("faster_whisper")
    # 设置 faster_whisper 日志记录器的级别为 WARNING
    faster_whisper_logger.setLevel(logging.WARNING)


    # 存储录音的内容
    recorder_content = ""
    # 是否在记录文本状态
    recoding_to_content = False

    my_logger.info("初始化 RealtimeSTT...")

    config_path = "config.json"

    config = Config(config_path)

    my_logger.info("配置加载完成")

    recorder_config = {
        "input_device_index": int(config.get("recorder", "device_index")),
        "gpu_device_index": 0,
        "level": logging.WARNING,
        'spinner': False,
        'model': 'large-v2',
        'language': 'zh',
        'silero_sensitivity': 0.4,
        'webrtc_sensitivity': 2,
        'post_speech_silence_duration': 0.2,
        'min_length_of_recording': 0,
        'min_gap_between_recordings': 0,        
        # 'enable_realtime_transcription': True,
        # 'realtime_processing_pause': 0.2,
        # 'realtime_model_type': 'tiny',
        # 'on_realtime_transcription_update': text_detected, 
        #'on_realtime_transcription_stabilized': text_detected,
    }

    search_online = SEARCH_ONLINE()
    audio_player =  AUDIO_PLAYER(config.get("audio_player"))
    # chatgpt = Chatgpt(config.get("openai"), config.get("chatgpt"))
    # audio = Audio(config_path)

    recorder = AudioToTextRecorder(**recorder_config)

    my_logger.info("请说点什么吧")

    # 冷却时间 0.5 秒
    cooldown = 0.5 
    last_pressed = 0

    # 从配置文件中读取触发键的字符串配置
    trigger_key = config.get("talk", "trigger_key")
    stop_trigger_key = config.get("talk", "stop_trigger_key")

    if config.get("talk", "key_listener_enable"):
        my_logger.info(f'单击键盘 {trigger_key} 按键进行录音喵~ 由于其他任务还要启动，如果按键没有反应，请等待一段时间')

    # 创建并启动按键监听线程
    thread = threading.Thread(target=key_listener)
    thread.start()

    while True:
        text = recorder.text(process_text)

              
