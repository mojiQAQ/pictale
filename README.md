# Word Video Generator

一个基于Python的单词音视频生成工具，可以将单词转换为包含图片、语音和字幕的视频。

## 功能特点

- 提示词扩写：基于LLM的智能提示词生成
- 图片生成：使用Stable Diffusion生成高质量图片
- 语音合成：集成腾讯云语音合成服务
- 字幕添加：支持HTML样式字幕渲染
- 视频剪辑：使用FFmpeg进行音视频合成

## 环境要求

- Python 3.8+
- FFmpeg
- 腾讯云账号（用于语音合成）
- Stable Diffusion API访问权限

## 安装

1. 克隆项目：
```bash
git clone [repository-url]
cd word-video-generator
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
```
编辑.env文件，填入必要的API密钥和配置信息。

## 使用方法

1. 配置模板：
编辑 `config/templates.yaml` 文件，设置图片生成和字幕样式模板。

2. 运行程序：
```bash
python app.py --word "example"
```

## 项目结构

```
word-video-generator/
├── app.py                 # 主程序入口
├── config/               # 配置文件目录
│   ├── templates.yaml    # 模板配置文件
│   └── settings.yaml     # 全局设置
├── modules/              # 功能模块
│   ├── prompt.py        # 提示词生成模块
│   ├── image.py         # 图片生成模块
│   ├── audio.py         # 语音合成模块
│   ├── subtitle.py      # 字幕处理模块
│   └── video.py         # 视频剪辑模块
├── utils/               # 工具函数
│   ├── html2image.py    # HTML转图片工具
│   └── ffmpeg.py        # FFmpeg工具封装
└── output/              # 输出目录
    ├── images/          # 生成的图片
    ├── audio/           # 生成的音频
    └── videos/          # 生成的视频
```

## 配置说明

### 模板配置 (templates.yaml)

```yaml
image_templates:
  - name: "default"
    style: "realistic"
    prompt_template: "A beautiful illustration of {word}, {style}"

subtitle_templates:
  - name: "default"
    font_family: "Arial"
    font_size: "24px"
    color: "#FFFFFF"
    position: "bottom"
```

### 环境变量配置 (.env)

```
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
SD_API_KEY=your_sd_api_key
```

## 许可证

MIT License 