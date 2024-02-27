import time, logging
import json, threading
import pygame
from queue import Queue, Empty
import asyncio
from copy import deepcopy
import traceback

from .common import Common
from .logger import Configure_logger
from .config import Config
from .my_tts import MY_TTS


class Audio:
    # 初始化多个pygame.mixer实例
    mixer_normal = pygame.mixer

    def __init__(self, config_path, type=1):  
        self.config = Config(config_path)
        self.common = Common()
        self.my_tts = MY_TTS(config_path)
    
        # 创建消息队列
        self.message_queue = Queue()
        # 创建音频路径队列
        self.voice_tmp_path_queue = Queue()
        # 文案单独一个线程排队播放
        self.only_play_copywriting_thread = None
        
        # 日志文件路径
        file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        Configure_logger(file_path)

        # 旧版同步写法
        # threading.Thread(target=self.message_queue_thread).start()
        # 改异步
        threading.Thread(target=lambda: asyncio.run(self.message_queue_thread())).start()

        # 音频合成单独一个线程排队播放
        threading.Thread(target=lambda: asyncio.run(self.only_play_audio())).start()

    # 音频合成消息队列线程
    async def message_queue_thread(self):
        logging.info("创建音频合成消息队列线程")
        while True:  # 无限循环，直到队列为空时退出
            try:
                message = self.message_queue.get(block=True)
                logging.debug(message)
                await self.my_play_voice(message)
                self.message_queue.task_done()

                # 加个延时 降低点edge-tts的压力
                # await asyncio.sleep(0.5)
            except Exception as e:
                logging.error(traceback.format_exc())


    # 只进行普通音频播放   
    async def only_play_audio(self):
        try:
            Audio.mixer_normal.init()
            while True:
                try:
                    # 从队列中获取音频文件路径 队列为空时阻塞等待
                    data_json = self.voice_tmp_path_queue.get(block=True)

                    logging.debug(f"普通音频播放队列 data_json={data_json}")

                    voice_tmp_path = data_json["voice_path"]

                    # 不仅仅是说话间隔，还是等待文本捕获刷新数据
                    # await asyncio.sleep(self.config.get("play_audio", "normal_interval"))

            
                    logging.debug(f"voice_tmp_path={voice_tmp_path}")
                    # 使用pygame播放音频
                    Audio.mixer_normal.music.load(voice_tmp_path)
                    Audio.mixer_normal.music.play()
                    while Audio.mixer_normal.music.get_busy():
                        pygame.time.Clock().tick(10)
                    Audio.mixer_normal.music.stop()
                except Exception as e:
                    logging.error(traceback.format_exc())
            Audio.mixer_normal.quit()
        except Exception as e:
            logging.error(traceback.format_exc())

    # 音频合成（edge-tts / vits_fast）并播放
    def audio_synthesis(self, message):
        try:
            logging.debug(message)

            # 是否语句切分
            if self.config.get("play_audio", "text_split_enable"):
                sentences = self.common.split_sentences(message['content'])
                for s in sentences:
                    message_copy = deepcopy(message)  # 创建 message 的副本
                    message_copy["content"] = s  # 修改副本的 content
                    logging.debug(f"s={s}")
                    if not self.common.is_all_space_and_punct(s):
                        self.message_queue.put(message_copy)  # 将副本放入队列中
            else:
                self.message_queue.put(message)
            

            # 单独开线程播放
            # threading.Thread(target=self.my_play_voice, args=(type, data, config, content,)).start()
        except Exception as e:
            logging.error(traceback.format_exc())
            return


    # 播放音频
    async def my_play_voice(self, message):
        """合成音频并插入待播放队列

        Args:
            message (dict): 待合成内容的json串

        Returns:
            bool: 合成情况
        """
        logging.debug(message)

        try:
            # 如果是tts类型为none，暂时这类为直接播放音频，所以就丢给路径队列
            if message["tts_type"] == "none":
                self.voice_tmp_path_queue.put(message)
                return
        except Exception as e:
            logging.error(traceback.format_exc())
            return

        try:
            logging.debug(f"合成音频前的原始数据：{message['content']}")
            message["content"] = self.common.remove_extra_words(message["content"], message["config"]["max_len"], message["config"]["max_char_len"])
            # logging.info("裁剪后的合成文本:" + text)

            message["content"] = message["content"].replace('\n', '。')

            # 空数据就散了吧
            if message["content"] == "":
                return
        except Exception as e:
            logging.error(traceback.format_exc())
            return
        

        # 判断消息类型，再变声并封装数据发到队列 减少冗余
        async def voice_change_and_put_to_queue(message, voice_tmp_path):
            # 拼接json数据，存入队列
            data_json = {
                "type": message['type'],
                "voice_path": voice_tmp_path,
                "content": message["content"]
            }

            if "insert_index" in message:
                data_json["insert_index"] = message["insert_index"]

            # 区分消息类型是否是 回复xxx 并且 关闭了变声
            if message["type"] == "reply" and False == self.config.get("read_user_name", "voice_change"):
                # 是否开启了音频播放，如果没开，则不会传文件路径给播放队列
                if self.config.get("play_audio", "enable"):
                    self.voice_tmp_path_queue.put(data_json)
                    return True
            # 区分消息类型是否是 念弹幕 并且 关闭了变声
            elif message["type"] == "read_comment" and False == self.config.get("read_comment", "voice_change"):
                # 是否开启了音频播放，如果没开，则不会传文件路径给播放队列
                if self.config.get("play_audio", "enable"):
                    self.voice_tmp_path_queue.put(data_json)
                    return True

            # 更新音频路径
            data_json["voice_path"] = voice_tmp_path

            # 是否开启了音频播放，如果没开，则不会传文件路径给播放队列
            if self.config.get("play_audio", "enable"):
                self.voice_tmp_path_queue.put(data_json)

            return True

        # 区分TTS类型
        try:
            if message["tts_type"] == "vits":
                # 语言检测
                language = self.common.lang_check(message["content"])

                logging.debug(f"message['content']={message['content']}")

                # 自定义语言名称（需要匹配请求解析）
                language_name_dict = {"en": "英文", "zh": "中文", "jp": "日文"}  

                if language in language_name_dict:
                    language = language_name_dict[language]
                else:
                    language = "自动"  # 无法识别出语言代码时的默认值

                # logging.info("language=" + language)

                data = {
                    "type": message["data"]["type"],
                    "api_ip_port": message["data"]["api_ip_port"],
                    "id": message["data"]["id"],
                    "format": message["data"]["format"],
                    "lang": language,
                    "length": message["data"]["length"],
                    "noise": message["data"]["noise"],
                    "noisew": message["data"]["noisew"],
                    "max": message["data"]["max"],
                    "sdp_radio": message["data"]["sdp_radio"],
                    "content": message["content"]
                }

                # 调用接口合成语音
                voice_tmp_path = await self.my_tts.vits_api(data)
            elif message["tts_type"] == "bert_vits2":
                if message["data"]["type"] == "hiyori":
                    if message["data"]["language"] == "auto":
                        # 自动检测语言
                        language = self.common.lang_check(message["content"])

                        logging.debug(f'language={language}')

                        # 自定义语言名称（需要匹配请求解析）
                        language_name_dict = {"en": "EN", "zh": "ZH", "ja": "JP"}  

                        if language in language_name_dict:
                            language = language_name_dict[language]
                        else:
                            language = "ZH"  # 无法识别出语言代码时的默认值
                    else:
                        language = message["data"]["language"]

                    data = {
                        "api_ip_port": message["data"]["api_ip_port"],
                        "type": message["data"]["type"],
                        "model_id": message["data"]["model_id"],
                        "speaker_name": message["data"]["speaker_name"],
                        "speaker_id": message["data"]["speaker_id"],
                        "language": language,
                        "length": message["data"]["length"],
                        "noise": message["data"]["noise"],
                        "noisew": message["data"]["noisew"],
                        "sdp_radio": message["data"]["sdp_radio"],
                        "auto_translate": message["data"]["auto_translate"],
                        "auto_split": message["data"]["auto_split"],
                        "emotion": message["data"]["emotion"],
                        "style_text": message["data"]["style_text"],
                        "style_weight": message["data"]["style_weight"],
                        "content": message["content"]
                    }

                    

                # 调用接口合成语音
                voice_tmp_path = await self.my_tts.bert_vits2_api(data)
            elif message["tts_type"] == "vits_fast":
                if message["data"]["language"] == "自动识别":
                    # 自动检测语言
                    language = self.common.lang_check(message["content"])

                    logging.debug(f'language={language}')

                    # 自定义语言名称（需要匹配请求解析）
                    language_name_dict = {"en": "English", "zh": "简体中文", "ja": "日本語"}  

                    if language in language_name_dict:
                        language = language_name_dict[language]
                    else:
                        language = "简体中文"  # 无法识别出语言代码时的默认值
                else:
                    language = message["data"]["language"]

                # logging.info("language=" + language)

                data = {
                    "api_ip_port": message["data"]["api_ip_port"],
                    "character": message["data"]["character"],
                    "speed": message["data"]["speed"],
                    "language": language,
                    "content": message["content"]
                }

                # 调用接口合成语音
                voice_tmp_path = self.my_tts.vits_fast_api(data)
                # logging.info(data_json)
            elif message["tts_type"] == "edge-tts":
                data = {
                    "content": message["content"],
                    "voice": message["data"]["voice"],
                    "rate": message["data"]["rate"],
                    "volume": message["data"]["volume"]
                }

                # 调用接口合成语音
                voice_tmp_path = await self.my_tts.edge_tts_api(data)
            
            elif message["tts_type"] == "genshinvoice_top":
                voice_tmp_path = await self.my_tts.genshinvoice_top_api(message["content"])
            elif message["tts_type"] == "tts_ai_lab_top":
                voice_tmp_path = await self.my_tts.tts_ai_lab_top_api(message["content"])
            elif message["tts_type"] == "bark_gui":
                data = {
                    "api_ip_port": message["data"]["api_ip_port"],
                    "spk": message["data"]["spk"],
                    "generation_temperature": message["data"]["generation_temperature"],
                    "waveform_temperature": message["data"]["waveform_temperature"],
                    "end_of_sentence_probability": message["data"]["end_of_sentence_probability"],
                    "quick_generation": message["data"]["quick_generation"],
                    "seed": message["data"]["seed"],
                    "batch_count": message["data"]["batch_count"],
                    "content": message["content"]
                }

                # 调用接口合成语音
                voice_tmp_path = self.my_tts.bark_gui_api(data)
            elif message["tts_type"] == "vall_e_x":
                data = {
                    "api_ip_port": message["data"]["api_ip_port"],
                    "language": message["data"]["language"],
                    "accent": message["data"]["accent"],
                    "voice_preset": message["data"]["voice_preset"],
                    "voice_preset_file_path": message["data"]["voice_preset_file_path"],
                    "content": message["content"]
                }

                # 调用接口合成语音
                voice_tmp_path = self.my_tts.vall_e_x_api(data)
            elif message["tts_type"] == "openai_tts":
                data = {
                    "type": message["data"]["type"],
                    "api_ip_port": message["data"]["api_ip_port"],
                    "model": message["data"]["model"],
                    "voice": message["data"]["voice"],
                    "api_key": message["data"]["api_key"],
                    "content": message["content"]
                }

                # 调用接口合成语音
                voice_tmp_path = self.my_tts.openai_tts_api(data)
            elif message["tts_type"] == "reecho_ai":
                voice_tmp_path = await self.my_tts.reecho_ai_api(message["content"])
            elif message["tts_type"] == "gradio_tts":
                data = {
                    "request_parameters": message["data"]["request_parameters"],
                    "content": message["content"]
                }

                voice_tmp_path = self.my_tts.gradio_tts_api(data)  
            elif message["tts_type"] == "gpt_sovits":
                if message["data"]["language"] == "自动识别":
                    # 自动检测语言
                    language = self.common.lang_check(message["content"])

                    logging.debug(f'language={language}')

                    # 自定义语言名称（需要匹配请求解析）
                    language_name_dict = {"en": "英文", "zh": "中文", "ja": "日文"}  

                    if language in language_name_dict:
                        language = language_name_dict[language]
                    else:
                        language = "中文"  # 无法识别出语言代码时的默认值
                else:
                    language = message["data"]["language"]
                    
                data = {
                    "type": message["data"]["type"],
                    "ws_ip_port": message["data"]["ws_ip_port"],
                    "api_ip_port": message["data"]["api_ip_port"],
                    "ref_audio_path": message["data"]["ref_audio_path"],
                    "prompt_text": message["data"]["prompt_text"],
                    "prompt_language": message["data"]["prompt_language"],
                    "language": language,
                    "cut": message["data"]["cut"],
                    "webtts": message["data"]["webtts"],
                    "content": message["content"]
                }

                voice_tmp_path = await self.my_tts.gpt_sovits_api(data)  
            elif message["tts_type"] == "clone_voice":
                data = {
                    "type": message["data"]["type"],
                    "api_ip_port": message["data"]["api_ip_port"],
                    "voice": message["data"]["voice"],
                    "language": message["data"]["language"],
                    "speed": message["data"]["speed"],
                    "content": message["content"]
                }

                voice_tmp_path = await self.my_tts.clone_voice_api(data) 
            elif message["tts_type"] == "none":
                pass
        except Exception as e:
            logging.error(traceback.format_exc())
            return False
        
        if voice_tmp_path is None:
            logging.error(f"{message['tts_type']}合成失败，请排查配置、网络等问题")
            self.abnormal_alarm_handle("tts")
            
            return False
        
        logging.info(f"{message['tts_type']}合成成功，合成内容：【{message['content']}】，输出到={voice_tmp_path}")
                 
        await voice_change_and_put_to_queue(message, voice_tmp_path)  

        return True
