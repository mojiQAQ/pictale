import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    _instance = None
    _settings = None
    _subtitle_templates = None
    _output_dirs = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_configs()
            cls._instance._setup_output_dirs()
        return cls._instance

    def _load_configs(self):
        """加载所有配置文件"""
        config_dir = Path(__file__).parent.parent / 'config'
        self._settings = self._load_yaml(config_dir / 'settings.yaml')
        
    def _setup_output_dirs(self):
        """初始化输出目录配置"""
        base_dir = Path(__file__).parent.parent / 'output'
        self._output_dirs = {
            'base': base_dir
        }

        # 确保所有输出目录存在
        for dir_path in self._output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML配置文件"""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON配置文件"""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)

    @property
    def settings(self) -> Dict[str, Any]:
        """获取应用程序设置"""
        return self._settings

    @property
    def subtitle_templates(self) -> Dict[str, Any]:
        """获取字幕模板配置"""
        return self._subtitle_templates
    
    @property
    def output_dirs(self) -> Dict[str, Path]:
        """获取输出目录配置"""
        return self._output_dirs

    # Azure OpenAI 相关配置
    def get_azure_config(self) -> Dict[str, str]:
        """获取Azure OpenAI配置"""
        if 'azure_openai' not in self.settings:
            raise KeyError("Azure OpenAI configuration not found in settings")
        return self.settings['azure_openai']
    
    # ComfyUI 相关配置
    def get_comfy_config(self) -> Dict[str, Any]:
        """获取ComfyUI配置"""
        if 'comfyui' not in self.settings:
            # 如果配置文件中没有，提供默认配置
            return {
                'api_url': 'http://127.0.0.1:8188',
                'width': 1024,
                'height': 1024,
                'steps': 30,
                'cfg_scale': 7.0,
                'sampler': 'euler_a',
                'model_name': 'dreamshaper_8',
                'negative_prompt': '',
                'seed': 42,
                'timeout': 120,
            }
        return self.settings['comfyui']
    
    # 腾讯云 API 相关配置
    def get_tencent_config(self) -> Dict[str, Any]:
        """获取腾讯云API配置"""
        if 'tencent_cloud' not in self.settings:
            # 如果配置文件中没有，尝试从环境变量获取
            return {
                'secret_id': os.getenv('TENCENT_SECRET_ID'),
                'secret_key': os.getenv('TENCENT_SECRET_KEY')
            }
        return self.settings['tencent_cloud']

    # 魔音工坊相关配置
    def get_moyin_config(self) -> Dict[str, Any]:
        """获取魔音工坊配置"""
        if 'moyin' not in self.settings:
            return {}
        return self.settings['moyin']

    def get_output_base_dir(self) -> Path:
        """获取输出目录"""
        return self._output_dirs['base']

    # FFmpeg相关配置
    def get_ffmpeg_config(self) -> Dict[str, Any]:
        """获取FFmpeg配置"""
        if 'ffmpeg' not in self.settings:
            return {
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'audio_bitrate': '192k',
            }
        return self.settings['ffmpeg']

    def get_aliyun_config(self) -> Dict[str, Any]:
        """获取阿里云配置"""
        return self.settings['aliyun']
