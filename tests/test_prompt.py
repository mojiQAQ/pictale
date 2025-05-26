import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from modules.prompt import PromptGenerator
from modules.config import ConfigManager

@pytest.fixture
def mock_azure_config():
    return {
        'endpoint': "https://mock-endpoint.openai.azure.com",
        'api_key': "mock-api-key",
        'api_version': "2024-02-15-preview",
        'deployment_name': "mock-deployment"
    }

@pytest.fixture
def mock_image_template():
    return {
        'name': 'default',
        'style': 'realistic',
        'prompt_template': "Base template: {word}, {style}"
    }

@pytest.mark.asyncio
@patch('modules.prompt.AsyncAzureOpenAI')
async def test_generate_prompt_success(MockAzureClient, mock_azure_config, mock_image_template):
    # 配置 mock 客户端
    mock_client = AsyncMock()
    MockAzureClient.return_value = mock_client
    
    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=", additional details from AI"))
    ]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # 模拟 ConfigManager
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get_azure_config.return_value = mock_azure_config
    mock_config_manager.get_image_template.return_value = mock_image_template
    
    # 注入模拟的 ConfigManager
    with patch('modules.prompt.ConfigManager', return_value=mock_config_manager):
        generator = PromptGenerator()
        result = await generator.generate("test", "default")
    
    # 验证结果格式
    assert "Base template: test, realistic" in result
    assert "additional details from AI" in result
    
    # 验证 API 调用参数
    mock_client.chat.completions.create.assert_awaited_once_with(
        model="mock-deployment",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a creative prompt engineer for image generation."},
            {"role": "user", "content": "Generate a detailed prompt for generating an image of the word 'test' in realistic style. The prompt should be suitable for Stable Diffusion."}
        ]
    )
    
    # 验证 ConfigManager 调用
    mock_config_manager.get_azure_config.assert_called()
    mock_config_manager.get_image_template.assert_called_with("default")

@pytest.mark.asyncio
async def test_config_manager_error():
    # 模拟 ConfigManager 抛出异常
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get_azure_config.side_effect = KeyError("Azure OpenAI configuration not found in settings")
    
    with patch('modules.prompt.ConfigManager', return_value=mock_config_manager):
        with pytest.raises(KeyError) as exc_info:
            generator = PromptGenerator()
        
        assert "Azure OpenAI configuration not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_template_not_found():
    # 模拟 ConfigManager
    mock_config_manager = MagicMock(spec=ConfigManager)
    mock_config_manager.get_azure_config.return_value = {
        'endpoint': "https://mock-endpoint.openai.azure.com",
        'api_key': "mock-api-key",
        'api_version': "2024-02-15-preview",
        'deployment_name': "mock-deployment"
    }
    mock_config_manager.get_image_template.side_effect = ValueError("No image template found")
    
    with patch('modules.prompt.ConfigManager', return_value=mock_config_manager):
        generator = PromptGenerator()
        with pytest.raises(ValueError) as exc_info:
            await generator.generate("test", "invalid_template")
        
        assert "No image template found" in str(exc_info.value) 