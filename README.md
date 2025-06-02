# Word Video Generator (Pictale)

一个基于Python的单词音视频生成工具，可以将单词转换为包含图片、多语音轨道和字幕的视频。

## 功能特点

- **智能提示词生成**：基于Azure OpenAI的LLM智能提示词生成
- **图片生成**：使用ComfyUI/Stable Diffusion生成高质量图片
- **多语音合成**：支持英文单词、中文单词、英文短语和中文短语四轨语音
- **字幕生成**：自动生成与音频同步的SRT字幕文件
- **视频合成**：使用FFmpeg将图片和多轨语音合成为视频
- **批量处理**：支持批量处理多个单词并合并为单个视频

## 环境要求

- Python 3.8+
- FFmpeg (用于音视频处理)
- ComfyUI (用于图像生成)
- 魔音API或腾讯云账号 (用于语音合成)
- Azure OpenAI API (用于提示词生成)

## 安装

1. 克隆项目：
```bash
git clone https://github.com/mojiQAQ/pictale.git
cd pictale
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量和设置文件：
```bash
cp setting.yaml.exmple setting.yaml
```
编辑 `setting.yaml` 文件，填入API密钥和配置信息。

## 使用方法

### 基本用法

生成单个单词的视频：
```bash
python app.py --word "apple"
```

批量处理多个单词：
```bash
python app.py --words "apple" "banana" "orange"
```

从文件读取单词列表：
```bash
python app.py --words-file "words.txt"
```

### 高级选项

**调整音频参数**：
```bash
python app.py --word "apple" --lead-silence 0.8 --audio-gap 0.5 --end-pause 1.5
```

**合并生成的多个视频**：
```bash
python app.py --words "apple" "banana" "orange" --combine
```

**自定义文件路径**：
```bash
python app.py --word "apple" --image-path "custom_image.png"
```

**跳过特定步骤**：
```bash
python app.py --word "apple" --skip-prompt --skip-image
```

### 完整参数列表

| 参数 | 说明 |
| --- | --- |
| `--word`, `-w` | 单个单词 |
| `--words`, `-ws` | 多个单词（空格分隔） |
| `--words-file`, `-wf` | 包含单词列表的文件路径 |
| `--template`, `-t` | 使用的模板名称 |
| `--skip-prompt` | 跳过提示词生成 |
| `--skip-image` | 跳过图像生成 |
| `--skip-audio` | 跳过音频生成 |
| `--skip-subtitle` | 跳过字幕生成 |
| `--skip-video` | 跳过视频生成 |
| `--lead-silence` | 视频前导静音时长（秒） |
| `--audio-gap` | 各段音频之间的间隔时间（秒） |
| `--end-pause` | 视频结束静置时间（秒） |
| `--combine`, `-c` | 合并生成的多个视频 |
| `--play` | 生成后自动播放视频 |
| `--debug` | 显示详细错误信息 |

## 处理流程

每个单词的处理过程如下：

1. **提示词生成**：通过Azure OpenAI生成适合图片生成的提示词，同时提供单词中英文和短语中英文
2. **图片生成**：使用ComfyUI/Stable Diffusion根据提示词生成图片
3. **音频生成**：为单词和短语的中英文分别生成音频文件（共4个音频）
4. **字幕生成**：根据音频时长自动生成同步的SRT字幕文件
5. **视频生成**：将图片和四个音频轨道合成为视频
6. **添加字幕**：将SRT字幕硬编码到视频中

## 项目结构

```
pictale/
├── app.py                 # 主程序入口
├── config/                # 配置文件目录
│   ├── prompts.json       # 提示词模板
│   ├── settings.yaml      # 全局设置
│   └── workflows/         # ComfyUI工作流
├── modules/               # 功能模块
│   ├── prompt.py          # 提示词生成模块
│   ├── image.py           # 图片生成模块
│   ├── audio.py           # 腾讯云语音合成模块
│   ├── audio_my.py        # 魔音语音合成模块
│   ├── srt.py             # 字幕生成模块
│   ├── video.py           # 视频合成模块
│   ├── config.py          # 配置管理模块
│   └── logger.py          # 日志模块
├── logs/                  # 日志目录
└── output/                # 输出目录
    ├── images/            # 生成的图片
    ├── audio/             # 生成的音频
    └── videos/            # 生成的视频
```

## 配置说明

### 全局配置 (settings.yaml)

```yaml
# Azure OpenAI 配置
azure_openai:
  endpoint: "https://your-endpoint.openai.azure.com/"
  api_key: "your-api-key"
  api_version: "2024-05-01-preview"
  deployment_name: "gpt-4o"
  prompts_file: "config/prompts.json"

# ComfyUI 配置
comfyui:
  api_url: "http://127.0.0.1:8188"
  workflow_file: "config/workflows/prod.json"

# 墨因配置
moyin:
  api_key: "your-api-key"
  api_secret: "your-api-secret"
  api_url: "https://open.mobvoi.com/api/tts/v1"
  speaker_zh: "jupiter_BV064"
  speaker_en: "mercury_jane_24k"
```

## 许可证

MIT License 