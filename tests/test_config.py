import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from modules.config import ConfigManager

@pytest.fixture
def mock_settings_yaml():
    return """
azure_openai:
  endpoint: "https://test-endpoint.openai.azure.com"
  api_key: "test-api-key"
  api_version: "2024-02-15-preview"
  deployment_name: "test-deployment"
    """

@pytest.fixture
def mock_templates_yaml():
    return """
image_templates:
  - name: "default"
    style: "realistic"
    prompt_template: "Test template: {word}, {style}"
  - name: "cartoon"
    style: "cartoon style"
    prompt_template: "Test cartoon: {word}, {style}"

subtitle_templates:
  - name: "default"
    font_family: "Arial"
    font_size: "24px"
    color: "#FFFFFF"
    position: "bottom"
    """

def test_singleton_pattern():
    """测试ConfigManager是否正确实现了单例模式"""
    with patch('modules.config.ConfigManager._load_configs'):
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

def test_load_configs(mock_settings_yaml, mock_templates_yaml):
    """测试配置文件加载"""
    # 模拟文件存在检查
    with patch('pathlib.Path.exists', return_value=True):
        # 模拟open调用，根据文件路径返回不同的内容
        with patch('builtins.open', side_effect=lambda p, mode: 
                mock_open(read_data=mock_settings_yaml if 'settings.yaml' in str(p) else mock_templates_yaml)()) as m:
            
            # 重置单例实例，这样我们可以重新加载配置
            ConfigManager._instance = None
            config = ConfigManager()
            
            # 验证配置是否正确加载
            assert 'azure_openai' in config.settings
            assert config.settings['azure_openai']['endpoint'] == "https://test-endpoint.openai.azure.com"
            assert len(config.templates['image_templates']) == 2
            assert config.templates['image_templates'][0]['name'] == "default"

def test_file_not_found():
    """测试文件不存在的异常处理"""
    with patch('pathlib.Path.exists', return_value=False):
        ConfigManager._instance = None
        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigManager()
        assert "Configuration file not found" in str(exc_info.value)

def test_get_azure_config():
    """测试获取Azure配置"""
    with patch.object(ConfigManager, '_load_configs'):
        ConfigManager._instance = None
        config = ConfigManager()
        config._settings = {'azure_openai': {'key': 'value'}}
        
        assert config.get_azure_config() == {'key': 'value'}

def test_azure_config_not_found():
    """测试Azure配置不存在的情况"""
    with patch.object(ConfigManager, '_load_configs'):
        ConfigManager._instance = None
        config = ConfigManager()
        config._settings = {}
        
        with pytest.raises(KeyError) as exc_info:
            config.get_azure_config()
        assert "Azure OpenAI configuration not found" in str(exc_info.value)

def test_get_image_template():
    """测试获取图片模板"""
    with patch.object(ConfigManager, '_load_configs'):
        ConfigManager._instance = None
        config = ConfigManager()
        config._templates = {
            'image_templates': [
                {'name': 'default', 'style': 'test'},
                {'name': 'cartoon', 'style': 'cartoon'}
            ]
        }
        
        # 测试获取默认模板
        template = config.get_image_template()
        assert template['name'] == 'default'
        
        # 测试获取指定模板
        template = config.get_image_template('cartoon')
        assert template['name'] == 'cartoon'
        
        # 测试获取不存在的模板（应该返回默认模板）
        template = config.get_image_template('nonexistent')
        assert template['name'] == 'default'

def test_template_not_found():
    """测试模板不存在的情况"""
    with patch.object(ConfigManager, '_load_configs'):
        ConfigManager._instance = None
        config = ConfigManager()
        config._templates = {'image_templates': []}
        
        with pytest.raises(ValueError) as exc_info:
            config.get_image_template()
        assert "No image template found" in str(exc_info.value) 