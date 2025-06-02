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
        self.output_dir = self.config_manager.get_output_base_dir()
    
    def generate_draft(self, word_results_list, output_path=None):
        """
        根据单词处理结果列表生成剪映草稿
        
        Args:
            word_results_list: 包含单词处理结果的列表，每个元素包含以下字段:
                {
                    'word': 单词文本,
                    'word_zh': 单词中文翻译,
                    'phrase': 短语文本,
                    'phrase_zh': 短语中文翻译,
                    'word_image_path': 单词图片路径,
                    'phrase_image_path': 短语图片路径,
                    'word_audio_path': 单词英文发音路径,
                    'word_zh_audio_path': 单词中文发音路径,
                    'phrase_audio_path': 短语英文发音路径,
                    'phrase_zh_audio_path': 短语中文发音路径
                }
            output_path: 输出草稿文件路径，默认为None（自动生成）
        
        Returns:
            str: 生成的草稿文件路径
        """
        try:
            self.logger.info(f"开始生成剪映草稿，共 {len(word_results_list)} 个单词")
            
            # 如果未指定输出路径，则自动生成
            if not output_path:
                timestamp = int(time.time())
                output_path = self.output_dir / f"pictale_draft_{timestamp}.jy"
            else:
                output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建一个新的草稿对象 (1920x1080)
            new_draft = Script_file(1920, 1080)
            
            # 存储资源ID对应表
            resource_map = {}
            
            # 第一步：添加所有资源到草稿中
            self.logger.info("添加媒体资源...")
            for word_result in word_results_list:
                # 添加单词图片资源
                if 'word_image_path' in word_result and os.path.exists(word_result['word_image_path']):
                    img_path = word_result['word_image_path']
                    img_id = new_draft.addImageResource(img_path)
                    resource_map[img_path] = img_id
                    self.logger.debug(f"添加单词图片资源: {img_path}")
                
                # 添加短语图片资源
                if 'phrase_image_path' in word_result and os.path.exists(word_result['phrase_image_path']):
                    phrase_img_path = word_result['phrase_image_path']
                    phrase_img_id = new_draft.addImageResource(phrase_img_path)
                    resource_map[phrase_img_path] = phrase_img_id
                    self.logger.debug(f"添加短语图片资源: {phrase_img_path}")
                
                # 添加单词英文音频资源
                if 'word_audio_path' in word_result and os.path.exists(word_result['word_audio_path']):
                    audio_path = word_result['word_audio_path']
                    audio_id = new_draft.addAudioResource(audio_path)
                    resource_map[audio_path] = audio_id
                    self.logger.debug(f"添加单词英文音频资源: {audio_path}")
                
                # 添加单词中文音频资源
                if 'word_zh_audio_path' in word_result and os.path.exists(word_result['word_zh_audio_path']):
                    audio_zh_path = word_result['word_zh_audio_path']
                    audio_zh_id = new_draft.addAudioResource(audio_zh_path)
                    resource_map[audio_zh_path] = audio_zh_id
                    self.logger.debug(f"添加单词中文音频资源: {audio_zh_path}")
                    
                # 添加短语英文音频资源
                if 'phrase_audio_path' in word_result and os.path.exists(word_result['phrase_audio_path']):
                    phrase_audio_path = word_result['phrase_audio_path']
                    phrase_audio_id = new_draft.addAudioResource(phrase_audio_path)
                    resource_map[phrase_audio_path] = phrase_audio_id
                    self.logger.debug(f"添加短语英文音频资源: {phrase_audio_path}")
                
                # 添加短语中文音频资源
                if 'phrase_zh_audio_path' in word_result and os.path.exists(word_result['phrase_zh_audio_path']):
                    phrase_zh_audio_path = word_result['phrase_zh_audio_path']
                    phrase_zh_audio_id = new_draft.addAudioResource(phrase_zh_audio_path)
                    resource_map[phrase_zh_audio_path] = phrase_zh_audio_id
                    self.logger.debug(f"添加短语中文音频资源: {phrase_zh_audio_path}")
            
            # 第二步：按轨道组织内容
            self.logger.info("组织轨道内容...")
            current_time = 0  # 当前时间位置 (毫秒)
            
            for index, word_result in enumerate(word_results_list):
                word = word_result.get('word', f'Word_{index}')
                phrase = word_result.get('phrase', f'Phrase_{index}')
                
                self.logger.debug(f"处理单词 '{word}' 和短语 '{phrase}'")
                
                # 轨道1：图片轨道 - 单词图片 + 短语图片
                word_img_id = resource_map.get(word_result.get('word_image_path'))
                phrase_img_id = resource_map.get(word_result.get('phrase_image_path'))
                
                word_img_duration = 3000  # 单词图片持续3秒
                phrase_img_duration = 3000  # 短语图片持续3秒
                
                if word_img_id:
                    new_draft.addImageClip(word_img_id, current_time, word_img_duration)
                    self.logger.debug(f"添加单词图片片段: {word} 从 {current_time}ms 开始，持续 {word_img_duration}ms")
                
                if phrase_img_id:
                    phrase_start_time = current_time + word_img_duration
                    new_draft.addImageClip(phrase_img_id, phrase_start_time, phrase_img_duration)
                    self.logger.debug(f"添加短语图片片段: {phrase} 从 {phrase_start_time}ms 开始，持续 {phrase_img_duration}ms")
                
                # 轨道2：英文音频轨道 - 单词英文 + 短语英文
                word_en_audio_id = resource_map.get(word_result.get('word_audio_path'))
                phrase_en_audio_id = resource_map.get(word_result.get('phrase_audio_path'))
                
                if word_en_audio_id:
                    # 单词英文音频在单词图片开始后0.5秒播放
                    word_audio_start = current_time + 500
                    word_audio_duration = 2000  # 预设2秒
                    new_draft.addAudioClip(word_en_audio_id, word_audio_start, word_audio_duration)
                    self.logger.debug(f"添加单词英文音频: {word} 从 {word_audio_start}ms 开始")
                
                if phrase_en_audio_id:
                    # 短语英文音频在短语图片开始后0.5秒播放
                    phrase_audio_start = current_time + word_img_duration + 500
                    phrase_audio_duration = 2000  # 预设2秒
                    new_draft.addAudioClip(phrase_en_audio_id, phrase_audio_start, phrase_audio_duration)
                    self.logger.debug(f"添加短语英文音频: {phrase} 从 {phrase_audio_start}ms 开始")
                
                # 轨道3：中文音频轨道 - 单词中文 + 短语中文
                word_zh_audio_id = resource_map.get(word_result.get('word_zh_audio_path'))
                phrase_zh_audio_id = resource_map.get(word_result.get('phrase_zh_audio_path'))
                
                if word_zh_audio_id:
                    # 单词中文音频在单词英文音频结束后0.3秒播放
                    word_zh_audio_start = current_time + 500 + 2000 + 300
                    word_zh_audio_duration = 1500  # 预设1.5秒
                    new_draft.addAudioClip(word_zh_audio_id, word_zh_audio_start, word_zh_audio_duration)
                    self.logger.debug(f"添加单词中文音频: {word_result.get('word_zh')} 从 {word_zh_audio_start}ms 开始")
                
                if phrase_zh_audio_id:
                    # 短语中文音频在短语英文音频结束后0.3秒播放
                    phrase_zh_audio_start = current_time + word_img_duration + 500 + 2000 + 300
                    phrase_zh_audio_duration = 1500  # 预设1.5秒
                    new_draft.addAudioClip(phrase_zh_audio_id, phrase_zh_audio_start, phrase_zh_audio_duration)
                    self.logger.debug(f"添加短语中文音频: {word_result.get('phrase_zh')} 从 {phrase_zh_audio_start}ms 开始")
                
                # 添加文本字幕
                # 单词英文字幕
                if word_result.get('word'):
                    word_text_params = {
                        "text": word_result.get('word'),
                        "color": "#FFFFFF",  # 白色
                        "fontSize": 80,  # 字体大小
                        "fontWeight": "bold",  # 粗体
                        "position": "center",  # 居中
                        "y_pos": 0.75  # 垂直位置
                    }
                    new_draft.addTextClip(current_time, word_img_duration, word_text_params)
                
                # 单词中文字幕
                if word_result.get('word_zh'):
                    word_zh_text_params = {
                        "text": word_result.get('word_zh'),
                        "color": "#FFFF00",  # 黄色
                        "fontSize": 60,  # 字体大小
                        "fontWeight": "normal",  # 正常粗细
                        "position": "center",  # 居中
                        "y_pos": 0.85  # 在英文下方
                    }
                    new_draft.addTextClip(current_time, word_img_duration, word_zh_text_params)
                
                # 短语英文字幕
                if word_result.get('phrase'):
                    phrase_start_time = current_time + word_img_duration
                    phrase_text_params = {
                        "text": word_result.get('phrase'),
                        "color": "#FFFFFF",  # 白色
                        "fontSize": 70,  # 字体大小
                        "fontWeight": "bold",  # 粗体
                        "position": "center",  # 居中
                        "y_pos": 0.75  # 垂直位置
                    }
                    new_draft.addTextClip(phrase_start_time, phrase_img_duration, phrase_text_params)
                
                # 短语中文字幕
                if word_result.get('phrase_zh'):
                    phrase_start_time = current_time + word_img_duration
                    phrase_zh_text_params = {
                        "text": word_result.get('phrase_zh'),
                        "color": "#FFFF00",  # 黄色
                        "fontSize": 55,  # 字体大小
                        "fontWeight": "normal",  # 正常粗细
                        "position": "center",  # 居中
                        "y_pos": 0.85  # 在英文下方
                    }
                    new_draft.addTextClip(phrase_start_time, phrase_img_duration, phrase_zh_text_params)
                
                # 更新时间位置（单词3秒 + 短语3秒 + 间隔1秒）
                current_time += word_img_duration + phrase_img_duration + 1000
            
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
        if not process_results:
            raise ValueError("处理结果列表不能为空")
        
        self.logger.info(f"从 {len(process_results)} 个处理结果生成剪映草稿")
        return self.generate_draft(process_results, output_path)

