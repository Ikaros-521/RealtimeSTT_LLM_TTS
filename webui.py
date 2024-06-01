from nicegui import ui, app
import sys, os, json, subprocess, asyncio
import logging, traceback
# from functools import partial

import pyautogui

from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger


"""

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@.:;;;++;;;;:,@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@:;+++++;;++++;;;.@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@:++++;;;;;;;;;;+++;,@@@@@@@@@@@@@@@@@
@@@@@@@@@@@.;+++;;;;;;;;;;;;;;++;:@@@@@@@@@@@@@@@@
@@@@@@@@@@;+++;;;;;;;;;;;;;;;;;;++;:@@@@@@@@@@@@@@
@@@@@@@@@:+++;;;;;;;;;;;;;;;;;;;;++;.@@@@@@@@@@@@@
@@@@@@@@;;+;;;;;;;;;;;;;;;;;;;;;;;++:@@@@@@@@@@@@@
@@@@@@@@;+;;;;:::;;;;;;;;;;;;;;;;:;+;,@@@@@@@@@@@@
@@@@@@@:+;;:;;:::;:;;:;;;;::;;:;:::;+;.@@@@@@@@@@@
@@@@@@.;+;::;:,:;:;;+:++:;:::+;:::::++:+@@@@@@@@@@
@@@@@@:+;;:;;:::;;;+%;*?;;:,:;*;;;;:;+;:@@@@@@@@@@
@@@@@@;;;+;;+;:;;;+??;*?++;,:;+++;;;:++:@@@@@@@@@@
@@@@@.++*+;;+;;;;+?;?**??+;:;;+.:+;;;;+;;@@@@@@@@@
@@@@@,+;;;;*++*;+?+;**;:?*;;;;*:,+;;;;+;,@@@@@@@@@
@@@@@,:,+;+?+?++?+;,?#%*??+;;;*;;:+;;;;+:@@@@@@@@@
@@@@@@@:+;*?+?#%;;,,?###@#+;;;*;;,+;;;;+:@@@@@@@@@
@@@@@@@;+;??+%#%;,,,;SSS#S*+++*;..:+;?;+;@@@@@@@@@
@@@@@@@:+**?*?SS,,,,,S#S#+***?*;..;?;**+;@@@@@@@@@
@@@@@@@:+*??*??S,,,,,*%SS+???%++;***;+;;;.@@@@@@@@
@@@@@@@:*?*;*+;%:,,,,;?S?+%%S?%+,:?;+:,,,@@@@@@@@
@@@@@@@,*?,;+;+S:,,,,%?+;S%S%++:+??+:,,,:@@@@@@@@
@@@@@@@,:,@;::;+,,,,,+?%*+S%#?*???*;,,,,,.@@@@@@@@
@@@@@@@@:;,::;;:,,,,,,,,,?SS#??*?+,.,,,:,@@@@@@@@@
@@@@@@;;+;;+:,:%?%*;,,,,SS#%*??%,.,,,,,:@@@@@@@@@
@@@@@.+++,++:;???%S?%;.+#####??;.,,,,,,:@@@@@@@@@
@@@@@:++::??+S#??%#??S%?#@#S*+?*,,,,,,:,@@@@@@@@@@
@@@@@:;;:*?;+%#%?S#??%SS%+#%..;+:,,,,,,@@@@@@@@@@@
@@@@@@,,*S*;?SS?%##%?S#?,.:#+,,+:,,,,,,@@@@@@@@@@@
@@@@@@@;%?%#%?*S##??##?,..*#,,+:,,;*;.@@@@@@@@@@@
@@@@@@.*%??#S*?S#@###%;:*,.:#:,+;:;*+:@@@@@@@@@@@@
@@@@@@,%S??SS%##@@#%S+..;;.,#*;???*?+++:@@@@@@@@@@
@@@@@@:S%??%####@@S,,*,.;*;+#*;+?%??#S%+.@@@@@@@@@
@@@@@@:%???%@###@@?,,:**S##S*;.,%S?;+*?+.,..@@@@@@
@@@@@@;%??%#@###@@#:.;@@#@%%,.,%S*;++*++++;.@@@@@
@@@@@@,%S?S@@###@@@%+#@@#@?;,.:?;??++?%?***+.@@@@@
@@@@@@.*S?S####@@####@@##@?..:*,+:??**%+;;;;..@@@@
@@@@@@:+%?%####@@####@@#@%;:.;;:,+;?**;++;,:;:,@@@
@@@@@@;;*%?%@##@@@###@#S#*:;*+,;.+***?******+:.@@@
@@@@@@:;:??%@###%##@#%++;+*:+;,:;+%?*;+++++;:.@@@@
@@@@@@.+;:?%@@#%;+S*;;,:::**+,;:%??*+.@....@@@@@@@
@@@@@@@;*::?#S#S+;,..,:,;:?+?++*%?+::@@@@@@@@@@@@@
@@@@@@@.+*+++?%S++...,;:***??+;++:.@@@@@@@@@@@@@@@
@@@@@@@@:::..,;+*+;;+*?**+;;;+;:.@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@,+*++;;:,..@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@::,.@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

"""


"""
全局变量
"""
# 创建一个全局变量，用于表示程序是否正在运行
running_flag = False

# 创建一个子进程对象，用于存储正在运行的外部程序
running_process = None

common = None
config = None
audio = None
my_handle = None
config_path = None


web_server_port = 12345


"""
初始化基本配置
"""
def init():
    global config_path, config, common, audio

    common = Common()

    if getattr(sys, 'frozen', False):
        # 当前是打包后的可执行文件
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
        file_relative_path = os.path.dirname(os.path.abspath(bundle_dir))
    else:
        # 当前是源代码
        file_relative_path = os.path.dirname(os.path.abspath(__file__))

    # logging.info(file_relative_path)

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


init()

# 暗夜模式
dark = ui.dark_mode()

"""
通用函数
"""
def textarea_data_change(data):
    """
    字符串数组数据格式转换
    """
    tmp_str = ""
    for tmp in data:
        tmp_str = tmp_str + tmp + "\n"
    
    return tmp_str



"""
                                                                                                    
                                               .@@@@@                           @@@@@.              
                                               .@@@@@                           @@@@@.              
        ]]]]]   .]]]]`   .]]]]`   ,]@@@@@\`    .@@@@@,/@@@\`   .]]]]]   ]]]]]`  ]]]]].              
        =@@@@^  =@@@@@`  =@@@@. =@@@@@@@@@@@\  .@@@@@@@@@@@@@  *@@@@@   @@@@@^  @@@@@.              
         =@@@@ ,@@@@@@@ .@@@@` =@@@@^   =@@@@^ .@@@@@`  =@@@@^ *@@@@@   @@@@@^  @@@@@.              
          @@@@^@@@@\@@@^=@@@^  @@@@@@@@@@@@@@@ .@@@@@   =@@@@@ *@@@@@   @@@@@^  @@@@@.              
          ,@@@@@@@^ \@@@@@@@   =@@@@^          .@@@@@.  =@@@@^ *@@@@@  .@@@@@^  @@@@@.              
           =@@@@@@  .@@@@@@.    \@@@@@]/@@@@@` .@@@@@@]/@@@@@. .@@@@@@@@@@@@@^  @@@@@.              
            \@@@@`   =@@@@^      ,\@@@@@@@@[   .@@@@^\@@@@@[    .\@@@@@[=@@@@^  @@@@@.    
            
"""
# 配置
webui_ip = config.get("webui", "ip")
webui_port = config.get("webui", "port")
webui_title = config.get("webui", "title")

# CSS
theme_choose = config.get("webui", "theme", "choose")
tab_panel_css = config.get("webui", "theme", "list", theme_choose, "tab_panel")
card_css = config.get("webui", "theme", "list", theme_choose, "card")
button_bottom_css = config.get("webui", "theme", "list", theme_choose, "button_bottom")
button_bottom_color = config.get("webui", "theme", "list", theme_choose, "button_bottom_color")
button_internal_css = config.get("webui", "theme", "list", theme_choose, "button_internal")
button_internal_color = config.get("webui", "theme", "list", theme_choose, "button_internal_color")
switch_internal_css = config.get("webui", "theme", "list", theme_choose, "switch_internal")


def goto_func_page():
    """
    跳转到功能页
    """
    global audio

    """

      =@@^      ,@@@^        .@@@. .....   =@@.      ]@\  ,]]]]]]]]]]]]]]].  .]]]]]]]]]]]]]]]]]]]]    ,]]]]]]]]]]]]]]]]]`    ,/. @@@^ /]  ,@@@.               
      =@@^ .@@@@@@@@@@@@@@^  /@@\]]@@@@@=@@@@@@@@@.  \@@@`=@@@@@@@@@@@@@@@.  .@@@@@@@@@@@@@@@@@@@@    =@@@@@@@@@@@@@@@@@^   .\@@^@@@\@@@`.@@@^                
    @@@@@@@^@@@@@@@@@@@@@@^ =@@@@@^ =@@\]]]/@@]]@@].  =@/`=@@^  .@@@  .@@@.  .@@@^    @@@^    =@@@             ,/@@@@/`     =@@@@@@@@@@@^=@@@@@@@@@.          
    @@@@@@@^@@@^@@\`   =@@^.@@@]]]`=@@^=@@@@@@@@@@@.]]]]` =@@^=@@@@@@@^@@@.  .@@@\]]]]@@@\]]]]/@@@   @@@\/@\..@@@@[./@/@@@. ,[[\@@@@/[[[\@@@`..@@@`           
      =@@^ ,]]]/@@@]]]]]]]].\@@@@@^@@@OO=@@@@@@@@@..@@@@^ =@@^]]]@@@]]`@@@.  .@@@@@@@@@@@@@@@@@@@@   @@@^=@@@^@@@^/@@@\@@@..]@@@@@@@@@@]@@@@^ .@@@.           
      =@@@@=@@@@@@@@@@@@@@@. =@@^ .OO@@@.[[\@@[[[[.  =@@^ =@@^@@@@@@@@^@@@.  .@@@^    @@@^    =@@@   @@@^ .`,]@@@^`,` =@@@. \@/.]@@@^,@@@@@@\ =@@^            
   .@@@@@@@. .@@@`   /@@/  .@@@@@@@,.=@@=@@@@@@@@@^  =@@^,=@@^=@@@@@@@.@@@.  .@@@\]]]]@@@\]]]]/@@@   @@@^]@@@@@@@@@@@]=@@@. ]]]@@@\]]]]] .=@@\@@@.            
    @@\@@^  .@@@\.  /@@@.    =@@^ =@\@@^.../@@.....  =@@@@=@@^=@@[[\@@.@@@.  .@@@@@@@@@@@@@@@@@@@@   @@@@@@/..@@@^,@@@@@@@. O@@@@@@@@@@@  .@@@@@^             
      =@@^   ,\@@@@@@@@.     =@@^/^\@@@`@@@@@@@@@@^  /@@@/@@@`=@@OO@@@.@@@.  =@@@`    @@@^    =@@@   @@@^  \@@@@@^   .=@@@. .@@@@\`/@@/    /@@@\.             
      =@@^    ,/@@@@@@@@]    =@@@@^/@@@@]` =@@.     .\@/.=@@@ =@@[[[[[.@@@.  /@@@     @@@^   ./@@@   @@@^.............=@@@.    O@@@@@@\`,/@@@@@@@@`           
    @@@@@^.@@@@@@@/..[@@@@/. ,@@`/@@@`[@@@@@@@@@@@@.    /@@@^      =@@@@@@. /@@@^     @@@^,@@@@@@^   @@@@@@@@@@@@@@@@@@@@@..\@@@@@[,\@@\@@@@` ,@@@^           
    ,[[[.  .O[[.        [`        ,/         ......       ,^       .[[[[`     ,`      .... [[[[`                      ,[[[. .[.         ,/.     .`

    """

    # 创建一个函数，用于运行外部程序
    def run_external_program(config_path="config.json", type="webui"):
        global running_flag, running_process

        if running_flag:
            if type == "webui":
                ui.notify(position="top", type="warning", message="运行中，请勿重复运行")
            return

        try:
            
            running_flag = True

            # 在这里指定要运行的程序和参数
            # 例如，运行一个名为 "bilibili.py" 的 Python 脚本
            running_process = subprocess.Popen(["python", f"{select_run_py.value}.py"])

            if type == "webui":
                ui.notify(position="top", type="positive", message="程序开始运行")
            logging.info("程序开始运行")

            return {"code": 200, "msg": "程序开始运行"}
        except Exception as e:
            if type == "webui":
                ui.notify(position="top", type="negative", message=f"错误：{e}")
            logging.error(traceback.format_exc())
            running_flag = False

            return {"code": -1, "msg": f"运行失败！{e}"}


    # 定义一个函数，用于停止正在运行的程序
    def stop_external_program(type="webui"):
        global running_flag, running_process

        if running_flag:
            try:
                running_process.terminate()  # 终止子进程
                running_flag = False
                if type == "webui":
                    ui.notify(position="top", type="positive", message="程序已停止")
                logging.info("程序已停止")
            except Exception as e:
                if type == "webui":
                    ui.notify(position="top", type="negative", message=f"停止错误：{e}")
                logging.error(f"停止错误：{e}")

                return {"code": -1, "msg": f"重启失败！{e}"}


    # 开关灯
    def change_light_status(type="webui"):
        if dark.value:
            button_light.set_text("关灯")
        else:
            button_light.set_text("开灯")
        dark.toggle()

    # 重启
    def restart_application(type="webui"):
        try:
            # 先停止运行
            stop_external_program(type)

            logging.info(f"重启webui")
            if type == "webui":
                ui.notify(position="top", type="ongoing", message=f"重启中...")
            python = sys.executable
            os.execl(python, python, *sys.argv)  # Start a new instance of the application
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"code": -1, "msg": f"重启失败！{e}"}
        
    # 恢复出厂配置
    def factory(src_path='config.json.bak', dst_path='config.json', type="webui"):
        # src_path = 'config.json.bak'
        # dst_path = 'config.json'

        try:
            with open(src_path, 'r', encoding="utf-8") as source:
                with open(dst_path, 'w', encoding="utf-8") as destination:
                    destination.write(source.read())
            logging.info("恢复出厂配置成功！")
            if type == "webui":
                ui.notify(position="top", type="positive", message=f"恢复出厂配置成功！")
            
            # 重启
            restart_application()

            return {"code": 200, "msg": "恢复出厂配置成功！"}
        except Exception as e:
            logging.error(f"恢复出厂配置失败！\n{e}")
            if type == "webui":
                ui.notify(position="top", type="negative", message=f"恢复出厂配置失败！\n{e}")
            
            return {"code": -1, "msg": f"恢复出厂配置失败！\n{e}"}
    
    
    # 页面滑到顶部
    def scroll_to_top():
        # 这段JavaScript代码将页面滚动到顶部
        ui.run_javascript("window.scrollTo(0, 0);")   


    """
    配置操作
    """

    async def get_mouse_xy():
        sleep_time = 5
        await asyncio.sleep(sleep_time)
        
        # 获取鼠标当前的 x 和 y 坐标
        x, y = pyautogui.position()
        logging.info(f'鼠标当前坐标：x={x}, y={y}')
        ui.notify(position="top", type="info", message=f'鼠标当前坐标：x={x}, y={y}')


    # 保存配置
    def save_config():
        global config, config_path

        try:
            with open(config_path, 'r', encoding="utf-8") as config_file:
                config_data = json.load(config_file)
        except Exception as e:
            logging.error(f"无法读取配置文件！\n{e}")
            ui.notify(position="top", type="negative", message=f"无法读取配置文件！{e}")
            return False

        def common_textarea_handle(content):
            """通用的textEdit 多行文本内容处理

            Args:
                content (str): 原始多行文本内容

            Returns:
                _type_: 处理好的多行文本内容
            """
            # 通用多行分隔符
            separators = [" ", "\n"]

            ret = [token.strip() for separator in separators for part in content.split(separator) if (token := part.strip())]
            if 0 != len(ret):
                ret = ret[1:]

            return ret


        try:
            """
            通用配置
            """
            if True:
                config_data["run_py"] = select_run_py.value
                config_data["audio_synthesis_type"] = select_audio_synthesis_type.value

                config_data["recorder"]["device_index"] = input_recorder_device_index.value
                config_data["recorder"]["start_cmd"] = common_textarea_handle(textarea_recorder_start_cmd.value)
                config_data["recorder"]["stop_cmd"] = common_textarea_handle(textarea_recorder_stop_cmd.value)
                config_data["recorder"]["drop_cmd"] = common_textarea_handle(textarea_recorder_drop_cmd.value)
                config_data["recorder"]["get_mouse_coordinate_cmd"] = common_textarea_handle(textarea_recorder_get_mouse_coordinate_cmd.value)

                config_data["zhipu"]["api_key"] = input_zhipu_api_key.value
                config_data["zhipu"]["model"] = select_zhipu_model.value
                config_data["zhipu"]["app_id"] = input_zhipu_app_id.value
                config_data["zhipu"]["system"] = input_zhipu_system.value
                config_data["zhipu"]["top_p"] = input_zhipu_top_p.value
                config_data["zhipu"]["temperature"] = input_zhipu_temperature.value
                config_data["zhipu"]["history_enable"] = switch_zhipu_history_enable.value
                config_data["zhipu"]["history_max_len"] = input_zhipu_history_max_len.value
                config_data["zhipu"]["user_info"] = input_zhipu_user_info.value
                config_data["zhipu"]["bot_info"] = input_zhipu_bot_info.value
                config_data["zhipu"]["bot_name"] = input_zhipu_bot_name.value
                config_data["zhipu"]["username"] = input_zhipu_username.value
                config_data["zhipu"]["remove_useless"] = switch_zhipu_remove_useless.value
            
                config_data["openai"]["api"] = input_openai_api.value
                config_data["openai"]["api_key"] = common_textarea_handle(textarea_openai_api_key.value)
                # logging.info(select_chatgpt_model.value)
                config_data["chatgpt"]["model"] = select_chatgpt_model.value
                config_data["chatgpt"]["temperature"] = round(float(input_chatgpt_temperature.value), 1)
                config_data["chatgpt"]["max_tokens"] = int(input_chatgpt_max_tokens.value)
                config_data["chatgpt"]["top_p"] = round(float(input_chatgpt_top_p.value), 1)
                config_data["chatgpt"]["presence_penalty"] = round(float(input_chatgpt_presence_penalty.value), 1)
                config_data["chatgpt"]["frequency_penalty"] = round(float(input_chatgpt_frequency_penalty.value), 1)
                config_data["chatgpt"]["preset"] = input_chatgpt_preset.value
                # config_data["chatgpt"]["prompt_template"] = input_chatgpt_prompt_template.value

                # config_data["openai_tts"]["type"] = select_openai_tts_type.value
                # config_data["openai_tts"]["api_ip_port"] = input_openai_tts_api_ip_port.value
                # config_data["openai_tts"]["model"] = select_openai_tts_model.value
                # config_data["openai_tts"]["voice"] = select_openai_tts_voice.value
                # config_data["openai_tts"]["api_key"] = input_openai_tts_api_key.value

                config_data["edge-tts"]["voice"] = select_edge_tts_voice.value
                config_data["edge-tts"]["rate"] = input_edge_tts_rate.value
                config_data["edge-tts"]["volume"] = input_edge_tts_volume.value

                config_data["gpt_sovits"]["type"] = select_gpt_sovits_type.value
                config_data["gpt_sovits"]["gradio_ip_port"] = input_gpt_sovits_gradio_ip_port.value
                config_data["gpt_sovits"]["api_ip_port"] = input_gpt_sovits_api_ip_port.value
                config_data["gpt_sovits"]["ws_ip_port"] = input_gpt_sovits_ws_ip_port.value
                config_data["gpt_sovits"]["ref_audio_path"] = input_gpt_sovits_ref_audio_path.value
                config_data["gpt_sovits"]["prompt_text"] = input_gpt_sovits_prompt_text.value
                config_data["gpt_sovits"]["prompt_language"] = select_gpt_sovits_prompt_language.value
                config_data["gpt_sovits"]["language"] = select_gpt_sovits_language.value
                config_data["gpt_sovits"]["cut"] = select_gpt_sovits_cut.value
                config_data["gpt_sovits"]["gpt_model_path"] = input_gpt_sovits_gpt_model_path.value
                config_data["gpt_sovits"]["sovits_model_path"] = input_gpt_sovits_sovits_model_path.value
                
                config_data["gpt_sovits"]["api_0322"]["ref_audio_path"] = input_gpt_sovits_api_0322_ref_audio_path.value
                config_data["gpt_sovits"]["api_0322"]["prompt_text"] = input_gpt_sovits_api_0322_prompt_text.value
                config_data["gpt_sovits"]["api_0322"]["prompt_lang"] = select_gpt_sovits_api_0322_prompt_lang.value
                config_data["gpt_sovits"]["api_0322"]["text_lang"] = select_gpt_sovits_api_0322_text_lang.value
                config_data["gpt_sovits"]["api_0322"]["text_split_method"] = select_gpt_sovits_api_0322_text_split_method.value
                config_data["gpt_sovits"]["api_0322"]["top_k"] = int(input_gpt_sovits_api_0322_top_k.value)
                config_data["gpt_sovits"]["api_0322"]["top_p"] = round(float(input_gpt_sovits_api_0322_top_p.value), 2)
                config_data["gpt_sovits"]["api_0322"]["temperature"] = round(float(input_gpt_sovits_api_0322_temperature.value), 2)
                config_data["gpt_sovits"]["api_0322"]["batch_size"] = int(input_gpt_sovits_api_0322_batch_size.value)
                config_data["gpt_sovits"]["api_0322"]["speed_factor"] = round(float(input_gpt_sovits_api_0322_speed_factor.value), 2)
                config_data["gpt_sovits"]["api_0322"]["fragment_interval"] = input_gpt_sovits_api_0322_fragment_interval.value
                config_data["gpt_sovits"]["api_0322"]["split_bucket"] = switch_gpt_sovits_api_0322_split_bucket.value
                config_data["gpt_sovits"]["api_0322"]["return_fragment"] = switch_gpt_sovits_api_0322_return_fragment.value
                
                config_data["gpt_sovits"]["webtts"]["version"] = select_gpt_sovits_webtts_version.value
                config_data["gpt_sovits"]["webtts"]["api_ip_port"] = input_gpt_sovits_webtts_api_ip_port.value
                config_data["gpt_sovits"]["webtts"]["spk"] = input_gpt_sovits_webtts_spk.value
                config_data["gpt_sovits"]["webtts"]["lang"] = select_gpt_sovits_webtts_lang.value
                config_data["gpt_sovits"]["webtts"]["speed"] = input_gpt_sovits_webtts_speed.value
                config_data["gpt_sovits"]["webtts"]["emotion"] = input_gpt_sovits_webtts_emotion.value
            """
            UI配置
            """
            if True:
                config_data["webui"]["title"] = input_webui_title.value
                config_data["webui"]["ip"] = input_webui_ip.value
                config_data["webui"]["port"] = int(input_webui_port.value)
                config_data["webui"]["auto_run"] = switch_webui_auto_run.value

                config_data["webui"]["theme"]["choose"] = select_webui_theme_choose.value

        except Exception as e:
            logging.error(f"无法写入配置文件！\n{e}")
            ui.notify(position="top", type="negative", message=f"无法写入配置文件！\n{e}")
            logging.error(traceback.format_exc())


        # 写入配置到配置文件
        try:
            with open(config_path, 'w', encoding="utf-8") as config_file:
                json.dump(config_data, config_file, indent=2, ensure_ascii=False)
                config_file.flush()  # 刷新缓冲区，确保写入立即生效

            logging.info("配置数据已成功写入文件！")
            ui.notify(position="top", type="positive", message="配置数据已成功写入文件！")

            return True
        except Exception as e:
            logging.error(f"无法写入配置文件！\n{e}")
            ui.notify(position="top", type="negative", message=f"无法写入配置文件！\n{e}")
            return False
    

    def talk_with_chatgpt(content):
        if content == "":
            return
        
        
        from utils.chatgpt import Chatgpt
        chatgpt = Chatgpt(config.get("openai"), config.get("chatgpt"))

        resp_content = chatgpt.get_gpt_resp("主人", content)

        textarea_talk_resp_content.value = resp_content

    def talk_with_online(content):
        
        from utils.search_online import SEARCH_ONLINE

        search_online = SEARCH_ONLINE()

        data_list = search_online.google(content, 1)
        summary_list = search_online.get_summary_list(data_list, 1)

        logging.info(f"{summary_list}")

        textarea_talk_resp_content.value = summary_list[0]

    def talk_with_online_chatgpt(content):
        from utils.search_online import SEARCH_ONLINE
        from utils.chatgpt import Chatgpt
        from datetime import datetime

        chatgpt = Chatgpt(config.get("openai"), config.get("chatgpt"))
        search_online = SEARCH_ONLINE()

        data_list = search_online.google(content, 1)
        logging.info(f"搜索结果：{data_list}")
        summary_list = search_online.get_summary_list(data_list, 1)

        summary_content = ""

        for summary in summary_list:
            summary_content += summary

        current_date = datetime.now().strftime("%Y年%m月%d日")
        # prompt = f"""当前中国北京日期：{current_date}，请判断并提取内容中与"{summary_content}"有关的详细内容，必须保留细节，准确的时间线以及富有逻辑的排版！如果与时间、前因后果、上下文等有关内容不能忽略，不可以胡编乱造！"""

        prompt = config.get("chatgpt", "prompt_template")
        # 提前定义所有可能的关键字参数
        format_args = {
            "current_date": current_date if current_date else "",
            "summary_content": summary_content if summary_content else "",
            "recorder_content": content if content else ""
        }

        # 一次性使用 .format 方法替换所有占位符
        prompt = prompt.format(**format_args)

        # prompt = f'当前中国北京日期：{current_date}，根据以下数据进行总结并提供答案。如果问题与数据不相关，使用你的常规知识回答，不可以胡编乱造！。\n参考数据：{summary_content}\n问题：{recorder_content}'

        resp_content = chatgpt.get_gpt_resp("主人", prompt)
        logging.info(f"AI回复：{resp_content}")

        textarea_talk_resp_content.value = resp_content

    # GPT-SoVITS加载模型
    def gpt_sovits_set_model():
        try:
            from urllib.parse import urljoin

            API_URL = urljoin(input_gpt_sovits_api_ip_port.value, '/set_model')

            data_json = {
                "gpt_model_path": input_gpt_sovits_gpt_model_path.value,
                "sovits_model_path": input_gpt_sovits_sovits_model_path.value
            }
            
            resp_data = common.send_request(API_URL, "POST", data_json, resp_data_type="content")

            if resp_data is None:
                content = "gpt_sovits加载模型失败，请查看双方日志排查问题"
                logging.error(content)
                ui.notify(position="top", type="negative", message=content)
            else:
                content = "gpt_sovits加载模型成功"
                logging.info(content)
                ui.notify(position="top", type="positive", message=content)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f'gpt_sovits未知错误: {e}')
            ui.notify(position="top", type="negative", message=f'gpt_sovits未知错误: {e}')


    """

    ..............................................................................................................
    ..............................................................................................................
    ..........................,]].................................................................................
    .........................O@@@@^...............................................................................
    .....=@@@@@`.....O@@@....,\@@[.....................................,@@@@@@@@@@]....O@@@^......=@@@@....O@@@^..
    .....=@@@@@@.....O@@@............................................=@@@@/`..,[@@/....O@@@^......=@@@@....O@@@^..
    .....=@@@@@@@....O@@@....,]]]].......]@@@@@]`.....,/@@@@\`....../@@@@..............O@@@^......=@@@@....O@@@^..
    .....=@@@/@@@\...O@@@....=@@@@....,@@@@@@@@@@^..,@@@@@@@@@@\...=@@@@...............O@@@^......=@@@@....O@@@^..
    .....=@@@^,@@@\..O@@@....=@@@@...,@@@@`........=@@@/....=@@@\..=@@@@....]]]]]]]]...O@@@^......=@@@@....O@@@^..
    .....=@@@^.=@@@^.O@@@....=@@@@...O@@@^.........@@@@......@@@@..=@@@@....=@@@@@@@...O@@@^......=@@@@....O@@@^..
    .....=@@@^..\@@@^=@@@....=@@@@...@@@@^........,@@@@@@@@@@@@@@..=@@@@.......=@@@@...O@@@^......=@@@@....O@@@^..
    .....=@@@^...\@@@/@@@....=@@@@...O@@@^.........@@@@`...........,@@@@`......=@@@@...O@@@^......=@@@@....O@@@^..
    .....=@@@^....@@@@@@@....=@@@@...,@@@@`........=@@@@......,.....=@@@@`.....=@@@@...=@@@@`.....@@@@^....O@@@^..
    .....=@@@^....,@@@@@@....=@@@@....,@@@@@@@@@@`..=@@@@@@@@@@@`....,@@@@@@@@@@@@@@....,@@@@@@@@@@@@`.....O@@@^..
    .....,[[[`.....,[[[[[....,[[[[.......[@@@@@[`.....,[@@@@@[`.........,\@@@@@@[`.........[@@@@@@[........[[[[`..
    ..............................................................................................................
    ..............................................................................................................

    """
    # 聊天类型所有配置项
    chat_type_options = {
        # 'none': '不启用', 
        # 'reread': '复读机', 
        'chatgpt': 'ChatGPT等OpenAI接口', 
        # 'claude': 'Claude', 
        # 'claude2': 'Claude2',
        # 'chatglm': 'ChatGLM',
        # 'qwen': 'Qwen',
        # 'chat_with_file': 'chat_with_file',
        # 'chatterbot': 'Chatterbot',
        # 'text_generation_webui': 'text_generation_webui',
        # 'sparkdesk': '讯飞星火',
        # 'langchain_chatglm': 'langchain_chatglm',
        # 'langchain_chatchat': 'langchain_chatchat',
        'zhipu': '智谱AI',
        # 'bard': 'Bard',
        # 'yiyan': '文心一言',
        # 'tongyixingchen': '通义星尘',
        # 'my_wenxinworkshop': '千帆大模型',
        # 'gemini': 'Gemini',
        # 'qanything': 'QAnything',
        # 'koboldcpp': 'koboldcpp',
        # 'anythingllm': 'AnythingLLM',
        # 'tongyi': '通义千问',
        # 'gpt4free': 'GPT4Free',
        # 'custom_llm': '自定义LLM',
    }

    # 语音合成所有配置项
    audio_synthesis_type_options = {
        'edge-tts': 'Edge-TTS', 
        # 'vits': 'VITS', 
        # 'bert_vits2': 'bert_vits2',
        # 'vits_fast': 'VITS-Fast', 
        # 'elevenlabs': 'elevenlabs',
        # 'genshinvoice_top': 'genshinvoice_top',
        # 'tts_ai_lab_top': 'tts_ai_lab_top',
        # 'bark_gui': 'bark_gui',
        # 'vall_e_x': 'VALL-E-X',
        # 'openai_tts': 'OpenAI TTS',
        # 'reecho_ai': '睿声AI',
        # 'gradio_tts': 'Gradio',
        'gpt_sovits': 'GPT_SoVITS',
        #'clone_voice': 'clone-voice'
    }

    with ui.tabs().classes('w-full') as tabs:
        common_config_page = ui.tab('通用配置')
        talk_page = ui.tab('聊天')
        web_page = ui.tab('页面配置')
        about_page = ui.tab('关于')

    with ui.tab_panels(tabs, value=common_config_page).classes('w-full'):
        with ui.tab_panel(common_config_page).style(tab_panel_css):
            with ui.row():
                select_run_py = ui.select(
                    label='运行py程序', 
                    options={
                        'RealtimeSTT_server': 'RealtimeSTT_server',
                        'RealtimeSTT_server2': 'RealtimeSTT_server2'
                    }, 
                    value=config.get("run_py")
                ).style("width:200px;")

                select_chat_type = ui.select(
                    label='聊天类型', 
                    options=chat_type_options, 
                    value=config.get("chat_type")
                ).style("width:200px;").tooltip('选用的LLM类型。相关的弹幕信息等会传递给此LLM进行推理，获取回答')

                select_audio_synthesis_type = ui.select(
                    label='语音合成', 
                    options=audio_synthesis_type_options, 
                    value=config.get("audio_synthesis_type")
                ).style("width:200px;")
            with ui.card().style("display:none"):
                ui.label("录音配置")
                with ui.row():
                    audio_device_info_list = common.get_all_audio_device_info("in")
                    # logging.info(f"audio_device_info_list={audio_device_info_list}")
                    audio_device_info_dict = {str(device['device_index']): device['device_info'] for device in audio_device_info_list}

                    logging.info(f"声卡输入设备={audio_device_info_dict}")

                    input_recorder_device_index = ui.input(label='输入音频设备', value=config.get("recorder", "device_index"), placeholder='输入音频设备索引值').style("width:250px;")
                    
                    # select_recorder_device_index = ui.select(
                    #     label='声卡输入设备', 
                    #     options=audio_device_info_dict, 
                    #     value=config.get("recorder", "device_index")
                    # ).style("width:300px;")
                with ui.row():
                    textarea_recorder_start_cmd = ui.textarea(label='开始记录录音命令', value=textarea_data_change(config.get("recorder", "start_cmd")), placeholder='开始记录录音数据的命令，支持多个，换行进行分隔').style("width:400px;")
                    textarea_recorder_stop_cmd = ui.textarea(label='停止记录录音命令', value=textarea_data_change(config.get("recorder", "stop_cmd")), placeholder='停止记录录音数据的命令，支持多个，换行进行分隔').style("width:400px;")
                    textarea_recorder_drop_cmd = ui.textarea(label='丢弃记录录音命令', value=textarea_data_change(config.get("recorder", "drop_cmd")), placeholder='丢弃记录录音数据的命令，支持多个，换行进行分隔').style("width:400px;")
                    textarea_recorder_get_mouse_coordinate_cmd = ui.textarea(label='获取鼠标坐标命令', value=textarea_data_change(config.get("recorder", "get_mouse_coordinate_cmd")), placeholder='获取鼠标坐标命令，支持多个，换行进行分隔').style("width:400px;")

            with ui.expansion('智谱AI', icon="settings", value=True).classes('w-full'):

                with ui.row():
                    input_zhipu_api_key = ui.input(label='api key', placeholder='具体参考官方文档，申请地址：https://open.bigmodel.cn/usercenter/apikeys', value=config.get("zhipu", "api_key"))
                    input_zhipu_api_key.style("width:200px")
                    lines = ['glm-3-turbo', 'glm-4', 'characterglm', 'chatglm_turbo', 'chatglm_pro', 'chatglm_std', 'chatglm_lite', 'chatglm_lite_32k', '应用']
                    data_json = {}
                    for line in lines:
                        data_json[line] = line
                    select_zhipu_model = ui.select(
                        label='模型', 
                        options=data_json, 
                        value=config.get("zhipu", "model"),
                        with_input=True,
                        new_value_mode='add-unique',
                        clearable=True
                    )
                    input_zhipu_app_id = ui.input(label='应用ID', value=config.get("zhipu", "app_id"), placeholder='在 模型为：应用，会自动检索你平台上添加的所有应用信息，然后从日志中复制你需要的应用ID即可').style("width:200px")
                    
                with ui.row():
                    input_zhipu_system = ui.input(label='system预设', placeholder='system预设', value=config.get("zhipu", "system"))
                    input_zhipu_system.style("width:200px")
                    
                    input_zhipu_top_p = ui.input(label='top_p', placeholder='用温度取样的另一种方法，称为核取样\n取值范围是：(0.0,1.0)；开区间，不能等于 0 或 1，默认值为 0.7\n模型考虑具有 top_p 概率质量的令牌的结果。所以 0.1 意味着模型解码器只考虑从前 10% 的概率的候选集中取tokens\n建议您根据应用场景调整 top_p 或 temperature 参数，但不要同时调整两个参数', value=config.get("zhipu", "top_p"))
                    input_zhipu_top_p.style("width:200px")
                    input_zhipu_temperature = ui.input(label='temperature', placeholder='采样温度，控制输出的随机性，必须为正数\n取值范围是：(0.0,1.0]，不能等于 0,默认值为 0.95\n值越大，会使输出更随机，更具创造性；值越小，输出会更加稳定或确定\n建议您根据应用场景调整 top_p 或 temperature 参数，但不要同时调整两个参数', value=config.get("zhipu", "temperature"))
                    input_zhipu_temperature.style("width:200px")
                    switch_zhipu_history_enable = ui.switch('上下文记忆', value=config.get("zhipu", "history_enable")).style(switch_internal_css)
                    input_zhipu_history_max_len = ui.input(label='最大记忆长度', placeholder='最长能记忆的问答字符串长度，超长会丢弃最早记忆的内容，请慎用！配置过大可能会有丢大米', value=config.get("zhipu", "history_max_len"))
                    input_zhipu_history_max_len.style("width:200px")
                with ui.row():
                    input_zhipu_user_info = ui.input(label='用户信息', placeholder='用户信息，当使用characterglm时需要配置', value=config.get("zhipu", "user_info"))
                    input_zhipu_user_info.style("width:400px")
                    input_zhipu_bot_info = ui.input(label='角色信息', placeholder='角色信息，当使用characterglm时需要配置', value=config.get("zhipu", "bot_info"))
                    input_zhipu_bot_info.style("width:400px")
                    input_zhipu_bot_name = ui.input(label='角色名称', placeholder='角色名称，当使用characterglm时需要配置', value=config.get("zhipu", "bot_name"))
                    input_zhipu_bot_name.style("width:200px")
                    input_zhipu_username = ui.input(label='用户名称', placeholder='用户名称，默认值为用户，当使用characterglm时需要配置', value=config.get("zhipu", "username"))
                    input_zhipu_username.style("width:200px")
                with ui.row():
                    switch_zhipu_remove_useless = ui.switch('删除无用字符', value=config.get("zhipu", "remove_useless")).style(switch_internal_css)
            
            with ui.expansion('ChatGPT | 闻达 | ChatGLM3 | Kimi Chat | Ollama | One-API等OpenAI接口模型', icon="settings", value=True).classes('w-full'):

                with ui.row():
                    input_openai_api = ui.input(label='API地址', placeholder='API请求地址，支持代理', value=config.get("openai", "api")).style("width:200px;")
                    textarea_openai_api_key = ui.textarea(label='API密钥', placeholder='API KEY，支持代理', value=textarea_data_change(config.get("openai", "api_key"))).style("width:400px;").tooltip("可以配置多行，但暂时仅支持第一个密钥")
                with ui.row():
                    chatgpt_models = [
                        "gpt-3.5-turbo",
                        "gpt-3.5-turbo-0301",
                        "gpt-3.5-turbo-0613",
                        "gpt-3.5-turbo-1106",
                        "gpt-3.5-turbo-16k",
                        "gpt-3.5-turbo-16k-0613",
                        "gpt-3.5-turbo-instruct",
                        "gpt-3.5-turbo-instruct-0914",
                        "gpt-4",
                        "gpt-4-0314",
                        "gpt-4-0613",
                        "gpt-4-32k",
                        "gpt-4-32k-0314",
                        "gpt-4-32k-0613",
                        "gpt-4-1106-preview",
                        "text-embedding-ada-002",
                        "text-davinci-003",
                        "text-davinci-002",
                        "text-curie-001",
                        "text-babbage-001",
                        "text-ada-001",
                        "text-moderation-latest",
                        "text-moderation-stable"
                    ]
                    data_json = {}
                    for line in chatgpt_models:
                        data_json[line] = line
                    select_chatgpt_model = ui.select(
                        label='模型', 
                        options=data_json, 
                        value=config.get("chatgpt", "model")
                    )
                    input_chatgpt_temperature = ui.input(label='温度', placeholder='控制生成文本的随机性。较高的温度值会使生成的文本更随机和多样化，而较低的温度值会使生成的文本更加确定和一致。', value=config.get("chatgpt", "temperature")).style("width:200px;")
                    input_chatgpt_max_tokens = ui.input(label='最大token数', placeholder='限制生成回答的最大长度。', value=config.get("chatgpt", "max_tokens")).style("width:200px;")
                    input_chatgpt_top_p = ui.input(label='前p个选择', placeholder='Nucleus采样。这个参数控制模型从累积概率大于一定阈值的令牌中进行采样。较高的值会产生更多的多样性，较低的值会产生更少但更确定的回答。', value=config.get("chatgpt", "top_p")).style("width:200px;")
                with ui.row():
                    input_chatgpt_presence_penalty = ui.input(label='存在惩罚', placeholder='控制模型生成回答时对给定问题提示的关注程度。较高的存在惩罚值会减少模型对给定提示的重复程度，鼓励模型更自主地生成回答。', value=config.get("chatgpt", "presence_penalty")).style("width:200px;")
                    input_chatgpt_frequency_penalty = ui.input(label='频率惩罚', placeholder='控制生成回答时对已经出现过的令牌的惩罚程度。较高的频率惩罚值会减少模型生成已经频繁出现的令牌，以避免重复和过度使用特定词语。', value=config.get("chatgpt", "frequency_penalty")).style("width:200px;")

                    input_chatgpt_preset = ui.input(label='预设', placeholder='用于指定一组预定义的设置，以便模型更好地适应特定的对话场景。', value=config.get("chatgpt", "preset")).style("width:500px") 
                # with ui.row():
                #     input_chatgpt_prompt_template = ui.input(label='提示词模板', placeholder='提示词模板，在每次提问时会使用此模板包装数据，{}内是变量数据，请勿随意删除', value=config.get("chatgpt", "prompt_template")).style("width:1000px") 

            with ui.expansion('Edge-TTS', icon="settings", value=True).classes('w-full'):

                with ui.row():
                    with open('data/edge-tts-voice-list.txt', 'r') as file:
                        file_content = file.read()
                    # 按行分割内容，并去除每行末尾的换行符
                    lines = file_content.strip().split('\n')
                    data_json = {}
                    for line in lines:
                        data_json[line] = line
                    select_edge_tts_voice = ui.select(
                        label='说话人', 
                        options=data_json, 
                        value=config.get("edge-tts", "voice")
                    )

                    input_edge_tts_rate = ui.input(label='语速增益', placeholder='语速增益 默认是 +0%，可以增减，注意 + - %符合别搞没了，不然会影响语音合成', value=config.get("edge-tts", "rate")).style("width:200px;")

                    input_edge_tts_volume = ui.input(label='音量增益', placeholder='音量增益 默认是 +0%，可以增减，注意 + - %符合别搞没了，不然会影响语音合成', value=config.get("edge-tts", "volume")).style("width:200px;")
        
        
            with ui.expansion('GPT-SoVITS', icon="settings", value=True).classes('w-full'):

                with ui.row():
                    select_gpt_sovits_type = ui.select(
                        label='API类型', 
                        options={'gradio':'gradio旧版', 'gradio_0322':'gradio_0322', 'api':'api', 'api_0322':'api_0322', 'webtts':'WebTTS'}, 
                        value=config.get("gpt_sovits", "type")
                    ).style("width:100px;")
                    input_gpt_sovits_gradio_ip_port = ui.input(
                        label='Gradio API地址', 
                        value=config.get("gpt_sovits", "gradio_ip_port"), 
                        placeholder='官方webui程序启动后gradio监听的地址',
                        validation={
                            '请输入正确格式的URL': lambda value: common.is_url_check(value),
                        }
                    ).style("width:200px;")
                    input_gpt_sovits_api_ip_port = ui.input(
                        label='API地址（http）', 
                        value=config.get("gpt_sovits", "api_ip_port"), 
                        placeholder='官方API程序启动后监听的地址',
                        validation={
                            '请输入正确格式的URL': lambda value: common.is_url_check(value),
                        }
                    ).style("width:200px;")
                    input_gpt_sovits_ws_ip_port = ui.input(label='WS地址（gradio）', value=config.get("gpt_sovits", "ws_ip_port"), placeholder='启动TTS推理后，ws的接口地址').style("width:200px;")
                    
                
                with ui.row():
                    input_gpt_sovits_gpt_model_path = ui.input(label='GPT模型路径', value=config.get("gpt_sovits", "gpt_model_path"), placeholder='GPT模型路径，填绝对路径').style("width:300px;")
                    input_gpt_sovits_sovits_model_path = ui.input(label='SOVITS模型路径', value=config.get("gpt_sovits", "sovits_model_path"), placeholder='SOVITS模型路径，填绝对路径').style("width:300px;")
                    button_gpt_sovits_set_model = ui.button('加载模型', on_click=gpt_sovits_set_model, color=button_internal_color).style(button_internal_css)
                
                with ui.card().style(card_css):
                    ui.label("api")
                    with ui.row():
                        input_gpt_sovits_ref_audio_path = ui.input(label='参考音频路径', value=config.get("gpt_sovits", "ref_audio_path"), placeholder='参考音频路径，建议填绝对路径').style("width:300px;")
                        input_gpt_sovits_prompt_text = ui.input(label='参考音频的文本', value=config.get("gpt_sovits", "prompt_text"), placeholder='参考音频的文本').style("width:200px;")
                        select_gpt_sovits_prompt_language = ui.select(
                            label='参考音频的语种', 
                            options={'中文':'中文', '日文':'日文', '英文':'英文'}, 
                            value=config.get("gpt_sovits", "prompt_language")
                        ).style("width:150px;")
                        select_gpt_sovits_language = ui.select(
                            label='需要合成的语种', 
                            options={'自动识别':'自动识别', '中文':'中文', '日文':'日文', '英文':'英文'}, 
                            value=config.get("gpt_sovits", "language")
                        ).style("width:150px;")
                        select_gpt_sovits_cut = ui.select(
                            label='语句切分', 
                            options={
                                '不切':'不切', 
                                '凑四句一切':'凑四句一切', 
                                '凑50字一切':'凑50字一切', 
                                '按中文句号。切':'按中文句号。切', 
                                '按英文句号.切':'按英文句号.切',
                                '按标点符号切':'按标点符号切'
                            }, 
                            value=config.get("gpt_sovits", "cut")
                        ).style("width:200px;")
                
                with ui.card().style(card_css):
                    ui.label("api_0322 | gradio_0322")
                    with ui.row():
                        input_gpt_sovits_api_0322_ref_audio_path = ui.input(label='参考音频路径', value=config.get("gpt_sovits", "api_0322", "ref_audio_path"), placeholder='参考音频路径，建议填绝对路径').style("width:300px;")
                        input_gpt_sovits_api_0322_prompt_text = ui.input(label='参考音频的文本', value=config.get("gpt_sovits", "api_0322", "prompt_text"), placeholder='参考音频的文本').style("width:200px;")
                        select_gpt_sovits_api_0322_prompt_lang = ui.select(
                            label='参考音频的语种', 
                            options={'中文':'中文', '日文':'日文', '英文':'英文'}, 
                            value=config.get("gpt_sovits", "api_0322", "prompt_lang")
                        ).style("width:150px;")
                        select_gpt_sovits_api_0322_text_lang = ui.select(
                            label='需要合成的语种', 
                            options={
                                '自动识别':'自动识别', 
                                '中文':'中文', 
                                '日文':'日文', 
                                '英文':'英文', 
                                '中英混合': '中英混合',
                                '日英混合': '日英混合',
                                '多语种混合': '多语种混合',
                            }, 
                            value=config.get("gpt_sovits", "api_0322", "text_lang")
                        ).style("width:150px;")
                        select_gpt_sovits_api_0322_text_split_method = ui.select(
                            label='语句切分', 
                            options={
                                '不切':'不切', 
                                '凑四句一切':'凑四句一切', 
                                '凑50字一切':'凑50字一切', 
                                '按中文句号。切':'按中文句号。切', 
                                '按英文句号.切':'按英文句号.切',
                                '按标点符号切':'按标点符号切'
                            }, 
                            value=config.get("gpt_sovits", "api_0322", "text_split_method")
                        ).style("width:200px;")
                    with ui.row():
                        input_gpt_sovits_api_0322_top_k = ui.input(label='top_k', value=config.get("gpt_sovits", "api_0322", "top_k"), placeholder='top_k').style("width:100px;")
                        input_gpt_sovits_api_0322_top_p = ui.input(label='top_p', value=config.get("gpt_sovits", "api_0322", "top_p"), placeholder='top_p').style("width:100px;")
                        input_gpt_sovits_api_0322_temperature = ui.input(label='temperature', value=config.get("gpt_sovits", "api_0322", "temperature"), placeholder='temperature').style("width:100px;")
                        input_gpt_sovits_api_0322_batch_size = ui.input(label='batch_size', value=config.get("gpt_sovits", "api_0322", "batch_size"), placeholder='batch_size').style("width:100px;")
                        input_gpt_sovits_api_0322_speed_factor = ui.input(label='speed_factor', value=config.get("gpt_sovits", "api_0322", "speed_factor"), placeholder='speed_factor').style("width:100px;")
                        input_gpt_sovits_api_0322_fragment_interval = ui.input(label='分段间隔(秒)', value=config.get("gpt_sovits", "api_0322", "fragment_interval"), placeholder='fragment_interval').style("width:100px;")
                        switch_gpt_sovits_api_0322_split_bucket = ui.switch('split_bucket', value=config.get("gpt_sovits", "api_0322", "split_bucket")).style(switch_internal_css)
                        switch_gpt_sovits_api_0322_return_fragment = ui.switch('return_fragment', value=config.get("gpt_sovits", "api_0322", "return_fragment")).style(switch_internal_css)
                    

                with ui.card().style(card_css):
                    ui.label("WebTTS相关配置")
                    with ui.row():
                        select_gpt_sovits_webtts_version = ui.select(
                            label='版本', 
                            options={
                                '1':'1', 
                                '1.4':'1.4', 
                                '2':'2'
                            }, 
                            value=config.get("gpt_sovits", "webtts", "version")
                        ).style("width:80px;")
                        input_gpt_sovits_webtts_api_ip_port = ui.input(label='API地址', value=config.get("gpt_sovits", "webtts", "api_ip_port"), placeholder='API监听地址').style("width:200px;")
                        input_gpt_sovits_webtts_spk = ui.input(label='音色', value=config.get("gpt_sovits", "webtts", "spk"), placeholder='音色').style("width:100px;")
                        select_gpt_sovits_webtts_lang = ui.select(
                            label='语言', 
                            options={
                                'zh':'中文', 
                                'en':'英文', 
                                'jp':'日文'
                            }, 
                            value=config.get("gpt_sovits", "webtts", "lang")
                        ).style("width:100px;")
                        input_gpt_sovits_webtts_speed = ui.input(label='语速', value=config.get("gpt_sovits", "webtts", "speed"), placeholder='语速').style("width:100px;")
                        input_gpt_sovits_webtts_emotion = ui.input(label='情感', value=config.get("gpt_sovits", "webtts", "emotion"), placeholder='情感').style("width:100px;")
    
                # ui.label("OpenAI TTS")
                # with ui.row():
                #     select_openai_tts_type = ui.select(
                #         label='类型', 
                #         options={'api': 'api', 'huggingface': 'huggingface'}, 
                #         value=config.get("openai_tts", "type")
                #     ).style("width:200px;")
                #     input_openai_tts_api_ip_port = ui.input(label='API地址', value=config.get("openai_tts", "api_ip_port"), placeholder='huggingface上对应项目的API地址').style("width:200px;")
                # with ui.row():
                #     select_openai_tts_model = ui.select(
                #         label='模型', 
                #         options={'tts-1': 'tts-1', 'tts-1-hd': 'tts-1-hd'}, 
                #         value=config.get("openai_tts", "model")
                #     ).style("width:200px;")
                #     select_openai_tts_voice = ui.select(
                #         label='说话人', 
                #         options={'alloy': 'alloy', 'echo': 'echo', 'fable': 'fable', 'onyx': 'onyx', 'nova': 'nova', 'shimmer': 'shimmer'}, 
                #         value=config.get("openai_tts", "voice")
                #     ).style("width:200px;")
                #     input_openai_tts_api_key = ui.input(label='api key', value=config.get("openai_tts", "api_key"), placeholder='OpenAI API KEY').style("width:300px;")
        
        with ui.tab_panel(talk_page).style(tab_panel_css):
            with ui.card().style(card_css):
                with ui.row():
                    input_talk_content = ui.input(label='输入框', placeholder='需要提问的内容', value="").style("width:1000px;")
                    ui.button("问ChatGPT", on_click=lambda: talk_with_chatgpt(input_talk_content.value))
                    ui.button("联网搜索", on_click=lambda: talk_with_online(input_talk_content.value))
                    ui.button("联网+ChatGPT", on_click=lambda: talk_with_online_chatgpt(input_talk_content.value))
                    textarea_talk_resp_content = ui.textarea(label='AI回复', value="", placeholder='显示AI回复的内容').style("width:1000px;")
                    

        with ui.tab_panel(web_page).style(tab_panel_css):
            with ui.card().style(card_css):
                ui.label("webui配置")
                with ui.row():
                    input_webui_title = ui.input(label='标题', placeholder='webui的标题', value=config.get("webui", "title")).style("width:250px;")
                    input_webui_ip = ui.input(label='IP地址', placeholder='webui监听的IP地址', value=config.get("webui", "ip")).style("width:150px;")
                    input_webui_port = ui.input(label='端口', placeholder='webui监听的端口', value=config.get("webui", "port")).style("width:100px;")
                    switch_webui_auto_run = ui.switch('自动运行', value=config.get("webui", "auto_run")).style(switch_internal_css)

            with ui.card().style(card_css):
                ui.label("CSS")
                with ui.row():
                    theme_list = config.get("webui", "theme", "list").keys()
                    data_json = {}
                    for line in theme_list:
                        data_json[line] = line
                    select_webui_theme_choose = ui.select(
                        label='主题', 
                        options=data_json, 
                        value=config.get("webui", "theme", "choose")
                    )

     
        with ui.tab_panel(about_page).style(tab_panel_css):
            with ui.card().style(card_css):
                ui.label('注意').style("font-size:24px;")
                ui.label('严禁将此项目用于一切违反《中华人民共和国宪法》，《中华人民共和国刑法》，《中华人民共和国治安管理处罚法》和《中华人民共和国民法典》之用途。')
                ui.label('严禁用于任何政治相关用途。')
    with ui.grid(columns=6).style("position: fixed; bottom: 10px; text-align: center;"):
        button_save = ui.button('保存配置', on_click=lambda: save_config(), color=button_bottom_color).style(button_bottom_css)
        button_run = ui.button('一键运行', on_click=lambda: run_external_program(), color=button_bottom_color).style(button_bottom_css)
        # 创建一个按钮，用于停止正在运行的程序
        button_stop = ui.button("停止运行", on_click=lambda: stop_external_program(), color=button_bottom_color).style(button_bottom_css)
        button_light = ui.button('关灯', on_click=lambda: change_light_status(), color=button_bottom_color).style(button_bottom_css)
        # button_stop.enabled = False  # 初始状态下停止按钮禁用
        restart_light = ui.button('重启', on_click=lambda: restart_application(), color=button_bottom_color).style(button_bottom_css)
        # factory_btn = ui.button('恢复出厂配置', on_click=lambda: factory(), color=button_bottom_color).style(tab_panel_css)

    with ui.row().style("position:fixed; bottom: 20px; right: 20px;"):
        ui.button('⇧', on_click=lambda: scroll_to_top(), color=button_bottom_color).style(button_bottom_css)

    # 是否启用自动运行功能
    if config.get("webui", "auto_run"):
        logging.info("自动运行 已启用")
        run_external_program(type="api")


goto_func_page()

ui.run(host=webui_ip, port=webui_port, title=webui_title, language="zh-CN", dark=False, reload=False)
