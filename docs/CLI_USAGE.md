# Word Video Generator 命令行工具使用说明

这是一个用于为单词生成音视频的命令行工具，可以自动完成提示词生成、图片生成、语音合成、字幕添加和视频剪辑等步骤。

## 基本用法

最基本的使用方式是提供一个单词：

```bash
python app.py --word "example"
```

这将执行完整的生成流程，包括：
1. 调用Azure OpenAI生成提示词
2. 使用ComfyUI生成图片
3. 使用腾讯云语音合成音频
4. 添加字幕到图片
5. 将图片和音频合成为视频

## 命令行参数

### 必要参数

- `--word`, `-w` - 要处理的单词

### 模板选项

- `--template`, `-t` - 使用的模板名称 (默认: "default")

### 跳过特定步骤

- `--skip-prompt` - 跳过提示词生成，直接使用单词或自定义提示词
- `--skip-image` - 跳过图像生成，需要配合 `--image-path` 使用
- `--skip-audio` - 跳过音频生成，需要配合 `--audio-path` 使用
- `--skip-subtitle` - 跳过字幕添加，直接使用原始图像
- `--skip-video` - 跳过视频生成，只执行前面的步骤

### 自定义路径选项

- `--image-path` - 指定使用已有图像文件的路径
- `--audio-path` - 指定使用已有音频文件的路径
- `--custom-prompt` - 提供自定义提示词而不是生成的提示词
- `--output-dir` - 指定输出文件目录

### 其他选项

- `--play` - 生成完成后自动播放视频
- `--debug` - 发生错误时显示详细的错误信息和堆栈跟踪
- `--no-color` - 禁用彩色输出
- `--version` - 显示版本信息并退出

## 使用示例

### 基本用法 - 生成完整视频
```bash
python app.py --word "apple"
```

### 使用特定模板
```bash
python app.py --word "forest" --template "watercolor"
```

### 使用自定义提示词
```bash
python app.py --word "ocean" --skip-prompt --custom-prompt "a beautiful deep blue ocean with waves, realistic style"
```

### 使用已有图像和音频
```bash
python app.py --word "computer" --skip-image --skip-audio --image-path "./my_image.png" --audio-path "./my_audio.mp3"
```

### 只生成图像，不生成视频
```bash
python app.py --word "mountain" --skip-audio --skip-video
```

### 指定输出目录
```bash
python app.py --word "city" --output-dir "./outputs/cities"
```

### 生成后立即播放
```bash
python app.py --word "music" --play
```

## 错误处理

- 如果任何步骤失败，程序将显示错误消息并返回非零退出码
- 使用 `--debug` 参数可以查看详细的错误信息
- 按 Ctrl+C 可以随时中断执行

## 配置

工具的配置在以下文件中管理：

- `config/settings.yaml` - 一般设置，包括API密钥和服务配置
- `config/templates.yaml` - 图片生成和字幕样式模板

## 注意事项

1. 需要有效的Azure OpenAI API密钥用于生成提示词
2. 需要运行中的ComfyUI服务用于图像生成
3. 需要有效的腾讯云API密钥用于语音合成
4. 需要安装Chrome浏览器用于字幕渲染
5. 需要安装FFmpeg用于视频生成 