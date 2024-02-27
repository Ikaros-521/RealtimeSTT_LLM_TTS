import requests
from bs4 import BeautifulSoup
import traceback
import logging

from .common import Common
from .logger import Configure_logger
from .config import Config


class SEARCH_ONLINE:
    def __init__(self):
        self.common = Common()
        # 日志文件路径
        file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        Configure_logger(file_path)

        # self.proxies = {
        #     "http": "http://127.0.0.1:10809",
        #     "https": "http://127.0.0.1:10809",
        #     "socks5": "socks://127.0.0.1:10808"
        # }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'Content-Type': 'text/plain',
        }
        self.proxies = None
        


    def google(self, query, id=1):
        def google_1(query):
            query = query # 在此处替换您要搜索的关键词
            url = f"https://www.google.com/search?q={query}"
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    if link.startswith('/url?q='):
                        link = link[7:]
                    if not link.startswith('http'):
                        continue
                    title = g.find('h3').text
                    item = {'title': title, 'link': link}
                    results.append(item)
            for r in results:
                logging.debug(r['link'])
            return results


        def google_2(query):
            results = []
            url = "https://lite.duckduckgo.com/lite/"

            data={
                "q":query

            }
            response = requests.post(url, data=data, headers=self.headers, proxies=self.proxies)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, 'html.parser')
            # soup=soup.find("tbody")
            for g in soup.find_all("a"):
                item = {'title': g, 'link': g['href']}
                logging.debug(g['href'])
                results.append(item)
            return results
        
        if id == 1:
            return google_1(query)
        elif id == 2:
            return google_2(query)


    def get_url2(self, url) -> str:
        """Scrape text from a webpage

        Args:
            url (str): The URL to scrape text from

        Returns:
            str: The scraped text
        """

        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
            if response.encoding == "ISO-8859-1": response.encoding = response.apparent_encoding
        except Exception as e:
            logging.debug(traceback.format_exc())
            return "无法连接到该网页"
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text


    def get_url(self, url):
        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            paragraphs = soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            paragraphs_text = [p.get_text() for p in paragraphs]
            return paragraphs_text
        except requests.exceptions.RequestException as e:
            logging.warning("无法访问该URL: %s, error: %s", url, str(e))
            return None


    def get_summary(self, item):
        logging.debug("正在获取链接内容：%s", item["link"])
        link_content = self.get_url(item["link"])
        if not link_content:
            logging.warning("无法获取链接内容：%s", item["link"])
            return None
        logging.debug("link_content: %s", link_content)
        # 获取链接内容字符数量
        link_content_str = ' '.join(link_content)
        content_length = len(link_content_str)
        logging.debug("content_length: %s", content_length)

        # 如果内容少于50个字符，则pass
        if content_length < 50:
            logging.warning("链接内容低于50个字符：%s", item["link"])
            return None
        # 如果内容大于15000个字符，则截取中间部分
        elif content_length > 8000:
            logging.warning("链接内容高于15000个字符，进行裁断：%s", item["link"])
            start = (content_length - 8000) // 2
            end = start + 8000
            link_content = link_content[start:end]

        resp_content = ""
        for content in link_content:
            resp_content += content.rstrip()

        logging.debug("正在提取摘要：%s", resp_content)
        return resp_content


    def get_summary_list(self, data_list, count=3):
        """获取总结列表

        Args:
            data_list (dict): 链接相关数据json
            count (int, optional): 总结总数. Defaults to 3.

        Returns:
            list: 总结列表
        """
        num = 0
        summary_list = []

        logging.debug(f"data_list={data_list}")

        for data in data_list:
            summary = self.get_summary(data)
            if summary:
                summary_list.append(summary)
                num += 1

            if num >= count:
                break

        logging.info(f"summary_list={summary_list}")
        return summary_list


if __name__ == '__main__':

    search_online = SEARCH_ONLINE()

    data_list = search_online.google("伊卡洛斯", 1)
    search_online.get_summary_list(data_list, 1)