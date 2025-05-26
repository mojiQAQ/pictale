# ComfyUI 工作流使用说明

本目录包含了预设的ComfyUI工作流配置文件，可以直接被应用程序使用来生成图像。

## 如何从ComfyUI导出工作流

1. 在ComfyUI中创建并调试你的工作流
2. 点击界面右上角的 **Save (💾)** 按钮
3. 选择 "Save (API Format)"，这将导出可直接用于API调用的JSON格式工作流
4. 将导出的JSON文件保存到此目录中

## 工作流文件规范

工作流文件应该包含以下节点：

1. **CLIPTextEncode** 节点：用于处理提示词，程序会自动查找并替换其中的文本内容
2. **KSampler** 节点：用于生成图像，程序会自动替换种子值（如果配置了使用随机种子）
3. **SaveImage** 节点：用于保存图像结果

## 配置文件设置

在 `config/settings.yaml` 中可以配置工作流相关选项：

```yaml
comfyui:
  workflow_file: "config/workflows/default_workflow.json"  # 工作流文件路径
  use_random_seed: true  # 是否每次生成都使用随机种子
  negative_prompt: "低质量, 模糊"  # 负面提示词(会替换工作流中的负面提示节点文本)
```

## 工作流识别逻辑

程序会自动分析工作流中的节点连接，来确定哪些是正向提示词节点、哪些是负向提示词节点：

1. 检查连接到KSampler的"positive"输入的CLIPTextEncode节点作为正向提示词
2. 检查连接到KSampler的"negative"输入的CLIPTextEncode节点作为负向提示词

如果无法通过连接关系判断，会默认将第一个遇到的CLIPTextEncode节点视为正向提示词节点。

## 示例工作流

`default_workflow.json` 提供了一个基础的文生图工作流，可以作为参考或备用选项。

## 注意事项

1. 确保工作流文件中使用的模型（checkpoint）已在你的ComfyUI安装中可用
2. 复杂工作流（如包含ControlNet、LoRA等）也可以正常工作，程序只会替换提示词和种子值
3. 如果工作流文件不存在或加载失败，程序会回退到使用内置的默认工作流 