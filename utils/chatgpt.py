import traceback, logging
from copy import deepcopy
import openai
from packaging import version

from .common import Common
from .logger import Configure_logger


class Chatgpt:
    # 设置会话初始值
    # session_config = {'msg': [{"role": "system", "content": config_data['chatgpt']['preset']}]}
    session_config = {}
    sessions = {}
    current_key_index = 0
    data_openai = {}
    data_chatgpt = {}

    def __init__(self, data_openai, data_chatgpt):
        self.common = Common()
        # 日志文件路径
        file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        Configure_logger(file_path)

        # 设置会话初始值
        self.session_config = {'msg': [{"role": "system", "content": data_chatgpt["preset"]}]}
        self.data_openai = data_openai
        self.data_chatgpt = data_chatgpt


    # chatgpt相关
    def chat(self, msg, sessionid):
        """
        ChatGPT 对话函数
        :param msg: 用户输入的消息
        :param sessionid: 当前会话 ID
        :return: ChatGPT 返回的回复内容
        """
        try:
            # 获取当前会话
            session = self.get_chat_session(sessionid)

            # 将用户输入的消息添加到会话中
            session['msg'].append({"role": "user", "content": msg})

            # 添加当前时间到会话中
            session['msg'][1] = {"role": "system", "content": "current time is:" + self.common.get_bj_time()}

            # 调用 ChatGPT 接口生成回复消息
            message = self.chat_with_gpt(session['msg'])

            # 如果返回的消息包含最大上下文长度限制，则删除超长上下文并重试
            if message.__contains__("This model's maximum context length is 409"):
                del session['msg'][0:3]
                del session['msg'][len(session['msg']) - 1:len(session['msg'])]
                message = self.chat(msg, sessionid)

            # 将 ChatGPT 返回的回复消息添加到会话中
            session['msg'].append({"role": "assistant", "content": message})

            # 输出会话 ID 和 ChatGPT 返回的回复消息
            logging.info("会话ID: " + str(sessionid))
            logging.debug("ChatGPT返回内容: ")
            logging.debug(message)

            # 返回 ChatGPT 返回的回复消息
            return message

        # 捕获异常并打印堆栈跟踪信息
        except Exception as error:
            logging.error(traceback.format_exc())
            return None


    def get_chat_session(self, sessionid):
        """
        获取指定 ID 的会话，如果不存在则创建一个新的会话
        :param sessionid: 会话 ID
        :return: 指定 ID 的会话
        """
        sessionid = str(sessionid)
        if sessionid not in self.sessions:
            config = deepcopy(self.session_config)
            config['id'] = sessionid
            config['msg'].append({"role": "system", "content": "current time is:" + self.common.get_bj_time()})
            self.sessions[sessionid] = config
        return self.sessions[sessionid]


    def chat_with_gpt(self, messages):
        """
        使用 ChatGPT 接口生成回复消息
        :param messages: 上下文消息列表
        :return: ChatGPT 返回的回复消息
        """
        max_length = len(self.data_openai['api_key']) - 1

        try:
            openai.api_base = self.data_openai['api']

            if not self.data_openai['api_key']:
                logging.error(f"请设置openai Api Key")
                return None
            else:
                # 判断是否所有 API key 均已达到速率限制
                if self.current_key_index > max_length:
                    self.current_key_index = 0
                    logging.warning(f"全部Key均已达到速率限制,请等待一分钟后再尝试")
                    return None
                openai.api_key = self.data_openai['api_key'][self.current_key_index]

            logging.debug(f"openai.__version__={openai.__version__}")

            # 判断openai库版本，1.x.x和0.x.x有破坏性更新
            if version.parse(openai.__version__) < version.parse('1.0.0'):
                # 调用 ChatGPT 接口生成回复消息
                resp = openai.ChatCompletion.create(
                    model=self.data_chatgpt['model'],
                    messages=messages,
                    timeout=30
                )

                resp = resp['choices'][0]['message']['content']
            else:
                logging.debug(f"base_url={openai.api_base}, api_key={openai.api_key}")

                client = openai.OpenAI(base_url=openai.api_base, api_key=openai.api_key)
                # 调用 ChatGPT 接口生成回复消息
                resp = client.chat.completions.create(
                    model=self.data_chatgpt['model'],
                    messages=messages,
                    timeout=30
                )

                resp = resp.choices[0].message.content
        # 处理 OpenAIError 异常
        except openai.OpenAIError as e:
            if str(e).__contains__("Rate limit reached for default-gpt-3.5-turbo") and self.current_key_index <= max_length:
                self.current_key_index = self.current_key_index + 1
                logging.warning("速率限制，尝试切换key")
                msg = self.chat_with_gpt(messages)
                return msg
            elif str(e).__contains__(
                    "Your access was terminated due to violation of our policies") and self.current_key_index <= max_length:
                logging.warning("请及时确认该Key: " + str(openai.api_key) + " 是否正常，若异常，请移除")

                # 判断是否所有 API key 均已尝试
                if self.current_key_index + 1 > max_length:
                    return str(e)
                else:
                    logging.warning("访问被阻止，尝试切换Key")
                    self.current_key_index = self.current_key_index + 1
                    msg = self.chat_with_gpt(messages)
                    return msg
            else:
                logging.error('openai 接口报错: ' + str(e))
                return None

        return resp


    # 调用gpt接口，获取返回内容
    def get_gpt_resp(self, user_name, prompt):
        # 获取当前用户的会话
        session = self.get_chat_session(str(user_name))
        # 调用 ChatGPT 接口生成回复消息
        resp_content = self.chat(prompt, session)

        return resp_content