import os
import time
import subprocess
from pathlib import Path
from modules.config import ConfigManager
from modules.logger import get_logger

class SrtGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.output_dir = self.config_manager.get_output_dir('videos')
    
    def _get_audio_duration(self, audio_path):
        """获取音频文件的持续时间（秒）"""
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", 
                  "default=noprint_wrappers=1:nokey=1", audio_path]
            duration = float(subprocess.check_output(cmd).decode().strip())
            return duration
        except Exception as e:
            self.logger.warning(f"无法获取音频 {audio_path} 时长，使用默认值: {e}")
            return 2.0  # 默认2秒
    
    def _format_time(self, seconds):
        """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"
    
    def generate(self, word_data, lead_silence=1.0, audio_gap=1.0, output_path=None):
        """
        根据单词数据生成SRT字幕文件
        
        Args:
            word_data: 包含单词数据的字典，需要包含以下字段:
                - word: 单词文本
                - word_zh: 单词中文翻译
                - phrase: 短语文本
                - phrase_zh: 短语中文翻译
                - word_audio_path: 单词音频路径
                - word_zh_audio_path: 单词中文音频路径
                - phrase_audio_path: 短语音频路径
                - phrase_zh_audio_path: 短语中文音频路径
            lead_silence: 前导静音时间（秒）
            audio_gap: 各段音频之间的间隔时间（秒）
            output_path: 输出SRT文件路径（可选）
            
        Returns:
            str: 生成的SRT文件路径
        """
        try:
            # 如果未指定输出路径，则自动生成
            if not output_path:
                timestamp = int(time.time())
                output_path = self.output_dir / f"subtitle_{timestamp}.srt"
            else:
                output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 提取单词数据
            word = word_data.get('word', '')
            word_zh = word_data.get('word_zh', '')
            phrase = word_data.get('phrase', '')
            phrase_zh = word_data.get('phrase_zh', '')
            
            # 获取音频路径
            word_audio_path = word_data.get('word_audio_path')
            word_zh_audio_path = word_data.get('word_zh_audio_path')
            phrase_audio_path = word_data.get('phrase_audio_path')
            phrase_zh_audio_path = word_data.get('phrase_zh_audio_path')
            
            # 计算各段音频时长
            durations = {}
            current_time = lead_silence  # 从前导静音后开始
            
            # 添加单词英文
            if word_audio_path and os.path.exists(word_audio_path):
                durations['word'] = {
                    'start': current_time,
                    'duration': self._get_audio_duration(word_audio_path)
                }
                current_time += durations['word']['duration'] + audio_gap
            
            # 添加单词中文
            if word_zh_audio_path and os.path.exists(word_zh_audio_path):
                durations['word_zh'] = {
                    'start': current_time,
                    'duration': self._get_audio_duration(word_zh_audio_path)
                }
                current_time += durations['word_zh']['duration'] + audio_gap
            
            # 添加短语英文
            if phrase_audio_path and os.path.exists(phrase_audio_path):
                durations['phrase'] = {
                    'start': current_time,
                    'duration': self._get_audio_duration(phrase_audio_path)
                }
                current_time += durations['phrase']['duration'] + audio_gap
            
            # 添加短语中文
            if phrase_zh_audio_path and os.path.exists(phrase_zh_audio_path):
                durations['phrase_zh'] = {
                    'start': current_time,
                    'duration': self._get_audio_duration(phrase_zh_audio_path)
                }
            
            # 创建SRT内容
            srt_content = []
            index = 1
            
            # 英文单词字幕
            if 'word' in durations:
                start_time = durations['word']['start']
                end_time = start_time + durations['word']['duration']
                srt_content.append(f"{index}")
                srt_content.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
                srt_content.append(f"{word}")
                srt_content.append("")
                index += 1
            
            # 中文单词字幕
            if 'word_zh' in durations:
                start_time = durations['word_zh']['start']
                end_time = start_time + durations['word_zh']['duration']
                srt_content.append(f"{index}")
                srt_content.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
                srt_content.append(f"{word_zh}")
                srt_content.append("")
                index += 1
            
            # 英文短语字幕
            if 'phrase' in durations:
                start_time = durations['phrase']['start']
                end_time = start_time + durations['phrase']['duration']
                srt_content.append(f"{index}")
                srt_content.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
                srt_content.append(f"{phrase}")
                srt_content.append("")
                index += 1
            
            # 中文短语字幕
            if 'phrase_zh' in durations:
                start_time = durations['phrase_zh']['start']
                end_time = start_time + durations['phrase_zh']['duration']
                srt_content.append(f"{index}")
                srt_content.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
                srt_content.append(f"{phrase_zh}")
                srt_content.append("")
            
            # 保存SRT文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            
            self.logger.info(f"字幕文件已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成字幕文件时出错: {str(e)}")
            raise Exception(f"Error generating SRT subtitle: {str(e)}")
    
    def attach_to_video(self, video_path, srt_path, output_path=None):
        """
        将SRT字幕文件附加到视频文件
        
        Args:
            video_path: 视频文件路径
            srt_path: SRT字幕文件路径
            output_path: 输出视频文件路径（可选）
        
        Returns:
            str: 带字幕的视频文件路径
        """
        try:
            # 如果未指定输出路径，则自动生成
            if not output_path:
                video_file = Path(video_path)
                timestamp = int(time.time())
                output_path = video_file.with_name(f"{video_file.stem}_subtitled_{timestamp}{video_file.suffix}")
            
            # 使用FFmpeg添加字幕
            command = [
                'ffmpeg',
                '-i', video_path,
                '-i', srt_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'mov_text',  # 使用MOV文本格式的字幕
                '-metadata:s:s:0', 'language=eng',  # 设置字幕语言为英语
                str(output_path)
            ]
            
            self.logger.debug(f"FFmpeg命令: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True)
            
            self.logger.info(f"带字幕的视频已生成: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"添加字幕到视频时出错: {error_message}")
            raise Exception(f"Error attaching subtitle to video: {error_message}")
        except Exception as e:
            self.logger.error(f"添加字幕到视频时出错: {str(e)}")
            raise Exception(f"Error attaching subtitle to video: {str(e)}")

    def hard_attach_to_video(self, video_path, srt_path, output_path=None):
        """
        将SRT字幕文件硬编码到视频文件中
        
        Args:
            video_path: 视频文件路径
            srt_path: SRT字幕文件路径
            output_path: 输出视频文件路径（可选）
            
        Returns:
            str: 带硬编码字幕的视频文件路径
        """
        try:
            # 如果未指定输出路径，则自动生成
            if not output_path:
                video_file = Path(video_path)
                timestamp = int(time.time())
                output_path = video_file.with_name(f"{video_file.stem}_hard_subtitled_{timestamp}{video_file.suffix}")
            
            # 使用FFmpeg硬编码字幕
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=1,BorderStyle=3'",
                '-c:a', 'copy',
                str(output_path)
            ]
            
            self.logger.debug(f"FFmpeg命令: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True)
            
            self.logger.info(f"带硬编码字幕的视频已生成: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"硬编码字幕到视频时出错: {error_message}")
            raise Exception(f"Error hard-coding subtitle to video: {error_message}")
        except Exception as e:
            self.logger.error(f"硬编码字幕到视频时出错: {str(e)}")
            raise Exception(f"Error hard-coding subtitle to video: {str(e)}")
