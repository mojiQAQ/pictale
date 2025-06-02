import base64
import json
import time
import requests
import hashlib
from modules.config import ConfigManager
from modules.logger import get_logger

class MoyinAudioGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.moyin_config = self.config_manager.get_moyin_config()
        self.output_dir = self.config_manager.get_output_base_dir()
        self.api_url = self.moyin_config.get('api_url')
        self.speaker_zh = self.moyin_config.get('speaker_zh')
        self.speaker_en = self.moyin_config.get('speaker_en')
        
        # 检查配置是否存在
        if not self.moyin_config or 'api_key' not in self.moyin_config or 'api_secret' not in self.moyin_config:
            self.logger.warning("Moyin配置未找到，请在settings.yaml中添加moyin配置")
            self.moyin_config = {
                'api_key': '',
                'api_secret': ''
            }

    def __generate_signature(self, timestamp: int) -> str:
        """
        生成签名
        """
        content = f"{self.moyin_config.get('api_key')}{self.moyin_config.get('api_secret')}{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()

    def generate(self, text: str, type: str = "word", language: str = "en", output_path: str = None) -> str:
        """
        使用墨因API生成语音
        
        Args:
            text: 要转换为语音的文本
            type: 文本类型，默认为 word, 可选值为 word, phrase
            language: 语言，默认为英文
            output_path: 输出路径，默认为None
            
        Returns:
            str: 生成的音频文件路径
        """
        try:
            self.logger.info(f"开始生成语音: {text}")
            
            # 准备请求参数
            headers = {
                "Content-Type": "application/json"
            }
            
            timestamp = int(time.time())
            if language == "zh":
                voice_id = self.speaker_zh
            else:
                voice_id = self.speaker_en

            signature = self.__generate_signature(timestamp)
            payload = {
                "signature": signature,
                "timestamp": timestamp,
                "appkey": self.moyin_config.get('api_key'),
                "speaker": voice_id,
                "text": text,
                "audio_type": "wav",  # 音频格式，可选wav、mp3
                "speed": 0.8,  # 语速，范围0.5-2.0，默认1.0
                "pitch": 1.0,  # 音调，范围0.5-2.0，默认1.0
                "volume": 1.0,  # 音量，范围0.5-2.0，默认1.0
                "rate": 16000  # 采样率，范围16000-48000，默认16000
            }
            
            # 发送请求
            self.logger.debug("发送语音合成请求到 Moyin API")
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            # 检查响应
            if response.status_code != 200:
                self.logger.error(f"API请求失败: {response.status_code} - {response.text}")
                raise Exception(f"API request failed with status code {response.status_code}")
            
            headers = response.headers

            if headers.get('Content-Type') == 'audio/mpeg' or headers.get('Content-Type') == 'audio/wav':
                audio_data = response.content
                if not output_path:
                    timestamp = int(time.time())
                    output_path = self.output_dir / f"{timestamp}_{type}_{language}.wav"
                # 保存音频文件
                with open(output_path, 'wb', encoding='utf-8') as f:
                    f.write(audio_data)
            else:
                self.logger.error(f"API返回错误: {response.text}")
                raise Exception(f"API returned error: {response.text}")

            self.logger.info(f"语音文件已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成语音时出错: {str(e)}")
            raise Exception(f"Error generating audio: {str(e)}")
