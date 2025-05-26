import os
import time
import pyJianYingDraft as draft
from pyJianYingDraft import Script_file
from pathlib import Path
from modules.config import ConfigManager
from modules.logger import get_logger

class DraftGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.output_dir = self.config_manager.get_output_dir('videos')
    
    def generate_draft(self, word_data_list, output_path=None):
        """
        根据单词数据列表生成剪映草稿
        
        Args:
            word_data_list: 包含单词数据的列表，每个元素是一个字典，包含以下字段:
                {
                    'word': 单词文本,
                    'word_chinese': 单词中文翻译,
                    'image_path': 单词图片路径,
                    'word_audio_path': 单词英文发音路径,
                    'word_zh_audio_path': 单词中文发音路径
                }
            output_path: 输出草稿文件路径，默认为None（自动生成）
        
        Returns:
            str: 生成的草稿文件路径
        """
        try:
            self.logger.info(f"开始生成剪映草稿，共 {len(word_data_list)} 个单词")
            
            # 如果未指定输出路径，则自动生成
            if not output_path:
                timestamp = int(time.time())
                output_path = self.output_dir / f"pictale_draft_{timestamp}.jy"
            else:
                output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建一个新的草稿对象
            new_draft = Script_file(1920, 1080)
            draft.Video_material()
            
            # 存储图像和音频资源ID对应表
            resource_map = {}
            
            # 添加所有资源到草稿中
            for word_data in word_data_list:
                # 添加图片资源
                if 'image_path' in word_data and os.path.exists(word_data['image_path']):
                    img_path = word_data['image_path']
                    
                    img_id = new_draft.addImageResource(img_path)
                    resource_map[img_path] = img_id
                    self.logger.debug(f"添加图片资源: {img_path} -> {img_id}")
                
                # 添加单词英文音频资源
                if 'word_audio_path' in word_data and os.path.exists(word_data['word_audio_path']):
                    audio_path = word_data['word_audio_path']
                    audio_id = new_draft.addAudioResource(audio_path)
                    resource_map[audio_path] = audio_id
                    self.logger.debug(f"添加英文音频资源: {audio_path} -> {audio_id}")
                
                # 添加单词中文音频资源
                if 'word_zh_audio_path' in word_data and os.path.exists(word_data['word_zh_audio_path']):
                    audio_zh_path = word_data['word_zh_audio_path']
                    audio_zh_id = new_draft.addAudioResource(audio_zh_path)
                    resource_map[audio_zh_path] = audio_zh_id
                    self.logger.debug(f"添加中文音频资源: {audio_zh_path} -> {audio_zh_id}")
            
            # 创建轨道并添加片段
            for index, word_data in enumerate(word_data_list):
                # 获取图片和音频资源ID
                img_id = resource_map.get(word_data.get('image_path'))
                en_audio_id = resource_map.get(word_data.get('word_audio_path'))
                zh_audio_id = resource_map.get(word_data.get('word_zh_audio_path'))
                
                if not img_id:
                    self.logger.warning(f"单词 '{word_data.get('word')}' 缺少图片资源")
                    continue
                
                # 计算当前片段的开始时间（每个片段5秒）
                start_time = index * 5000  # 毫秒为单位
                
                # 添加图片片段（5秒持续时间）
                new_draft.addImageClip(img_id, start_time, 5000)
                self.logger.debug(f"添加图片片段: {word_data.get('word')} 从 {start_time}ms 开始")
                
                # 添加英文音频片段
                if en_audio_id:
                    # 获取音频文件的实际持续时间（如果可能）
                    try:
                        audio_duration = 2000  # 默认2秒
                        new_draft.addAudioClip(en_audio_id, start_time, audio_duration)
                        self.logger.debug(f"添加英文音频片段: {word_data.get('word')} 从 {start_time}ms 开始")
                    except Exception as e:
                        self.logger.error(f"添加英文音频片段时出错: {e}")
                
                # 添加中文音频片段（在英文之后播放）
                if zh_audio_id:
                    try:
                        zh_start_time = start_time + 2500  # 英文后2.5秒开始播放中文
                        zh_audio_duration = 2000  # 默认2秒
                        new_draft.addAudioClip(zh_audio_id, zh_start_time, zh_audio_duration)
                        self.logger.debug(f"添加中文音频片段: {word_data.get('word_chinese')} 从 {zh_start_time}ms 开始")
                    except Exception as e:
                        self.logger.error(f"添加中文音频片段时出错: {e}")
                
                # 添加文本字幕 - 英文
                text_params = {
                    "text": word_data.get('word', ''),
                    "color": "#FFFFFF",  # 白色
                    "fontSize": 72,  # 字体大小
                    "fontWeight": "bold",  # 粗体
                    "position": "center",  # 居中
                    "y_pos": 0.7  # 垂直位置 (0-1)
                }
                new_draft.addTextClip(start_time, 5000, text_params)
                
                # 添加文本字幕 - 中文
                if 'word_chinese' in word_data:
                    zh_text_params = {
                        "text": word_data.get('word_chinese', ''),
                        "color": "#FFFFFF",  # 白色
                        "fontSize": 60,  # 字体大小略小
                        "fontWeight": "normal",  # 正常粗细
                        "position": "center",  # 居中
                        "y_pos": 0.8  # 在英文下方
                    }
                    new_draft.addTextClip(start_time, 5000, zh_text_params)
            
            # 保存草稿文件
            new_draft.export(str(output_path))
            self.logger.info(f"剪映草稿已保存: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成剪映草稿时出错: {str(e)}")
            raise Exception(f"Error generating JianYing draft: {str(e)}")
    
    def generate_from_results(self, process_results, output_path=None):
        """
        从处理结果直接生成剪映草稿
        
        Args:
            process_results: 处理结果列表，由process_single_word函数生成
            output_path: 输出草稿文件路径
            
        Returns:
            str: 生成的草稿文件路径
        """
        word_data_list = []
        
        for result in process_results:
            word_data = {
                'word': result.get('word'),
                'word_chinese': result.get('word_zh'),
                'image_path': result.get('image_path'),
                'word_audio_path': result.get('word_audio_path'),
                'word_zh_audio_path': result.get('word_zh_audio_path')
            }
            word_data_list.append(word_data)
        
        return self.generate_draft(word_data_list, output_path)

