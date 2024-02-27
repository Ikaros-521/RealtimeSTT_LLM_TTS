# 导入所需的库
import re, random, requests, json
import time
import os
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import traceback
import langid

from urllib.parse import urlparse

import difflib, pyaudio

import shutil


class Common:
    def __init__(self):  
        self.count = 1

    """
    数字操作
    """

    # 获取北京时间
    def get_bj_time(self, type=0):
        """获取北京时间

        Args:
            type (int, str): 返回时间类型. 默认为 0.
                0 返回数据：年-月-日 时:分:秒
                1 返回数据：年-月-日
                2 返回数据：当前时间的秒
                3 返回数据：自1970年1月1日以来的秒数
                4 返回数据：根据调用次数计数到100循环
                5 返回数据：当前 时点分
                6 返回数据：当前时间的 时, 分

        Returns:
            str: 返回指定格式的时间字符串
            int, int
        """
        if type == 0:
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)  # 获取当前 UTC 时间
            SHA_TZ = timezone(
                timedelta(hours=8),
                name='Asia/Shanghai',
            )
            beijing_now = utc_now.astimezone(SHA_TZ)  # 将 UTC 时间转换为北京时间
            fmt = '%Y-%m-%d %H:%M:%S'
            now_fmt = beijing_now.strftime(fmt)
            return now_fmt
        elif type == 1:
            now = datetime.now()  # 获取当前时间
            year = now.year  # 获取当前年份
            month = now.month  # 获取当前月份
            day = now.day  # 获取当前日期

            return str(year) + "-" + str(month) + "-" + str(day)
        elif type == 2:
            now = time.localtime()  # 获取当前时间

            # hour = now.tm_hour   # 获取当前小时
            # minute = now.tm_min  # 获取当前分钟 
            second = now.tm_sec  # 获取当前秒数

            return str(second)
        elif type == 3:
            current_time = time.time()  # 返回自1970年1月1日以来的秒数

            return str(current_time)
        elif type == 4:
            self.count = (self.count % 100) + 1

            return str(self.count)
        elif type == 5:
            now = time.localtime()  # 获取当前时间

            hour = now.tm_hour   # 获取当前小时
            minute = now.tm_min  # 获取当前分钟

            return str(hour) + "点" + str(minute) + "分"
        elif type == 6:
            now = time.localtime()  # 获取当前时间

            hour = now.tm_hour   # 获取当前小时
            minute = now.tm_min  # 获取当前分钟 

            return hour, minute
    
    def get_random_value(self, lower_limit, upper_limit):
        """获得2个数之间的随机值

        Args:
            lower_limit (float): 随机数下限
            upper_limit (float): 随机数上限

        Returns:
            float: 2个数之间的随机值
        """
        if lower_limit == upper_limit:
            return round(lower_limit, 2)

        if lower_limit > upper_limit:
            lower_limit, upper_limit = upper_limit, lower_limit

        random_float = round(random.uniform(lower_limit, upper_limit), 2)
        return random_float
    

    """
                                                                                                              
                   .,]`                    ]]]`            ,]]`                      .`    .]`                
                  ,@@@@                    @@@^            =@@^  .@@@@@@@@@@@@^      /@@@  /@@@               
         =@@@@@@@@@@@@@@@@@@@@@@^ O@@@@@@@@@@@@@@@@@@@@@ ..=@@\...@@@]]]]]]/@@^     =@@@` =@@@@@@@@@@@@@\     
         =@@@@@@@@@@@@@@@@@@@@@@^ O@@@@@@@@@@@@@@@@@@@@@ =@@@@@@^.@@@@@@@@@@@@^    ,@@@^ ,@@@@@@@@@@@@@@@     
             =@@@^      /@@@^            /@@@@@@\          =@@^ .@@@@@@O.@@@@@@@  ,@@@@^=@@@^=@@@.            
              =@@@^    =@@@/           ,@@@@@@@@@@`        =@@^..@@^.@@@.@@^.@@@ ,@@@@@^\@@` =@@@@@@@@@^      
               \@@@\ ./@@@/          ,@@@@`@@@^.@@@@`    /@@@@@@*@@@@@@@.@@@@@@@ =@@@@@^ \.  =@@@@@@@@@^      
                ,@@@@@@@@`         ,@@@@/  @@@^  =@@@@]  =@@@@/`      =@@O       .@.@@@^     =@@@.            
                 ]@@@@@@`        =@@@@@]]]]@@@\]]]]@@@@@^  =@@^ @@@@@@@@@@@@@@@@^   @@@^     =@@@@@@@@@@      
             ,/@@@@@@@@@@@@\`     ,@/.=@@@@@@@@@@@@^ \/.   =@@^    ,@@@@@@@@]       @@@^     =@@@@@@@@@@      
         =@@@@@@@@/.  .\@@@@@@@@`          @@@^          ,]/@@^,/@@@@`=@@@.\@@@@`   @@@^     =@@@.            
          ,@@@/`          ,\@@/.           @@@^          =@@@@` ,@[.  =@@@   ,\`    @@@^     =@@@.            
                                                                                                              

    """

    # 删除多余单词
    def remove_extra_words(self, text="", max_len=30, max_char_len=50):
        words = text.split()
        if len(words) > max_len:
            words = words[:max_len]  # 列表切片，保留前30个单词
            text = ' '.join(words) + '...'  # 使用join()函数将单词列表重新组合为字符串，并在末尾添加省略号
        return text[:max_char_len]


    # 本地敏感词检测 传入敏感词库文件路径和待检查的文本
    def check_sensitive_words(self, file_path, text):
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = [line.strip() for line in file.readlines()]

        for word in sensitive_words:
            if word in text:
                return True

        return False
    

    # 本地敏感词检测 Aho-Corasick 算法 传入敏感词库文件路径和待检查的文本
    # def check_sensitive_words2(self, file_path, text):
    #     with open(file_path, 'r', encoding='utf-8') as file:
    #         sensitive_words = [line.strip() for line in file.readlines()]

    #     # 创建 Aho-Corasick 自动机
    #     automaton = ahocorasick.Automaton()

    #     # 添加违禁词到自动机中
    #     for word in sensitive_words:
    #         automaton.add_word(word, word)

    #     # 构建自动机的转移函数和失效函数
    #     automaton.make_automaton()

    #     # 在文本中搜索违禁词
    #     for _, found_word in automaton.iter(text):
    #         logging.warning(f"命中本地违禁词：{found_word}")
    #         return found_word

    #     return None


    # 本地敏感词转拼音检测 传入敏感词库文件路径和待检查的文本
    def check_sensitive_words3(self, file_path, text):
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = [line.strip() for line in file.readlines()]

        pinyin_text = self.text2pinyin(text)
        # logging.info(f"pinyin_text={pinyin_text}")

        for word in sensitive_words:
            pinyin_word = self.text2pinyin(word)
            pattern = r'\b' + re.escape(pinyin_word) + r'\b'
            if re.search(pattern, pinyin_text):
                logging.warning(f"同音违禁拼音：{pinyin_word}")
                return True

        return False


    # 链接检测
    def is_url_check(self, text):
        parsed_url = urlparse(text)
        return all([parsed_url.scheme, parsed_url.netloc])

        # url_pattern = re.compile(r'(?i)((?:(?:https?|ftp):\/\/)?[^\s/$.?#]+\.[^\s>]+)')

        # if url_pattern.search(text):
        #     return True
        # else:
        #     return False


    # 语言检测 TODO:有内存泄漏风险
    def lang_check(self, text, need="none"):
        # 语言检测 一个是语言，一个是概率
        language, score = langid.classify(text)

        if need == "none":
            return language
        else:
            if language != need:
                return None
            else:
                return language


    # 判断字符串是否全为标点符号
    def is_punctuation_string(self, string):
        # 使用正则表达式匹配标点符号
        pattern = r'^[^\w\s]+$'
        return re.match(pattern, string) is not None
    
    # 判断字符串是否全为空格和特殊字符
    def is_all_space_and_punct(self, text):
        pattern = r'^[\s\W]+$'
        return re.match(pattern, text) is not None

    # 违禁词校验
    # def profanity_content(self, content):
    #     return profanity.contains_profanity(content)

    # 判断字符串是否以一个list中任意一个字符串打头
    def starts_with_any(self, string, prefixes):
        """判断字符串是否以一个list中任意一个字符串打头

        Args:
            string (str): 待判断的字符串
            prefixes (list): 匹配的字符串数组

        Returns:
            str: 命中的匹配到的字符串/None
        """
        try:
            for prefix in prefixes:
                if string.startswith(prefix):
                    return prefix
        except AttributeError as e:
            # 处理异常，例如打印错误消息或者返回 False
            logging.error(f"Error: {e}")
            return None
        
        return None

    # 中文语句切分(只根据特定符号切分)
    def split_sentences1(self, text):
        # 使用正则表达式切分句子
        # .的过滤可能会导致 序号类的回复被切分
        sentences = re.split('([。！？!?])', text)
        result = []
        for sentence in sentences:
            if sentence not in ["。", "！", "？", ".", "!", "?", ""]:
                result.append(sentence)
        
        # 替换换行
        result = [s.replace('\n', '。') for s in result]

        # print(result)
        return result
    

    # 文本切分算法 旧算法，有最大长度限制
    def split_sentences2(self, text):
        # 最大长度限制，超过后会强制切分
        max_limit_len = 40

        # 使用正则表达式切分句子
        sentences = re.split('([。！？!?])', text)
        result = []
        current_sentence = ""
        for i in range(len(sentences)):
            if sentences[i] not in ["。", "！", "？", ".", "!", "?", ""]:
                # 去除换行和空格
                sentence = sentences[i].replace('\n', '。')
                # 如果句子长度小于10个字，则与下一句合并
                if len(current_sentence) < 10:
                    current_sentence += sentence
                    # 如果合并后的句子长度超过max_limit_len个字，则进行二次切分
                    if len(current_sentence) > max_limit_len:
                        # 判断是否有分隔符可用于二次切分
                        if i+1 < len(sentences) and len(sentences[i+1]) > 0 and sentences[i+1][0] not in ["。", "！", "？", ".", "!", "?"]:
                            next_sentence = sentences[i+1].replace('\n', '。')
                            # 寻找常用分隔符进行二次切分
                            for separator in [",", "，", ";", "；"]:
                                if separator in next_sentence:
                                    split_index = next_sentence.index(separator) + 1
                                    current_sentence += next_sentence[:split_index]
                                    result.append(current_sentence)
                                    current_sentence = next_sentence[split_index:]
                                    break
                        else:
                            # 如果合并后的句子长度超过max_limit_len个字，进行二次切分
                            while len(current_sentence) > max_limit_len:
                                result.append(current_sentence[:max_limit_len])
                                current_sentence = current_sentence[max_limit_len:]
                else:
                    result.append(current_sentence)
                    current_sentence = sentence

        # 添加最后一句
        if current_sentence:
            result.append(current_sentence)

        # 2次切分长字符串
        result2 = []
        for string in result:
            if len(string) > max_limit_len:
                split_strings = re.split(r"[,，;；。！!]", string)
                result2.extend(split_strings)
            else:
                result2.append(string)

        return result2


    # 文本切分算法
    def split_sentences(self, text):
        # 使用正则表达式切分句子
        sentences = re.split(r'(?<=[。！？!?])', text)
        result = []
        current_sentence = ""
        
        for sentence in sentences:
            # 去除换行和空格
            sentence = sentence.replace('\n', '')
            
            # 如果句子为空则跳过
            if not sentence:
                continue
            
            # 如果句子长度小于10个字，则与下一句合并
            if len(current_sentence) < 10:
                current_sentence += sentence
            else:
                # 判断当前句子是否以标点符号结尾
                if current_sentence[-1] in ["。", "！", "？", ".", "!", "?"]:
                    result.append(current_sentence)
                    current_sentence = sentence
                else:
                    # 如果当前句子不以标点符号结尾，则进行二次切分
                    split_sentences = re.split(r'(?<=[,，;；])', current_sentence)
                    if len(split_sentences) > 1:
                        result.extend(split_sentences[:-1])
                        current_sentence = split_sentences[-1] + sentence
                    else:
                        current_sentence += sentence
        
        # 添加最后一句
        if current_sentence:
            result.append(current_sentence)
        
        return result


    # 字符串匹配算法来计算字符串之间的相似度，并选择匹配度最高的字符串作为结果
    def find_best_match(self, substring, string_list, similarity=0.5):
        """字符串匹配算法来计算字符串之间的相似度，并选择匹配度最高的字符串作为结果

        Args:
            substring (str): 要搜索的子串
            string_list (list): 字符串列表
            similarity (float): 最低相似度

        Returns:
            _type_: 匹配到的字符串 或 None
        """
        best_match = None
        best_ratio = 0
        
        for string in string_list:
            ratio = difflib.SequenceMatcher(None, substring, string).ratio()
            # print(f"String: {string}, Ratio: {ratio}")  # 添加调试语句，输出每个字符串的相似度
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = string
        
        # 如果相似度不到similarity，则认为匹配不成功
        if best_ratio < similarity:
            return None

        return best_match
    

    # 在字符串列表中查找是否存在作为待查询字符串子串的字符串。
    def find_substring_in_list(self, query_string, string_list):
        """
        在字符串列表中查找是否存在作为待查询字符串子串的字符串。

        Args:
        query_string (str): 待查询的字符串。
        string_list (list of str): 被查询的字符串列表。

        Returns:
        str or None: 如果找到子串，则返回该子串；否则返回 None。
        """
        for string in string_list:
            if string in query_string:
                return string
        return None



    def merge_consecutive_asterisks(self, s):
        """合并字符串末尾连续的*

        Args:
            s (str): 待处理的字符串

        Returns:
            str: 处理完后的字符串
        """
        # 从字符串末尾开始遍历，找到连续的*的起始索引
        idx = len(s) - 1
        while idx >= 0 and s[idx] == '*':
            idx -= 1

        # 如果找到了超过3个连续的*，则进行替换
        if len(s) - 1 - idx > 3:
            s = s[:idx + 1] + '*' + s[len(s) - 1:]

        return s


    def replace_special_characters(self, input_string, special_characters):
        """
        将指定的特殊字符替换为空字符。

        Args:
            input_string (str): 要替换特殊字符的输入字符串。
            special_characters (str): 包含要替换的特殊字符的字符串。

        Returns:
            str: 替换后的字符串。
        """
        for char in special_characters:
            input_string = input_string.replace(char, "")
        
        return input_string


    # 将cookie数据字符串分割成键值对列表
    def parse_cookie_data(self, data_str, field_name):
        """将cookie数据字符串分割成键值对列表

        Args:
            data_str (str): 待提取数据的cookie字符串
            field_name (str): 要提取的键名

        Returns:
            str: 键所对应的值
        """
        # 将数据字符串分割成键值对列表
        key_value_pairs = data_str.split(';')

        # print(key_value_pairs)

        # 遍历键值对列表，查找指定字段名
        for pair in key_value_pairs:
            key, value = pair.strip().split('=')
            if key == field_name:
                return value

        # 如果未找到指定字段，返回空字符串
        return ""


    # 动态变量替换
    def dynamic_variable_replacement(self, template, data_json):
        """动态变量替换

        Args:
            template (str): 待替换变量的字符串
            data_json (dict): 用于替换的变量json数据

        Returns:
            str: 替换完成后的字符串
        """
        pattern = r"{(\w+)}"
        var_names = re.findall(pattern, template)

        for var_name in var_names:
            if var_name in data_json:
                template = template.replace("{"+var_name+"}", str(data_json[var_name]))
            else:
                # 变量不存在,保留原样
                pass

        logging.debug(f"template={template}")

        return template


    """
    
            .@@@             @@@        @@^ =@@@@@@@@    /@@ /@@              =@@@@@*,@@\]]]]  ,@@@@@@@@@@@@*                      .@@@         @@/.\]`@@@       =@@\]]]]]]]   =@@..@@@@@@@@@   =@@\   /@@^           
      *@@@@@@@@@@@@@@@*=@@@@@@@@@@@@@@.@@@@@=@@@@@@@@   =@@`=@@@@@@@@@^       =@/[@@@@@@@@@@/.@@@`     .]@@/                 *@@@@@@@@@@@@@@@* =@@.=@@]@@@]]]. ,@@@@@@@@@@@@ ,@@@@@@@@/[[[\@@ =@@@@@@@@@@@@@^         
         =@@`   ,@@^       .@@@@@.      @@^=@@@@^@@@@@ =@@@=@@`@@^            =@@@@@,[@@@@@/  \/,@@`]/@@@@@]                    =@@`   ,@@^   ,@@@,@@@@@@@@@/.\@/,@@@`/@@@`  .[\@@[[@@@@@@@@@ ,[[[[[@@@[[[[[`         
          \@@` ,@@/       /@@@@@@@\    .@@@O@\/@^@@]@@=@@@@,@`*@@@@@@^        ]]=@@=@@@@@@@@@^,@@@,@@/`  .\@@.                   \@@` ,@@/   ,@@@@[@/  @@@       ,]@@@@[      ,@@@@\@@^   =@@.@@@@@@@@@@@@@@@`        
           =@@@@@^     ./@@/ @@@ \@@\`=@@@/`   =@@     @=@@   *@@^     =@@@@^ @@=@@@,@@@@@@@^,@@@^.@@@@@@@@@^                     =@@@@@^    .@\@@@@@@@@@@@@@/@@@@@@@@@@@@@@.,@@@@[`@@@@@@@@@.[[[[[\@@@/[[[[[`        
          ,/@@@@@\`   .\@/@@@@@@@@@\@/  @@^\@@@@@@@@@/. =@@   *@@@@@@@        @@=@@ *@@[[[@@^ .=@^    =@@.    ./`                ,/@@@@@\`     =@@     @@@      @@@      =@@..@=@@..@@^   =@@    ,/@@[@@@`            
      .@@@@@@` ,\@@@@@`      @@@      ,]@@^/@@/=@@[@@@` =@@   *@@^           =@@@@@@^@@@@@@@^  =@^@@@@@@@@@@@^,@@@`          .@@@@@@` ,\@@@@@` =@@     @@@      @@@@@@@@@@@@.  =@@..@@@@@@@@@./@@@@/   [@@@@@`        
       .[`         ,[        \@/      .[[[ ..  ,@/      ,@/   .@@`            .     .@/.  \@`  ,[`,[[[[[[[[[[.  ,[            .[`         ,[   ,@/     \@/      \@/      ,[[.  ,@/..\@`   ,@/ .[[         ,[    
    
    """
    
    # 读取指定文件中所有文本内容并返回 如果文件不存在则创建
    def read_file_return_content(self, file_path):
        try:
            if not os.path.exists(file_path):
                logging.warning(f"文件不存在，将创建新文件: {file_path}")
                # 创建文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    content = ""
                return content
        
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except IOError as e:
            logging.error(f"无法写入文件:{file_path}\n{e}")
            return None


    
    # 将一个文件路径的字符串切分成路径和文件名
    def split_path_and_filename(self, file_path):
        folder_path, file_name = os.path.split(file_path)
        # 检查路径末尾是否已经包含了'/'，如果没有，则添加
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        return folder_path, file_name


    # 从文件路径中提取出带有扩展名的文件名
    def extract_filename(self, file_path, with_extension=False):
        """从文件路径中提取出带有扩展名的文件名

        Args:
            file_path (_type_): 文件路径
            with_extension (bool, optional): 是否需要拓展名. Defaults to False.

        Returns:
            str: 文件名
        """
        file_name_with_extension = os.path.basename(file_path)
        if with_extension:
            return file_name_with_extension
        else:
            file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
            return file_name_without_extension


    # 获取指定文件夹下的所有文件夹的名称
    def get_folder_names(self, path):
        folder_names = next(os.walk(path))[1]
        return folder_names


    # 返回指定文件夹内所有文件的文件绝对路径（包括文件扩展名）
    def get_all_file_paths(self, folder_path):
        """返回指定文件夹内所有文件的文件绝对路径（包括文件扩展名）

        Args:
            folder_path (str): 文件夹路径

        Returns:
            list: 文件绝对路径列表
        """
        file_paths = []  # 用于存储文件绝对路径的列表

        # 使用 os.walk 遍历文件夹内所有文件和子文件夹
        for root, directories, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)  # 获取文件的绝对路径
                file_paths.append(file_path)

        return file_paths

    def remove_extension_from_list(self, file_name_list):
        """
        将包含多个带有拓展名的文件名的列表中的拓展名去掉，只返回文件名部分组成的新列表

        Args:
            file_name_list (list): 包含多个带有拓展名的文件名的列表

        Returns:
            list: 文件名组成的新列表
        """
        # 使用列表推导来处理整个列表，去掉每个文件名的拓展名
        file_name_without_extension_list = [file_name.split('.')[0] for file_name in file_name_list]
        return file_name_without_extension_list


    def is_audio_file(self, file_path):
        """判断文件是否是音频文件

        Args:
            file_path (str): 文件路径

        Returns:
            bool: True / False
        """
        # List of supported audio file extensions
        SUPPORTED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.MP3', '.WAV', '.ogg']

        _, extension = os.path.splitext(file_path)
        return extension.lower() in SUPPORTED_AUDIO_EXTENSIONS


    def random_search_a_audio_file(self, root_dir):
        """搜索指定文件夹内所有的音频文件，并随机返回一个音频文件路径

        Args:
            root_dir (str): 搜索的文件夹路径

        Returns:
            str: 随机返回一个音频文件路径
        """
        audio_files = []

        for root, dirs, files in os.walk(root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_dir)
                relative_path = relative_path.replace("\\", "/")

                logging.debug(file_path)

                # 判断文件是否是音频文件
                if self.is_audio_file(relative_path):
                    audio_files.append(file_path)

        if audio_files:
            # 随机返回一个音频文件路径
            return random.choice(audio_files)
        else:
            return None

    # 获取Live2D模型名
    def get_live2d_model_name(self, path):
        content = self.read_file_return_content(path)
        if content is None:
            logging.error(f"读取Live2D模型名失败")
            return None
        
        pattern = r'"(.*?)"'
        result = re.search(pattern, content)

        if result:
            content = result.group(1)
            return content
        else:
            return None


    """
                                                                                                 
              .]]@@              .@]]       @@@@        O@@`  ,]]]]]]]]]]]].      /]]   /@]`                  
               =@@@\             =@@@`.@@@^ @@@@        @@@^  =@@@@@@@@@@@@.     =@@@` =@@@`                  
      @@@@@@@@@@@@@@@@@@@@@@@   ,@@@^ =@@@` @@@@      ]]@@@\]`=@@@@@@@@@@@@.    ,@@@^ ,@@@@@@@@@@@@@@^        
      @@@@@@@@@@@@@@@@@@@@@@@  .@@@@ .@@@@@@@@@@@@@@@ @@@@@@@^,[[[[[[[[[[[[.   .@@@@..@@@@@@@@@@@@@@@`        
          \@@@`     =@@@@     .@@@@@ =@@@[[[@@@@[[[[`   @@@^ =@@@@@@^=@@@@@@^ .@@@@@,@@@/ @@@^                
          .@@@@`   ,@@@@.     /@@@@@,@@@^   @@@@        @@@\]=@@ =@@^=@@.=@@^.@@@@@@.@@/  @@@@@@@@@@          
            \@@@\./@@@@      .@@@@@@,]]]]]]]@@@@]]]]]/@@@@@@@=@@@@@@^=@@@@@@^ @@O@@@..`   @@@/[[[[[[          
             =@@@@@@@^        =/=@@@=@@@@@@@@@@@@@@@@^@@@@@^,]]]]]]@@@\]]]]]] =`=@@@.     @@@^                
            ./@@@@@@@]          =@@@        @@@@        @@@^=@@@@@@@@@@@@@@@@   =@@@.     @@@@@@@@@@^         
        ,]@@@@@@@[@@@@@@@]`     =@@@        @@@@        @@@^  .]@@@@@@@@@\.     =@@@.     @@@/[[[[[[`         
      \@@@@@@@[    .[@@@@@@@/   =@@@        @@@@     .@@@@@`@@@@@` @@@^.\@@@@.  =@@@.     @@@^                
       ,@/[            .[\@`    =@@@        @@@@      \@@@`  ,`    @@@^   .[    =@@@.     @@@^             

    """

    # 写入内容到指定文件中 返回T/F
    def write_content_to_file(self, file_path, content, write_log=True):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"内容已成功写入文件:{file_path}")

            return True
        except IOError as e:
            logging.error(f"无法写入文件:{file_path}\n{e}")
            return False

    # 移动文件到指定路径 src dest
    def move_file(self, source_path, destination_path, rename=None, format="wav"):
        """移动文件到指定路径

        Args:
            source_path (str): 文件路径含文件名
            destination_path (_type_): 目标文件夹
            rename (str, optional): 文件名. Defaults to None.
            format (str, optional): 文件格式（实际上只是个假拓展名）. Defaults to "wav".

        Returns:
            str: 输出到的完整路径含文件名
        """
        logging.debug(f"source_path={source_path},destination_path={destination_path},rename={rename}")

        # if os.path.exists(destination_path):
        #     # 如果目标位置已存在同名文件，则先将其移动到回收站
        #     send2trash(destination_path)
        
        # if rename is not None:
        #     destination_path = os.path.join(os.path.dirname(destination_path), rename)
        
        # shutil.move(source_path, destination_path)
        # logging.info(f"文件移动成功：{source_path} -> {destination_path}")
        destination_directory = os.path.dirname(destination_path)
        logging.debug(f"destination_directory={destination_directory}")
        destination_filename = os.path.basename(source_path)

        if rename is not None:
            destination_filename = rename + "." + format
        
        destination_path = os.path.join(destination_directory, destination_filename)
        
        if os.path.exists(destination_path):
            # 如果目标位置已存在同名文件，则先删除
            os.remove(destination_path)

        shutil.move(source_path, destination_path)
        print(f"文件移动成功：{source_path} -> {destination_path}")

        return destination_path


    # 删除文件
    def del_file(self, file_path) -> bool:
        """
        删除文件

        Args:
            file_path (str): 文件路径

        Returns:
            bool：True/False
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"文件删除成功：{file_path}")

                return True
            
            logging.error(f"文件不存在：{file_path}")
            return False
        except Exception as e:
            logging.error(traceback.format_exc())
            return False

    """
    
                   ,@@@^              .@@@. .@@@@@@@@@@@@.  .@@@.  ,]]]]]]]]]]]]`     ]@@@`     ,@@@\.        
          .@@@@@@@@@@@@@@@@@@@@@^ .@@O.@@@\]`@@@@@@@@@@@@.  .@@@.  =@@@@@@@@@@@@^      \@@@@.  =@@@/          
              .]@@^     ,@@\`     .@@O.@@@@@^,]]/@@@]]]]`.@@@@@@@@@=@@^     .@@@^  =@@@@@@@@@@@@@@@@@@@@      
         .@@@@@@@@@@@@@@@@@@@@@@@..@@O.@@@.  =@@@@@@@@@@^.[[[@@@/[[=@@@]]]]]/@@@^  =@@@@@@@@@@@@@@@@@@@O      
         .@@@@@@@@@@@@@@@@@@@@@@@*@@@@@@@@@@@=@@^,]]`=@@^   /@@@`  =@@@@@@@@@@@@^          =@@@^              
            =@@@@@@@@@@@@@@@@@^       =@@O   =@@^=@@^=@@^  /@@@@@@@/@@^     .@@@^.@@@@@@@@@@@@@@@@@@@@@@@.    
            =@@@@@@@@@@@@@@@@@^    /@@\@@O=@@/@@^=@@^=@@^./@@@@@[@`=@@@@@@@@@@@@^.O@@@@@@@@@@@@@@@@@@@@@O.    
            =@@@]]]]]]]]]]]@@@^   =@@^=@@@@@/=@@^@@@.=@@^.@@`@@@.  =@@@@@@@@@@@@^        .@@@@@@@`            
            =@@@@@@@@@@@@@@@@@^  .,\^ ./@@@^ ,[[@@@@\,[[` =`.@@@.  =@@^     .@@@^      ,@@@@/ \@@@@]          
            =@@@]]]]]]]]]]]@@@^    .]@@@@/   ,/@@@/@@@@]    .@@@.  =@@@@@@@@@@@@^ .,/@@@@@/.   .\@@@@@@\].    
            =@@@@@@@@@@@@@@@@@^   \@@@@`   ,@@@@[   .\@@@.  .@@@.  =@@@@@@@@@@@@^ ,@@@@@`         ,\@@@/.     
            ....           ....    ,.        ,.        .     ...   ....     .....   .                        

    """
    # 获取新的音频路径
    def get_new_audio_path(self, audio_out_path, file_name):
        # 判断路径是否为绝对路径
        if os.path.isabs(audio_out_path):
            # 如果是绝对路径，直接使用
            voice_tmp_path = os.path.join(audio_out_path, file_name)
        else:
            # 如果不是绝对路径，检查是否包含 ./，如果不包含，添加 ./，然后拼接路径
            if not audio_out_path.startswith('./'):
                audio_out_path = './' + audio_out_path
            voice_tmp_path = os.path.normpath(os.path.join(audio_out_path, file_name))

        voice_tmp_path = os.path.abspath(voice_tmp_path)

        return voice_tmp_path


    # 获取所有的声卡设备信息
    def get_all_audio_device_info(self, type):
        """获取所有的声卡设备信息

        Args:
            type (str): 声卡类型，"in" 或 "out"

        Returns:
            list: 声卡设备信息列表
        """
        audio = pyaudio.PyAudio()
        device_infos = []
        device_count = audio.get_device_count()

        for device_index in range(device_count):
            device_info = audio.get_device_info_by_index(device_index)
            if type == "out":
                if device_info['maxOutputChannels'] > 0:
                    device_infos.append({"device_index": device_index, "device_info": device_info['name']})
            elif type == "in":
                if device_info['maxInputChannels'] > 0:
                    device_infos.append({"device_index": device_index, "device_info": device_info['name']})
            else:
                device_infos.append({"device_index": device_index, "device_info": device_info['name']})

        return device_infos

    """

                                                                        ..        ,]]].                ,]]].  ,]            
    .@@@@.      ,@@@\ .@@@@@@@@@@@@@@`@@@@@@@@@@@@@@` =@@@@@@\]]`    =@@@^ ,]]]]]/@@@\]]]]]]          =@@@. \@@@@`         
    .@@@@.      =@@@@ *@@@@@@@@@@@@@@^@@@@@@@@@@@@@@^ =@@@@@@@@@@@\   ,@@@\,[[[[[\@@@[[[[[[[ ]]]]]]]]]/@@@\]]]/@\]]]       
    .@@@@.      =@@@@      .@@@@.         .@@@@.      =@@@^   .@@@@^   .[` .@@@@@@@@@@@@@@@. @@@@@@@@@@@@@@@@@@@@@@@       
    .@@@@.      =@@@@      .@@@@.         .@@@@.      =@@@^    =@@@@,]]]]],]]]]]]/@@@]]]]]]]`  ,@`    =@@@`     /\.        
    .@@@@@@@@@@@@@@@@      .@@@@.         .@@@@.      =@@@^  .]@@@@`=@@@@@,[[[[[[[[[[[[[[[[[` ,@@@@\. =@@@@` ./@@@@`       
    .@@@@@@@@@@@@@@@@      .@@@@.         .@@@@.      =@@@@@@@@@@/.   =@@@  =@@@@@@@@@@@@@^     .\@@` =@@@@@@@@@/.         
    .@@@@.      =@@@@      .@@@@.         .@@@@.      =@@@/[[`.       =@@@  =@@@]]]]]]]@@@^       ,/@@@@@@\@@@\            
    .@@@@.      =@@@@      .@@@@.         .@@@@.      =@@@^           =@@@.`=@@@@@@@@@@@@@^  .]@@@@@@/\@@@.,@@@@@]         
    .@@@@.      =@@@@      .@@@@.         .@@@@.      =@@@^           =@@@@@=@@@@@@@@@@@@@^  \@@@/`   =@@@.  ,@@@@@@       
    .[[[[.      ,[[[[      .[[[[.         .[[[[.      ,[[[`           =@@@@[=@@@      .@@@^   [.  @@@@@@@@.     [@/        
                                                                    .@/.  =@@@  ,@@@@@@@.       =@@@@@@`            
                                                                    
    """
    def send_request(self, url, method='GET', json_data=None):
        """
        发送 HTTP 请求并返回结果

        Parameters:
            url (str): 请求的 URL
            method (str): 请求方法，'GET' 或 'POST'
            json_data (dict): JSON 数据，用于 POST 请求

        Returns:
            dict: 包含响应的 JSON 数据
        """
        headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=json.dumps(json_data))
            else:
                raise ValueError('无效 method. 支持的 methods 为 GET 和 POST.')

            # 检查请求是否成功
            response.raise_for_status()

            # 解析响应的 JSON 数据
            result = response.json()

            return result

        except requests.exceptions.RequestException as e:
            logging.error(traceback.format_exc())
            logging.error(f"请求出错: {e}")
            return None

    # 请求web字幕打印机
    def send_to_web_captions_printer(self, api_ip_port, data):
        """请求web字幕打印机

        Args:
            api_ip_port (str): api请求地址
            data (dict): 包含用户名,弹幕内容

        Returns:
            bool: True/False
        """

        # user_name = data["username"]
        content = data["content"]

        # 记录数据库):
        try:
            response = requests.get(url=api_ip_port + f'/send_message?content={content}')
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = json.loads(result)

            logging.debug(ret)

            if ret['code'] == 200:
                logging.debug(ret['message'])
                return True
            else:
                logging.error(ret['message'])
                return False
        except Exception as e:
            logging.error('web字幕打印机请求失败！请确认配置是否正确或者服务端是否运行！')
            logging.error(traceback.format_exc())
            return False
        
    
    # openai 测试key可用性
    def test_openai_key(self, data_json, type=1):
        if type == 1:
            from urllib.parse import urljoin
            
            # 检查可用性
            def check_useful(data_json):
                # 尝试调用 list engines 接口
                try:
                    api_key = data_json["api_keys"].split('\n')[0].rstrip()

                    url = urljoin(data_json["base_url"], '/v1/chat/completions')

                    logging.debug(f"url=【{url}】, api_keys=【{api_key}】")
    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }

                    data = {
                        "model": data_json["model"],
                        "messages": [{"role": "user", "content": "hi"}],
                        "temperature": data_json["temperature"],
                        "max_tokens": data_json["max_tokens"],
                        "top_p": data_json["top_p"],
                        "presence_penalty": data_json["presence_penalty"],
                        "frequency_penalty": data_json["frequency_penalty"]
                    }

                    response = requests.post(url, headers=headers, json=data)
                    response_data = response.json()

                    logging.debug(response_data)

                    resp = response_data["choices"][0]["message"]["content"]

                    logging.info("OpenAI API key 可用")

                    return True
                except Exception as e:
                    logging.error(f"OpenAI API key 不可用: {e}")
                    return False
        else:
            import openai
            from packaging import version

            # os.environ['http_proxy'] = "http://127.0.0.1:10809"
            # os.environ['https_proxy'] = "http://127.0.0.1:10809"

            # 检查可用性
            def check_useful(data_json):
                # 尝试调用 list engines 接口
                try:
                    api_key = data_json["api_keys"].split('\n')[0].rstrip()

                    logging.info(f'base_url=【{data_json["base_url"]}】, api_keys=【{api_key}】')

                    # openai.base_url = self.data_openai['api']
                    # openai.api_key = self.data_openai['api_key'][0]

                    logging.debug(f"openai.__version__={openai.__version__}")

                    openai.api_base = data_json["base_url"]
                    openai.api_key = api_key

                    # 判断openai库版本，1.x.x和0.x.x有破坏性更新
                    if version.parse(openai.__version__) < version.parse('1.0.0'):
                        # 调用 ChatGPT 接口生成回复消息
                        resp = openai.ChatCompletion.create(
                            model=data_json["model"],
                            messages=[{"role": "user", "content": "Hi"}],
                            temperature=data_json["temperature"],
                            max_tokens=data_json["max_tokens"],
                            top_p=data_json["top_p"],
                            presence_penalty=data_json["presence_penalty"],
                            frequency_penalty=data_json["frequency_penalty"],
                            timeout=30
                        )
                    else:
                        client = openai.OpenAI(base_url=openai.api_base, api_key=openai.api_key)
                        # 调用 ChatGPT 接口生成回复消息
                        resp = client.chat.completions.create(
                            model=data_json["model"],
                            messages=[{"role": "user", "content": "Hi"}],
                            temperature=data_json["temperature"],
                            max_tokens=data_json["max_tokens"],
                            top_p=data_json["top_p"],
                            presence_penalty=data_json["presence_penalty"],
                            frequency_penalty=data_json["frequency_penalty"],
                            timeout=30
                        )

                    logging.debug(resp)
                    logging.info("OpenAI API key 可用")

                    return True
                except openai.OpenAIError as e:
                    logging.error(f"OpenAI API key 不可用: {e}")
                    return False
        
        return check_useful(data_json)


    def check_useful(self):
        import ntplib

        def get_ntp_time(server="ntp.aliyun.com"):
            c = ntplib.NTPClient()
            response = c.request(server, version=3)
            return response.tx_time

        # 获取网络时间的时间戳
        timestamp = get_ntp_time()

        import requests
        import json

        # 指定要下载的 JSON 文件的 URL
        url = 'https://github.com/Ikaros-521/Ikaros-521/releases/download/data/data.json'

        try:
            # 发送 GET 请求下载 JSON 文件内容
            response = requests.get(url)

            # 确保请求成功
            if response.status_code == 200:
                # 解析 JSON 数据到字典
                data = json.loads(response.text)

                # 打印字典内容
                logging.debug(data)

                tmp = float(data["RealtimeSTT"]["1"]["expiration_time"]) - float(timestamp)
                if tmp > 0:
                    logging.info(f"账号剩余可用时长：{tmp / 60 / 60}小时")
                    return {"ret": 0, "msg": f"账号剩余可用时长：{tmp / 60 / 60}小时"}
                else:
                    logging.warning(f"账号已到期，请续费后使用")
                    return {"ret": 1, "msg": f"账号已到期，请续费后使用"}
            else:
                logging.error(f"请求失败，状态码：{response.status_code}")
                return {"ret": 2, "msg": str(e)}
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"ret": 3, "msg": str(e)}

