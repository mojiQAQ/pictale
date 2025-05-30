import base64
import json
import time
from pathlib import Path
import os
import ssl
import urllib3

# 阿里云SDK
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
import nls

from modules.config import ConfigManager
from modules.logger import get_logger

# 全局禁用SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AudioGenerator_ali:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.ali_config = self.config_manager.get_aliyun_config()
        self.output_dir = self.config_manager.get_output_base_dir()
        
        # 初始化阿里云客户端
        credentials = AccessKeyCredential(
            self.ali_config['access_key_id'], 
            self.ali_config['access_key_secret']
        )
        self.client = AcsClient(
            region_id=self.ali_config.get('region', 'cn-shanghai'),
            credential=credentials
        )
        
        # 初始化NLS客户端
        self.url = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
        self.appkey = self.ali_config['appkey']
        self.token = None
        self.file_handle = None
        
        # 设置环境变量禁用证书验证
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''

    def __get_token(self):
        """获取访问令牌"""
        try:
            # 创建请求对象
            request = CommonRequest()
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')
            request.set_method('POST')
            
            # 发送请求
            response = self.client.do_action_with_exception(request)
            token_json = json.loads(response.decode('utf-8'))
            token = token_json.get('Token', {}).get('Id')
            
            if not token:
                raise Exception("无法获取阿里云访问令牌")
            
            return token
        except Exception as e:
            self.logger.error(f"获取Token失败: {str(e)}")
            raise

    def __on_metainfo(self, message):
        self.logger.debug(f"on_metainfo: {message}")
    
    def __on_error(self, message):
        self.logger.error(f"on_error: {message}")
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    def __on_close(self):
        self.logger.debug("on_close")
        # if self.file_handle:
        #     self.file_handle.close()
        #     self.file_handle = None

    def __on_completed(self):
        self.logger.debug("on_completed")
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    def __on_data(self, data, *args):
        self.logger.debug(f"on_data: {data}, {args}")
        if self.file_handle:
            try:
                self.file_handle.write(data)
            except Exception as e:
                self.logger.error(f"写入数据失败: {str(e)}")
                if self.file_handle:
                    self.file_handle.close()
                    self.file_handle = None

    def generate(self, text: str, type: str = "word", language: str = "en", output_path: str = None) -> str:
        """
        使用阿里云API生成语音
        
        Args:
            text: 要转换为语音的文本
            type: 文本类型，默认为 word, 可选值为 word, phrase
            language: 语言，默认为英文 (en)，可选值为中文 (zh)
            output_path: 输出路径，默认为None
            
        Returns:
            str: 生成的音频文件路径
        """
        try:
            self.logger.info(f"开始生成语音(阿里云): {text}")
            
            # 再次确保SSL验证被禁用
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # 获取token
            self.token = self.__get_token()
            self.logger.debug(f"token: {self.token}")
            
            # 根据语言选择不同的参数
            if language == "zh":
                voice = self.ali_config.get('voice_zh', 'xiaoyun')  # 中文默认音色
                speech_rate = 0  # 正常语速
            else:
                voice = self.ali_config.get('voice_en', 'samantha')  # 英文默认音色
                speech_rate = -100  # 稍慢语速，适合学习
            
            # 确定输出路径
            if not output_path:
                timestamp = int(time.time())
                output_path = self.output_dir / f"{timestamp}_{type}_{language}.wav"
            else:
                output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 打开文件
            self.file_handle = open(str(output_path), 'wb')
            
            # 创建语音合成器
            nls.enableTrace(True)
            
            tts = nls.NlsSpeechSynthesizer(
                url=self.url,
                token=self.token,
                appkey=self.appkey,
                on_metainfo=self.__on_metainfo,
                on_error=self.__on_error,
                on_close=self.__on_close,
                on_data=self.__on_data,
                on_completed=self.__on_completed
            )
            
            self.logger.debug(f"tts: {tts}")
            # 开始合成
            result = tts.start(
                text=text,
                voice=voice,
                aformat="wav",
                sample_rate=16000,
                volume=50,
                speech_rate=speech_rate,
                pitch_rate=0,
                wait_complete=True
            )
            
            self.logger.debug(f"result: {result}")
            
            self.logger.info(f"语音文件已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成语音时出错: {str(e)}")
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
            raise Exception(f"Error generating audio: {str(e)}") 