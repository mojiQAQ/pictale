#!/usr/bin/env python3
import os
import sys
import json
import argparse
import asyncio
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from modules.prompt import PromptGenerator
from modules.image import ImageGenerator
from modules.audio_my import MoyinAudioGenerator
from modules.audio import AudioGenerator
from modules.video import VideoGenerator
from modules.srt import SrtGenerator
from modules.config import ConfigManager
from modules.logger import get_logger, COLORS
import subprocess

# 初始化日志记录器
logger = get_logger("app")

def log_step(step_num, total_steps, desc):
    """记录步骤信息"""
    logger.info(f"{COLORS['BLUE']}[{step_num}/{total_steps}]{COLORS['RESET']} {COLORS['BOLD']}{desc}{COLORS['RESET']}")

def log_success(message):
    """记录成功信息"""
    logger.info(f"{COLORS['GREEN']}✓ {message}{COLORS['RESET']}")

def log_warning(message):
    """记录警告信息"""
    logger.warning(f"{COLORS['YELLOW']}⚠ {message}{COLORS['RESET']}")

def log_error(message):
    """记录错误信息"""
    logger.error(f"{COLORS['RED']}✗ {message}{COLORS['RESET']}")

def print_banner():
    """打印工具横幅"""
    banner = f"""
{COLORS['BOLD']}{COLORS['BLUE']}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      Word Video Generator                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{COLORS['RESET']}
    """
    logger.info(banner)

async def process_single_word(word, args, config_manager, task_id, total_steps=5):
    """处理单个单词的视频生成流程"""
    results = {
        'task_id': task_id,
        'word': word
    }
    start_time = time.time()
    output_base_dir = config_manager.get_output_base_dir() / str(task_id) / word
    output_base_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_base_dir}")

    try:
        # 1. 生成提示词
        if not args.skip_prompt:
            log_step(1, total_steps, f"为单词 '{word}' 生成图像提示词...")
            prompt_gen = PromptGenerator()
            word_prompt = await prompt_gen.generate(word)
            log_success(f"生成提示词: {word_prompt}")
            word_prompt = json.loads(word_prompt)

            results['word'] = word_prompt['word']
            results['word_zh'] = word_prompt['word_zh']
            results['word_prompt'] = word_prompt['word_prompt']
            results['phrase'] = word_prompt['phrase']
            results['phrase_zh'] = word_prompt['phrase_zh']
            results['phrase_prompt'] = word_prompt['phrase_prompt']

            # 保存结果到JSON文件
            json_path = output_base_dir / "result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            log_success(f"结果已保存到: {json_path}")
        else:
            log_warning(f"跳过单词 '{word}' 的提示词生成")
            results['word_prompt'] = word_prompt['word_prompt']
            results['phrase_prompt'] = word_prompt['phrase_prompt']

        # 2. 生成图片
        if not args.skip_image:
            log_step(2, total_steps, f"为单词 '{word}' 生成图像...")
            image_gen = ImageGenerator()
            word_image_path = image_gen.generate(results['word_prompt'], output_path=output_base_dir / "word_image.png")
            log_success(f"单词图像已保存: {word_image_path}")
            results['word_image_path'] = word_image_path

            phrase_image_path = image_gen.generate(results['phrase_prompt'], output_path=output_base_dir / "phrase_image.png")
            log_success(f"句子图像已保存: {phrase_image_path}")
            results['phrase_image_path'] = phrase_image_path
        elif args.image_path:
            log_warning(f"为单词 '{word}' 使用已有图像: {args.image_path}")
            results['image_path'] = args.image_path
        else:
            log_error("需要图像路径，请提供--image-path或不使用--skip-image")
            return None

        # 3. 生成语音
        if not args.skip_audio:
            log_step(3, total_steps, f"为单词 '{word}' 生成语音...")
            if args.tts == 'tencent':
                audio_gen = AudioGenerator()
            elif args.tts == 'moyin':
                audio_gen = MoyinAudioGenerator()
            else:
                log_error("不支持的语音类型，请使用--tts参数指定语音类型")
                return None
            
            word_audio_path = audio_gen.generate(results['word'], 'word', 'en', output_path=output_base_dir / "word_audio.wav")
            log_success(f"单词语音已保存: {word_audio_path}")
            results['word_audio_path'] = word_audio_path

            word_zh_audio_path = audio_gen.generate(results['word_zh'], 'word', 'zh', output_path=output_base_dir / "word_zh_audio.wav")
            log_success(f"单词中文语音已保存: {word_zh_audio_path}")
            results['word_zh_audio_path'] = word_zh_audio_path

            phrase_audio_path = audio_gen.generate(results['phrase'], 'phrase', 'en', output_path=output_base_dir / "phrase_audio.wav")
            log_success(f"短语语音已保存: {phrase_audio_path}")
            results['phrase_audio_path'] = phrase_audio_path

            phrase_zh_audio_path = audio_gen.generate(results['phrase_zh'], 'phrase', 'zh', output_path=output_base_dir / "phrase_zh_audio.wav")
            log_success(f"短语中文语音已保存: {phrase_zh_audio_path}")
            results['phrase_zh_audio_path'] = phrase_zh_audio_path
        elif args.audio_path:
            log_warning(f"为单词 '{word}' 使用已有音频: {args.audio_path}")
            results['audio_path'] = args.audio_path
        else:
            log_error("需要音频路径，请提供--audio-path或不使用--skip-audio")
            return None
        
        # 4. 生成SRT字幕文件
        if not args.skip_subtitle:
            log_step(4, total_steps, f"为单词 '{word}' 生成SRT字幕...")
            srt_gen = SrtGenerator()
            # 使用与视频生成相同的参数值
            lead_silence = args.lead_silence if hasattr(args, 'lead_silence') else 1.0
            audio_gap = args.audio_gap if hasattr(args, 'audio_gap') else 1.0
            
            # 为单词部分生成字幕
            word_srt_path = srt_gen.generate(
                audio_path=results['word_audio_path'],
                audio_zh_path=results['word_zh_audio_path'],
                text=results['word'],
                text_zh=results['word_zh'],
                lead_silence=lead_silence,
                audio_gap=audio_gap,
                output_path=output_base_dir / f"word_subtitle.srt"
            )
            log_success(f"单词SRT字幕已保存: {word_srt_path}")
            results['word_srt_path'] = word_srt_path
            
            # 为短语部分生成字幕
            phrase_srt_path = srt_gen.generate(
                audio_path=results['phrase_audio_path'],
                audio_zh_path=results['phrase_zh_audio_path'],
                text=results['phrase'],
                text_zh=results['phrase_zh'],
                lead_silence=lead_silence,
                audio_gap=audio_gap,
                output_path=output_base_dir / f"phrase_subtitle.srt"
            )
            log_success(f"短语SRT字幕已保存: {phrase_srt_path}")
            results['phrase_srt_path'] = phrase_srt_path
        else:
            log_warning(f"跳过单词 '{word}' 的字幕生成")
        
        # 5. 生成视频
        if not args.skip_video:
            log_step(5, total_steps, f"为单词 '{word}' 生成视频...")
            video_gen = VideoGenerator()
            lead_silence = args.lead_silence if hasattr(args, 'lead_silence') else 1.0
            audio_gap = args.audio_gap if hasattr(args, 'audio_gap') else 1.0
            end_pause = args.end_pause if hasattr(args, 'end_pause') else 1.0
            
            # 生成单词视频
            word_video_path = video_gen.generate(
                str(results['word_image_path']),
                audio_path=str(results['word_audio_path']),
                audio_zh_path=str(results['word_zh_audio_path']),
                lead_silence_duration=lead_silence,
                audio_gap=audio_gap,
                end_pause=end_pause,
                output_video_path=str(output_base_dir / "word_video.mp4"),
                output_audio_path=str(output_base_dir / "word_audio.aac")
            )
            log_success(f"单词视频已生成: {word_video_path}")
            results['word_video_path'] = word_video_path
            
            # 生成短语视频
            phrase_video_path = video_gen.generate(
                str(results['phrase_image_path']),
                audio_path=str(results['phrase_audio_path']),
                audio_zh_path=str(results['phrase_zh_audio_path']),
                lead_silence_duration=lead_silence,
                audio_gap=audio_gap,
                end_pause=end_pause,
                output_video_path=str(output_base_dir / "phrase_video.mp4"),
                output_audio_path=str(output_base_dir / "phrase_audio.aac")
            )
            log_success(f"短语视频已生成: {phrase_video_path}")
            results['phrase_video_path'] = phrase_video_path

        else:
            log_warning(f"跳过单词 '{word}' 的视频生成")

        # 完成
        elapsed_time = time.time() - start_time
        logger.info(f"{COLORS['GREEN']}单词 '{word}' 处理完成! 用时: {elapsed_time:.2f}秒{COLORS['RESET']}")
        
        return results
        
    except Exception as e:
        log_error(f"处理单词 '{word}' 过程中出错: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return None

async def generate_video(args, config_manager):
    """生成视频的主要流程，支持批量处理"""
    start_time = time.time()
    task_id = int(time.time())
    logger.info(f"开始执行任务，ID: {task_id}")
    
    # 解析单词列表
    words = []
    if args.words:  # 直接从命令行参数获取多个单词
        words = args.words
    elif args.word:  # 兼容旧版单个单词参数
        words = [args.word]
    elif args.words_file:  # 从文件中读取单词列表
        try:
            with open(args.words_file, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
        except Exception as e:
            log_error(f"读取单词文件时出错: {str(e)}")
            return None
    
    if not words:
        log_error("没有指定要处理的单词，请使用--words或--words-file参数")
        return None
    
    # 显示要处理的单词
    log_success(f"将处理 {len(words)} 个单词: {', '.join(words)}")
    
    # 存储每个单词的处理结果
    all_results = []
    video_paths = []
    
    # 处理每个单词
    for i, word in enumerate(words):
        log_step(i + 1, len(words), f"处理单词 '{word}'...")
        result = await process_single_word(word, args, config_manager, task_id)

        if result:
            all_results.append(result)
            # 优先使用带字幕的视频
            if 'subtitled_video_path' in result:
                video_paths.append(result['subtitled_video_path'])
            elif 'video_path' in result:
                video_paths.append(result['video_path'])
    
    # 如果需要合并视频
    if args.combine and len(video_paths) > 0:
        log_step(len(words) + 1, len(words) + 1, "合并所有视频...")
        output_dir = config_manager.get_output_base_dir() / str(task_id)
        combined_video_path = output_dir / f"combined.mp4"

        # 创建临时文件列表
        temp_list_file = output_dir / "video_list.txt"
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        # 使用ffmpeg直接合并视频
        try:
            subprocess.run([
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_list_file),
                '-c', 'copy',
                str(combined_video_path)
            ], check=True, capture_output=True)
            combined_path = str(combined_video_path)
        except subprocess.CalledProcessError as e:
            log_error(f"合并视频失败: {e.stderr.decode()}")
            combined_path = None
        finally:
            # 清理临时文件
            if temp_list_file.exists():
                temp_list_file.unlink()

        if combined_path:
            log_success(f"所有视频已合并: {combined_path}")
            
            # 如果需要播放
            if args.play:
                play_video(combined_path)
            
            # 添加到结果中
            final_result = {'combined_video_path': combined_path, 'individual_results': all_results}
        else:
            log_error("视频合并失败")
            final_result = {'individual_results': all_results}
    else:
        final_result = {'individual_results': all_results}
    
    # 完成
    elapsed_time = time.time() - start_time
    logger.info(f"\n{COLORS['GREEN']}{COLORS['BOLD']}✨ 任务 {task_id} 所有操作完成! 总用时: {elapsed_time:.2f}秒{COLORS['RESET']}")
    
    return final_result

def play_video(video_path):
    """使用系统默认播放器播放视频"""
    try:
        if sys.platform == "darwin":  # macOS
            os.system(f"open {video_path}")
        elif sys.platform == "win32":  # Windows
            os.system(f"start {video_path}")
        else:  # Linux
            os.system(f"xdg-open {video_path}")
    except Exception as e:
        log_warning(f"无法播放视频: {str(e)}")

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Word Video Generator - 生成单词的音视频',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 单词输入选项（三选一）
    word_group = parser.add_mutually_exclusive_group(required=True)
    word_group.add_argument('--word', '-w', help='要生成视频的单个单词（向后兼容）')
    word_group.add_argument('--words', '-ws', nargs='+', help='要生成视频的多个单词，空格分隔')
    word_group.add_argument('--words-file', '-wf', help='包含单词列表的文件路径，每行一个单词')
    
    # 跳过特定步骤的选项
    parser.add_argument('--skip-prompt', action='store_true', help='跳过提示词生成')
    parser.add_argument('--skip-image', action='store_true', help='跳过图像生成')
    parser.add_argument('--skip-audio', action='store_true', help='跳过音频生成')
    parser.add_argument('--skip-subtitle', action='store_true', help='跳过字幕添加')
    parser.add_argument('--skip-video', action='store_true', help='跳过视频生成')
    
    # 自定义路径选项
    parser.add_argument('--image-path', help='使用已有图像文件路径')
    parser.add_argument('--audio-path', help='使用已有音频文件路径')
    parser.add_argument('--custom-prompt', help='使用自定义提示词而非生成的提示词')
    parser.add_argument('--output-dir', help='指定输出目录')
    
    # 视频和音频参数
    parser.add_argument('--tts', '-tts', default='tencent', help='语音合成类型，可选值: tencent, moyin')
    parser.add_argument('--lead-silence', type=float, default=0.3, help='视频前导静音时长（秒）')
    parser.add_argument('--audio-gap', type=float, default=0.3, help='各段音频之间的间隔时间（秒）')
    parser.add_argument('--end-pause', type=float, default=0, help='每个单词视频结束后的静置时间（秒）')
    
    # 视频合并选项
    parser.add_argument('--combine', '-c', action='store_true', help='合并生成的多个视频')

    # 其他选项
    parser.add_argument('--play', action='store_true', help='生成后自动播放视频')
    parser.add_argument('--no-color', action='store_true', help='禁用彩色输出')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    
    args = parser.parse_args()
    
    # 处理版本信息请求
    if args.version:
        logger.info("Word Video Generator v1.0.0")
        return
    
    # 如果指定了禁用颜色，重置所有颜色代码
    if args.no_color:
        for key in COLORS:
            COLORS[key] = ""
    
    # 如果指定了输出目录，更新配置
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        # TODO: 更新配置中的输出目录
    
    # 显示横幅
    print_banner()
    
    # 运行视频生成流程
    results = await generate_video(args, config_manager)
    
    # 返回适当的退出代码
    if results is None:
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_warning("\n操作已被用户中断")
        sys.exit(130)
