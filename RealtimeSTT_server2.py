from RealtimeSTT import AudioToTextRecorder
import asyncio, aiohttp
import websockets
import threading
import numpy as np
from scipy.signal import resample
import json
import sys, os, logging, traceback, base64
import requests
from collections import defaultdict
from zhipuai import ZhipuAI

from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger

from utils.search_online import SEARCH_ONLINE
from utils.audio_player import AUDIO_PLAYER

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

# 为每个客户端连接创建一个消息队列
text_message_queues = defaultdict(asyncio.Queue)
audio_message_queues = defaultdict(asyncio.Queue)

# 客户端列表
text_clients = {}
audio_clients = {}
client_threads = {}

my_clients = []

def generate_unique_client_id():
    import uuid
    
    return str(uuid.uuid4())


def contains_chinese_punctuation(s):
    # 定义中文标点符号集合
    chinese_punctuation = "。、，；！？"
    # 检查字符串中是否有中文标点符号
    for char in s:
        if char in chinese_punctuation:
            return True
    return False

async def download_audio(self, type: str, file_url: str, timeout: int=30, request_type: str="get", data=None, json_data=None):
    async with aiohttp.ClientSession() as session:
        try:
            if request_type == "get":
                async with session.get(file_url, params=data, timeout=timeout) as response:
                    if response.status == 200:
                        content = await response.read()
                        file_name = type + '_' + common.get_bj_time(4) + '.wav'
                        voice_tmp_path = common.get_new_audio_path(config.get("play_audio", "out_path"), file_name)
                        with open(voice_tmp_path, 'wb') as file:
                            file.write(content)
                        return voice_tmp_path
                    else:
                        logging.error(f'{type} 下载音频失败: {response.status}')
                        return None
            else:
                async with session.post(file_url, data=data, json=json_data, timeout=timeout) as response:
                    if response.status == 200:
                        content = await response.read()
                        file_name = type + '_' + common.get_bj_time(4) + '.wav'
                        voice_tmp_path = common.get_new_audio_path(config.get("play_audio", "out_path"), file_name)
                        with open(voice_tmp_path, 'wb') as file:
                            file.write(content)
                        return voice_tmp_path
                    else:
                        logging.error(f'{type} 下载音频失败: {response.status}')
                        return None
        except asyncio.TimeoutError:
            logging.error("{type} 下载音频超时")
            return None

# 请求Edge-TTS接口获取合成后的音频路径
async def edge_tts_api(data):
    import edge_tts

    try:
        file_name = 'edge_tts_' + common.get_bj_time(4) + '.mp3'
        voice_tmp_path = common.get_new_audio_path(config.get("play_audio", "out_path"), file_name)
        # voice_tmp_path = './out/' + common.get_bj_time(4) + '.mp3'
        # 过滤" '字符
        data["content"] = data["content"].replace('"', '').replace("'", '')
        # 使用 Edge TTS 生成回复消息的语音文件
        communicate = edge_tts.Communicate(text=data["content"], voice=data["voice"], rate=data["rate"], volume=data["volume"])
        await communicate.save(voice_tmp_path)

        return voice_tmp_path
    except Exception as e:
        my_logger.error(traceback.format_exc())
        my_logger.error(e)
        return None

async def gpt_sovits_api(data):
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
        elif data["type"] == "api_0322":
            try:

                data_json = {
                    "text": data["content"],
                    "text_lang": data["api_0322"]["text_lang"],
                    "ref_audio_path": data["api_0322"]["ref_audio_path"],
                    "prompt_text": data["api_0322"]["prompt_text"],
                    "prompt_lang": data["api_0322"]["prompt_lang"],
                    "top_k": data["api_0322"]["top_k"],
                    "top_p": data["api_0322"]["top_p"],
                    "temperature": data["api_0322"]["temperature"],
                    "text_split_method": data["api_0322"]["text_split_method"],
                    "batch_size":int(data["api_0322"]["batch_size"]),
                    "speed_factor":float(data["api_0322"]["speed_factor"]),
                    "split_bucket":data["api_0322"]["split_bucket"],
                    "return_fragment":data["api_0322"]["return_fragment"],
                    "fragment_interval":data["api_0322"]["fragment_interval"],
                }
                                    
                return await download_audio("gpt_sovits", data["api_ip_port"], 60, "post", None, data_json)
            except aiohttp.ClientError as e:
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

async def llm_and_tts(client_id, prompt, client_type="text"):
    try:
        async def tts_handle(tmp_content):
            if contains_chinese_punctuation(tmp_content):
                my_logger.info(f"【LLM】：{tmp_content}")

                voice_tmp_path = None

                if config.get("audio_synthesis_type") == "gpt_sovits":
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
                    voice_tmp_path = await gpt_sovits_api(data)
                    # print(voice_tmp_path)
                elif config.get("audio_synthesis_type") == "edge-tts":
                    data = {
                        "type": config.get("audio_synthesis_type"),
                        "voice": "zh-CN-XiaoyiNeural",
                        "rate": "+0%",
                        "volume": "+0%",
                        "content": tmp_content
                    }
                    voice_tmp_path = await edge_tts_api(data)

                if voice_tmp_path is not None:
                    my_logger.info(f"【TTS】音频合成完毕，输出在：{voice_tmp_path}")

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
                    # audio_player.play(data_json)

                    await send_to_client(
                        client_id,
                        json.dumps({
                            'type': 'fullSentence',
                            'text': data["content"]
                        }),
                        client_type
                    )
                    await send_audio_to_client(client_id, voice_tmp_path)

                    return True
            return False
                
        my_logger.info(f"【用户】：{prompt}")

        response = None
        tmp_content = ""

        if config.get("chat_type") == "zhipu":
            # 实例化
            client = ZhipuAI(api_key=config.get("zhipu", "api_key")) # 请填写您自己的APIKey

            response = client.chat.completions.create(
                model=config.get("zhipu", "model"),  # 填写需要调用的模型名称
                messages=[
                    {"role": "system", "content": config.get("zhipu", "system")},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            for chunk in response:
                tmp_content += chunk.choices[0].delta.content
                ret = await tts_handle(tmp_content)
                if ret:
                    # 清空文本
                    tmp_content = ""

                # my_logger.info(chunk)
                if chunk.choices[0].finish_reason == "stop":
                    my_logger.info("任务完成")
                    return None
        elif config.get("chat_type") == "chatgpt":
            import openai
            from packaging import version

            # 判断openai库版本，1.x.x和0.x.x有破坏性更新
            if version.parse(openai.__version__) < version.parse('1.0.0'):
                openai.api_base = config.get("openai", "api")
                openai.api_key = config.get("openai", "api_key")[0]

                response = openai.ChatCompletion.create(
                    model=config.get("chatgpt", "model"),
                    messages=[
                        {"role": "system", "content": config.get("zhipu", "preset")},
                        {"role": "user", "content": prompt},
                    ],
                    top_p=config.get("chatgpt", "top_p"),
                    temperature=config.get("chatgpt", "temperature"),
                    presence_penalty=config.get("chatgpt", "presence_penalty"),
                    frequency_penalty=config.get("chatgpt", "frequency_penalty"),
                    stream=True,
                )
            else:
                my_logger.debug(f"base_url={openai.api_base}, api_key={openai.api_key}")

                client = openai.OpenAI(base_url=openai.api_base, api_key=openai.api_key)

                # 调用 ChatGPT 接口生成回复消息
                response = client.chat.completions.create(
                    model=config.get("chatgpt", "model"),
                    messages=[
                        {"role": "system", "content": config.get("zhipu", "preset")},
                        {"role": "user", "content": prompt},
                    ],
                    top_p=config.get("chatgpt", "top_p"),
                    temperature=config.get("chatgpt", "temperature"),
                    presence_penalty=config.get("chatgpt", "presence_penalty"),
                    frequency_penalty=config.get("chatgpt", "frequency_penalty"),
                    stream=True,
                )


            for chunk in response:
                tmp_content += chunk.choices[0].delta.content
                ret = await tts_handle(tmp_content)
                if ret:
                    # 清空文本
                    tmp_content = ""

                # my_logger.info(chunk)
                if chunk.choices[0].finish_reason == "stop":
                    my_logger.info("任务完成")
                    return None
    except Exception as e:
        my_logger.error(traceback.format_exc())
        return None
        
if __name__ == '__main__':

    def find_audio_id_by_text_id(mapping_list, text_client_id):
        for mapping in mapping_list:
            if mapping.get('text_id') == text_client_id:
                return mapping.get('audio_id')
        return None  # 如果没有找到匹配的text_id，返回None

    async def send_to_client(client_id, message, client_type="text"):
        try:
            my_logger.debug(f"client_id={client_id}, client_type={client_type}")

            if client_type == "text":
                if client_id in text_clients:
                    my_logger.debug("存在对应的文本客户端，即将发送文本数据")
                    await text_clients[client_id].send(message)
                else:
                    my_logger.debug("不存在对应的文本客户端")
            else:
                if client_id in audio_clients:
                    my_logger.debug("存在对应的音频客户端，即将发送音频数据")
                    await audio_clients[client_id].send(message)
                else:
                    my_logger.debug("不存在对应的音频客户端")
        except Exception as e:
            my_logger.error(f"发送消息到客户端失败：{str(e)}")

    async def send_audio_to_client(client_id, audio_file_path):
        # 从文件扩展名中提取音频格式
        _, audio_extension = os.path.splitext(audio_file_path)
        audio_format = audio_extension.lstrip('.')  # 移除点，获取格式如"mp3"

        # 读取音频文件内容
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # 将音频数据编码为Base64字符串
        audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')

        # 创建包含音频数据和格式的消息
        message = json.dumps({'type': 'audio', 'audioData': audio_data_base64, 'format': audio_format})

        client_id = find_audio_id_by_text_id(my_clients, client_id)

        if client_id:
            # 通过WebSocket发送消息
            await send_to_client(client_id, message, client_type="audio")


    # 处理 WebSocket 消息的异步协程函数
    async def client_thread(client_id, websocket, client_type):
        try:
            my_logger.debug(f"client_id={client_id}, websocket={websocket}, client_type={client_type}")
        
            while True:
                # 使用 await websocket.recv() 显式等待接收消息
                message = await text_clients[client_id].recv()
                print(f"Received message from {client_id}: {message}")

                
                if client_type == "text":
                    try:
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

                        # 处理完成后将结果发送回对应客户端
                        # result = process_audio(resampled_chunk)
                        # await send_to_client(client_id, "result", client_type="text")
                    except Exception as e:
                        my_logger.error(f"Error handling text client: {e}")

                elif client_type == "audio":
                    try:
                        print(message)
                        # 处理音频数据
                        # result = process_audio(message)
                        # # 将结果发送回对应客户端
                        # await send_to_client(client_id, result, client_type="audio")
                    except Exception as e:
                        my_logger.error(f"Error handling text client: {e}")
        except Exception as e:
            my_logger.error(f"Error handling client: {e}")
        finally:
            # 如果 WebSocket 连接已关闭，它会执行一些清理工作，例如从相关字典中删除客户端信息，并从线程字典中删除当前线程的信息。
            if websocket.closed:
                if client_type == "text" and client_id in text_clients:
                    del text_clients[client_id]
                elif client_type == "audio" and client_id in audio_clients:
                    del audio_clients[client_id]
                if client_id in client_threads:
                    del client_threads[client_id]


    # 每个客户端连接创建的新线程的入口点。这个函数负责设置和管理每个线程的异步事件循环
    def thread_target(client_id, websocket, client_type):
        # 创建一个新的异步事件循环
        loop = asyncio.new_event_loop()
        # 设置当前线程的事件循环
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client_thread(client_id, websocket, client_type))
        loop.close()


    async def text_process_message_queue(client_id):
        try:
            while True:
                message = await text_message_queues[client_id].get()
                
                # 处理消息
                # print(f"text Processing message from {client_id}: {message}")
                if not recorder_ready.is_set():
                    # print("Recorder not ready")
                    continue

                metadata_length = int.from_bytes(message[:4], byteorder='little')
                metadata_json = message[4:4+metadata_length].decode('utf-8')
                metadata = json.loads(metadata_json)
                sample_rate = metadata['sampleRate']
                chunk = message[4+metadata_length:]
                resampled_chunk = decode_and_resample(chunk, sample_rate, 16000)
                recorder.feed_audio(resampled_chunk)
        except asyncio.CancelledError:
            print(f"客户端 text {client_id} 的任务被取消")
            raise  # 可以重新抛出异常，也可以进行清理操作
        except Exception as e:
            my_logger.error(f"Error processing message: {e}")

    async def audio_process_message_queue(client_id):
        try:
            while True:
                message = await audio_message_queues[client_id].get()
                
                # 处理消息
                my_logger.info(f"audio Processing message from {client_id}: {message}")
        except asyncio.CancelledError:
            print(f"客户端 audio {client_id} 的任务被取消")
            raise  # 可以重新抛出异常，也可以进行清理操作
        except Exception as e:
            my_logger.error(f"Error processing message: {e}")

    def terminate_thread(thread):
        import ctypes

        if not thread.is_alive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("非法的线程ID")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc失败")

    async def start_client_thread(client_id, websocket, stop_event):
        # 这个函数将在新线程中运行，负责设置新的事件循环，
        # 并在这个事件循环中运行协程函数 handle_client
        def thread_target():
            loop = asyncio.new_event_loop()  # 为新线程创建新的事件循环
            asyncio.set_event_loop(loop)
            
            # 在新的事件循环中运行 handle_client 协程，并等待它完成
            loop.run_until_complete(handle_client(client_id, websocket, stop_event))
            
            print("stop_event.wait")
            # 等待停止事件被设置，然后清理并关闭事件循环
            stop_event.wait()
            print("stop_event.set")
            loop.close()  # 协程执行完毕后关闭事件循环

        # 创建并启动新线程
        client_thread = threading.Thread(target=thread_target)
        client_threads[client_id] = (client_thread, stop_event)  # 存储线程和停止事件
        client_thread.start()


    async def text_websocket_handler(websocket, path, client_id):
        # my_logger.info(f"client_id={client_id}")
        # my_logger.info("text_websocket_handler started")
        text_clients[client_id] = websocket

        stop_event = threading.Event()  # 创建一个停止事件
        print(f"Event ID in text_websocket_handler: {id(stop_event)}")

        await start_client_thread(client_id, websocket, stop_event)
        
        # my_logger.info("handle_client started")

        task = asyncio.create_task(text_process_message_queue(client_id))  # 启动消息处理协程
        try:
            async for message in websocket:
                await text_message_queues[client_id].put(message)
        except websockets.exceptions.ConnectionClosed as e:
            my_logger.info(f"Text WebSocket connection closed: {client_id}, reason: {e.reason}")
        except Exception as e:
            my_logger.error(f"Error receiving text message: {e}")
        finally:
            my_logger.info(f"Text WebSocket connection closed: {client_id}")

            # 执行断开连接后的清理工作
            # WebSocket连接关闭，设置停止事件，通知线程结束
            stop_event.set()

            if stop_event.is_set():
                print("stop_event.is_set")

            task.cancel()  # 请求取消任务

            try:
                await task  # 等待任务处理取消
            except asyncio.CancelledError:
                my_logger.info("text_process_message_queue任务已经被取消")

            # 执行其他断开连接后的清理工作
            del client_threads[client_id]  # 从字典中移除线程和停止事件

    async def audio_websocket_handler(websocket, path, client_id):
        # my_logger.info(f"client_id={client_id}")
        # start_client_thread(client_id, websocket, stop_event)
        audio_clients[client_id] = websocket

        task = asyncio.create_task(audio_process_message_queue(client_id))  # 启动消息处理协程

        try:
            async for message in websocket:
                await audio_message_queues[client_id].put(message)
        except websockets.exceptions.ConnectionClosed as e:
            my_logger.info(f"Audio WebSocket connection closed: {client_id}, reason: {e.reason}")
        except Exception as e:
            my_logger.error(f"Error receiving audio message: {e}")
        finally:
            # 执行断开连接后的清理工作
            my_logger.info("Audio WebSocket connection closed")
            
            task.cancel()  # 请求取消任务

            try:
                await task  # 等待任务处理取消
            except asyncio.CancelledError:
                my_logger.info("audio_process_message_queue任务已经被取消")

    import functools
    
    client_id = generate_unique_client_id()  # 获取或生成客户端 ID
    client_id2 = generate_unique_client_id()

    tmp = {"text_id": client_id, "audio_id": client_id2}
    my_clients.append(tmp)

    my_logger.info(f"tmp={tmp}")
    # 使用functools.partial来预填充处理器函数的参数
    partial_text_handler = functools.partial(text_websocket_handler, path='/', client_id=client_id)
    partial_audio_handler = functools.partial(audio_websocket_handler, path='/', client_id=client_id2)


    # 使用预填充的处理器函数启动 WebSocket 服务器
    start_text_server = websockets.serve(partial_text_handler, "0.0.0.0", 9001)
    start_audio_server = websockets.serve(partial_audio_handler, "0.0.0.0", 9002)

    

    async def client_handler(websocket, path):
        client_id = generate_unique_client_id()  # 需要实现这个函数
        print("等待关闭ws连接")

        await websocket.wait_closed()
        # WebSocket连接关闭时，清理资源
        client_thread.join()  # 等待线程完成
        del client_threads[client_id]  # 移除引用

    

    async def handle_client(client_id, websocket, stop_event):
        global recorder, recoding_to_content, recorder_content, file_path

        async def text_detected(text):
            await send_to_client(
                client_id,
                json.dumps({
                    'type': 'realtime',
                    'text': text
                }),
                client_type="text"
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
            # 指定录制会话应持续的最短持续时间（以秒为单位），以确保有意义的音频捕获，防止录制时间过短或碎片化。
            'min_length_of_recording': 0.5,
            # 在认为录制完成之前，语音之后必须保持沉默的持续时间（以秒为单位）。这可确保演讲过程中的任何短暂停顿都不会过早结束录制。
            'post_speech_silence_duration': 1,
            # 指定一个录制会话结束和另一个录制会话开始之间应存在的最小时间间隔（以秒为单位），以防止快速连续录制。
            'min_gap_between_recordings': 1,
            'enable_realtime_transcription': True,
            # 指定音频块转录后的时间间隔（以秒为单位）。较低的值将导致更“实时”（频繁）的转录更新，但可能会增加计算负载
            'realtime_processing_pause': 0,
            'realtime_model_type': 'tiny',
            # 一个回调函数，每当实时听录中有更新时就会触发，并返回更高质量、稳定的文本作为其参数。
            # 'on_realtime_transcription_stabilized': text_detected,
            # 音频在正式录制之前缓冲的时间跨度（以秒为单位）。这有助于抵消语音活动检测中固有的延迟，确保不会遗漏任何初始音频
            'pre_recording_buffer_duration': 0.2,
            
            # 用于启动录制的唤醒词。可以以逗号分隔的字符串形式提供多个唤醒词。支持的唤醒词有：alexa、americano、blueberry、bumblebee、computer、grapefruits、grasshopper、hey google、hey siri、jarvis、ok google、picovoice、porcupine、terminator
            # 'wake_words': 'ok google',
            # 唤醒词检测的灵敏度级别（0 表示最不敏感，1 表示最敏感）
            # 'wake_words_sensitivity': 0.6,
            # 默认值=0 如果最初未检测到语音，则在系统切换到唤醒词激活之前，监控开始后的持续时间（以秒为单位）。如果设置为零，系统将立即使用唤醒词激活
            # 'wake_word_activation_delay': 0,
            # 默认值=5 识别唤醒词后的持续时间（以秒为单位）。如果在此窗口中未检测到后续语音活动，系统将转换回非活动状态，等待下一个唤醒词或语音激活。
            # 'wake_word_timeout': 5,
        }

        Configure_logger(file_path)
        my_logger = logging.getLogger(f"my_logger_{client_id}")
        my_logger.setLevel(logging.INFO)

        my_logger.info(f"Initializing RealtimeSTT for client {client_id}...")
        recorder = AudioToTextRecorder(**recorder_config)  # 假设每个客户端都有独立的录音器实例
        my_logger.info(f"RealtimeSTT initialized for client {client_id}")
        my_logger.info(f"RealtimeSTT 初始化完毕，你可以说话啦~")

        # 设置日志级别以屏蔽不必要的日志消息
        faster_whisper_logger = logging.getLogger("faster_whisper")
        faster_whisper_logger.setLevel(logging.WARNING)

        audio_recorder_logger = logging.getLogger("audio_recorder")
        audio_recorder_logger.setLevel(logging.WARNING)

        recorder_ready.set()
        try:
            while not stop_event.is_set():
                full_sentence = recorder.text()  # 假设这个方法读取客户端发送的音频并返回文本
                
                # 再次检查stop_event状态
                if stop_event.is_set():
                    break
                
                await send_to_client(client_id, json.dumps({
                    'type': 'fullSentence',
                    'text': full_sentence
                }), client_type="text")

                my_logger.info(f"【识别内容】：{full_sentence} for client {client_id}")

                # 这里是处理命令逻辑，例如"开始记录"、"结束记录"等
                # 注意，这里需要根据具体的实现细节进行调整
                # 例如，你可能需要从WebSocket接收消息并处理，而不是从recorder.text()
                input_type = "auto"

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
                            

                            await llm_and_tts(recorder_content)

                            recorder_content = ""

                            break

                    if recoding_to_content == True:
                        recorder_content += full_sentence
                elif input_type == "auto":
                    await llm_and_tts(client_id, full_sentence, client_type="text")


        except Exception as e:
            my_logger.error(f"Error in client {client_id} thread: {e}")
        finally:
            # 清理资源，例如关闭日志文件、停止录音等
            my_logger.info(f"Closing client {client_id} connection")


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



    print("Server started. Press Ctrl+C to stop the server.")
    asyncio.get_event_loop().run_until_complete(start_text_server)
    asyncio.get_event_loop().run_until_complete(start_audio_server)
    asyncio.get_event_loop().run_forever()
