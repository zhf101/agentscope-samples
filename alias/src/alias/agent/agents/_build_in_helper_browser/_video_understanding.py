# -*- coding: utf-8 -*-
"""
================================================================================
Video Understanding - 视频理解助手
================================================================================

【什么是视频理解助手？】
这是一个帮助 Agent "看懂"视频内容的工具：
- 从视频中提取关键帧
- 提取音频并转录为文字
- 用多模态模型分析视频内容

【视频理解的挑战】
1. 数据量大
   - 视频是连续的图像序列
   - 不能直接传给模型处理

2. 信息多模态
   - 视觉信息（画面）
   - 音频信息（声音、对话）

3. 时序关系
   - 事件有先后顺序
   - 需要理解因果关系

【解决方案】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          视频理解处理流程                                     │
│                                                                              │
│  输入：视频文件                                                              │
│         │                                                                    │
│         ├──────────────────────────────────────────────────────────┐        │
│         │                                                          │        │
│         ▼                                                          ▼        │
│  ┌───────────────────┐                                    ┌───────────────┐  │
│  │ 提取关键帧         │                                    │ 提取音频       │  │
│  │ (extract_frames)  │                                    │ (extract_audio)│  │
│  │                   │                                    │               │  │
│  │ 使用 ffmpeg       │                                    │ 使用 ffmpeg   │  │
│  │ 提取 N 帧图片     │                                    │ 提取 WAV 音频 │  │
│  └─────────┬─────────┘                                    └───────┬───────┘  │
│            │                                                      │         │
│            ▼                                                      ▼         │
│  ┌───────────────────┐                                    ┌───────────────┐  │
│  │ 帧图片列表         │                                    │ 音频转录      │  │
│  │ [frame_0.jpg,     │                                    │ (audio2text)  │  │
│  │  frame_1.jpg,     │                                    │               │  │
│  │  ...]             │                                    │ DashScope ASR │  │
│  └─────────┬─────────┘                                    └───────┬───────┘  │
│            │                                                      │         │
│            └──────────────────┬───────────────────────────────────┘         │
│                               │                                              │
│                               ▼                                              │
│                    ┌───────────────────────┐                                │
│                    │ 构建多模态消息        │                                │
│                    │ - 图片块（关键帧）    │                                │
│                    │ - 文本块（转录文字）  │                                │
│                    │ - 文本块（任务描述）  │                                │
│                    └───────────┬───────────┘                                │
│                                │                                             │
│                                ▼                                             │
│                    ┌───────────────────────┐                                │
│                    │ 多模态模型分析        │                                │
│                    │ (Vision + Text LLM)   │                                │
│                    └───────────┬───────────┘                                │
│                                │                                             │
│                                ▼                                             │
│                         返回分析结果                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【依赖工具】
1. ffmpeg：视频/音频处理命令行工具
   - 提取视频帧
   - 提取音频轨道
   - 视频格式转换

2. DashScope ASR：阿里云语音识别服务
   - 音频转文字
   - 支持中文识别

【学习要点】
1. subprocess 模块（调用外部命令）
2. base64 编码（图片数据传输）
3. 多模态消息构建
4. 错误处理和异常捕获
5. 临时文件管理
"""
# flake8: noqa: E501
# pylint: disable=W0212
# pylint: disable=too-many-lines
# pylint: disable=C0301
from __future__ import annotations

import json
import os
import subprocess  # 调用外部命令（如 ffmpeg）
import tempfile  # 临时文件和目录
import uuid
from base64 import b64encode  # base64 编码
from pathlib import Path  # 路径处理
from typing import Any, List, Optional

from agentscope.message import (
    Base64Source,
    ImageBlock,
    Msg,
    TextBlock,
)
from agentscope.tool import ToolResponse


# ==============================================================================
# 主要入口函数
# ==============================================================================
async def video_understanding(
    browser_agent: Any,
    video_path: str,
    task: str,
) -> ToolResponse:
    """
    视频理解入口函数 - 分析视频内容。

    【工作流程】
    1. 准备工作目录
    2. 提取视频关键帧
    3. 提取音频并转录
    4. 构建多模态消息
    5. 调用模型分析

    Args:
        browser_agent: 主 Agent 实例
        video_path: 视频文件路径
        task: 要执行的任务或问题

    Returns:
        ToolResponse: 包含分析结果的响应
    """
    # 准备工作目录
    workdir = _prepare_workdir(browser_agent)

    # 提取关键帧
    try:
        frames_dir = os.path.join(workdir, "frames")
        frames = extract_frames(video_path, frames_dir)
    except Exception as exc:
        return _error_response(f"Failed to extract frames: {exc}")

    # 提取音频
    audio_path = os.path.join(
        workdir,
        f"audio_{getattr(browser_agent, 'iter_n', 0)}.wav",
    )
    try:
        extract_audio(video_path, audio_path)
    except Exception as exc:
        return _error_response(f"Failed to extract audio: {exc}")

    # 音频转文字
    try:
        transcript = audio2text(audio_path)
    except Exception as exc:
        return _error_response(f"Failed to transcribe audio: {exc}")

    # 构建系统提示
    sys_prompt = (
        "You are a web video analysis expert. "
        "Given the following video frames and audio transcript, "
        "analyze the content and provide a solution to the task. "
        'Return ONLY a JSON object: {"answer": <your answer>}'
    )

    # 构建多模态消息内容
    content_blocks = _build_multimodal_blocks(frames, transcript, task)

    # 格式化消息
    prompt = await browser_agent.formatter.format(
        msgs=[
            Msg("system", sys_prompt, role="system"),
            Msg("user", content_blocks, role="user"),
        ],
    )

    # 调用模型分析
    res = await browser_agent.model(prompt)
    if browser_agent.model.stream:
        async for chunk in res:
            model_text = chunk.content[0]["text"]
    else:
        model_text = res.content[0]["text"]

    # 解析结果
    try:
        if "```json" in model_text:
            model_text = model_text.replace("```json", "").replace(
                "```",
                "",
            )
        answer_info = json.loads(model_text)
        answer = answer_info.get("answer", "")
    except Exception:  # pylint: disable=broad-except
        return _error_response("Failed to parse answer from model output.")

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    "Video analysis completed.\n" f"Task solution: {answer}"
                ),
            ),
        ],
    )


# ==============================================================================
# 音频转文字
# ==============================================================================
def audio2text(audio_path: str) -> str:
    """
    使用 DashScope ASR 将音频转换为文字。

    【DashScope 是什么？】
    阿里云的 AI 服务平台，提供：
    - 语音识别（ASR）
    - 语音合成（TTS）
    - 大语言模型

    【为什么需要语音识别？】
    视频中的对话、旁白包含重要信息，
    通过转录可以：
    - 理解视频内容
    - 提取关键信息
    - 辅助视觉分析

    Args:
        audio_path: 音频文件路径（WAV 格式）

    Returns:
        转录的文字内容
    """
    # 延迟导入，避免未使用时加载依赖
    try:
        from dashscope.audio.asr import Recognition, RecognitionCallback
    except ImportError as exc:
        raise RuntimeError(
            "dashscope.audio is required for audio transcription.",
        ) from exc

    # 创建识别回调
    callback = RecognitionCallback()

    # 创建识别器
    recognizer = Recognition(
        model="paraformer-realtime-v1",  # 实时语音识别模型
        format="wav",  # 音频格式
        sample_rate=16000,  # 采样率
        callback=callback,
    )

    # 调用识别
    result = recognizer.call(audio_path)

    # 提取识别结果
    sentences = result.get("output", {}).get("sentence", [])
    return " ".join(sentence.get("text", "") for sentence in sentences)


# ==============================================================================
# 视频帧提取
# ==============================================================================
def extract_frames(
    video_path: str,
    output_dir: str,
    max_frames: int = 16,
) -> List[str]:
    """
    使用 ffmpeg 从视频中提取关键帧。

    【为什么提取帧而不是处理整个视频？】
    1. 数据量问题
       - 1 分钟视频 = 60 * 30 = 1800 帧
       - 太多帧会超出模型上下文限制

    2. 信息冗余
       - 相邻帧高度相似
       - 关键帧足够表达内容

    【采样策略】
    根据视频时长计算采样率：
    - 短视频：每秒提取更多帧
    - 长视频：降低采样率，保持总帧数限制

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        max_frames: 最大帧数（默认 16）

    Returns:
        帧图片路径列表
    """
    if max_frames <= 0:
        raise ValueError("max_frames must be greater than zero.")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video path not found: {video_path}")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 清理旧帧
    for existing in Path(output_dir).glob("frame_*.jpg"):
        try:
            existing.unlink()
        except OSError:
            pass

    # 获取视频时长
    duration = _probe_video_duration(video_path)

    # 计算采样帧率
    if duration and duration > 0:
        fps = max_frames / duration
    else:
        fps = 1.0

    # 限制帧率范围
    fps = max(min(fps, 30.0), 0.1)

    # 构建 ffmpeg 命令
    # ffmpeg 参数说明：
    # -y: 覆盖输出文件
    # -i: 输入文件
    # -vf fps=X: 视频滤镜，按帧率采样
    # -frames:v N: 最多提取 N 帧
    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"fps={fps:.5f}",
        "-frames:v",
        str(max_frames),
        os.path.join(output_dir, "frame_%04d.jpg"),  # 输出文件名模式
    ]

    # 执行命令
    try:
        subprocess.run(
            command,
            check=True,  # 检查返回码
            stdout=subprocess.DEVNULL,  # 丢弃标准输出
            stderr=subprocess.DEVNULL,  # 丢弃标准错误
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg is required to extract frames from video.",
        ) from exc

    # 收集生成的帧文件
    frame_files = sorted(
        str(path) for path in Path(output_dir).glob("frame_*.jpg")
    )

    if not frame_files:
        raise RuntimeError("No frames could be extracted from the video.")

    return frame_files


# ==============================================================================
# 音频提取
# ==============================================================================
def extract_audio(video_path: str, audio_path: str) -> str:
    """
    使用 ffmpeg 从视频中提取音频轨道。

    【音频参数说明】
    - pcm_s16le: 16 位 PCM 编码（无损）
    - -ar 16000: 采样率 16kHz（语音识别常用）
    - -ac 1: 单声道（语音识别常用）

    Args:
        video_path: 视频文件路径
        audio_path: 输出音频路径

    Returns:
        音频文件路径
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video path not found: {video_path}")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    # 构建 ffmpeg 命令
    # 参数说明：
    # -vn: 不处理视频
    # -acodec pcm_s16le: 音频编码格式
    # -ar 16000: 采样率
    # -ac 1: 声道数
    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",  # no video
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path,
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg is required to extract audio from video.",
        ) from exc

    return audio_path


# ==============================================================================
# 视频信息探测
# ==============================================================================
def _probe_video_duration(video_path: str) -> Optional[float]:
    """
    使用 ffprobe 获取视频时长。

    【ffprobe vs ffmpeg】
    - ffmpeg: 媒体处理工具（转换、提取）
    - ffprobe: 媒体信息工具（查询元数据）

    Args:
        video_path: 视频文件路径

    Returns:
        视频时长（秒），失败返回 None
    """
    # 构建命令
    # -v error: 只显示错误
    # -show_entries format=duration: 只显示时长
    # -of default=noprint_wrappers=1:nokey=1: 只输出值
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.DEVNULL,
            text=True,  # 返回字符串而非字节
        )
        duration_str = result.stdout.strip()
        if duration_str:
            return float(duration_str)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError):
        return None

    return None


# ==============================================================================
# 辅助函数
# ==============================================================================
def _build_multimodal_blocks(
    frames: List[str],
    transcript: str,
    task: str,
) -> list:
    """
    构建多模态消息内容块。

    【消息结构】
    1. 图片块（多个关键帧）
    2. 文本块（音频转录）
    3. 文本块（任务描述）

    Args:
        frames: 帧图片路径列表
        transcript: 音频转录文字
        task: 任务描述

    Returns:
        内容块列表
    """
    blocks: list = []

    # 添加图片块
    for frame_path in frames:
        # 读取图片并编码为 base64
        with open(frame_path, "rb") as file:
            data = b64encode(file.read()).decode("ascii")

        # 创建图片块
        image_block = ImageBlock(
            type="image",
            source=Base64Source(
                type="base64",
                media_type="image/jpeg",
                data=data,
            ),
        )
        blocks.append(image_block)

    # 添加转录文本块
    blocks.append(
        TextBlock(
            type="text",
            text=f"Audio transcript:\n{transcript}",
        ),
    )

    # 添加任务描述块
    blocks.append(
        TextBlock(
            type="text",
            text=f"The task to be solved is: {task}",
        ),
    )

    return blocks


def _prepare_workdir(browser_agent: Any) -> str:
    """
    准备工作目录。

    【目录用途】
    存放处理过程中的临时文件：
    - 提取的帧图片
    - 提取的音频文件

    Args:
        browser_agent: 主 Agent 实例（获取保存目录）

    Returns:
        工作目录路径
    """
    # 获取基础目录
    base_dir = getattr(browser_agent, "state_saving_dir", None)
    if not base_dir:
        # 使用系统临时目录
        base_dir = tempfile.gettempdir()

    # 创建唯一工作目录
    workdir = os.path.join(base_dir, "video_understanding", uuid.uuid4().hex)
    os.makedirs(workdir, exist_ok=True)

    return workdir


def _error_response(message: str) -> ToolResponse:
    """
    创建标准化错误响应。

    Args:
        message: 错误消息

    Returns:
        包含错误信息的 ToolResponse
    """
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=message,
            ),
        ],
        metadata={"success": False},
    )