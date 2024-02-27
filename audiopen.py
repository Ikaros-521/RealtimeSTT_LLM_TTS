from RealtimeSTT import AudioToTextRecorder

import logging, time, schedule
from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger

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

config_path = "config.json"
config = Config(config_path)

def check():
    import os

    try:
        ret_json = common.check_useful()
        if ret_json["ret"] != 0:
            os._exit(0)

        return ret_json["ret"]
    except Exception as e:
        logging.error(f'{e}')
        os._exit(0)
        return 3

if __name__ == '__main__':
    my_logger.info("初始化 RealtimeSTT...")

    def process_text(text):
        my_logger.info(f"识别内容为：{text}")

        for start_cmd in config.get("start_cmd"):
            if start_cmd in text:
                import webbrowser, pyautogui

                url = "https://audiopen.ai/"
                sleep_time = 5

                my_logger.info(f'打开{url}, {sleep_time}秒后开始录音')
                webbrowser.open(url)
                
                time.sleep(sleep_time)

                pyautogui.click(x=config.get("audiopen", "start_x"), y=config.get("audiopen", "start_y"))

                return
            
        for stop_cmd in config.get("stop_cmd"):
            if stop_cmd in text:
                import pyautogui

                pyautogui.click(x=config.get("audiopen", "stop_x"), y=config.get("audiopen", "stop_y"))

                return
        
        for get_mouse_coordinate_cmd in config.get("get_mouse_coordinate_cmd"):
            if get_mouse_coordinate_cmd in text:
                import pyautogui

                # 获取鼠标当前的 x 和 y 坐标
                x, y = pyautogui.position()
                my_logger.info(f'鼠标当前坐标：x={x}, y={y}')

                return

    # 安排任务每24小时执行一次
    schedule.every(24).hours.do(check)

    if check() == 0:
        recorder_config = {
            "input_device_index": int(config.get("recorder", "device_index")),
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

        recorder = AudioToTextRecorder(**recorder_config)

        my_logger.info("请说点什么吧")

        while True:
            text = recorder.text(process_text)

            # 检查并执行任何待处理的任务
            schedule.run_pending()
