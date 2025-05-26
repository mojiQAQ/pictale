import os
import subprocess
from pathlib import Path
import time
import tempfile
from modules.config import ConfigManager
from modules.logger import get_logger

class VideoGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.output_dir = self.config_manager.get_output_base_dir()
        self.ffmpeg_config = self.config_manager.get_ffmpeg_config()
    
    def generate(self, image_path: str, audio_path: str, audio_zh_path: str = None, 
                quality: str = 'medium',
                lead_silence_duration: float = 1,
                end_pause: float = 1,
                audio_gap: float = 1,
                output_video_path: str = None,
                output_audio_path: str = None) -> str:
        """生成视频，将多个音频和一个图片合成为视频
        
        Args:
            image_path: 图像路径
            audio_path: 音频路径
            audio_zh_path: 中文音频路径（可选）
            quality: 视频质量，可选值: 'low', 'medium', 'high'
            lead_silence_duration: 前导静音时间（秒）
            end_pause: 音频结束后的静置时间（秒）
            audio_gap: 各段音频之间的间隔时间（秒）
            output_path: 输出视频路径（可选）

        Returns:
            str: 生成的视频路径
        """
        if output_video_path is None:
            timestamp = int(time.time())
            output_video_path = self.output_dir / f"video_{timestamp}.mp4"
        
        if output_audio_path is None:
            timestamp = int(time.time()) if 'timestamp' not in locals() else timestamp
            output_audio_path = self.output_dir / f"audio_{timestamp}.aac"

        # Convert Path objects to strings
        image_path = str(image_path)
        audio_path = str(audio_path) if audio_path else None
        audio_zh_path = str(audio_zh_path) if audio_zh_path else None
        output_video_path = str(output_video_path)
        output_audio_path = str(output_audio_path)

        print("path", image_path, audio_path, audio_zh_path, output_video_path, output_audio_path)
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 收集所有存在的音频文件路径
            audio_paths = []
            if audio_path and os.path.exists(audio_path):
                audio_paths.append(audio_path)
            if audio_zh_path and os.path.exists(audio_zh_path):
                audio_paths.append(audio_zh_path)
            
            if not audio_paths:
                self.logger.error("没有提供有效的音频文件")
                raise ValueError("至少需要提供一个有效的音频文件")
            
            # 计算所有音频的总时长
            total_audio_duration = 0
            for audio_path in audio_paths:
                try:
                    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", 
                          "default=noprint_wrappers=1:nokey=1", audio_path]
                    duration = float(subprocess.check_output(cmd).decode().strip())
                    total_audio_duration += duration
                    self.logger.debug(f"音频 {audio_path} 时长: {duration}秒")
                except Exception as e:
                    self.logger.warning(f"无法获取音频 {audio_path} 时长，使用默认值: {e}")
                    total_audio_duration += 2.0  # 默认每个音频2秒
            
            # 添加音频间隔时间
            total_audio_duration += audio_gap * (len(audio_paths) - 1)
            
            # 在音频结束后添加指定的静置时间
            total_duration = total_audio_duration + end_pause
            self.logger.debug(f"添加 {end_pause}秒 结束暂停，总时长: {total_duration}秒")

            # 添加前导静音
            silence_file = os.path.join(temp_dir, "silence.aac")
            silence_cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(lead_silence_duration),
                "-c:a", "aac",
                "-b:a", "192k",
                silence_file
            ]
            subprocess.run(silence_cmd, check=True, capture_output=True)
            
            # 创建音频间隔文件
            gap_file = os.path.join(temp_dir, "gap.aac")
            if audio_gap > 0:
                gap_cmd = [
                    "ffmpeg",
                    "-f", "lavfi",
                    "-i", f"anullsrc=r=44100:cl=stereo",
                    "-t", str(audio_gap),
                    "-c:a", "aac",
                    "-b:a", "192k",
                    gap_file
                ]
                subprocess.run(gap_cmd, check=True, capture_output=True)
            
            # 准备合并所有音频
            concat_parts = []
            concat_inputs = []
            
            # 添加前导静音
            concat_inputs = ["-i", silence_file]
            concat_parts = ["[0:a]"]
            
            # 添加所有音频文件和间隔
            for i, audio_path in enumerate(audio_paths):
                # 添加音频文件
                concat_inputs.extend(["-i", audio_path])
                concat_parts.append(f"[{len(concat_parts)}:a]")

                # 添加间隔文件
                if i < len(audio_paths) - 1:
                    concat_inputs.extend(["-i", gap_file])
                    concat_parts.append(f"[{len(concat_parts)}:a]")

            self.logger.debug(f'concat_inputs: {concat_inputs}')
            self.logger.debug(f'concat_parts: {concat_parts}')
            
            # 拼接所有音频
            concat_string = "".join(concat_parts)
            concat_count = len(concat_parts)
            filter_complex = f"{concat_string}concat=n={concat_count}:v=0:a=1[out]"
            
            # 合并所有音频文件
            combined_audio = output_audio_path
            concat_audio_cmd = [
                "ffmpeg",
                *concat_inputs,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:a", "aac",
                "-b:a", "192k",
                combined_audio
            ]
            
            self.logger.debug(f"合并音频命令: {' '.join(concat_audio_cmd)}")
            subprocess.run(concat_audio_cmd, check=True, capture_output=True)
            
            # 根据质量设置编码参数
            quality_presets = {
                'low': {
                    'video_bitrate': '1M',
                    'preset': 'ultrafast',
                    'crf': '28'
                },
                'medium': {
                    'video_bitrate': '2M',
                    'preset': 'medium',
                    'crf': '23'
                },
                'high': {
                    'video_bitrate': '4M',
                    'preset': 'slow',
                    'crf': '18'
                }
            }
            
            # 使用默认质量如果未指定
            quality_settings = quality_presets.get(quality, quality_presets['medium'])
            
            # 更新总时长，加上前导静音时长
            total_duration += lead_silence_duration
            
            # 使用FFmpeg将图片和音频合成为视频
            command = [
                'ffmpeg',
                '-loop', '1',
                '-i', image_path,
                '-i', combined_audio,
                '-c:v', self.ffmpeg_config.get('video_codec', 'libx264'),
                '-preset', quality_settings['preset'],
                '-crf', quality_settings['crf'],
                '-b:v', quality_settings['video_bitrate'],
                '-tune', 'stillimage',
                '-c:a', self.ffmpeg_config.get('audio_codec', 'aac'),
                '-b:a', self.ffmpeg_config.get('audio_bitrate', '192k'),
                '-pix_fmt', self.ffmpeg_config.get('pixel_format', 'yuv420p'),
                '-vf', 'scale=-2:1080,format=yuv420p', # 确保1080p和兼容性
                '-t', str(total_duration),  # 指定时长确保音频完全播放
                output_video_path
            ]
            
            self.logger.info(f"开始生成视频，使用图像: {image_path} 和 {len(audio_paths)} 个音频文件")
            self.logger.debug(f"FFmpeg命令: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True)
            self.logger.info(f"视频生成成功: {output_video_path}")
            return output_video_path
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode()
            self.logger.error(f"生成视频时出错: {error_message}")
            raise Exception(f"Error generating video: {error_message}")
        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir) 