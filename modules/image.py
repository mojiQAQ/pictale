import requests
import time
import json
import base64
from io import BytesIO
from PIL import Image
import os
import random
from pathlib import Path
import websocket
import threading
import uuid
from modules.config import ConfigManager
from modules.logger import get_logger

class ImageGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.comfy_config = self.config_manager.get_comfy_config()
        self.output_dir = self.config_manager.get_output_dir('images')
        
        # ComfyUI API连接信息
        self.base_url = self.comfy_config.get('api_url', 'http://127.0.0.1:8188')
        self.ws_url = self.base_url.replace('http://', 'ws://') + "/ws"
        
        # 初始化客户端ID和工作流属性
        self.client_id = str(uuid.uuid4())
        self.workflow = None
        self.workflow_cache = {}
        self.is_model_loaded = False
        self.status_data = {}
        self.ws = None
        self.prompt_id = None
        
        # 如果配置了预热模式，则在初始化时加载模型
        if self.comfy_config.get('preload_model', True):
            self._preload_workflow()
    
    def _preload_workflow(self):
        """预加载工作流和模型"""
        try:
            # 连接WebSocket以获取状态更新
            self._connect_websocket()
            
            # 加载工作流
            workflow_path = self.comfy_config.get('workflow_file')
            if workflow_path and os.path.exists(workflow_path):
                self.workflow = self._load_workflow_from_file(workflow_path, "placeholder prompt")
            
            # 提取模型信息，创建只包含模型加载部分的工作流
            model_nodes = {}
            for node_id, node in self.workflow.items():
                if node.get('class_type') in ['CheckpointLoaderSimple', 'LoraLoader', 'VAELoader', 'CLIPLoader']:
                    model_nodes[node_id] = node
            
            if model_nodes:
                self.logger.info("正在预加载模型，这可能需要一些时间...")
                # 只提交模型加载部分
                prompt_id = self._submit_workflow(self.base_url, model_nodes)
                if prompt_id:
                    # 等待模型加载完成
                    self._wait_for_execution(prompt_id)
                    self.is_model_loaded = True
                    self.logger.info("模型预加载完成，后续生成将更快")
        except Exception as e:
            self.logger.error(f"预加载模型时出错: {str(e)}")
            self.is_model_loaded = False
    
    def _connect_websocket(self):
        """连接到ComfyUI WebSocket进行状态监控"""
        try:
            self.ws = websocket.create_connection(f"{self.ws_url}?clientId={self.client_id}")
            
            # 启动一个线程来处理WebSocket消息
            def ws_thread():
                while True:
                    try:
                        message = json.loads(self.ws.recv())
                        if message['type'] == 'status':
                            self.status_data = message['data']
                    except Exception as e:
                        self.logger.error(f"WebSocket错误: {str(e)}")
                        break
            
            threading.Thread(target=ws_thread, daemon=True).start()
            return True
        except Exception as e:
            self.logger.error(f"无法连接到ComfyUI WebSocket: {str(e)}")
            return False
    
    def generate(self, prompt: str, output_path: str = None) -> str:
        """生成图像"""
        try:
            # 确保WebSocket连接
            if not self.ws:
                self._connect_websocket()
            
            # 从缓存获取工作流或创建新工作流
            cache_key = self.comfy_config.get('workflow_file', 'default')
            if cache_key in self.workflow_cache and self.is_model_loaded:
                workflow = self.workflow_cache[cache_key].copy()
            else:
                # 加载或创建工作流
                workflow_path = self.comfy_config.get('workflow_file')
                self.logger.info(f"加载工作流: {workflow_path}")
                if workflow_path and os.path.exists(workflow_path):
                    workflow = self._load_workflow_from_file(workflow_path)
                
                # 缓存工作流模板
                self.workflow_cache[cache_key] = workflow.copy()
            
            # 更新工作流中的提示词和种子
            self._update_workflow_for_prompt(workflow, prompt)
            
            # # 如果模型已加载，移除模型加载节点
            # if self.is_model_loaded:
            #     workflow = self._optimize_workflow(workflow)
            self.logger.debug(f"提交工作流: {workflow}")
            # 提交工作流执行
            prompt_id = self._submit_workflow(self.base_url, workflow)
            if not prompt_id:
                raise Exception("提交工作流失败")
            
            # 等待图像生成
            image_data = self._wait_for_image(self.base_url, prompt_id)
            if not image_data:
                raise Exception("图像生成失败")
            
            # 保存图像
            if not output_path:
                timestamp = int(time.time())
                output_path = self.output_dir / f"generated_{timestamp}.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            return str(output_path)
        except Exception as e:
            self.logger.error(f"生成图像时出错: {str(e)}")
            # 重置连接状态以便下次重试
            self.is_model_loaded = False
            self.ws = None
            raise
    
    def _update_workflow_for_prompt(self, workflow: dict, prompt: str):
        """更新工作流中的提示词和随机种子"""
        negative_prompt = self.comfy_config.get('negative_prompt', '')
        
        # 查找提示词节点并更新
        positive_nodes = self.comfy_config.get('positive_prompt_nodes', [])
        negative_nodes = self.comfy_config.get('negative_prompt_nodes', [])
        
        self.logger.debug(f"positive_nodes: {positive_nodes}")
        self.logger.debug(f"negative_nodes: {negative_nodes}")
        # 更新提示词节点的文本
        for node_id, node in workflow.items():
            if node.get('class_type') == 'CLIPTextEncode' and 'inputs' in node:
                if node_id in positive_nodes:
                    node['inputs']['text'] = prompt
                elif node_id in negative_nodes and negative_prompt:
                    node['inputs']['text'] = negative_prompt
                elif not positive_nodes and not negative_nodes:
                    # 如果没有找到明确的连接，使用第一个遇到的作为正向提示词
                    node['inputs']['text'] = prompt
                    break
    
    def _optimize_workflow(self, workflow: dict) -> dict:
        """优化工作流，移除已加载模型的节点"""
        # 如果模型已经加载，我们可以移除模型加载节点，但需保留引用
        # 由于ComfyUI的图处理机制，只移除不需要重新计算的节点
        
        # 找出所有模型加载节点
        model_nodes = {}
        for node_id, node in workflow.items():
            if node.get('class_type') in ['CheckpointLoaderSimple', 'VAELoader', 'CLIPLoader', 'LoraLoader']:
                model_nodes[node_id] = True
        
        # 优化策略1: 保留模型节点但将其标记为"已执行"
        # ComfyUI会跳过已执行的节点，这是更安全的方法
        # 此处我们不需要做什么，因为ComfyUI会处理缓存状态
        
        return workflow
    
    def _load_workflow_from_file(self, workflow_path: str) -> dict:
        """从文件加载工作流"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载工作流文件失败: {e}")
            return None

    def _submit_workflow(self, base_url: str, workflow: dict) -> str:
        """提交工作流到ComfyUI"""
        try:
            response = requests.post(
                f"{base_url}/prompt",
                json={
                    "prompt": workflow,
                    "client_id": self.client_id  # 添加客户端ID，使ComfyUI能够跟踪状态
                }
            )
            if response.status_code != 200:
                self.logger.error(f"提交工作流失败: {response.text}")
                return None
            
            result = response.json()
            return result.get('prompt_id')
            
        except Exception as e:
            self.logger.error(f"提交工作流时出错: {e}")
            return None
    
    def _wait_for_execution(self, prompt_id: str, timeout: int = None) -> bool:
        """等待工作流执行完成，不需要返回图像数据"""
        if timeout is None:
            timeout = self.comfy_config.get('timeout', 120)
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查执行状态
            try:
                # 使用已有的状态数据
                if self.status_data:
                    execution_queue = self.status_data.get('exec_info', {}).get('queue_remaining', 0)
                    if execution_queue == 0:
                        # 检查历史记录确认是否完成
                        response = requests.get(f"{self.base_url}/history")
                        if response.status_code == 200 and prompt_id in response.json():
                            return True
                
                # 如果没有通过WebSocket收到状态，直接查询历史
                response = requests.get(f"{self.base_url}/history")
                if response.status_code == 200 and prompt_id in response.json():
                    return True
                    
            except Exception as e:
                self.logger.error(f"检查执行状态时出错: {e}")
            
            time.sleep(0.5)
        
        self.logger.warning(f"等待工作流执行超时，已等待{timeout}秒")
        return False
    
    def _wait_for_image(self, base_url: str, prompt_id: str) -> bytes:
        """等待图像生成并获取结果"""
        timeout = self.comfy_config.get('timeout', 120)
        
        # 等待执行完成
        if not self._wait_for_execution(prompt_id, timeout):
            return None
        
        # 获取生成的图像
        try:
            response = requests.get(f"{base_url}/history")
            if response.status_code != 200:
                return None
            
            history = response.json()
            self.logger.debug(f"history: {history[prompt_id]}")
            if prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                # 查找SaveImage节点的输出
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        image_info = node_output['images'][0]
                        image_url = f"{base_url}/view?filename={image_info['filename']}&type={image_info['type']}"
                        
                        # 下载图像
                        img_response = requests.get(image_url)
                        self.logger.debug(f"img_response: {img_response}")
                        if img_response.status_code == 200:
                            return img_response.content
                
                self.logger.warning("工作流完成但未找到图像输出")
                return None
        except Exception as e:
            self.logger.error(f"获取图像时出错: {e}")
        
        return None
    
    def __del__(self):
        """清理资源"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass 