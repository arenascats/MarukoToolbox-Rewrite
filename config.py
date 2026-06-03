import platform
from pathlib import Path


APP_TITLE = "小丸工具箱粉丝致敬版"
WINDOW_SIZE = "1320x820"

BUILD_VERSION = "1.1.1"
WINDOW_MIN_SIZE = (1120, 700)
APP_DIR = Path(__file__).resolve().parent


def _platform_default_output_dir():
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        return Path("D:/maru-output")
    if system == "Darwin":
        movies_dir = home / "Movies"
        return (movies_dir if movies_dir.exists() else home) / "maru-output"
    videos_dir = home / "Videos"
    return (videos_dir if videos_dir.exists() else home) / "maru-output"


DEFAULT_OUTPUT_DIR = _platform_default_output_dir()
DEFAULT_PREVIEW_PATH = DEFAULT_OUTPUT_DIR / "_lut_preview.png"

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".ts",
    ".mts",
    ".m2ts",
    ".rm",
    ".rmvb",
    ".vob",
    ".mpg",
    ".mpeg",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".m4a",
    ".ogg",
    ".opus",
    ".wma",
    ".aiff",
    ".alac",
}

ENCODERS = {
    "GPU H.265 / HEVC (hevc_nvenc)": "hevc_nvenc",
    "GPU H.265 10-bit / HEVC Main10": "hevc_nvenc_10bit",
    "GPU H.264 / AVC (h264_nvenc)": "h264_nvenc",
    "GPU AV1 (av1_nvenc, RTX 40+)": "av1_nvenc",
    "GPU AV1 10-bit (av1_nvenc, RTX 40+)": "av1_nvenc_10bit",
    "AMD H.265 / HEVC (hevc_amf, RDNA2/RDNA3)": "hevc_amf",
    "AMD H.264 / AVC (h264_amf, RDNA2/RDNA3)": "h264_amf",
    "AMD AV1 (av1_amf, RDNA3)": "av1_amf",
    "Intel H.265 / HEVC (hevc_qsv)": "hevc_qsv",
    "Intel H.265 10-bit / HEVC Main10": "hevc_qsv_10bit",
    "Intel H.264 / AVC (h264_qsv)": "h264_qsv",
    "Intel AV1 (av1_qsv, Arc+)": "av1_qsv",
    "Apple H.265 / HEVC (hevc_videotoolbox)": "hevc_videotoolbox",
    "Apple H.264 / AVC (h264_videotoolbox)": "h264_videotoolbox",
    "CPU H.265 / HEVC (libx265)": "libx265",
    "CPU H.265 10-bit / HEVC Main10": "libx265_10bit",
    "CPU H.264 / AVC (libx264)": "libx264",
    "CPU AV1 (libsvtav1)": "libsvtav1",
    "CPU VP9 (libvpx-vp9)": "libvpx-vp9",
    "Apple ProRes 422 HQ (prores_ks)": "prores_ks",
}

COMMON_ENCODERS = [
    "GPU H.265 / HEVC (hevc_nvenc)",
    "AMD H.265 / HEVC (hevc_amf, RDNA2/RDNA3)",
    "Intel H.265 / HEVC (hevc_qsv)",
    "Apple H.265 / HEVC (hevc_videotoolbox)",
    "GPU H.264 / AVC (h264_nvenc)",
    "AMD H.264 / AVC (h264_amf, RDNA2/RDNA3)",
    "Intel H.264 / AVC (h264_qsv)",
    "Apple H.264 / AVC (h264_videotoolbox)",
    "CPU H.264 / AVC (libx264)",
]

ENCODER_FILENAME_TAGS = {
    "hevc_nvenc": "h265",
    "hevc_nvenc_10bit": "h265_10bit",
    "h264_nvenc": "h264",
    "av1_nvenc": "av1",
    "av1_nvenc_10bit": "av1_10bit",
    "hevc_amf": "amd_h265",
    "h264_amf": "amd_h264",
    "av1_amf": "amd_av1",
    "hevc_qsv": "intel_h265",
    "hevc_qsv_10bit": "intel_h265_10bit",
    "h264_qsv": "intel_h264",
    "av1_qsv": "intel_av1",
    "hevc_videotoolbox": "apple_h265",
    "h264_videotoolbox": "apple_h264",
    "libx265": "h265",
    "libx265_10bit": "h265_10bit",
    "libx264": "h264",
    "libsvtav1": "av1",
    "libvpx-vp9": "vp9",
    "prores_ks": "prores",
}

PRESETS = {
    "极速": ("p1", "ultrafast"),
    "高速": ("p3", "veryfast"),
    "均衡": ("p5", "medium"),
    "高画质": ("p7", "slow"),
}

QUALITY_MODES = {
    "CRF / 恒定质量": "crf",
    "2PASS / 两遍码率": "2pass",
    "自定义命令": "custom",
}

RESOLUTIONS = {
    "保持原分辨率": "",
    "2160p / 4K": "3840:-2",
    "1440p / 2K": "2560:-2",
    "1080p": "1920:-2",
    "720p": "1280:-2",
    "竖屏 4K 2160x3840": "2160:3840",
    "竖屏 1440x2560": "1440:2560",
    "竖屏 1080x1920": "1080:1920",
    "竖屏 720x1280": "720:1280",
    "自定义宽高": "custom",
}

SHARPEN_LEVELS = {
    "关闭": "",
    "轻度": "unsharp=5:5:0.6:3:3:0.0",
    "中度": "unsharp=5:5:1.0:3:3:0.0",
    "强力": "unsharp=7:7:1.4:5:5:0.0",
}

VIDEO_MUXERS = {
    "MP4 (.mp4)": ".mp4",
    "MKV (.mkv)": ".mkv",
    "MOV (.mov)": ".mov",
    "WebM (.webm)": ".webm",
    "TS (.ts)": ".ts",
    "保持源容器": "source",
}

AUDIO_MODES = {
    "复制音频流": "copy",
    "AAC 重新编码": "aac",
    "Opus 重新编码": "libopus",
    "MP3 重新编码": "libmp3lame",
    "FLAC 无损编码": "flac",
    "移除音频": "none",
}

AUDIO_ENCODERS = {
    "AAC (.m4a)": ("aac", ".m4a"),
    "MP3 (.mp3)": ("libmp3lame", ".mp3"),
    "Opus (.opus)": ("libopus", ".opus"),
    "FLAC (.flac)": ("flac", ".flac"),
    "WAV PCM (.wav)": ("pcm_s16le", ".wav"),
}

AUDIO_BITRATE_PRESETS = {
    "AAC (.m4a)": ["96k", "128k", "160k", "192k", "256k", "320k"],
    "MP3 (.mp3)": ["128k", "192k", "256k", "320k"],
    "Opus (.opus)": ["64k", "96k", "128k", "160k", "192k"],
    "FLAC (.flac)": ["无损"],
    "WAV PCM (.wav)": ["无损"],
}

BATCH_PRESETS = {
    "高质量归档 H.265 4K": {
        "encoder": "GPU H.265 / HEVC (hevc_nvenc)",
        "resolution": "2160p / 4K",
        "cq": 22,
        "audio": "AAC 重新编码",
        "audio_bitrate": "192k",
        "muxer": "MP4 (.mp4)",
    },
    "高质量归档 H.265 2K": {
        "encoder": "GPU H.265 / HEVC (hevc_nvenc)",
        "resolution": "1440p / 2K",
        "cq": 23,
        "audio": "AAC 重新编码",
        "audio_bitrate": "192k",
        "muxer": "MP4 (.mp4)",
    },
    "网盘归档 H.265 1080p": {
        "encoder": "GPU H.265 / HEVC (hevc_nvenc)",
        "resolution": "1080p",
        "cq": 24,
        "audio": "AAC 重新编码",
        "audio_bitrate": "160k",
        "muxer": "MP4 (.mp4)",
    },
    "极速体积压缩 H.265 720p": {
        "encoder": "GPU H.265 / HEVC (hevc_nvenc)",
        "resolution": "720p",
        "cq": 27,
        "audio": "AAC 重新编码",
        "audio_bitrate": "128k",
        "muxer": "MP4 (.mp4)",
    },
    "高兼容 H.264 1080p": {
        "encoder": "GPU H.264 / AVC (h264_nvenc)",
        "resolution": "1080p",
        "cq": 23,
        "audio": "AAC 重新编码",
        "audio_bitrate": "192k",
        "muxer": "MP4 (.mp4)",
    },
}

VIDEO_FILETYPES = [
    ("视频文件", "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm *.m4v *.ts *.mts *.m2ts *.rm *.rmvb *.vob *.mpg *.mpeg"),
    ("所有文件", "*.*"),
]

RETRO_FORMATS = {
    "AVI - MPEG4 + MP3 (.avi)": {
        "suffix": ".avi",
        "video": ["-c:v", "mpeg4", "-q:v", "5"],
        "audio": ["-c:a", "libmp3lame", "-b:a", "128k"],
        "tag": "avi",
    },
    "AVI - MJPEG + PCM (.avi)": {
        "suffix": ".avi",
        "video": ["-c:v", "mjpeg", "-q:v", "4"],
        "audio": ["-c:a", "pcm_s16le"],
        "tag": "avi_mjpeg",
    },
    "WMV - WMV2 + WMA (.wmv)": {
        "suffix": ".wmv",
        "video": ["-c:v", "wmv2", "-b:v", "1200k"],
        "audio": ["-c:a", "wmav2", "-b:a", "128k"],
        "tag": "wmv",
    },
    "ASF - WMV2 + WMA (.asf)": {
        "suffix": ".asf",
        "video": ["-c:v", "wmv2", "-b:v", "1000k"],
        "audio": ["-c:a", "wmav2", "-b:a", "96k"],
        "tag": "asf",
    },
    "RM - RealVideo 1.0 (.rm)": {
        "suffix": ".rm",
        "video": ["-c:v", "rv10", "-b:v", "700k"],
        "audio": ["-c:a", "ac3", "-b:a", "96k"],
        "tag": "rm",
    },
    "MPG - MPEG1 Video (.mpg)": {
        "suffix": ".mpg",
        "video": ["-c:v", "mpeg1video", "-b:v", "1150k"],
        "audio": ["-c:a", "mp2", "-b:a", "128k"],
        "tag": "mpg",
    },
    "FLV - H.263 + MP3 (.flv)": {
        "suffix": ".flv",
        "video": ["-c:v", "flv", "-b:v", "700k"],
        "audio": ["-c:a", "libmp3lame", "-b:a", "96k"],
        "tag": "flv",
    },
    "WMA - 仅导出音频 (.wma)": {
        "suffix": ".wma",
        "video": ["-vn"],
        "audio": ["-c:a", "wmav2", "-b:a", "128k"],
        "tag": "wma",
    },
}

RETRO_RESOLUTIONS = {
    "保持原分辨率": "",
    "VCD 352x288": "352:288",
    "QVGA 320x240": "320:240",
    "VGA 640x480": "640:480",
    "DVD 720x576": "720:576",
}

AUDIO_FILETYPES = [
    ("音频文件", "*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff *.alac"),
    ("所有文件", "*.*"),
]

LUT_FILETYPES = [
    ("LUT 文件", "*.cube *.3dl *.dat *.m3d"),
    ("所有文件", "*.*"),
]
