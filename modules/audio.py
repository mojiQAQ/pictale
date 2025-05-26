
import base64
import json
import time
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tts.v20190823 import tts_client, models
from modules.config import ConfigManager
from modules.logger import get_logger

class AudioGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.tencent_config = self.config_manager.get_tencent_config()
        self.output_dir = self.config_manager.get_output_dir('audio')
        
        # 初始化腾讯云客户端
        cred = credential.Credential(
            self.tencent_config['secret_id'], 
            self.tencent_config['secret_key']
        )
        http_profile = HttpProfile()
        http_profile.endpoint = "tts.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self.client = tts_client.TtsClient(
            cred, 
            self.tencent_config.get('region', 'ap-guangzhou'), 
            client_profile
        )

    def generate(self, text: str) -> str:
        try:
            self.logger.info(f"开始生成语音: {text}")
            # 创建请求对象
            req = models.TextToVoiceRequest()
            params = {
                "Text": text,
                "SessionId": f"session-{int(time.time())}",
                "ModelType": 1,  # 1: 标准音色
                "Volume": 5,     # 音量大小
                "Speed": 0,      # 语速
                "SampleRate": 16000,  # 采样率
                "Codec": "wav",  # 音频格式
                "PrimaryLanguage": 2,  # 主语言类型 1: 中文 2: 英文
                "VoiceType": 501009,  # 音色 WeRose 101051, WeWinny 501009
            }
            req.from_json_string(json.dumps(params))
            
            # 发送请求
            self.logger.debug("发送语音合成请求到腾讯云")
            resp = self.client.TextToVoice(req)
            # 保存音频文件
            timestamp = int(time.time())
            output_path = self.output_dir / f"generated_{timestamp}.wav"

            decoded_audio_data = base64.b64decode(resp.Audio)
            with open(output_path, 'wb') as f:
                f.write(decoded_audio_data)
            
            self.logger.info(f"语音文件已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成语音时出错: {str(e)}")
            raise Exception(f"Error generating audio: {str(e)}") 