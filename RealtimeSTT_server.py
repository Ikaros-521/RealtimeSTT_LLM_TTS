from RealtimeSTT import AudioToTextRecorder
import asyncio
import websockets
import threading
import numpy as np
from scipy.signal import resample
import json
import sys, os, logging, traceback
import requests
from zhipuai import ZhipuAI

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
        my_logger.debug(f"data={data}")

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
                my_logger.error(traceback.format_exc())
                my_logger.error(f'gpt_sovits请求失败: {e}')
            except Exception as e:
                my_logger.error(traceback.format_exc())
                my_logger.error(f'gpt_sovits未知错误: {e}')
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
                my_logger.error(traceback.format_exc())
                my_logger.error(f'gpt_sovits请求失败: {e}')
            except Exception as e:
                my_logger.error(traceback.format_exc())
                my_logger.error(f'gpt_sovits未知错误: {e}')
    except Exception as e:
        my_logger.error(traceback.format_exc())

    
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
        
if __name__ == '__main__':
    common = Common()

    if getattr(sys, 'frozen', False):
        # 当前是打包后的可执行文件
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
        file_relative_path = os.path.dirname(os.path.abspath(bundle_dir))
    else:
        # 当前是源代码
        file_relative_path = os.path.dirname(os.path.abspath(__file__))

    # my_logger.info(file_relative_path)

    # 初始化文件夹
    def init_dir():
        # 创建日志文件夹
        log_dir = os.path.join(file_relative_path, 'log')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建音频输出文件夹
        audio_out_dir = os.path.join(file_relative_path, 'out')
        if not os.path.exists(audio_out_dir):
            os.makedirs(audio_out_dir)
            
        # # 创建配置文件夹
        # config_dir = os.path.join(file_relative_path, 'config')
        # if not os.path.exists(config_dir):
        #     os.makedirs(config_dir)

    init_dir()

    # 配置文件路径
    config_path = os.path.join(file_relative_path, 'config.json')

    # 日志文件路径
    file_path = "./log/log-" + common.get_bj_time(1) + ".txt"
    Configure_logger(file_path)

    my_logger = logging.getLogger("my_logger")
    my_logger.setLevel(logging.INFO)

    # 获取 httpx 库的日志记录器
    httpx_logger = logging.getLogger("httpx")
    # 设置 httpx 日志记录器的级别为 WARNING
    httpx_logger.setLevel(logging.WARNING)

    # 获取特定库的日志记录器
    watchfiles_logger = logging.getLogger("watchfiles")
    # 设置日志级别为WARNING或更高，以屏蔽INFO级别的日志消息
    watchfiles_logger.setLevel(logging.WARNING)

    my_logger.info("启动服务中，请稍后...")

    my_logger.debug("配置文件路径=" + str(config_path))

    # 实例化配置类
    config = Config(config_path)

    my_logger.info("配置加载完毕")

    search_online = SEARCH_ONLINE()
    audio_player =  AUDIO_PLAYER(config.get("audio_player"))

    

    # 存储录音的内容
    recorder_content = ""
    # 是否在记录文本状态
    recoding_to_content = False

    recorder = None
    recorder_ready = threading.Event()
    client_websocket = None

    async def send_to_client(message):
        if client_websocket:
            await client_websocket.send(message)

    def text_detected(text):
        asyncio.new_event_loop().run_until_complete(
            send_to_client(
                json.dumps({
                    'type': 'realtime',
                    'text': text
                })
            )
        )
        # print(f"\r{text}", flush=True, end='')

        # my_logger.info(f"【返回内容】：{text}")

    recorder_config = {
        'spinner': False,
        'use_microphone': False,
        'model': 'large-v2',
        'language': 'zh',
        'silero_sensitivity': 0.4,
        'webrtc_sensitivity': 2,
        'post_speech_silence_duration': 0.7,
        'min_length_of_recording': 0,
        'min_gap_between_recordings': 0,
        'enable_realtime_transcription': True,
        'realtime_processing_pause': 0,
        'realtime_model_type': 'tiny',
        'on_realtime_transcription_stabilized': text_detected,
    }

    

    def recorder_thread():
        global recorder, recoding_to_content, recorder_content, file_path

        Configure_logger(file_path)
        my_logger = logging.getLogger("my_logger")
        my_logger.setLevel(logging.INFO)

        my_logger.info("Initializing RealtimeSTT...")
        recorder = AudioToTextRecorder(**recorder_config)
        my_logger.info("RealtimeSTT initialized")

        my_logger.setLevel(logging.INFO)

        # 获取特定库的日志记录器
        faster_whisper_logger = logging.getLogger("faster_whisper")
        # 设置日志级别为WARNING或更高，以屏蔽INFO级别的日志消息
        faster_whisper_logger.setLevel(logging.WARNING)

        audio_recorder_logger = logging.getLogger("audio_recorder")
        audio_recorder_logger.setLevel(logging.WARNING)

        recorder_ready.set()
        while True:
            full_sentence = recorder.text()
            asyncio.new_event_loop().run_until_complete(
                send_to_client(
                    json.dumps({
                        'type': 'fullSentence',
                        'text': full_sentence
                    })
                )
            )
            # print(f"\r识别内容: {full_sentence}")

            my_logger.info(f"【识别内容】：{full_sentence}")

            input_type = "keyword"

            if input_type == "keyword":
                for drop_cmd in config.get("recorder", "drop_cmd"):
                    if drop_cmd in full_sentence:
                        my_logger.info(f'清空录音')

                        recorder_content = ""

                        break
                        
                for start_cmd in config.get("recorder", "start_cmd"):
                    if start_cmd in full_sentence:
                        my_logger.info(f'开始记录录音')

                        if not recoding_to_content:
                            recoding_to_content = True

                            break
                    
                for stop_cmd in config.get("recorder", "stop_cmd"):
                    if stop_cmd in full_sentence:
                        my_logger.info("结束记录录音")

                        if recorder_content == "":
                            break

                        # my_logger.info(f"联网搜素内容：{recorder_content}")
                        # data_list = search_online.google(recorder_content, 1)
                        # my_logger.info(f"搜索结果：{data_list}")
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

                        break

                if recoding_to_content == True:
                    recorder_content += full_sentence

    def decode_and_resample(
            audio_data,
            original_sample_rate,
            target_sample_rate):

        # Decode 16-bit PCM data to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate the number of samples after resampling
        num_original_samples = len(audio_np)
        num_target_samples = int(num_original_samples * target_sample_rate /
                                 original_sample_rate)

        # Resample the audio
        resampled_audio = resample(audio_np, num_target_samples)

        return resampled_audio.astype(np.int16).tobytes()

    async def echo(websocket, path):
        print("Client connected")
        global client_websocket
        client_websocket = websocket
        async for message in websocket:

            if not recorder_ready.is_set():
                print("Recorder not ready")
                continue

            metadata_length = int.from_bytes(message[:4], byteorder='little')
            metadata_json = message[4:4+metadata_length].decode('utf-8')
            metadata = json.loads(metadata_json)
            sample_rate = metadata['sampleRate']
            chunk = message[4+metadata_length:]
            resampled_chunk = decode_and_resample(chunk, sample_rate, 16000)
            recorder.feed_audio(resampled_chunk)

    start_server = websockets.serve(echo, "localhost", 9001)

    recorder_thread = threading.Thread(target=recorder_thread)
    recorder_thread.start()
    recorder_ready.wait()

    print("Server started. Press Ctrl+C to stop the server.")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
