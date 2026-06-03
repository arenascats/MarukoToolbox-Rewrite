from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompressionSettings:
    encoder_key: str
    preset_name: str
    resolution_name: str
    sharpen_name: str
    custom_width: int
    custom_height: int
    quality_mode: str
    cq_value: int
    bitrate: str
    custom_command: str
    audio_mode: str
    audio_bitrate: str
    muxer_name: str
    output_speed: float
    thumbnail_time: float
    overwrite: bool
    use_lut: bool
    lut_path: str
    extra_ffmpeg_args: str
    hidden_watermark_enabled: bool
    hidden_watermark_mode: str
    hidden_watermark_text: str
    hidden_watermark_image: str


@dataclass(frozen=True)
class EnvironmentInfo:
    ffmpeg: str
    ffprobe: str
    has_nvenc: bool
    has_amf: bool
    has_qsv: bool
    has_videotoolbox: bool = False


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    ok: bool
    elapsed_seconds: float
    size_mb: float
    target: Path


@dataclass(frozen=True)
class CompressionResult:
    source: Path
    target: Path
    ok: bool
    elapsed_seconds: float
    source_size: int
    target_size: int
    started_at: str = ""
    ended_at: str = ""

    @property
    def saved_ratio(self):
        if self.source_size <= 0 or self.target_size <= 0:
            return 0
        return max(0, (1 - self.target_size / self.source_size) * 100)


@dataclass(frozen=True)
class AudioSettings:
    encoder_name: str
    bitrate: str
    sample_rate: str
    channels: str
    overwrite: bool
    normalize: bool
    output_mode: str
    overwrite_source: bool


@dataclass(frozen=True)
class RetroSettings:
    format_name: str
    resolution_name: str
    cq_value: int
    bitrate: str
    audio_bitrate: str
    deinterlace: bool
    denoise: bool
    overwrite: bool
