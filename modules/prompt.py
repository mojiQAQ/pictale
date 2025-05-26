import os
import json
from pathlib import Path
from openai import AsyncAzureOpenAI
from modules.config import ConfigManager
from modules.logger import get_logger

class PromptGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        azure_config = self.config_manager.get_azure_config()
        prompts_file = azure_config['prompts_file']
        with open(prompts_file, 'r', encoding='utf-8') as f:
            self.prompts = json.load(f)
        
        self.client = AsyncAzureOpenAI(
            api_key=azure_config['api_key'],
            azure_endpoint=azure_config['endpoint'],
            api_version=azure_config['api_version']
        )
    
    async def generate(self, word: str) -> str:
        azure_config = self.config_manager.get_azure_config()
        # 使用模板中定义的system_prompt，如果没有则使用默认值
        system_prompt = self.prompts['system_prompt']
        assistant_prompt = json.dumps(self.prompts['assistant_prompt'], ensure_ascii=False)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": word},
            {"role": "assistant", "content": assistant_prompt}
        ]
        self.logger.debug(f"messages: {messages}")
        
        try:
            self.logger.debug(f"调用Azure OpenAI API")
            response = await self.client.chat.completions.create(
                model=azure_config['deployment_name'],
                response_format={ "type": "json_object" },
                messages=messages,
                temperature=0.7
            )
            
            generated_prompt = response.choices[0].message.content.strip()
            self.logger.info(f"生成的提示词: {generated_prompt[:50]}{'...' if len(generated_prompt) > 50 else ''}")
            return generated_prompt
        except Exception as e:
            self.logger.error(f"生成提示词时出错: {str(e)}")
            raise