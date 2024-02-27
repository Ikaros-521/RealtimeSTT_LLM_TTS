import logging
import requests
import json, threading
import traceback

# 对接AUDIO_PLAYER 音频播放器项目
class AUDIO_PLAYER:
    def __init__(self, data):
        try:
            self.api_ip_port = data["api_ip_port"]
        except Exception as e:
            logging.error(traceback.format_exc())
            return None

    def play(self, data):
        try:
            url = f"{self.api_ip_port}/play"

            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                data_json = response.json()
                # logging.info(data_json)
                if data_json["code"] != 200:
                    logging.error(data_json["message"])
                    return False
                    
                return True
            else:
                logging.error(response.text)
                return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False

    def pause_stream(self):
        try:
            url = f"{self.api_ip_port}/pause_stream"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if data["code"] != 200:
                    logging.error(data["message"])
                    return False
                    
                return True
            else:
                logging.error(response.text)
                return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False

    def resume_stream(self):
        try:
            url = f"{self.api_ip_port}/resume_stream"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if data["code"] != 200:
                    logging.error(data["message"])
                    return False
                    
                return True
            else:
                logging.error(response.text)
                return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False

    def skip_current_stream(self):
        """
        跳过当前播放音频
        """
        try:
            url = f"{self.api_ip_port}/skip_current_stream"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if data["code"] != 200:
                    logging.error(data["message"])
                    return False
                    
                return True
            else:
                logging.error(response.text)
                return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False

    def get_list(self):
        """
        获取音频播放队列列表
        """
        try:
            url = f"{self.api_ip_port}/get_list"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if data["code"] != 200:
                    logging.error(data["message"])
                    return None
                
                return data["message"]
            else:
                logging.error(response.text)
                return None
        except Exception as e:
            logging.error(traceback.format_exc())
            return None

    def clear(self):
        """
        清空播放队列
        """
        try:
            url = f"{self.api_ip_port}/clear"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if data["code"] != 200:
                    logging.error(data["message"])
                    return False

                return True
            else:
                logging.error(response.text)
                return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False
        