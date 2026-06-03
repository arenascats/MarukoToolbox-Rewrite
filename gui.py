import os
import csv
import queue
import traceback
import subprocess
import threading
import time
import ctypes
import re
import json
import shlex
import shutil
import platform
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tkinter import (
    BooleanVar,
    Canvas,
    DoubleVar,
    END,
    HORIZONTAL,
    IntVar,
    Listbox,
    PhotoImage,
    StringVar,
    Text,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
    simpledialog,
    ttk,
)

import ffmpeg_utils as ffmpeg
from config import (
    APP_DIR,
    APP_TITLE,
    BUILD_VERSION,
    AUDIO_ENCODERS,
    AUDIO_BITRATE_PRESETS,
    AUDIO_EXTENSIONS,
    AUDIO_FILETYPES,
    AUDIO_MODES,
    BATCH_PRESETS,
    COMMON_ENCODERS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREVIEW_PATH,
    ENCODERS,
    ENCODER_FILENAME_TAGS,
    LUT_FILETYPES,
    PRESETS,
    QUALITY_MODES,
    RETRO_FORMATS,
    RETRO_RESOLUTIONS,
    RESOLUTIONS,
    SHARPEN_LEVELS,
    VIDEO_MUXERS,
    VIDEO_EXTENSIONS,
    VIDEO_FILETYPES,
    WINDOW_MIN_SIZE,
    WINDOW_SIZE,
)
from data import AudioSettings, CompressionResult, CompressionSettings, RetroSettings


class VideoCompressorApp:
    LIGHT_COLORS = {
        "bg": "#eef1f5",
        "surface": "#ffffff",
        "surface_alt": "#f7f9fc",
        "panel": "#ffffff",
        "panel_border": "#cfd6df",
        "text": "#1f2937",
        "muted": "#657283",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_pressed": "#1e40af",
        "button": "#f8fafc",
        "button_hover": "#e8eef7",
        "button_pressed": "#dbe4f0",
        "list_bg": "#ffffff",
        "list_fg": "#1f2937",
        "list_select": "#2f6fed",
        "sparkline_cpu_label": "#166534",
        "sparkline_gpu_label": "#15803d",
        "sparkline_cpu_line": "#16a34a",
        "sparkline_gpu_line": "#22c55e",
        "sparkline_bg": "#f8fafc",
        "sparkline_border": "#d1d5db",
        "entry_bg": "#ffffff",
        "progress_trough": "#dbe3ee",
        "notebook_tab_bg": "#e2e8f0",
        "notebook_tab_hover": "#f1f5f9",
        "tree_heading_bg": "#e9eef5",
        "scrollbar_bg": "#d8e0eb",
    }

    DARK_COLORS = {
        "bg": "#0f172a",
        "surface": "#111827",
        "surface_alt": "#1e293b",
        "panel": "#1f2937",
        "panel_border": "#334155",
        "text": "#e5e7eb",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "accent_hover": "#0ea5e9",
        "accent_pressed": "#0284c7",
        "button": "#273449",
        "button_hover": "#334155",
        "button_pressed": "#3b4a61",
        "list_bg": "#172235",
        "list_fg": "#e5e7eb",
        "list_select": "#0ea5e9",
        "sparkline_cpu_label": "#86efac",
        "sparkline_gpu_label": "#6ee7b7",
        "sparkline_cpu_line": "#4ade80",
        "sparkline_gpu_line": "#2dd4bf",
        "sparkline_bg": "#0b1220",
        "sparkline_border": "#334155",
        "entry_bg": "#0b1220",
        "progress_trough": "#1e293b",
        "notebook_tab_bg": "#233146",
        "notebook_tab_hover": "#2e3f59",
        "tree_heading_bg": "#263449",
        "scrollbar_bg": "#2b3d55",
    }

    MOJIBAKE_TEXT_MAP = {
        "涓枃": "中文",
        "姝ｅ父": "正常",
        "浼樺厛 GPU": "优先 GPU",
        "鑷畾涔?": "自定义",
        "鑷畾涔": "自定义",
        "楂橀€?": "高速",
        "楂橀€": "高速",
        "淇濇寔鍘熷垎杈ㄧ巼": "保持原分辨率",
        "鍏抽棴": "关闭",
        "CRF / 鎭掑畾璐ㄩ噺": "CRF / 恒定质量",
        "澶嶅埗闊抽娴?": "复制音频流",
        "澶嶅埗闊抽娴": "复制音频流",
        "閲嶅懡鍚?": "重命名",
        "閲嶅懡鍚": "重命名",
        "淇濈暀鍙嶆尋鍘嬪鐢诲箙": "保留反挤压宽画幅",
        "淇濇寔鍙嶆尋鍘嬪昂瀵?": "保持反挤压尺寸",
        "淇濇寔鍙嶆尋鍘嬪昂瀵": "保持反挤压尺寸",
        "澶嶅埗闊抽": "复制音频",
        "缃戠洏褰掓。 H.265 1080p": "网盘归档 H.265 1080p",
        "瑙嗛": "视频",
        "鍙樺舰": "反挤压",
        "灏佽": "封装",
        "瀛楀箷": "字幕",
        "闊抽": "音频",
        "甯哥敤": "常用",
        "澶嶅彜": "复古",
        "Lut璋冭壊": "Lut调色",
        "鎵归噺鍘嬬缉": "批量压缩",
        "浠诲姟绠＄悊": "任务管理",
        "AAC 閲嶆柊缂栫爜": "AAC 重新编码",
        "Opus 閲嶆柊缂栫爜": "Opus 重新编码",
        "MP3 閲嶆柊缂栫爜": "MP3 重新编码",
        "FLAC 鏃犳崯缂栫爜": "FLAC 无损编码",
        "绉婚櫎闊抽": "移除音频",
        "楂樿川閲忓綊妗?H.265 4K": "高质量归档 H.265 4K",
        "楂樿川閲忓綊妗?H.265 2K": "高质量归档 H.265 2K",
        "鏋侀€熶綋绉帇缂?H.265 720p": "极速体积压缩 H.265 720p",
        "楂樺吋瀹?H.264 1080p": "高兼容 H.264 1080p",
        "鏃犳崯": "无损",
        "WMA - 浠呭鍑洪煶棰?(.wma)": "WMA - 仅导出音频 (.wma)",
    }

    def __init__(self, root):
        self.COLORS = dict(self.LIGHT_COLORS)
        self.root = root
        self.base_dir = APP_DIR
        self.app_version = f"v{BUILD_VERSION}"
        self.display_title = f"{APP_TITLE}    {self.app_version}"
        self.root.title(self.display_title)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.icon_bitmap_path = self.base_dir / "gzya5-3b5gl-001.ico"
        self.icon_image_path = self.base_dir / "logo.png"
        self.window_icon_image = None
        self._set_window_icon(self.root)

        self.files = []
        self.common_trim_video = StringVar(value="")
        self.subtitle_source = StringVar(value="")
        self.subtitle_output_dir = StringVar(value=str(DEFAULT_OUTPUT_DIR / "subtitles"))
        self.subtitle_output_format = StringVar(value="MKV (.mkv)")
        self.subtitle_tracks = []
        self.subtitle_external_files = []
        self.audio_files = []
        self.retro_files = []
        self.anamorphic_files = []
        self.mux_merge_files = []
        self.mux_convert_files = []
        self.task_counter = 0
        self.active_workers = {}
        self.active_ffmpeg_jobs = {}
        self.cancelled_ffmpeg_jobs = set()
        self.job_windows = {}
        self.multi_job_mode = False
        self.multi_job_total = 0
        self.multi_job_finished = 0
        self.queued_tasks = {}
        self.worker = None
        self.stop_requested = False
        self.messages = queue.Queue()

        self.encoder_name = StringVar(value=self._initial_video_encoder_name())
        self.advanced_encoders = BooleanVar(value=False)
        self.preferred_device = StringVar(value="优先 GPU")
        self.auto_open_output = BooleanVar(value=False)
        self.shutdown_when_finished = BooleanVar(value=False)
        self.play_finish_sound = BooleanVar(value=True)
        self.restore_last_page_on_startup = BooleanVar(value=True)
        self.enable_drag_drop = BooleanVar(value=True)
        self.confirm_overwrite = BooleanVar(value=True)
        self.confirm_export_settings = BooleanVar(value=False)
        self.interface_size = StringVar(value="小")
        self.preset_name = StringVar(value="高速")
        self.resolution_name = StringVar(value="保持原分辨率")
        self.sharpen_name = StringVar(value="关闭")
        self.custom_width = IntVar(value=1920)
        self.custom_height = IntVar(value=1080)
        self.resolution_name.trace_add("write", lambda *_: self._sync_custom_size_state())
        self.quality_mode = StringVar(value="CRF / 恒定质量")
        self.cq_value = IntVar(value=23)
        self.bitrate = StringVar(value="")
        self.custom_command = StringVar(value='-y -i "{input}" -c:v libx264 -crf 23 -c:a copy "{output}"')
        self.audio_mode = StringVar(value="复制音频流")
        self.audio_bitrate = StringVar(value="160k")
        self.muxer_name = StringVar(value="MP4 (.mp4)")
        self.output_speed = DoubleVar(value=1.0)
        self.create_thumbnail = BooleanVar(value=True)
        self.thumbnail_only_selected = BooleanVar(value=False)
        self.thumbnail_time = DoubleVar(value=1.0)
        self.parallel_jobs = IntVar(value=2)
        self.extra_ffmpeg_args = StringVar(value="")
        self.use_lut = BooleanVar(value=False)
        self.lut_path = StringVar(value="")
        self.hidden_watermark_enabled = BooleanVar(value=False)
        self.hidden_watermark_mode = StringVar(value="text")
        self.hidden_watermark_text = StringVar(value="")
        self.hidden_watermark_image = StringVar(value="")
        self.output_dir = StringVar(value=str(self._default_output_dir()))
        self.audio_output_dir = StringVar(value=str(self._default_output_dir("audio")))
        self.audio_output_mode = StringVar(value="自定义")
        self.audio_overwrite_source = BooleanVar(value=False)
        self.audio_encoder_name = StringVar(value="AAC (.m4a)")
        self.audio_page_bitrate = StringVar(value="192k")
        self.audio_sample_rate = StringVar(value="48000")
        self.audio_channels = StringVar(value="2")
        self.audio_normalize = BooleanVar(value=False)
        self.common_output_dir = StringVar(value=str(self._default_output_dir("common")))
        self.common_trim_start = StringVar(value="00:00:00")
        self.common_trim_end = StringVar(value="00:00:10")
        self.common_trim_encoder = StringVar(value="CPU H.264 / AVC (libx264)")
        self.common_trim_muxer = StringVar(value="MP4 (.mp4)")
        self.common_channel_copy_mode = StringVar(value="左复制到右")
        self.anamorphic_output_dir = StringVar(value=str(self._default_output_dir("anamorphic")))
        self.anamorphic_factor = StringVar(value="1.33")
        self.anamorphic_mode = StringVar(value="保留反挤压宽画幅")
        self.anamorphic_target_aspect = StringVar(value="2.39:1")
        self.anamorphic_resolution = StringVar(value="保持反挤压尺寸")
        self.anamorphic_encoder_name = StringVar(value="CPU H.264 / AVC (libx264)")
        self.anamorphic_keep_audio = BooleanVar(value=True)
        self.anamorphic_auto_crop = BooleanVar(value=False)
        self.mux_output_dir = StringVar(value=str(self._default_output_dir("mux")))
        self.mux_merge_name = StringVar(value="merged")
        self.mux_merge_format = StringVar(value="MP4 (.mp4)")
        self.mux_convert_format = StringVar(value="MP4 (.mp4)")
        self.mux_audio_mode = StringVar(value="复制音频")
        self.mux_audio_bitrate = StringVar(value="192k")
        self.batch_input_dir = StringVar(value="")
        self.batch_output_dir = StringVar(value=str(self._default_output_dir("batch")))
        self.batch_preset_name = StringVar(value="网盘归档 H.265 1080p")
        self.batch_keep_tree = BooleanVar(value=True)
        self.batch_include_audio = BooleanVar(value=True)
        self.batch_vertical_mode = BooleanVar(value=False)
        self.queue_parallel_jobs = IntVar(value=1)
        self.retro_output_dir = StringVar(value=str(self._default_output_dir("retro")))
        self.retro_format_name = StringVar(value="AVI - MPEG4 + MP3 (.avi)")
        self.retro_resolution_name = StringVar(value="VCD 352x288")
        self.retro_bitrate = StringVar(value="900k")
        self.retro_audio_bitrate = StringVar(value="128k")
        self.retro_deinterlace = BooleanVar(value=True)
        self.retro_denoise = BooleanVar(value=True)
        self.retro_remux_format = StringVar(value="MP4 (.mp4)")
        self.retro_remux_audio = StringVar(value="复制音频")
        self.overwrite = BooleanVar(value=False)
        self.file_conflict_action = StringVar(value="重命名")
        self.auto_fallback_cpu_h264 = BooleanVar(value=True)
        self.progress = DoubleVar(value=0)
        self.current_task = StringVar(value="待命中")
        self.resource_status = StringVar(value="CPU --%  |  GPU --%")
        self._last_cpu_times = None
        self._last_gpu_usage = None
        self._gpu_poll_running = False
        self._scrollregion_jobs = {}
        self._scrollregion_cache = {}
        self._scrollable_canvases = []
        self._restore_video_defaults_prompt_open = False
        self.cpu_history = []
        self.gpu_history = []
        self.preview_image = None
        self.preview_path = DEFAULT_PREVIEW_PATH
        self.preview_window = None
        self.preview_source_path = None
        self.preview_seconds = DoubleVar(value=0.0)
        self.preview_duration = 0.0
        self.preview_playing = False
        self.preview_after_id = None
        self.screenshot_dir = StringVar(value=str(self._default_output_dir("screenshots")))
        self.preview_frame_path = DEFAULT_OUTPUT_DIR / "_player_preview.png"
        self.anamorphic_preview_image = None
        self.anamorphic_preview_window = None
        self.anamorphic_preview_label = None
        self.lut_page_video = StringVar(value="")
        self.lut_page_folder = StringVar(value="")
        self.lut_page_output = StringVar(value=str(self._default_output_dir("lut_previews")))
        self.lut_page_time = DoubleVar(value=1.0)
        self.lut_preview_images = {}
        self.lut_thumb_images = {}
        self.lut_tooltip_after = None
        self.lut_tooltip = None
        self.media_info_path = StringVar(value="")
        self.avs_video_path = StringVar(value="")
        self.avs_subtitle_path = StringVar(value="")
        self.avs_output_path = StringVar(value=str(self._default_output_dir("avs")))
        self.avs_enable_addborders = BooleanVar(value=False)
        self.avs_border_left = IntVar(value=0)
        self.avs_border_top = IntVar(value=0)
        self.avs_border_right = IntVar(value=0)
        self.avs_border_bottom = IntVar(value=0)
        self.avs_enable_crop = BooleanVar(value=False)
        self.avs_crop_left = IntVar(value=0)
        self.avs_crop_top = IntVar(value=0)
        self.avs_crop_right = IntVar(value=0)
        self.avs_crop_bottom = IntVar(value=0)
        self.avs_enable_trim = BooleanVar(value=False)
        self.avs_trim_start = IntVar(value=0)
        self.avs_trim_end = IntVar(value=1440)
        self.avs_enable_brightness = BooleanVar(value=False)
        self.avs_brightness = IntVar(value=0)
        self.avs_enable_sharpen = BooleanVar(value=False)
        self.avs_sharpen_amount = DoubleVar(value=0.2)
        self.avs_enable_denoise = BooleanVar(value=False)
        self.avs_denoise_strength = IntVar(value=4)
        self._avs_script_refresh_job = None
        self._avs_script_updating = False
        self._avs_script_user_edited = False
        for var in (
            self.avs_video_path,
            self.avs_subtitle_path,
            self.avs_output_path,
            self.avs_enable_addborders,
            self.avs_border_left,
            self.avs_border_top,
            self.avs_border_right,
            self.avs_border_bottom,
            self.avs_enable_crop,
            self.avs_crop_left,
            self.avs_crop_top,
            self.avs_crop_right,
            self.avs_crop_bottom,
            self.avs_enable_trim,
            self.avs_trim_start,
            self.avs_trim_end,
            self.avs_enable_brightness,
            self.avs_brightness,
            self.avs_enable_sharpen,
            self.avs_sharpen_amount,
            self.avs_enable_denoise,
            self.avs_denoise_strength,
        ):
            try:
                var.trace_add("write", self._schedule_avs_script_refresh)
            except Exception:
                pass
        self.media_compare_path_a = StringVar(value="")
        self.media_compare_path_b = StringVar(value="")
        self.media_compare_frame_time = DoubleVar(value=1.0)
        self.media_compare_generate_frames_on_export = BooleanVar(value=True)
        self.media_compare_rows = []
        self.media_compare_window = None
        self.media_compare_popup_tree = None
        self.media_compare_show_diff_only = BooleanVar(value=False)
        self.theme_mode = StringVar(value="日间模式")
        self.interface_language = StringVar(value="中文")
        self.tray_mode = BooleanVar(value=True)
        self.x264_priority = StringVar(value="正常")
        self.x264_threads = IntVar(value=0)
        self.x264_command = StringVar(value="")
        self.default_player = StringVar(value="")
        self.export_filename_format = StringVar(value="原名_标签")
        self.default_output_root = self._default_output_dir()
        self.settings_path = self._app_settings_path()
        self.user_video_presets = []
        self.export_record_context = None
        self.tab_order = ["视频", "音频", "常用", "字幕", "AVS", "反挤压", "封装", "复古", "Lut调色", "批量压缩", "MediaInfo", "任务管理"]
        self.first_run_guide_completed = False
        self._guide_blink_jobs = []
        self._header_button_refs = {}
        self._guide_window = None
        self._guide_steps = []
        self._guide_step_index = 0
        self._guide_status_labels = []
        self._guide_step_title_var = StringVar(value="")
        self._guide_step_text_var = StringVar(value="")
        self._guide_progress_var = StringVar(value="")
        self._guide_action_flags = {
            "checked_env": False,
            "pressed_start": False,
            "opened_github": False,
        }
        self.runtime_environment = None
        self.detected_gpu_names = []
        self.detected_has_nvidia = False
        self.detected_has_amd = False
        self.detected_has_intel = False

        self._detect_runtime_hardware()
        self._configure_style()
        self._build_ui()
        self._bind_keys()
        self._bind_delete_shortcuts()
        self._setup_drag_drop()
        self._restore_default_window_settings_on_startup = self._ask_restore_default_window_settings_on_startup()
        self._load_app_settings()
        self._ensure_output_dirs_valid(show_message=True)
        self._apply_theme(self.theme_mode.get(), persist=False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_main_close)
        self._poll_messages()
        self._poll_resources()
        self.root.after(900, self._maybe_start_first_run_guide)

    def _ui_metrics(self):
        size = self.interface_size.get() if hasattr(self, "interface_size") else "小"
        metrics = {
            "小": {"font": 10, "small_font": 9, "title_font": 18, "button_pad": (12, 7), "accent_pad": (14, 8), "entry_pad": (8, 5), "tab_pad": (18, 9), "tree_rowheight": 30},
            "中": {"font": 11, "small_font": 10, "title_font": 20, "button_pad": (14, 8), "accent_pad": (16, 9), "entry_pad": (9, 6), "tab_pad": (20, 10), "tree_rowheight": 34},
            "大": {"font": 12, "small_font": 11, "title_font": 22, "button_pad": (16, 10), "accent_pad": (18, 11), "entry_pad": (10, 7), "tab_pad": (22, 12), "tree_rowheight": 38},
        }
        return metrics.get(size, metrics["小"])

    def _configure_style(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        colors = self.COLORS
        metrics = self._ui_metrics()
        self.root.configure(bg=colors["bg"])
        self.root.option_add("*Font", ("Microsoft YaHei UI", metrics["font"]))
        self.root.option_add("*Listbox.Font", ("Microsoft YaHei UI", metrics["font"]))
        self.root.option_add("*TCombobox*Listbox.Font", ("Microsoft YaHei UI", metrics["font"]))
        self.root.option_add("*TCombobox*Listbox.background", colors["entry_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", colors["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", colors["list_select"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        style.configure(".", font=("Microsoft YaHei UI", 10), background=colors["bg"], foreground=colors["text"])
        style.configure("TFrame", background=colors["bg"])
        style.configure("Surface.TFrame", background=colors["surface"])
        style.configure("Header.TFrame", background=colors["surface"])
        style.configure("TLabel", background=colors["panel"], foreground=colors["text"])
        style.configure("Surface.TLabel", background=colors["surface"], foreground=colors["text"])
        style.configure("Title.TLabel", background=colors["surface"], foreground=colors["text"], font=("Microsoft YaHei UI", metrics["title_font"], "bold"))
        style.configure("Hint.TLabel", background=colors["bg"], foreground=colors["muted"], font=("Microsoft YaHei UI", metrics["small_font"]))
        style.configure("HeaderHint.TLabel", background=colors["surface"], foreground=colors["muted"], font=("Microsoft YaHei UI", metrics["small_font"]))
        style.configure("Status.TLabel", background=colors["surface"], foreground=colors["accent"], font=("Microsoft YaHei UI", metrics["font"], "bold"))

        style.configure(
            "TLabelframe",
            background=colors["panel"],
            bordercolor=colors["panel_border"],
            lightcolor=colors["panel_border"],
            darkcolor=colors["panel_border"],
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "TLabelframe.Label",
            background=colors["panel"],
            foreground=colors["text"],
            font=("Microsoft YaHei UI", metrics["font"], "bold"),
        )

        style.configure(
            "TButton",
            background=colors["button"],
            foreground=colors["text"],
            bordercolor=colors["panel_border"],
            lightcolor=colors["button"],
            darkcolor=colors["panel_border"],
            borderwidth=1,
            focusthickness=0,
            focuscolor=colors["button"],
            padding=metrics["button_pad"],
            relief="solid",
        )
        style.map(
            "TButton",
            background=[("active", colors["button_hover"]), ("pressed", colors["button_pressed"])],
            bordercolor=[("active", "#aeb9c8"), ("pressed", "#93a4b8")],
        )
        style.configure(
            "Accent.TButton",
            background=colors["accent"],
            foreground="#ffffff",
            bordercolor=colors["accent"],
            borderwidth=1,
            focuscolor=colors["accent"],
            font=("Microsoft YaHei UI", metrics["font"], "bold"),
            padding=metrics["accent_pad"],
        )
        style.map(
            "Accent.TButton",
            background=[("active", colors["accent_hover"]), ("pressed", colors["accent_pressed"])],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )
        style.configure(
            "OutputDir.TButton",
            background=colors["surface_alt"],
            foreground=colors["accent"],
            bordercolor=colors["accent"],
            lightcolor=colors["surface_alt"],
            darkcolor=colors["accent"],
            borderwidth=1,
            focuscolor=colors["surface_alt"],
            padding=metrics["button_pad"],
            relief="solid",
        )
        style.map(
            "OutputDir.TButton",
            background=[("active", colors["button_hover"]), ("pressed", colors["button_pressed"])],
            bordercolor=[("active", colors["accent_hover"]), ("pressed", colors["accent_pressed"])],
            foreground=[("active", colors["accent"]), ("pressed", colors["accent"])],
        )

        style.configure("TEntry", fieldbackground=colors["entry_bg"], bordercolor=colors["panel_border"], padding=metrics["entry_pad"], relief="flat")
        style.map("TEntry", bordercolor=[("focus", colors["accent"])])
        style.configure(
            "TCombobox",
            fieldbackground=colors["entry_bg"],
            background=colors["entry_bg"],
            foreground=colors["text"],
            bordercolor=colors["panel_border"],
            arrowcolor=colors["muted"],
            padding=metrics["entry_pad"],
        )
        style.map(
            "TCombobox",
            bordercolor=[("focus", colors["accent"]), ("readonly", colors["panel_border"])],
            fieldbackground=[
                ("readonly", colors["entry_bg"]),
                ("readonly", "!focus", colors["entry_bg"]),
                ("readonly", "focus", colors["entry_bg"]),
                ("active", colors["entry_bg"]),
            ],
            background=[
                ("readonly", colors["entry_bg"]),
                ("readonly", "!focus", colors["entry_bg"]),
                ("readonly", "focus", colors["entry_bg"]),
                ("active", colors["entry_bg"]),
            ],
            foreground=[
                ("readonly", colors["text"]),
                ("readonly", "!focus", colors["text"]),
                ("readonly", "focus", colors["text"]),
                ("active", colors["text"]),
            ],
            selectforeground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["entry_bg"])],
            arrowcolor=[("readonly", colors["muted"]), ("active", colors["text"])],
        )
        style.configure("TSpinbox", fieldbackground=colors["entry_bg"], bordercolor=colors["panel_border"], padding=metrics["entry_pad"])
        for option_style in ("TCheckbutton", "TRadiobutton"):
            style.configure(
                option_style,
                background=colors["panel"],
                foreground=colors["text"],
                focuscolor=colors["panel"],
            )
            style.map(
                option_style,
                background=[
                    ("active", colors["button_hover"]),
                    ("pressed", colors["button_pressed"]),
                    ("selected", colors["panel"]),
                ],
                foreground=[
                    ("active", colors["text"]),
                    ("pressed", colors["text"]),
                    ("selected", colors["text"]),
                    ("disabled", colors["muted"]),
                ],
            )
        style.configure("Horizontal.TScale", background=colors["panel"], troughcolor=colors["progress_trough"], sliderthickness=16)
        style.configure("Horizontal.TProgressbar", troughcolor=colors["progress_trough"], background=colors["accent"], bordercolor=colors["bg"], lightcolor=colors["accent"], darkcolor=colors["accent"])

        style.configure("TNotebook", background=colors["bg"], borderwidth=0, tabmargins=(0, 6, 0, 0))
        style.configure("TNotebook.Tab", background=colors["notebook_tab_bg"], foreground=colors["muted"], padding=metrics["tab_pad"], font=("Microsoft YaHei UI", metrics["font"], "bold"))
        style.map("TNotebook.Tab", background=[("selected", colors["surface"]), ("active", colors["notebook_tab_hover"])], foreground=[("selected", colors["text"]), ("active", colors["text"])])

        style.configure("Treeview", background=colors["entry_bg"], fieldbackground=colors["entry_bg"], foreground=colors["text"], rowheight=metrics["tree_rowheight"], bordercolor=colors["panel_border"])
        style.configure("Treeview.Heading", background=colors["tree_heading_bg"], foreground=colors["text"], font=("Microsoft YaHei UI", metrics["font"], "bold"), padding=metrics["entry_pad"])
        style.map("Treeview", background=[("selected", colors["list_select"])], foreground=[("selected", "#ffffff")])
        style.configure("Vertical.TScrollbar", background=colors["scrollbar_bg"], troughcolor=colors["bg"], arrowcolor=colors["muted"], bordercolor=colors["panel_border"])

        style.configure(
            "GuideGlow.TButton",
            background=colors["accent_hover"],
            foreground="#ffffff",
            bordercolor=colors["accent_hover"],
            lightcolor=colors["accent_hover"],
            darkcolor=colors["accent_hover"],
            borderwidth=1,
            focuscolor=colors["accent_hover"],
            font=("Microsoft YaHei UI", metrics["font"], "bold"),
            padding=metrics["accent_pad"],
        )
        style.map(
            "GuideGlow.TButton",
            background=[("active", colors["accent"]), ("pressed", colors["accent_pressed"])],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        style.configure(
            "GuideGlow.TCombobox",
            fieldbackground=colors["entry_bg"],
            background=colors["entry_bg"],
            foreground=colors["text"],
            bordercolor=colors["accent"],
            arrowcolor=colors["accent"],
            padding=metrics["entry_pad"],
        )
        style.map(
            "GuideGlow.TCombobox",
            bordercolor=[("focus", colors["accent_hover"]), ("readonly", colors["accent"])],
            fieldbackground=[("readonly", colors["entry_bg"])],
            background=[("readonly", colors["entry_bg"])],
            foreground=[("readonly", colors["text"])],
            selectforeground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["entry_bg"])],
            arrowcolor=[("readonly", colors["accent"])],
        )

    def _is_macos(self):
        return platform.system() == "Darwin"

    def _command_creationflags(self):
        return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def _guide_enabled(self):
        return not self._is_macos()

    def _initial_video_encoder_name(self):
        if self._is_macos():
            return "Apple H.265 / HEVC (hevc_videotoolbox)"
        return "GPU H.265 / HEVC (hevc_nvenc)"

    def _hardware_encoder_candidates(self):
        candidates = []
        info = self.runtime_environment
        if self._is_macos():
            if info is None or info.has_videotoolbox:
                candidates.extend([
                    "Apple H.265 / HEVC (hevc_videotoolbox)",
                    "Apple H.264 / AVC (h264_videotoolbox)",
                ])
        if info is None or info.has_nvenc:
            candidates.extend([
                "GPU H.265 / HEVC (hevc_nvenc)",
                "GPU H.264 / AVC (h264_nvenc)",
            ])
        if info is None or info.has_amf:
            candidates.extend([
                "AMD H.265 / HEVC (hevc_amf, RDNA2/RDNA3)",
                "AMD H.264 / AVC (h264_amf, RDNA2/RDNA3)",
            ])
        if info is None or info.has_qsv:
            candidates.extend([
                "Intel H.265 / HEVC (hevc_qsv)",
                "Intel H.264 / AVC (h264_qsv)",
            ])
        return [name for name in candidates if name in ENCODERS]

    def _preferred_video_encoder_name(self, prefer_gpu=True):
        if not prefer_gpu:
            return "CPU H.264 / AVC (libx264)"
        visible = set(self._encoder_choices()) if hasattr(self, "advanced_encoders") else set()
        for candidate in self._hardware_encoder_candidates():
            if not visible or candidate in visible:
                return candidate
        return "CPU H.264 / AVC (libx264)"

    def _resolve_platform_encoder(self, encoder_name):
        if encoder_name in ENCODERS and self._encoder_visible(encoder_name):
            return encoder_name
        return self._preferred_video_encoder_name(prefer_gpu=True)

    def _set_window_icon(self, window):
        if self.icon_image_path.exists():
            try:
                self.window_icon_image = PhotoImage(file=str(self.icon_image_path))
                window.iconphoto(True, self.window_icon_image)
                return
            except Exception:
                self.window_icon_image = None
        if self.icon_bitmap_path.exists():
            try:
                window.iconbitmap(str(self.icon_bitmap_path))
            except Exception:
                pass

    def _set_window_geometry(self, window, geometry, center=True):
        if center:
            window.withdraw()
            window.geometry(geometry)
            window.update_idletasks()
            self._center_window_on_parent(window)
            window.deiconify()
        else:
            window.geometry(geometry)

    def _center_window_on_parent(self, window, parent=None):
        parent = parent or self.root
        if not window.winfo_exists():
            return
        try:
            parent.update_idletasks()
            window.update_idletasks()
            width = max(window.winfo_width(), window.winfo_reqwidth())
            height = max(window.winfo_height(), window.winfo_reqheight())
            parent_width = max(parent.winfo_width(), 1)
            parent_height = max(parent.winfo_height(), 1)
            x = parent.winfo_rootx() + (parent_width - width) // 2
            y = parent.winfo_rooty() + (parent_height - height) // 2
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = max(0, min(x, screen_width - width))
            y = max(0, min(y, screen_height - height))
            window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def _theme_palette(self, mode):
        return self.DARK_COLORS if mode == "黑暗模式" else self.LIGHT_COLORS

    def _apply_theme(self, mode, persist=True):
        normalized = "黑暗模式" if mode == "黑暗模式" else "日间模式"
        self.theme_mode.set(normalized)
        self.COLORS = dict(self._theme_palette(normalized))
        self._configure_style()
        self._refresh_theme_widgets()
        self._draw_theme_switch()
        self._draw_resource_chart()
        if persist:
            self._save_app_settings()

    def _toggle_theme(self, _event=None):
        target = "黑暗模式" if self.theme_mode.get() == "日间模式" else "日间模式"
        self._apply_theme(target, persist=True)

    def _refresh_theme_widgets(self):
        colors = self.COLORS
        self.root.configure(bg=colors["bg"])
        self._refresh_widget_tree_theme(self.root)

    def _refresh_widget_tree_theme(self, widget):
        metrics = self._ui_metrics()
        for child in widget.winfo_children():
            self._refresh_widget_tree_theme(child)
        klass = widget.winfo_class()
        if klass == "Canvas":
            bg = self.COLORS["bg"]
            if widget in {getattr(self, "resource_canvas", None), getattr(self, "lut_result_canvas", None)}:
                bg = self.COLORS["surface_alt"]
            if widget is getattr(self, "theme_switch_canvas", None):
                bg = self.COLORS["surface"]
            try:
                widget.configure(bg=bg, highlightbackground=self.COLORS["panel_border"], highlightcolor=self.COLORS["accent"])
            except Exception:
                pass
        elif klass == "Listbox":
            try:
                widget.configure(
                    background=self.COLORS["list_bg"],
                    foreground=self.COLORS["list_fg"],
                    selectbackground=self.COLORS["list_select"],
                    selectforeground="#ffffff",
                    highlightbackground=self.COLORS["panel_border"],
                    highlightcolor=self.COLORS["accent"],
                    font=("Microsoft YaHei UI", metrics["font"]),
                )
            except Exception:
                pass
        elif klass == "Text":
            try:
                widget.configure(background=self.COLORS["entry_bg"], foreground=self.COLORS["text"], insertbackground=self.COLORS["text"])
            except Exception:
                pass

    def _draw_theme_switch(self):
        canvas = getattr(self, "theme_switch_canvas", None)
        if not canvas:
            return
        colors = self.COLORS
        is_dark = self.theme_mode.get() == "黑暗模式"
        canvas.configure(bg=colors["surface"])
        canvas.delete("all")
        x0, y0, x1, y1 = 2, 4, 66, 28
        radius = (y1 - y0) // 2
        fill = colors["accent"] if is_dark else colors["button"]
        knob_fill = "#f8fafc" if is_dark else "#ffffff"
        label_color = "#ffffff" if is_dark else colors["muted"]

        canvas.create_oval(x0, y0, x0 + radius * 2, y1, outline=fill, fill=fill)
        canvas.create_rectangle(x0 + radius, y0, x1 - radius, y1, outline=fill, fill=fill)
        canvas.create_oval(x1 - radius * 2, y0, x1, y1, outline=fill, fill=fill)
        knob_x = x1 - radius * 2 if is_dark else x0
        canvas.create_oval(knob_x, y0, knob_x + radius * 2, y1, outline="#94a3b8", fill=knob_fill)
        canvas.create_text((x0 + x1) // 2, 16, text="夜" if is_dark else "日", fill=label_color, font=("Microsoft YaHei UI", 9, "bold"))

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=0)

        self._build_header(main)
        self._build_tabs(main)
        self._build_bottom_panel(main)

    def _build_header(self, parent):
        header = ttk.Frame(parent, style="Header.TFrame", padding=(16, 12))
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, minsize=260)
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="FFmpeg + NVIDIA NVENC / AMD AMF 批量压缩、CPU 对比和缩略图生成",
            style="HeaderHint.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        header_actions = ttk.Frame(header, style="Header.TFrame")
        header_actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for column in range(7):
            header_actions.columnconfigure(column, weight=1)
        header_buttons = [
            ("settings", "⚙ 设置", self.open_settings_window, ""),
            ("start", "▶ 开始压缩", self.start_compression, "Accent.TButton"),
            ("queue", "＋ 视频任务入队", self.add_current_video_to_queue, ""),
            ("stop", "■ 停止", self.stop, ""),
            ("check_env", "✓ 检测环境", self.check_environment, ""),
            ("github", "GitHub Issues", self.open_github_project, ""),
        ]
        if self._guide_enabled():
            header_buttons.insert(1, ("guide", "新手向导", self.start_first_run_guide, ""))
        for column, (button_id, text, command, style) in enumerate(header_buttons):
            options = {"text": text, "command": command}
            if style:
                options["style"] = style
            button = ttk.Button(header_actions, **options)
            button.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))
            self._header_button_refs[button_id] = button

        resource = ttk.Frame(header, style="Header.TFrame")
        resource.grid(row=0, column=1, rowspan=3, sticky="nse", padx=(18, 0))
        resource.columnconfigure(0, weight=1)
        switch_wrap = ttk.Frame(resource, style="Header.TFrame")
        switch_wrap.grid(row=0, column=0, sticky="e")
        self.theme_switch_canvas = Canvas(switch_wrap, width=68, height=32, bg=self.COLORS["surface"], highlightthickness=0, bd=0)
        self.theme_switch_canvas.pack(side="right")
        self.theme_switch_canvas.bind("<Button-1>", self._toggle_theme)
        ttk.Label(resource, textvariable=self.resource_status, style="Status.TLabel").grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.resource_canvas = Canvas(resource, width=240, height=46, bg=self.COLORS["surface_alt"], highlightthickness=1, highlightbackground=self.COLORS["panel_border"])
        self.resource_canvas.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._draw_theme_switch()

    def _build_tabs(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)
        self.common_tab = ttk.Frame(self.notebook, padding=0)
        self.video_tab = ttk.Frame(self.notebook, padding=0)
        self.subtitle_tab = ttk.Frame(self.notebook, padding=0)
        self.avs_tab = ttk.Frame(self.notebook, padding=0)
        self.anamorphic_tab = ttk.Frame(self.notebook, padding=0)
        self.mux_tab = ttk.Frame(self.notebook, padding=0)
        self.audio_tab = ttk.Frame(self.notebook, padding=0)
        self.retro_tab = ttk.Frame(self.notebook, padding=0)
        self.lut_tab = ttk.Frame(self.notebook, padding=0)
        self.batch_tab = ttk.Frame(self.notebook, padding=0)
        self.mediainfo_tab = ttk.Frame(self.notebook, padding=0)
        self.tasks_tab = ttk.Frame(self.notebook, padding=0)
        self.tab_frames = {
            "视频": self.video_tab,
            "字幕": self.subtitle_tab,
            "反挤压": self.anamorphic_tab,
            "封装": self.mux_tab,
            "音频": self.audio_tab,
            "常用": self.common_tab,
            "复古": self.retro_tab,
            "Lut调色": self.lut_tab,
            "批量压缩": self.batch_tab,
            "MediaInfo": self.mediainfo_tab,
            "任务管理": self.tasks_tab,
            "AVS": self.avs_tab,
        }
        self._apply_tab_order()
        self._build_common_tab(self.common_tab)
        self._build_video_tab(self.video_tab)
        self._build_subtitle_tab(self.subtitle_tab)
        self._build_avs_tab(self.avs_tab)
        self._build_anamorphic_tab(self.anamorphic_tab)
        self._build_mux_tab(self.mux_tab)
        self._build_audio_tab(self.audio_tab)
        self._build_retro_tab(self.retro_tab)
        self._build_lut_tab(self.lut_tab)
        self._build_batch_tab(self.batch_tab)
        self._build_mediainfo_tab(self.mediainfo_tab)
        self._build_tasks_tab(self.tasks_tab)

    def _apply_tab_order(self):
        if not hasattr(self, "notebook") or not hasattr(self, "tab_frames"):
            return
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        for name in self.tab_order:
            frame = self.tab_frames.get(name)
            if frame is not None:
                self.notebook.add(frame, text=name)

    def _on_notebook_tab_changed(self, _event=None):
        self.root.after(16, self._refresh_visible_scrollregions)

    def _refresh_visible_scrollregions(self):
        current = self.notebook.select() if hasattr(self, "notebook") else ""
        if not current:
            return
        try:
            current_widget = self.root.nametowidget(current)
        except Exception:
            return
        for canvas in list(self._scrollable_canvases):
            if not canvas.winfo_exists():
                self._scrollable_canvases.remove(canvas)
                continue
            parent = canvas.master
            while parent is not None and parent is not current_widget:
                parent = parent.master
            if parent is current_widget:
                self._schedule_scrollregion_update(canvas)

    def _build_video_tab(self, parent):
        panel = self._scrollable_frame(parent)
        panel.columnconfigure(0, weight=3)
        panel.columnconfigure(1, weight=2)
        panel.rowconfigure(0, weight=1)
        self._build_video_file_panel(panel)
        self._build_settings_panel(panel)

    def _build_common_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=1)
        trim = ttk.LabelFrame(parent, text="截取视频", padding=12)
        trim.grid(row=0, column=0, sticky="ew")
        trim.columnconfigure(1, weight=1)
        ttk.Label(trim, text="视频文件").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(trim, textvariable=self.common_trim_video).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(trim, text="选择…", command=self.choose_common_trim_video).grid(row=0, column=2, pady=5)
        ttk.Button(trim, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.common_output_dir)).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(trim, textvariable=self.common_output_dir).grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(trim, text="浏览…", command=self.choose_common_output_dir).grid(row=1, column=2, pady=5)
        time_row = ttk.Frame(trim)
        time_row.grid(row=2, column=1, sticky="ew", padx=8, pady=5)
        time_row.columnconfigure((0, 2), weight=1)
        ttk.Label(trim, text="截取时间").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(time_row, textvariable=self.common_trim_start).grid(row=0, column=0, sticky="ew")
        ttk.Label(time_row, text="到").grid(row=0, column=1, padx=8)
        ttk.Entry(time_row, textvariable=self.common_trim_end).grid(row=0, column=2, sticky="ew")
        ttk.Label(trim, text="编码器").grid(row=3, column=0, sticky="w", pady=5)
        self.common_trim_encoder_combo = ttk.Combobox(trim, textvariable=self.common_trim_encoder, values=self._filtered_encoder_list(list(COMMON_ENCODERS)), state="readonly")
        self.common_trim_encoder_combo.grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Label(trim, text="输出容器").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Combobox(trim, textvariable=self.common_trim_muxer, values=[name for name in VIDEO_MUXERS if VIDEO_MUXERS[name] != "source"], state="readonly").grid(row=4, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Button(trim, text="▶ 开始截取", style="Accent.TButton", command=self.start_common_trim).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(trim, text="时间可输入 00:01:23、01:23 或秒数；会按选择的编码器和容器重新输出片段。", style="Hint.TLabel").grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 0))

        tools = ttk.LabelFrame(parent, text="音视频工具", padding=12)
        tools.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        tools.columnconfigure(1, weight=1)
        ttk.Label(tools, text="声道复制").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(tools, textvariable=self.common_channel_copy_mode, values=["左复制到右", "右复制到左"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        action_row = ttk.Frame(tools)
        action_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        action_row.columnconfigure((0, 1), weight=1)
        ttk.Button(action_row, text="分离音视频", command=self.start_common_demux).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(action_row, text="复制左右声道", command=self.start_common_channel_copy).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Label(tools, text="使用上方“视频文件”和“输出目录”；支持从视频提取音频或复制单侧声道。", style="Hint.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_video_file_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="任务列表", padding=12)
        panel.grid(row=0, column=0, sticky="new", padx=(0, 10))
        panel.rowconfigure(2, weight=0)
        panel.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(panel)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.video_add_button = ttk.Button(toolbar, text="＋ 添加视频", command=self.add_files)
        self.video_add_button.pack(side="left")
        ttk.Button(toolbar, text="▤ 添加文件夹", command=self.add_folder).pack(side="left", padx=6)
        ttk.Button(toolbar, text="▶ 预览", command=self.open_player_preview).pack(side="left")
        ttk.Button(toolbar, text="− 移除", command=self.remove_selected).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="清空", command=self.clear_files).pack(side="left", padx=6)

        output = ttk.Frame(panel)
        output.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        output.columnconfigure(1, weight=1)
        self.video_output_dir_button = ttk.Button(output, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.output_dir))
        self.video_output_dir_button.grid(row=0, column=0, sticky="w")
        ttk.Entry(output, textvariable=self.output_dir).grid(row=0, column=1, sticky="ew", padx=8)
        self.video_output_browse_button = ttk.Button(output, text="浏览…", command=self.choose_output_dir)
        self.video_output_browse_button.grid(row=0, column=2)

        list_frame = ttk.Frame(panel)
        list_frame.grid(row=2, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=0)
        list_frame.columnconfigure(0, weight=1)
        self.file_list = self._create_work_listbox(list_frame, selectmode="extended", height=self._video_task_list_height())
        self.file_list.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

    def _video_task_list_height(self):
        try:
            screen_height = self.root.winfo_screenheight()
        except Exception:
            screen_height = 1080
        if screen_height <= 1200:
            return 7
        if screen_height <= 1800:
            return 9
        return 11

    def _build_subtitle_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        tracks_box = ttk.LabelFrame(parent, text="媒体轨道", padding=12)
        tracks_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tracks_box.rowconfigure(2, weight=1)
        tracks_box.columnconfigure(1, weight=1)
        ttk.Label(tracks_box, text="视频文件").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(tracks_box, textvariable=self.subtitle_source).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(tracks_box, text="选择…", command=self.choose_subtitle_source).grid(row=0, column=2, pady=5)
        track_actions = ttk.Frame(tracks_box)
        track_actions.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 8))
        ttk.Button(track_actions, text="保留/取消选中轨道", command=self.toggle_selected_subtitle_track).pack(side="left")
        ttk.Button(track_actions, text="导出选中字幕", command=self.start_subtitle_export).pack(side="left", padx=8)
        columns = ("keep", "type", "index", "codec", "lang", "title")
        self.subtitle_track_tree = ttk.Treeview(tracks_box, columns=columns, show="headings", height=12)
        for key, text, width in [
            ("keep", "保留", 70),
            ("type", "类型", 70),
            ("index", "流", 60),
            ("codec", "编码", 110),
            ("lang", "语言", 80),
            ("title", "标题", 220),
        ]:
            self.subtitle_track_tree.heading(key, text=text)
            self.subtitle_track_tree.column(key, width=width, stretch=True)
        self.subtitle_track_tree.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.subtitle_track_tree.bind("<Double-1>", lambda event: self.toggle_selected_subtitle_track())
        track_scroll = ttk.Scrollbar(tracks_box, orient="vertical", command=self.subtitle_track_tree.yview)
        track_scroll.grid(row=2, column=3, sticky="ns")
        self.subtitle_track_tree.configure(yscrollcommand=track_scroll.set)

        ops = ttk.LabelFrame(parent, text="字幕操作", padding=12)
        ops.grid(row=0, column=1, sticky="nsew")
        ops.rowconfigure(4, weight=1)
        ops.columnconfigure(1, weight=1)
        ttk.Button(ops, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.subtitle_output_dir)).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(ops, textvariable=self.subtitle_output_dir).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(ops, text="浏览…", command=self.choose_subtitle_output_dir).grid(row=0, column=2, pady=5)
        ttk.Label(ops, text="输出格式").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(ops, textvariable=self.subtitle_output_format, values=[name for name in VIDEO_MUXERS if VIDEO_MUXERS[name] != "source"], state="readonly").grid(row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        sub_actions = ttk.Frame(ops)
        sub_actions.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 8))
        ttk.Button(sub_actions, text="＋ 导入字幕", command=self.import_subtitle_files).pack(side="left")
        ttk.Button(sub_actions, text="− 移除导入", command=self.remove_selected_external_subtitle).pack(side="left", padx=8)
        self.external_subtitle_list = self._create_work_listbox(ops, selectmode="extended", height=7)
        self.external_subtitle_list.grid(row=3, column=0, columnspan=3, sticky="nsew")
        ttk.Button(ops, text="▶ 保存为新视频文件", style="Accent.TButton", command=self.start_subtitle_mux).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(ops, text="双击轨道可决定是否保留；导入的字幕会放进新视频文件里。", style="Hint.TLabel").grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 0))

    def _build_avs_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=1)

        source_box = ttk.LabelFrame(parent, text="AVS 输入输出", padding=12)
        source_box.grid(row=0, column=0, sticky="ew")
        source_box.columnconfigure(1, weight=1)
        ttk.Button(source_box, text="视频", style="OutputDir.TButton", command=lambda: self.choose_avs_video()).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(source_box, textvariable=self.avs_video_path).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(source_box, text="浏览…", command=self.choose_avs_video).grid(row=0, column=2, pady=5)
        ttk.Button(source_box, text="字幕", style="OutputDir.TButton", command=lambda: self.choose_avs_subtitle()).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(source_box, textvariable=self.avs_subtitle_path).grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(source_box, text="浏览…", command=self.choose_avs_subtitle).grid(row=1, column=2, pady=5)
        ttk.Button(source_box, text="输出", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.avs_output_path)).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(source_box, textvariable=self.avs_output_path).grid(row=2, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(source_box, text="浏览…", command=self.choose_avs_output).grid(row=2, column=2, pady=5)

        feature_box = ttk.LabelFrame(parent, text="AVS 功能", padding=12)
        feature_box.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        feature_box.columnconfigure(1, weight=1)

        border_row = ttk.Frame(feature_box)
        border_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(border_row, text="加黑边", variable=self.avs_enable_addborders).pack(side="left")
        self._build_avs_number_pair(border_row, "左", self.avs_border_left)
        self._build_avs_number_pair(border_row, "上", self.avs_border_top)
        self._build_avs_number_pair(border_row, "右", self.avs_border_right)
        self._build_avs_number_pair(border_row, "下", self.avs_border_bottom)

        crop_row = ttk.Frame(feature_box)
        crop_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(crop_row, text="裁剪", variable=self.avs_enable_crop).pack(side="left")
        self._build_avs_number_pair(crop_row, "左", self.avs_crop_left)
        self._build_avs_number_pair(crop_row, "上", self.avs_crop_top)
        self._build_avs_number_pair(crop_row, "右", self.avs_crop_right)
        self._build_avs_number_pair(crop_row, "下", self.avs_crop_bottom)

        trim_row = ttk.Frame(feature_box)
        trim_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(trim_row, text="截取", variable=self.avs_enable_trim).pack(side="left")
        ttk.Label(trim_row, text="起始帧").pack(side="left", padx=(10, 4))
        ttk.Spinbox(trim_row, from_=0, to=999999, increment=1, width=8, textvariable=self.avs_trim_start).pack(side="left")
        ttk.Label(trim_row, text="结束帧").pack(side="left", padx=(10, 4))
        ttk.Spinbox(trim_row, from_=0, to=999999, increment=1, width=8, textvariable=self.avs_trim_end).pack(side="left")

        tone_row = ttk.Frame(feature_box)
        tone_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(tone_row, text="亮度", variable=self.avs_enable_brightness).pack(side="left")
        ttk.Label(tone_row, text="值").pack(side="left", padx=(10, 4))
        ttk.Spinbox(tone_row, from_=-255, to=255, increment=1, width=8, textvariable=self.avs_brightness).pack(side="left")
        ttk.Label(tone_row, text="(Tweak bright)").pack(side="left", padx=(6, 0))

        sharpen_row = ttk.Frame(feature_box)
        sharpen_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(sharpen_row, text="锐化", variable=self.avs_enable_sharpen).pack(side="left")
        ttk.Label(sharpen_row, text="强度").pack(side="left", padx=(10, 4))
        ttk.Spinbox(sharpen_row, from_=0.0, to=2.0, increment=0.05, width=8, textvariable=self.avs_sharpen_amount).pack(side="left")
        ttk.Label(sharpen_row, text="(Sharpen)").pack(side="left", padx=(6, 0))

        denoise_row = ttk.Frame(feature_box)
        denoise_row.grid(row=5, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(denoise_row, text="降噪", variable=self.avs_enable_denoise).pack(side="left")
        ttk.Label(denoise_row, text="强度").pack(side="left", padx=(10, 4))
        ttk.Spinbox(denoise_row, from_=1, to=20, increment=1, width=8, textvariable=self.avs_denoise_strength).pack(side="left")
        ttk.Label(denoise_row, text="(TemporalSoften)").pack(side="left", padx=(6, 0))
        ttk.Label(feature_box, text="黑边和裁剪按像素填写；截取按帧号填写。", style="Hint.TLabel").grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))

        preview_box = ttk.LabelFrame(parent, text="AVS 脚本预览", padding=12)
        preview_box.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        preview_box.columnconfigure(0, weight=1)
        preview_box.rowconfigure(0, weight=1)
        self.avs_script_text = Text(
            preview_box,
            wrap="none",
            height=18,
            background=self.COLORS["entry_bg"],
            foreground=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief="solid",
            borderwidth=1,
            font=("Microsoft YaHei UI", 10),
            padx=10,
            pady=8,
        )
        self.avs_script_text.grid(row=0, column=0, sticky="nsew")
        self.avs_script_text.bind("<<Modified>>", self._on_avs_script_modified)
        avs_scroll = ttk.Scrollbar(preview_box, orient="vertical", command=self.avs_script_text.yview)
        avs_scroll.grid(row=0, column=1, sticky="ns")
        avs_xscroll = ttk.Scrollbar(preview_box, orient="horizontal", command=self.avs_script_text.xview)
        avs_xscroll.grid(row=1, column=0, sticky="ew")
        self.avs_script_text.configure(yscrollcommand=avs_scroll.set, xscrollcommand=avs_xscroll.set)

        actions = ttk.Frame(parent)
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        actions.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(actions, text="生成脚本", style="Accent.TButton", command=self.generate_avs_script).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="保存为 .avs", command=self.save_avs_script).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(actions, text="复制脚本", command=self.copy_avs_script).grid(row=0, column=2, sticky="ew", padx=6)
        ttk.Button(actions, text="清空", command=self.clear_avs_script).grid(row=0, column=3, sticky="ew", padx=(6, 0))
        ttk.Label(parent, text="这里生成的是可编辑的 AVS 模板，方便你再接后续滤镜或交给别的处理流程。", style="Hint.TLabel").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.generate_avs_script()

    def _build_avs_number_pair(self, parent, label, variable):
        ttk.Label(parent, text=label).pack(side="left", padx=(10, 4))
        ttk.Spinbox(parent, from_=0, to=999999, increment=1, width=7, textvariable=variable).pack(side="left")

    def _build_settings_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="压缩设置", padding=12)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(1, weight=1)
        self.settings_panel = panel

        row = self._add_preset_controls(panel, 0)
        row = self._add_encoder_controls(panel, row)
        row = self._add_lut_controls(panel, row)
        row = self._add_hidden_watermark_controls(panel, row)
        row = self._add_thumbnail_controls(panel, row)

    def _rebuild_settings_panel(self):
        if not hasattr(self, "settings_panel"):
            return
        for child in self.settings_panel.winfo_children():
            child.destroy()
        row = self._add_preset_controls(self.settings_panel, 0)
        row = self._add_encoder_controls(self.settings_panel, row)
        row = self._add_lut_controls(self.settings_panel, row)
        row = self._add_hidden_watermark_controls(self.settings_panel, row)
        self._add_thumbnail_controls(self.settings_panel, row)

    def _add_preset_controls(self, panel, row):
        preset_box = ttk.LabelFrame(panel, text="预设管理", padding=(10, 8))
        preset_box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        preset_box.columnconfigure((0, 1), weight=1)
        ttk.Button(preset_box, text="保存预设", command=self.save_video_settings).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(preset_box, text="加载预设", command=self.load_video_preset).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        return row + 1

    def _build_retro_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        files = ttk.LabelFrame(parent, text="古老素材任务", padding=12)
        files.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        files.rowconfigure(1, weight=1)
        files.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(files)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="＋ 添加素材", command=self.add_retro_files).pack(side="left")
        ttk.Button(toolbar, text="▤ 添加文件夹", command=self.add_retro_folder).pack(side="left", padx=6)
        ttk.Button(toolbar, text="− 移除", command=self.remove_selected_retro).pack(side="left")
        ttk.Button(toolbar, text="清空", command=self.clear_retro_files).pack(side="left", padx=6)
        list_frame = ttk.Frame(files)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.retro_file_list = self._create_work_listbox(list_frame, selectmode="extended")
        self.retro_file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.retro_file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.retro_file_list.configure(yscrollcommand=scrollbar.set)
        output = ttk.Frame(files)
        output.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        output.columnconfigure(1, weight=1)
        ttk.Button(output, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.retro_output_dir)).grid(row=0, column=0, sticky="w")
        ttk.Entry(output, textvariable=self.retro_output_dir).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(output, text="浏览…", command=self.choose_retro_output_dir).grid(row=0, column=2)

        settings = ttk.LabelFrame(parent, text="复古输出设置", padding=12)
        settings.grid(row=0, column=1, sticky="nsew")
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="输出格式").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.retro_format_name, values=list(RETRO_FORMATS), state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="分辨率").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.retro_resolution_name, values=list(RETRO_RESOLUTIONS), state="readonly").grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="视频码率").grid(row=2, column=0, sticky="w", pady=5)
        retro_rate = ttk.Frame(settings)
        retro_rate.grid(row=2, column=1, sticky="ew", pady=5)
        self._build_bitrate_buttons(retro_rate, self.retro_bitrate, ["500k", "700k", "900k", "1200k", "2000k"])
        ttk.Label(settings, text="音频码率").grid(row=3, column=0, sticky="w", pady=5)
        retro_audio_rate = ttk.Frame(settings)
        retro_audio_rate.grid(row=3, column=1, sticky="ew", pady=5)
        self._build_bitrate_buttons(retro_audio_rate, self.retro_audio_bitrate, ["64k", "96k", "128k", "192k"])
        ttk.Checkbutton(settings, text="反交错 yadif", variable=self.retro_deinterlace).grid(row=4, column=0, columnspan=2, sticky="w", pady=6)
        ttk.Checkbutton(settings, text="轻度降噪 hqdn3d", variable=self.retro_denoise).grid(row=5, column=0, columnspan=2, sticky="w", pady=6)
        ttk.Button(settings, text="▶ 开始复古处理", style="Accent.TButton", command=self.start_retro_processing).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Label(settings, text="RM/WMA 等老格式是否可写入，取决于本机 FFmpeg 编译支持。", style="Hint.TLabel").grid(row=7, column=0, columnspan=2, sticky="w", pady=(12, 0))

        remux = ttk.LabelFrame(parent, text="封装转换", padding=12)
        remux.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        remux.columnconfigure(1, weight=1)
        ttk.Label(remux, text="输出格式").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(remux, textvariable=self.retro_remux_format, values=[name for name in VIDEO_MUXERS if VIDEO_MUXERS[name] != "source"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(remux, text="音频编码").grid(row=1, column=0, sticky="w", pady=5)
        audio_row = ttk.Frame(remux)
        audio_row.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Radiobutton(audio_row, text="复制音频", value="复制音频", variable=self.retro_remux_audio).pack(side="left")
        ttk.Radiobutton(audio_row, text="AAC 重新编码", value="AAC 重新编码", variable=self.retro_remux_audio).pack(side="left", padx=(14, 0))
        ttk.Button(remux, text="▶ 开始封装转换", style="Accent.TButton", command=self.start_retro_remux).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(remux, text="默认输出到源文件所在目录；视频流直接复制，只更换容器或音频编码。", style="Hint.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_anamorphic_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        files = ttk.LabelFrame(parent, text="反挤压素材", padding=12)
        files.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        files.rowconfigure(1, weight=1)
        files.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(files)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="＋ 添加视频", command=self.add_anamorphic_files).pack(side="left")
        ttk.Button(toolbar, text="▤ 添加文件夹", command=self.add_anamorphic_folder).pack(side="left", padx=6)
        ttk.Button(toolbar, text="− 移除", command=self.remove_selected_anamorphic).pack(side="left")
        ttk.Button(toolbar, text="清空", command=self.clear_anamorphic_files).pack(side="left", padx=6)
        list_frame = ttk.Frame(files)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.anamorphic_file_list = self._create_work_listbox(list_frame, selectmode="extended")
        self.anamorphic_file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.anamorphic_file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.anamorphic_file_list.configure(yscrollcommand=scrollbar.set)

        output = ttk.Frame(files)
        output.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        output.columnconfigure(1, weight=1)
        ttk.Button(output, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.anamorphic_output_dir)).grid(row=0, column=0, sticky="w")
        ttk.Entry(output, textvariable=self.anamorphic_output_dir).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(output, text="浏览…", command=self.choose_anamorphic_output_dir).grid(row=0, column=2)

        settings = ttk.LabelFrame(parent, text="反挤压与画幅", padding=12)
        settings.grid(row=0, column=1, sticky="nsew")
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="反挤压比例").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.anamorphic_factor, values=["1.25", "1.33", "1.50", "1.60", "1.80", "2.00"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="画幅处理").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(
            settings,
            textvariable=self.anamorphic_mode,
            values=["保留反挤压宽画幅", "裁切到目标画幅", "加黑边适配目标画幅"],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="目标画幅").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.anamorphic_target_aspect, values=["16:9", "1.85:1", "2.00:1", "2.35:1", "2.39:1", "2.40:1"], state="readonly").grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="输出分辨率").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.anamorphic_resolution, values=["保持反挤压尺寸", "4K 宽 3840", "2K 宽 2048", "1080p 宽 1920", "720p 宽 1280"], state="readonly").grid(row=3, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="编码器").grid(row=4, column=0, sticky="w", pady=5)
        self.anamorphic_encoder_combo = ttk.Combobox(settings, textvariable=self.anamorphic_encoder_name, values=self._filtered_encoder_list(list(COMMON_ENCODERS)), state="readonly")
        self.anamorphic_encoder_combo.grid(row=4, column=1, sticky="ew", pady=5)
        ttk.Checkbutton(settings, text="保留音频", variable=self.anamorphic_keep_audio).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(settings, text="轻度锐化反挤压后的画面", variable=self.anamorphic_auto_crop).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Button(settings, text="▶ 开始反挤压处理", style="Accent.TButton", command=self.start_anamorphic_processing).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(settings, text="▣ 生成预览帧", command=self.start_anamorphic_preview).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(settings, text="适合手机外接变形镜头、微单变形镜头和素材反挤压归档。", style="Hint.TLabel").grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _build_audio_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        files = ttk.LabelFrame(parent, text="音频任务", padding=12)
        files.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        files.rowconfigure(1, weight=1)
        files.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(files)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="＋ 添加音频", command=self.add_audio_files).pack(side="left")
        ttk.Button(toolbar, text="▤ 添加文件夹", command=self.add_audio_folder).pack(side="left", padx=6)
        ttk.Button(toolbar, text="− 移除", command=self.remove_selected_audio).pack(side="left")
        ttk.Button(toolbar, text="清空", command=self.clear_audio_files).pack(side="left", padx=6)
        list_frame = ttk.Frame(files)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.audio_file_list = self._create_work_listbox(list_frame, selectmode="extended")
        self.audio_file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.audio_file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.audio_file_list.configure(yscrollcommand=scrollbar.set)
        output = ttk.Frame(files)
        output.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        output.columnconfigure(1, weight=1)
        ttk.Button(output, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.audio_output_dir)).grid(row=0, column=0, sticky="w")
        ttk.Entry(output, textvariable=self.audio_output_dir).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(output, text="浏览…", command=self.choose_audio_output_dir).grid(row=0, column=2)
        audio_output_modes = ttk.Frame(output)
        audio_output_modes.grid(row=1, column=1, columnspan=2, sticky="w", padx=8, pady=(8, 0))
        ttk.Radiobutton(audio_output_modes, text="自定义", value="自定义", variable=self.audio_output_mode).pack(side="left")
        ttk.Radiobutton(audio_output_modes, text="和源文件同一目录", value="和源文件同一目录", variable=self.audio_output_mode).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(output, text="覆盖源文件（警告）", variable=self.audio_overwrite_source).grid(row=2, column=1, columnspan=2, sticky="w", padx=8, pady=(8, 0))

        settings = ttk.LabelFrame(parent, text="音频压缩设置", padding=12)
        settings.grid(row=0, column=1, sticky="nsew")
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="编码器").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.audio_encoder_name, values=list(AUDIO_ENCODERS), state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="码率").grid(row=1, column=0, sticky="w", pady=5)
        self.audio_bitrate_buttons_frame = ttk.Frame(settings)
        self.audio_bitrate_buttons_frame.grid(row=1, column=1, sticky="ew", pady=5)
        self._refresh_audio_bitrate_buttons()
        self.audio_encoder_name.trace_add("write", lambda *_: self._refresh_audio_bitrate_buttons())
        ttk.Label(settings, text="采样率").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.audio_sample_rate, values=["自动", "44100", "48000", "96000"], state="readonly").grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="声道").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Combobox(settings, textvariable=self.audio_channels, values=["自动", "1", "2", "6"], state="readonly").grid(row=3, column=1, sticky="ew", pady=5)
        ttk.Checkbutton(settings, text="响度标准化", variable=self.audio_normalize).grid(row=4, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(settings, text="▶ 开始音频压缩", style="Accent.TButton", command=self.start_audio_compression).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(settings, text="↩ 倒放保存", command=self.start_audio_reverse).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _build_mux_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        merge = ttk.LabelFrame(parent, text="合并文件", padding=12)
        merge.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        merge.rowconfigure(1, weight=1)
        merge.columnconfigure(0, weight=1)
        merge_toolbar = ttk.Frame(merge)
        merge_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(merge_toolbar, text="＋ 添加文件", command=self.add_mux_merge_files).pack(side="left")
        ttk.Button(merge_toolbar, text="− 移除", command=self.remove_selected_mux_merge).pack(side="left", padx=6)
        ttk.Button(merge_toolbar, text="清空", command=self.clear_mux_merge_files).pack(side="left")
        self.mux_merge_list = self._create_work_listbox(merge, selectmode="extended")
        self.mux_merge_list.grid(row=1, column=0, sticky="nsew")
        merge_scroll = ttk.Scrollbar(merge, orient="vertical", command=self.mux_merge_list.yview)
        merge_scroll.grid(row=1, column=1, sticky="ns")
        self.mux_merge_list.configure(yscrollcommand=merge_scroll.set)
        merge_options = ttk.Frame(merge)
        merge_options.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        merge_options.columnconfigure(1, weight=1)
        ttk.Label(merge_options, text="输出名称").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(merge_options, textvariable=self.mux_merge_name).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Label(merge_options, text="输出格式").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(merge_options, textvariable=self.mux_merge_format, values=[name for name in VIDEO_MUXERS if VIDEO_MUXERS[name] != "source"], state="readonly").grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(merge_options, text="▶ 合并输出", style="Accent.TButton", command=self.start_mux_merge).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        convert = ttk.LabelFrame(parent, text="封装转换", padding=12)
        convert.grid(row=0, column=1, sticky="nsew")
        convert.rowconfigure(1, weight=1)
        convert.columnconfigure(0, weight=1)
        convert_toolbar = ttk.Frame(convert)
        convert_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(convert_toolbar, text="＋ 添加文件", command=self.add_mux_convert_files).pack(side="left")
        ttk.Button(convert_toolbar, text="▤ 添加文件夹", command=self.add_mux_convert_folder).pack(side="left", padx=6)
        ttk.Button(convert_toolbar, text="− 移除", command=self.remove_selected_mux_convert).pack(side="left")
        ttk.Button(convert_toolbar, text="清空", command=self.clear_mux_convert_files).pack(side="left", padx=6)
        self.mux_convert_list = self._create_work_listbox(convert, selectmode="extended")
        self.mux_convert_list.grid(row=1, column=0, sticky="nsew")
        convert_scroll = ttk.Scrollbar(convert, orient="vertical", command=self.mux_convert_list.yview)
        convert_scroll.grid(row=1, column=1, sticky="ns")
        self.mux_convert_list.configure(yscrollcommand=convert_scroll.set)
        convert_options = ttk.Frame(convert)
        convert_options.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        convert_options.columnconfigure(1, weight=1)
        ttk.Button(convert_options, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.mux_output_dir)).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(convert_options, textvariable=self.mux_output_dir).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(convert_options, text="浏览…", command=self.choose_mux_output_dir).grid(row=0, column=2, pady=5)
        ttk.Label(convert_options, text="输出格式").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(convert_options, textvariable=self.mux_convert_format, values=[name for name in VIDEO_MUXERS if VIDEO_MUXERS[name] != "source"], state="readonly").grid(row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Label(convert_options, text="音频处理").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(convert_options, textvariable=self.mux_audio_mode, values=["复制音频", "AAC 编码", "MP3 编码", "Opus 编码", "FLAC 无损", "WAV PCM", "移除音频"], state="readonly").grid(row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Label(convert_options, text="音频码率").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(convert_options, textvariable=self.mux_audio_bitrate).grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Button(convert_options, text="▶ 开始封装转换", style="Accent.TButton", command=self.start_mux_convert).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    def _build_batch_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=1)
        box = ttk.LabelFrame(parent, text="批量压缩", padding=12)
        box.grid(row=0, column=0, sticky="nsew")
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text="输入文件夹").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(box, textvariable=self.batch_input_dir).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(box, text="浏览…", command=self.choose_batch_input_dir).grid(row=0, column=2, pady=5)
        ttk.Button(box, text="输出文件夹", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.batch_output_dir)).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(box, textvariable=self.batch_output_dir).grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(box, text="浏览…", command=self.choose_batch_output_dir).grid(row=1, column=2, pady=5)
        ttk.Label(box, text="批量预设").grid(row=2, column=0, sticky="w", pady=5)
        preset_row = ttk.Frame(box)
        preset_row.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)
        preset_row.columnconfigure(0, weight=1)
        ttk.Combobox(preset_row, textvariable=self.batch_preset_name, values=list(BATCH_PRESETS), state="readonly").grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(preset_row, text="竖屏模式", variable=self.batch_vertical_mode).grid(row=0, column=1, padx=(10, 0))
        ttk.Checkbutton(box, text="保留原目录结构", variable=self.batch_keep_tree).grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(box, text="同时处理音频文件", variable=self.batch_include_audio).grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Button(box, text="▶ 扫描并开始批量压缩", style="Accent.TButton", command=self.start_batch_compression).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(
            box,
            text="批量页适合整盘素材归档：自动扫描输入文件夹，视频按预设压缩，音频可同步转 AAC。",
            style="Hint.TLabel",
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _build_lut_tab(self, parent):
        parent = self._scrollable_frame(parent)
        parent.columnconfigure(0, weight=1)
        setup = ttk.LabelFrame(parent, text="LUT 批量缩略图对比", padding=12)
        setup.grid(row=0, column=0, sticky="ew")
        setup.columnconfigure(1, weight=1)
        ttk.Label(setup, text="视频文件").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(setup, textvariable=self.lut_page_video).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(setup, text="选择…", command=self.choose_lut_page_video).grid(row=0, column=2)
        ttk.Label(setup, text="LUT 文件夹").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(setup, textvariable=self.lut_page_folder).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(setup, text="选择…", command=self.choose_lut_page_folder).grid(row=1, column=2)
        ttk.Button(setup, text="输出目录", style="OutputDir.TButton", command=lambda: self.open_output_dir(self.lut_page_output)).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(setup, textvariable=self.lut_page_output).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Button(setup, text="选择…", command=self.choose_lut_page_output).grid(row=2, column=2)
        ttk.Label(setup, text="取帧时间").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Spinbox(setup, from_=0, to=3600, increment=0.5, textvariable=self.lut_page_time).grid(row=3, column=1, sticky="ew", padx=8)
        ttk.Button(setup, text="▶ 生成所有 LUT 缩略图", style="Accent.TButton", command=self.start_lut_folder_preview).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        result = ttk.LabelFrame(parent, text="缩略图结果", padding=12)
        result.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        result.columnconfigure(0, weight=1)
        result.rowconfigure(0, weight=1)
        self.lut_result_canvas = Canvas(result, height=240, bg=self.COLORS["surface_alt"], highlightthickness=1, highlightbackground=self.COLORS["panel_border"])
        self.lut_result_canvas.grid(row=0, column=0, sticky="nsew")
        lut_scroll = ttk.Scrollbar(result, orient="horizontal", command=self.lut_result_canvas.xview)
        lut_scroll.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.lut_result_canvas.configure(xscrollcommand=lut_scroll.set)
        self.lut_result_strip = ttk.Frame(self.lut_result_canvas)
        self.lut_result_window = self.lut_result_canvas.create_window((0, 0), window=self.lut_result_strip, anchor="nw")
        self.lut_result_strip.bind("<Configure>", lambda event: self.lut_result_canvas.configure(scrollregion=self.lut_result_canvas.bbox("all")))

    def _build_mediainfo_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        toolbar = ttk.LabelFrame(parent, text="媒体信息", padding=12)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)
        ttk.Button(toolbar, text="打开文件…", command=self.choose_mediainfo_file).grid(row=0, column=0, sticky="w")
        ttk.Entry(toolbar, textvariable=self.media_info_path).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(toolbar, text="读取信息", style="Accent.TButton", command=self.load_mediainfo).grid(row=0, column=2)
        ttk.Label(toolbar, text="支持拖入媒体文件；信息由本机 ffprobe 读取。", style="Hint.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        indicator_box = ttk.Frame(toolbar)
        indicator_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self.media_feature_labels = {}
        for index, name in enumerate(("杜比音效", "5.1声道", "HDR", "10-bit", "4K", "高帧率", "多音轨")):
            label = ttk.Label(indicator_box, text=f"○ {name}")
            label.grid(row=0, column=index, sticky="w", padx=(0, 14))
            self.media_feature_labels[name] = label

        compare_box = ttk.Frame(toolbar)
        compare_box.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        compare_box.columnconfigure(1, weight=1)
        ttk.Label(compare_box, text="对比文件 A").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(compare_box, textvariable=self.media_compare_path_a).grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(compare_box, text="选择…", command=self.choose_mediainfo_compare_a).grid(row=0, column=2, pady=4)
        ttk.Label(compare_box, text="对比文件 B").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(compare_box, textvariable=self.media_compare_path_b).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(compare_box, text="选择…", command=self.choose_mediainfo_compare_b).grid(row=1, column=2, pady=4)
        option_row = ttk.Frame(compare_box)
        option_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        option_row.columnconfigure(1, weight=1)
        ttk.Checkbutton(option_row, text="导出表格时自动生成 A/B 静态帧", variable=self.media_compare_generate_frames_on_export).grid(row=0, column=0, sticky="w")
        ttk.Label(option_row, text="取帧时间").grid(row=0, column=1, sticky="e", padx=(8, 4))
        ttk.Spinbox(option_row, from_=0, to=3600, increment=0.5, width=8, textvariable=self.media_compare_frame_time).grid(row=0, column=2, sticky="w")
        ttk.Label(option_row, text="秒", style="Hint.TLabel").grid(row=0, column=3, sticky="w", padx=(4, 0))

        action_row = ttk.Frame(compare_box)
        action_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        action_row.columnconfigure((0, 1), weight=1)
        ttk.Button(action_row, text="对比参数", style="Accent.TButton", command=self.compare_mediainfo_files).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(action_row, text="导出对比表格", command=self.export_mediainfo_comparison).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Label(compare_box, text="对比结果会弹出在独立窗口中，便于完整查看。", style="Hint.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        panel = ttk.LabelFrame(parent, text="单文件媒体信息", padding=12)
        panel.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        self.media_info_text = Text(
            panel,
            wrap="word",
            borderwidth=1,
            relief="solid",
            background=self.COLORS["entry_bg"],
            foreground=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            font=("Microsoft YaHei UI", 10),
            padx=12,
            pady=10,
        )
        self.media_info_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.media_info_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.media_info_text.configure(yscrollcommand=scrollbar.set)

    def _detect_runtime_hardware(self):
        try:
            info = ffmpeg.detect_environment()
        except Exception:
            info = None
        self.runtime_environment = info
        gpu_names = []
        if os.name == "nt":
            gpu_names = self._windows_cim_list("Win32_VideoController", "Name")
        self.detected_gpu_names = gpu_names
        normalized = " ".join(gpu_names).lower()
        self.detected_has_nvidia = any(token in normalized for token in ("nvidia", "geforce", "rtx", "gtx", "quadro", "tesla"))
        self.detected_has_amd = any(token in normalized for token in ("amd", "radeon", "rx ", "vega", "firepro", "instinct"))
        self.detected_has_intel = any(token in normalized for token in ("intel", "uhd graphics", "iris", "arc", "hd graphics"))

    def _encoder_visible(self, encoder_name):
        encoder_key = ENCODERS.get(encoder_name, "")
        info = self.runtime_environment
        if not encoder_key:
            return True
        if "nvenc" in encoder_key:
            supported = bool(info.has_nvenc) if info is not None else True
            hardware_ready = self.detected_has_nvidia if self.detected_gpu_names else True
            return supported and hardware_ready
        if encoder_key.endswith("_amf"):
            supported = bool(info.has_amf) if info is not None else True
            hardware_ready = self.detected_has_amd if self.detected_gpu_names else True
            return supported and hardware_ready
        if encoder_key.endswith("_qsv"):
            supported = bool(info.has_qsv) if info is not None else True
            hardware_ready = self.detected_has_intel if self.detected_gpu_names else True
            return supported and hardware_ready
        if encoder_key.endswith("_videotoolbox"):
            return bool(info.has_videotoolbox) if info is not None else self._is_macos()
        return True

    def _filtered_encoder_list(self, encoders):
        return [name for name in encoders if self._encoder_visible(name)]

    def _build_tasks_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        panel = ttk.LabelFrame(parent, text="任务队列", padding=12)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        self.task_tree = ttk.Treeview(panel, columns=("name", "status", "started", "finished"), show="headings", height=14)
        self.task_tree.heading("name", text="任务")
        self.task_tree.heading("status", text="状态")
        self.task_tree.heading("started", text="开始时间")
        self.task_tree.heading("finished", text="结束时间")
        self.task_tree.column("name", width=360)
        self.task_tree.column("status", width=82, anchor="center", stretch=False)
        self.task_tree.column("started", width=86, anchor="center", stretch=False)
        self.task_tree.column("finished", width=86, anchor="center", stretch=False)
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.task_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        self.task_tree.bind("<ButtonPress-1>", self._task_drag_start)
        self.task_tree.bind("<B1-Motion>", self._task_drag_motion)
        self.task_tree.bind("<Double-1>", lambda event: self.start_selected_queued_tasks())
        self.task_tree.bind("<Delete>", lambda event: self.remove_selected_tasks())
        actions = ttk.Frame(panel)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="▶ 开始选中", style="Accent.TButton", command=self.start_selected_queued_tasks).pack(side="left")
        ttk.Button(actions, text="▶ 开始全部", command=self.start_all_queued_tasks).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="移除选中", command=self.remove_selected_tasks).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="■ 停止全部", command=self.stop).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="清除已完成", command=self.clear_finished_tasks).pack(side="left", padx=8)

        options = ttk.Frame(panel)
        options.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(options, text="同时进行任务数").pack(side="left")
        ttk.Spinbox(options, from_=1, to=4, increment=1, width=6, textvariable=self.queue_parallel_jobs).pack(side="left", padx=(8, 16))
        ttk.Label(options, text="队列任务使用入队时的视频列表与压缩参数；拖动任务行可调整执行顺序，双击可启动选中任务。", style="Hint.TLabel").pack(side="left")

    def _scrollable_frame(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        canvas = Canvas(parent, highlightthickness=0, bg=self.COLORS["bg"], bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._scrollable_canvases.append(canvas)
        inner.bind("<Configure>", lambda event: self._schedule_scrollregion_update(canvas))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.bind("<Enter>", lambda event: self._bind_canvas_wheel(canvas))
        canvas.bind("<Leave>", lambda event: self._unbind_canvas_wheel(canvas))
        return inner

    def _schedule_scrollregion_update(self, canvas):
        if not canvas.winfo_exists():
            return
        previous = self._scrollregion_jobs.get(canvas)
        if previous is not None:
            try:
                self.root.after_cancel(previous)
            except Exception:
                pass
        self._scrollregion_jobs[canvas] = self.root.after_idle(lambda c=canvas: self._update_scrollregion(c))

    def _update_scrollregion(self, canvas):
        self._scrollregion_jobs.pop(canvas, None)
        if not canvas.winfo_exists():
            return
        try:
            bbox = canvas.bbox("all")
            if self._scrollregion_cache.get(canvas) == bbox:
                return
            self._scrollregion_cache[canvas] = bbox
            canvas.configure(scrollregion=bbox)
        except Exception:
            pass

    def _mousewheel_units(self, event):
        num = getattr(event, "num", None)
        if num == 4:
            return -1
        if num == 5:
            return 1
        delta = int(getattr(event, "delta", 0))
        if delta == 0:
            return 0
        step = int(delta / 120)
        if step == 0:
            step = 1 if delta > 0 else -1
        return -step

    def _scroll_canvas_units(self, canvas, units):
        canvas.yview_scroll(units, "units")
        return "break"

    def _bind_canvas_wheel(self, canvas):
        callback = getattr(canvas, "_wheel_callback", None)
        if callback is not None:
            return

        def on_wheel(event):
            units = self._mousewheel_units(event)
            if units:
                canvas.yview_scroll(units, "units")
            return "break"

        canvas._wheel_callback = on_wheel
        self.root.bind_all("<MouseWheel>", on_wheel)
        self.root.bind_all("<Button-4>", on_wheel)
        self.root.bind_all("<Button-5>", on_wheel)

    def _unbind_canvas_wheel(self, canvas):
        callback = getattr(canvas, "_wheel_callback", None)
        if callback is None:
            return
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        canvas._wheel_callback = None

    def _iter_widgets(self, widget):
        yield widget
        for child in widget.winfo_children():
            yield from self._iter_widgets(child)

    def _bind_scroll_to_widget_tree(self, root_widget, canvas, bind_keys=False):
        def on_wheel(event):
            units = self._mousewheel_units(event)
            if units:
                canvas.yview_scroll(units, "units")
            return "break"

        for widget in self._iter_widgets(root_widget):
            widget.bind("<MouseWheel>", on_wheel, add="+")
            widget.bind("<Button-4>", lambda event: self._scroll_canvas_units(canvas, -1), add="+")
            widget.bind("<Button-5>", lambda event: self._scroll_canvas_units(canvas, 1), add="+")
            if bind_keys:
                widget.bind("<Up>", lambda event: self._scroll_canvas_units(canvas, -2), add="+")
                widget.bind("<Down>", lambda event: self._scroll_canvas_units(canvas, 2), add="+")
                widget.bind("<Prior>", lambda event: self._scroll_canvas_units(canvas, -10), add="+")
                widget.bind("<Next>", lambda event: self._scroll_canvas_units(canvas, 10), add="+")

    def _bind_scroll_keys(self, window, canvas):
        window.bind("<Up>", lambda event: self._scroll_canvas_units(canvas, -2), add="+")
        window.bind("<Down>", lambda event: self._scroll_canvas_units(canvas, 2), add="+")
        window.bind("<Prior>", lambda event: self._scroll_canvas_units(canvas, -10), add="+")
        window.bind("<Next>", lambda event: self._scroll_canvas_units(canvas, 10), add="+")

    def _create_work_listbox(self, parent, **kwargs):
        metrics = self._ui_metrics()
        options = {
            "activestyle": "none",
            "borderwidth": 0,
            "highlightthickness": 1,
            "highlightbackground": self.COLORS["panel_border"],
            "highlightcolor": self.COLORS["accent"],
            "background": self.COLORS["list_bg"],
            "foreground": self.COLORS["list_fg"],
            "selectbackground": self.COLORS["list_select"],
            "selectforeground": "#ffffff",
            "relief": "flat",
            "font": ("Microsoft YaHei UI", metrics["font"]),
        }
        options.update(kwargs)
        return Listbox(parent, **options)

    def _build_bitrate_buttons(self, parent, variable, values):
        for child in parent.winfo_children():
            child.destroy()
        parent.columnconfigure(len(values), weight=1)
        for index, value in enumerate(values):
            ttk.Radiobutton(parent, text=value, value="" if value in {"无损", "无需设置"} else value, variable=variable).grid(row=0, column=index, padx=(0, 6), sticky="w")

    def _refresh_audio_bitrate_buttons(self):
        if not hasattr(self, "audio_bitrate_buttons_frame"):
            return
        values = AUDIO_BITRATE_PRESETS.get(self.audio_encoder_name.get(), ["128k", "192k", "320k"])
        current = self.audio_page_bitrate.get()
        normalized_values = ["" if value == "无损" else value for value in values]
        if current not in normalized_values:
            self.audio_page_bitrate.set(normalized_values[0])
        self._build_bitrate_buttons(self.audio_bitrate_buttons_frame, self.audio_page_bitrate, values)

    def _refresh_video_audio_bitrate_buttons(self):
        if not hasattr(self, "video_audio_bitrate_buttons_frame"):
            return
        mode = self.audio_mode.get()
        if "Opus" in mode:
            values = ["96k", "128k", "160k", "192k"]
        elif "MP3" in mode:
            values = ["128k", "192k", "256k", "320k"]
        elif "FLAC" in mode or "复制" in mode or "移除" in mode:
            values = ["无损"] if "FLAC" in mode else ["无需设置"]
        else:
            values = ["128k", "160k", "192k", "256k", "320k"]
        normalized_values = ["" if value in {"无损", "无需设置"} else value for value in values]
        if self.audio_bitrate.get() not in normalized_values:
            self.audio_bitrate.set(normalized_values[0])
        self._build_bitrate_buttons(self.video_audio_bitrate_buttons_frame, self.audio_bitrate, values)

    def _encoder_choices(self):
        choices = list(ENCODERS) if self.advanced_encoders.get() else list(COMMON_ENCODERS)
        filtered = self._filtered_encoder_list(choices)
        if not filtered:
            filtered = ["CPU H.264 / AVC (libx264)"]
        return filtered

    def refresh_encoder_choices(self):
        choices = self._encoder_choices()
        if hasattr(self, "encoder_combo"):
            self.encoder_combo.configure(values=choices)
        if hasattr(self, "common_trim_encoder"):
            common_choices = self._filtered_encoder_list(list(COMMON_ENCODERS))
            if not common_choices:
                common_choices = ["CPU H.264 / AVC (libx264)"]
            try:
                self.common_trim_encoder_combo.configure(values=common_choices)
            except Exception:
                pass
            if self.common_trim_encoder.get() not in common_choices:
                self.common_trim_encoder.set(common_choices[0])
        if hasattr(self, "anamorphic_encoder_name"):
            anamorphic_choices = self._filtered_encoder_list(list(COMMON_ENCODERS))
            if not anamorphic_choices:
                anamorphic_choices = ["CPU H.264 / AVC (libx264)"]
            try:
                self.anamorphic_encoder_combo.configure(values=anamorphic_choices)
            except Exception:
                pass
            if self.anamorphic_encoder_name.get() not in anamorphic_choices:
                self.anamorphic_encoder_name.set(anamorphic_choices[0])
        if self.encoder_name.get() not in choices:
            self.encoder_name.set(choices[0])
        self._rebuild_settings_panel()

    def _add_encoder_controls(self, panel, row):
        ttk.Label(panel, text="编码器").grid(row=row, column=0, sticky="w", pady=5)
        encoder_row = ttk.Frame(panel)
        encoder_row.grid(row=row, column=1, sticky="ew", pady=5)
        encoder_row.columnconfigure(0, weight=1)
        self.encoder_combo = ttk.Combobox(encoder_row, textvariable=self.encoder_name, values=self._encoder_choices(), state="readonly")
        self.encoder_combo.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(encoder_row, text="高级模式", variable=self.advanced_encoders, command=self.refresh_encoder_choices).grid(row=0, column=1, padx=(8, 0))

        row += 1
        ttk.Label(panel, text="速度/质量").grid(row=row, column=0, sticky="w", pady=5)
        self.preset_combo = ttk.Combobox(panel, textvariable=self.preset_name, values=list(PRESETS), state="readonly")
        self.preset_combo.grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Checkbutton(
            panel,
            text="编码失败时自动回退到 CPU H.264（libx264）并重试一次",
            variable=self.auto_fallback_cpu_h264,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)

        if self.advanced_encoders.get():
            row += 1
            ttk.Label(panel, text="质量模式").grid(row=row, column=0, sticky="w", pady=5)
            ttk.Combobox(panel, textvariable=self.quality_mode, values=list(QUALITY_MODES), state="readonly").grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Label(panel, text="CRF").grid(row=row, column=0, sticky="w", pady=5)
        quality = ttk.Frame(panel)
        quality.grid(row=row, column=1, sticky="ew", pady=5)
        quality.columnconfigure(0, weight=1)
        ttk.Scale(quality, from_=16, to=32, orient=HORIZONTAL, variable=self.cq_value).grid(row=0, column=0, sticky="ew")
        ttk.Label(quality, textvariable=self.cq_value, width=4).grid(row=0, column=1, padx=(8, 0))

        if self.advanced_encoders.get():
            row += 1
            ttk.Label(panel, text="目标码率").grid(row=row, column=0, sticky="w", pady=5)
            bitrate_row = ttk.Frame(panel)
            bitrate_row.grid(row=row, column=1, sticky="ew", pady=5)
            bitrate_row.columnconfigure(0, weight=1)
            ttk.Entry(bitrate_row, textvariable=self.bitrate).grid(row=0, column=0, sticky="ew")
            ttk.Label(bitrate_row, text="2PASS 使用，如 4000k", style="Hint.TLabel").grid(row=0, column=1, padx=(8, 0))

            row += 1
            ttk.Label(panel, text="自定义命令").grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(panel, textvariable=self.custom_command).grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Label(panel, text="音频").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.audio_mode, values=list(AUDIO_MODES), state="readonly").grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Label(panel, text="音频码率").grid(row=row, column=0, sticky="w", pady=5)
        video_audio_rate_row = ttk.Frame(panel)
        video_audio_rate_row.grid(row=row, column=1, sticky="ew", pady=5)
        self.video_audio_bitrate_buttons_frame = video_audio_rate_row
        self._refresh_video_audio_bitrate_buttons()
        self.audio_mode.trace_add("write", lambda *_: self._refresh_video_audio_bitrate_buttons())

        row += 1
        ttk.Label(panel, text="分离器/容器").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.muxer_name, values=list(VIDEO_MUXERS), state="readonly").grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Label(panel, text="输出倍速").grid(row=row, column=0, sticky="w", pady=5)
        speed_row = ttk.Frame(panel)
        speed_row.grid(row=row, column=1, sticky="ew", pady=5)
        speed_row.columnconfigure(0, weight=1)
        ttk.Spinbox(speed_row, from_=0.1, to=10.0, increment=0.1, textvariable=self.output_speed).grid(row=0, column=0, sticky="ew")
        ttk.Label(speed_row, text="1.0 为原速；变速会重编码音频", style="Hint.TLabel").grid(row=0, column=1, padx=(8, 0))

        row += 1
        ttk.Label(panel, text="分辨率").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.resolution_name, values=list(RESOLUTIONS), state="readonly").grid(row=row, column=1, sticky="ew", pady=5)

        row += 1
        ttk.Label(panel, text="锐化").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(panel, textvariable=self.sharpen_name, values=list(SHARPEN_LEVELS), state="readonly").grid(row=row, column=1, sticky="ew", pady=5)

        if self.advanced_encoders.get():
            row += 1
            ttk.Label(panel, text="自定义宽高").grid(row=row, column=0, sticky="w", pady=5)
            size_row = ttk.Frame(panel)
            size_row.grid(row=row, column=1, sticky="ew", pady=5)
            size_row.columnconfigure((0, 2), weight=1)
            self.custom_width_spin = ttk.Spinbox(size_row, from_=320, to=7680, increment=2, textvariable=self.custom_width)
            self.custom_width_spin.grid(row=0, column=0, sticky="ew")
            ttk.Label(size_row, text="x", style="Hint.TLabel").grid(row=0, column=1, padx=8)
            self.custom_height_spin = ttk.Spinbox(size_row, from_=0, to=4320, increment=2, textvariable=self.custom_height)
            self.custom_height_spin.grid(row=0, column=2, sticky="ew")
            ttk.Label(size_row, text="宽 x 高；高度 0 表示自动保持比例", style="Hint.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
            self._sync_custom_size_state()

        row += 1
        ttk.Label(panel, text="并发任务").grid(row=row, column=0, sticky="w", pady=5)
        parallel_row = ttk.Frame(panel)
        parallel_row.grid(row=row, column=1, sticky="ew", pady=5)
        parallel_row.columnconfigure(0, weight=1)
        ttk.Spinbox(parallel_row, from_=1, to=8, increment=1, textvariable=self.parallel_jobs).grid(row=0, column=0, sticky="ew")
        ttk.Label(parallel_row, text="批量时提高 GPU 占用", style="Hint.TLabel").grid(row=0, column=1, padx=(8, 0))

        return row + 1

    def _sync_custom_size_state(self):
        width_spin = getattr(self, "custom_width_spin", None)
        height_spin = getattr(self, "custom_height_spin", None)
        if not width_spin or not height_spin:
            return
        is_custom = RESOLUTIONS.get(self.resolution_name.get()) == "custom"
        state = "normal" if is_custom else "disabled"
        try:
            width_spin.configure(state=state)
            height_spin.configure(state=state)
        except Exception:
            pass

    def _add_lut_controls(self, panel, row):
        if not self.advanced_encoders.get():
            return row
        ttk.Label(panel, text="LUT 调色").grid(row=row, column=0, sticky="w", pady=5)
        lut_row = ttk.Frame(panel)
        lut_row.grid(row=row, column=1, sticky="ew", pady=5)
        lut_row.columnconfigure(1, weight=1)
        ttk.Checkbutton(lut_row, text="启用", variable=self.use_lut).grid(row=0, column=0, sticky="w")
        ttk.Entry(lut_row, textvariable=self.lut_path).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(lut_row, text="选择…", command=self.choose_lut).grid(row=0, column=2)
        ttk.Button(lut_row, text="▶ 预览", command=self.start_lut_preview).grid(row=0, column=3, padx=(6, 0))

        row += 1
        preview_frame = ttk.Frame(panel)
        preview_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        preview_frame.columnconfigure(0, weight=1)
        self.preview_label = ttk.Label(preview_frame, text="选择视频和 LUT 后可预览当前缩略图时间点", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="ew")

        row += 1
        ttk.Label(panel, text="高级参数").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(panel, textvariable=self.extra_ffmpeg_args).grid(row=row, column=1, sticky="ew", pady=5)
        return row + 1

    def _add_thumbnail_controls(self, panel, row):
        ttk.Checkbutton(panel, text="压缩后生成 JPG 缩略图", variable=self.create_thumbnail).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
        if not self.advanced_encoders.get():
            return row + 1
        row += 1
        ttk.Checkbutton(panel, text="只给选中视频批量生成缩略图", variable=self.thumbnail_only_selected).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)

        row += 1
        ttk.Label(panel, text="缩略图时间").grid(row=row, column=0, sticky="w", pady=5)
        thumb_row = ttk.Frame(panel)
        thumb_row.grid(row=row, column=1, sticky="ew", pady=5)
        thumb_row.columnconfigure(0, weight=1)
        ttk.Spinbox(thumb_row, from_=0, to=3600, increment=0.5, textvariable=self.thumbnail_time).grid(row=0, column=0, sticky="ew")
        ttk.Label(thumb_row, text="秒", style="Hint.TLabel").grid(row=0, column=1, padx=(8, 0))

        return row + 1

    def _add_hidden_watermark_controls(self, panel, row):
        box = ttk.LabelFrame(panel, text="隐藏水印", padding=(10, 8))
        box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 10))
        box.columnconfigure(1, weight=1)
        ttk.Checkbutton(box, text="嵌入隐藏水印", variable=self.hidden_watermark_enabled).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(box, text="类型").grid(row=1, column=0, sticky="w", pady=4)
        wm_mode = ttk.Frame(box)
        wm_mode.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        ttk.Radiobutton(wm_mode, text="文字", value="text", variable=self.hidden_watermark_mode).pack(side="left")
        ttk.Radiobutton(wm_mode, text="图片", value="image", variable=self.hidden_watermark_mode).pack(side="left", padx=(10, 0))
        ttk.Label(box, text="水印文字").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(box, textvariable=self.hidden_watermark_text).grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Label(box, text="水印图片").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(box, textvariable=self.hidden_watermark_image).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Button(box, text="选择…", command=self.choose_hidden_watermark_image).grid(row=3, column=2, padx=(8, 0), pady=4)
        ttk.Button(box, text="解析隐藏水印", command=self.extract_hidden_watermark_from_file).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(box, text="只解析本软件写入的隐藏签名。", style="Hint.TLabel").grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))
        return row + 1

    def _add_action_buttons(self, panel, row):
        actions = ttk.Frame(panel)
        actions.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        actions.columnconfigure((0, 1), weight=1)
        conflict = ttk.LabelFrame(actions, text="如果文件已存在", padding=(10, 8))
        conflict.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for index, value in enumerate(("跳过", "覆盖", "重命名")):
            ttk.Radiobutton(conflict, text=value, value=value, variable=self.file_conflict_action).grid(row=0, column=index, sticky="w", padx=(0, 14))

        ttk.Button(actions, text="▶ 开始压缩", style="Accent.TButton", command=self.start_compression).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="■ 停止", command=self.stop).grid(row=1, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(actions, text="▣ 批量生成缩略图", command=self.start_thumbnail_batch).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))
        ttk.Button(actions, text="◷ CPU/GPU Benchmark", command=self.start_benchmark).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(8, 0))
        ttk.Button(actions, text="⬇ 生成代理文件", command=self.start_proxy_files).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        return row + 1

    def _build_bottom_panel(self, parent):
        panel = ttk.Frame(parent)
        panel.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, textvariable=self.current_task, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        post_actions = ttk.Frame(panel)
        post_actions.grid(row=1, column=0, sticky="w", pady=(3, 2))
        ttk.Checkbutton(post_actions, text="完成后关机", variable=self.shutdown_when_finished).pack(side="left")
        ttk.Checkbutton(post_actions, text="结束提示音", variable=self.play_finish_sound).pack(side="left", padx=(14, 0))
        ttk.Progressbar(panel, variable=self.progress, maximum=100).grid(row=2, column=0, sticky="ew", pady=6)
        self.log = self._create_work_listbox(panel, height=7)
        self.log.grid(row=3, column=0, sticky="nsew")

    def _bind_keys(self):
        self.root.bind("<space>", lambda event: self.toggle_preview_playback())
        self.root.bind("<Left>", lambda event: self.seek_preview(-5))
        self.root.bind("<Right>", lambda event: self.seek_preview(5))
        self.root.bind("<Control-Left>", lambda event: self.seek_preview(-30))
        self.root.bind("<Control-Right>", lambda event: self.seek_preview(30))
        self.root.bind("<Home>", lambda event: self.seek_preview_to(0))
        self.root.bind("<End>", lambda event: self.seek_preview_to(self.preview_duration))
        self.root.bind("<Key-s>", lambda event: self.save_current_screenshot())
        self.root.bind("<Key-o>", lambda event: self.choose_screenshot_dir())
        self.root.bind("<Delete>", self._handle_delete_key)

    def _bind_delete_shortcuts(self):
        bindings = [
            ("file_list", self.remove_selected),
            ("audio_file_list", self.remove_selected_audio),
            ("retro_file_list", self.remove_selected_retro),
            ("anamorphic_file_list", self.remove_selected_anamorphic),
            ("mux_merge_list", self.remove_selected_mux_merge),
            ("mux_convert_list", self.remove_selected_mux_convert),
            ("external_subtitle_list", self.remove_selected_external_subtitle),
            ("task_tree", self.remove_selected_tasks),
            ("user_preset_list", self.delete_selected_user_video_preset),
        ]
        for attr_name, handler in bindings:
            widget = getattr(self, attr_name, None)
            if not widget:
                continue
            try:
                widget.bind("<Delete>", lambda event, fn=handler: (fn(), "break")[1], add="+")
            except Exception:
                pass

    def _maybe_start_first_run_guide(self):
        if not self._guide_enabled():
            self.first_run_guide_completed = True
            return
        if self.first_run_guide_completed:
            return
        if not messagebox.askyesno("首次使用向导", "检测到你是首次使用，是否开始新手向导？\n\n向导会高亮按钮并分 4 步带你走完流程。"):
            return
        self.start_first_run_guide(mark_completed=True)

    def start_first_run_guide(self, mark_completed=True):
        if not self._guide_enabled():
            return
        if self._guide_window and self._guide_window.winfo_exists():
            self._guide_window.lift()
            return
        self._cancel_guide_blinks()
        self._guide_action_flags = {
            "checked_env": False,
            "pressed_start": False,
            "opened_github": False,
        }
        self._guide_step_index = 0
        self._guide_steps = [
            {
                "title": "步骤 1：检测环境",
                "text": "请点击顶部“✓ 检测环境”，确认编码器可用性。",
                "tab": None,
                "widgets": [self._header_button_refs.get("check_env")],
                "check": lambda: self._guide_action_flags["checked_env"],
            },
            {
                "title": "步骤 2：选择输入与输出",
                "text": "请在“视频”页添加输入文件，并确认输出目录。",
                "tab": "视频",
                "widgets": [getattr(self, "video_add_button", None), getattr(self, "video_output_browse_button", None)],
                "check": lambda: len(self.files) > 0 and bool(self.output_dir.get().strip()),
            },
            {
                "title": "步骤 3：选择参数并开始",
                "text": "请确认编码器与预设，然后点击“▶ 开始压缩”（无文件时点击也会计入练习）。",
                "tab": "视频",
                "widgets": [getattr(self, "encoder_combo", None), getattr(self, "preset_combo", None), self._header_button_refs.get("start")],
                "check": lambda: self._guide_action_flags["pressed_start"],
            },
            {
                "title": "步骤 4：问题反馈",
                "text": f"遇到问题请到 GitHub 的 Issues 反馈，并附带版本号：{self.app_version}",
                "tab": None,
                "widgets": [self._header_button_refs.get("github")],
                "check": lambda: self._guide_action_flags["opened_github"],
            },
        ]
        self._build_guide_window(mark_completed=mark_completed)

    def _build_guide_window(self, mark_completed):
        window = Toplevel(self.root)
        self._guide_window = window
        window.title("新手向导")
        self._set_window_geometry(window, "560x440")
        window.resizable(False, False)
        window.transient(self.root)
        self._set_window_icon(window)
        window.protocol("WM_DELETE_WINDOW", self._close_guide_window)

        shell = ttk.Frame(window, padding=14)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(2, weight=1)

        ttk.Label(shell, text="小丸工具箱新手向导", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(shell, text="按步骤完成真实操作，完成后会自动记录为“已引导”。", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 10))

        content = ttk.LabelFrame(shell, text="当前步骤", padding=12)
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        ttk.Label(content, textvariable=self._guide_progress_var, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(content, textvariable=self._guide_step_title_var, font=("Microsoft YaHei UI", 12, "bold")).grid(row=1, column=0, sticky="w", pady=(8, 4))
        ttk.Label(content, textvariable=self._guide_step_text_var, wraplength=510, justify="left").grid(row=2, column=0, sticky="w")

        checklist = ttk.LabelFrame(shell, text="步骤清单", padding=12)
        checklist.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        checklist.columnconfigure(0, weight=1)
        self._guide_status_labels = []
        for index, step in enumerate(self._guide_steps):
            var = StringVar(value=f"○ {index + 1}. {step['title']}")
            label = ttk.Label(checklist, textvariable=var)
            label.grid(row=index, column=0, sticky="w", pady=2)
            self._guide_status_labels.append(var)

        actions = ttk.Frame(shell)
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)
        ttk.Button(actions, text="定位并高亮", command=self._guide_focus_current_step).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._guide_prev_button = ttk.Button(actions, text="上一步", command=lambda: self._guide_move_step(-1))
        self._guide_prev_button.grid(row=0, column=1, sticky="ew", padx=6)
        self._guide_next_button = ttk.Button(actions, text="下一步", style="Accent.TButton", command=lambda: self._guide_move_step(1))
        self._guide_next_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        ttk.Button(actions, text="暂时关闭", command=self._exit_guide_early).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self._guide_refresh_ui()
        self._guide_focus_current_step()
        self.root.after(350, lambda: self._poll_guide_state(mark_completed))

    def _guide_move_step(self, direction):
        index = self._guide_step_index + direction
        self._guide_step_index = max(0, min(len(self._guide_steps) - 1, index))
        self._guide_refresh_ui()
        self._guide_focus_current_step()

    def _guide_refresh_ui(self):
        total = len(self._guide_steps)
        step = self._guide_steps[self._guide_step_index]
        self._guide_progress_var.set(f"进度 {self._guide_step_index + 1}/{total}")
        self._guide_step_title_var.set(step["title"])
        self._guide_step_text_var.set(step["text"])
        for index, item in enumerate(self._guide_steps):
            done = bool(item["check"]())
            prefix = "●" if index == self._guide_step_index else ("✓" if done else "○")
            self._guide_status_labels[index].set(f"{prefix} {index + 1}. {item['title']}")
        self._guide_prev_button.configure(state="normal" if self._guide_step_index > 0 else "disabled")
        current_done = bool(step["check"]())
        if self._guide_step_index == total - 1:
            self._guide_next_button.configure(text="完成向导", state="normal" if current_done else "disabled")
        else:
            self._guide_next_button.configure(text="下一步", state="normal" if current_done else "disabled")

    def _guide_focus_current_step(self):
        step = self._guide_steps[self._guide_step_index]
        tab_name = step.get("tab")
        if tab_name and tab_name in self.tab_frames:
            self.notebook.select(self.tab_frames[tab_name])
        self.root.update_idletasks()
        self._blink_widgets(step.get("widgets", []), blink_count=5)

    def _poll_guide_state(self, mark_completed):
        window = self._guide_window
        if not window or not window.winfo_exists():
            return
        self._guide_refresh_ui()
        total = len(self._guide_steps)
        all_done = all(bool(step["check"]()) for step in self._guide_steps)
        if all_done and self._guide_step_index == total - 1:
            self._guide_next_button.configure(state="normal")
        if self._guide_step_index == total - 1 and self._guide_steps[-1]["check"]():
            if self._guide_next_button.cget("text") == "完成向导":
                self._guide_next_button.configure(command=lambda: self._complete_guide(mark_completed))
        else:
            self._guide_next_button.configure(command=lambda: self._guide_move_step(1))
        self.root.after(350, lambda: self._poll_guide_state(mark_completed))

    def _complete_guide(self, mark_completed):
        if mark_completed:
            self.first_run_guide_completed = True
            self._save_app_settings()
        self._close_guide_window()
        messagebox.showinfo("向导完成", "向导已完成。后续可通过顶部“新手向导”再次打开。")

    def _exit_guide_early(self):
        if messagebox.askyesno("关闭向导", "当前向导尚未完成，确认暂时关闭吗？"):
            self._close_guide_window()

    def _close_guide_window(self):
        self._cancel_guide_blinks()
        if self._guide_window and self._guide_window.winfo_exists():
            try:
                self._guide_window.destroy()
            except Exception:
                pass
        self._guide_window = None

    def _blink_widgets(self, widgets, blink_count=6, interval=180):
        self._cancel_guide_blinks()
        targets = [widget for widget in widgets if widget and widget.winfo_exists()]
        if not targets:
            return
        states = {}
        for widget in targets:
            try:
                states[widget] = widget.cget("style")
            except Exception:
                states[widget] = ""

        def apply_style(active):
            for widget in targets:
                if not widget.winfo_exists():
                    continue
                style = states.get(widget, "")
                if active:
                    if widget.winfo_class() == "TCombobox":
                        style = "GuideGlow.TCombobox"
                    else:
                        style = "GuideGlow.TButton"
                try:
                    widget.configure(style=style)
                except Exception:
                    pass

        for index in range(blink_count * 2):
            active = index % 2 == 0
            delay = index * interval
            job = self.root.after(delay, lambda on=active: apply_style(on))
            self._guide_blink_jobs.append(job)
        restore_job = self.root.after(blink_count * 2 * interval + 20, lambda: apply_style(False))
        self._guide_blink_jobs.append(restore_job)

    def _cancel_guide_blinks(self):
        while self._guide_blink_jobs:
            job = self._guide_blink_jobs.pop()
            try:
                self.root.after_cancel(job)
            except Exception:
                pass

    def open_github_project(self):
        self._guide_action_flags["opened_github"] = True
        webbrowser.open("https://github.com/arenascats/MarukoToolbox-Rewrite")

    def _app_settings_path(self):
        return self._app_data_root_path() / "app_settings.json"

    def _default_output_dir(self, subdir=""):
        base = DEFAULT_OUTPUT_DIR
        return base / subdir if subdir else base

    def _app_data_root_path(self):
        if os.name == "nt":
            appdata = os.environ.get("APPDATA", "")
            base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
        elif self._is_macos():
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "marurebuild"

    def _preset_storage_dir(self):
        return self._app_data_root_path() / "presets"

    def _export_log_dir(self):
        return self._app_data_root_path() / "logs"

    @staticmethod
    def _safe_filename(name):
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name))
        cleaned = cleaned.strip().strip(".")
        return cleaned or "preset"

    def _output_dir_specs(self):
        return [
            ("视频输出目录", self.output_dir, self._default_output_dir()),
            ("音频输出目录", self.audio_output_dir, self._default_output_dir("audio")),
            ("常用输出目录", self.common_output_dir, self._default_output_dir("common")),
            ("字幕输出目录", self.subtitle_output_dir, self._default_output_dir("subtitles")),
            ("反挤压输出目录", self.anamorphic_output_dir, self._default_output_dir("anamorphic")),
            ("封装输出目录", self.mux_output_dir, self._default_output_dir("mux")),
            ("批量输出目录", self.batch_output_dir, self._default_output_dir("batch")),
            ("复古输出目录", self.retro_output_dir, self._default_output_dir("retro")),
            ("截图输出目录", self.screenshot_dir, self._default_output_dir("screenshots")),
            ("LUT 输出目录", self.lut_page_output, self._default_output_dir("lut_previews")),
        ]

    def _ensure_output_dirs_valid(self, show_message=True):
        fallback_messages = []
        for label, variable, fallback in self._output_dir_specs():
            raw = variable.get().strip()
            target = Path(raw) if raw else fallback
            try:
                target.mkdir(parents=True, exist_ok=True)
                variable.set(str(target))
            except Exception:
                try:
                    fallback.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                variable.set(str(fallback))
                fallback_messages.append(f"{label} 已改为 {fallback}")
        if show_message and fallback_messages:
            messagebox.showwarning("输出目录已重置", "检测到无效输出路径，已回退到默认目录：\n" + "\n".join(fallback_messages))

    def _is_shift_pressed(self):
        if os.name != "nt":
            return False
        try:
            return bool(ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000)
        except Exception:
            return False

    def _ask_restore_default_window_settings_on_startup(self):
        if not self._is_shift_pressed():
            return False
        return messagebox.askyesno(
            "恢复默认窗口设置",
            "检测到启动时按住 Shift。\n是否恢复默认窗口设置（窗口大小和位置）？",
        )

    def _window_geometry_snapshot(self):
        try:
            self.root.update_idletasks()
        except Exception:
            pass
        state = "normal"
        try:
            state = self.root.state()
        except Exception:
            state = "normal"
        if state not in {"normal", "zoomed"}:
            state = "normal"
        geometry = ""
        try:
            geometry = self.root.winfo_geometry()
        except Exception:
            geometry = ""
        return geometry, state

    def _apply_saved_main_window_settings(self, data):
        if self._restore_default_window_settings_on_startup:
            return
        geometry = data.get("main_window_geometry", "")
        if isinstance(geometry, str):
            text = geometry.strip()
            if re.match(r"^\d+x\d+([+-]\d+){2}$", text) or re.match(r"^\d+x\d+$", text):
                try:
                    self.root.geometry(text)
                except Exception:
                    pass
        if data.get("main_window_state") == "zoomed":
            try:
                self.root.state("zoomed")
            except Exception:
                pass

    def _handle_delete_key(self, event):
        if hasattr(self, "notebook") and self.notebook.select() == str(self.tasks_tab):
            self.remove_selected_tasks()

    def _normalize_user_video_presets(self, presets):
        normalized = []
        for item in presets or []:
            if not isinstance(item, dict):
                continue
            name = self._fix_mojibake_text(str(item.get("name", "")).strip())
            settings = self._fix_mojibake_value(item.get("settings"))
            if not name or not isinstance(settings, dict):
                continue
            normalized.append({"name": name, "settings": dict(settings)})
        return normalized

    def _builtin_video_presets(self):
        presets = {}
        for name, item in BATCH_PRESETS.items():
            presets[name] = {
                "encoder_name": self._resolve_platform_encoder(item["encoder"]),
                "resolution_name": item["resolution"],
                "cq_value": item["cq"],
                "audio_mode": item["audio"],
                "audio_bitrate": item["audio_bitrate"],
                "muxer_name": item["muxer"],
            }
        return presets

    def _find_user_video_preset_index(self, name):
        for index, item in enumerate(self.user_video_presets):
            if item["name"] == name:
                return index
        return -1

    def _upsert_user_video_preset(self, name, settings):
        index = self._find_user_video_preset_index(name)
        payload = {"name": name, "settings": dict(settings)}
        if index >= 0:
            self.user_video_presets[index] = payload
        else:
            self.user_video_presets.append(payload)

    def _user_video_preset_names(self):
        return [item["name"] for item in self.user_video_presets]

    def _write_user_preset_backup(self, name, settings):
        folder = self._preset_storage_dir()
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{self._safe_filename(name)}.json"
        target = folder / filename
        payload = dict(settings)
        payload["preset_title"] = name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def _sync_all_user_preset_backups(self):
        folder = self._preset_storage_dir()
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*.json"):
            try:
                file.unlink()
            except Exception:
                pass
        for item in self.user_video_presets:
            try:
                self._write_user_preset_backup(item["name"], item["settings"])
            except Exception:
                pass

    def _load_user_preset_backups(self):
        folder = self._preset_storage_dir()
        if not folder.exists():
            return []
        presets = []
        for file in sorted(folder.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            name = self._fix_mojibake_text(str(data.get("preset_title", file.stem)).strip())
            settings = self._fix_mojibake_value(dict(data))
            settings.pop("preset_title", None)
            if not name:
                continue
            presets.append({"name": name, "settings": settings})
        return self._normalize_user_video_presets(presets)

    def open_settings_window(self):
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title("设置")
        self._set_window_geometry(window, "620x760")
        window.minsize(560, 520)
        window.resizable(True, True)
        shell = ttk.Frame(window)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)
        canvas = Canvas(shell, highlightthickness=0, bg=self.COLORS["bg"], bd=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        box = ttk.Frame(canvas, padding=16)
        box_id = canvas.create_window((0, 0), window=box, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        box.bind("<Configure>", lambda event: self._schedule_scrollregion_update(canvas))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(box_id, width=event.width))
        box.columnconfigure(0, weight=1)
        initial_settings_snapshot = self._settings_window_snapshot()

        def close_settings_by_x():
            if self._settings_window_snapshot() == initial_settings_snapshot:
                window.destroy()
                return
            choice = messagebox.askyesnocancel("保存设置", "是否保存当前设置改动？", parent=window)
            if choice is None:
                return
            if choice:
                self._apply_app_settings()
            window.destroy()

        def apply_and_close():
            self._apply_app_settings()
            window.destroy()

        ui = ttk.LabelFrame(box, text="界面设置", padding=12)
        ui.grid(row=0, column=0, sticky="ew")
        ui.columnconfigure(1, weight=1)
        ttk.Label(ui, text="界面语言").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(ui, textvariable=self.interface_language, values=["中文", "English"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(ui, text="界面大小").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(ui, textvariable=self.interface_size, values=["小", "中", "大"], state="readonly").grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Checkbutton(ui, text="托盘模式：点击 X 后后台继续运行", variable=self.tray_mode).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(ui, text=f"当前版本 {self.app_version}", style="Hint.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        order_box = ttk.LabelFrame(box, text="页面排序", padding=12)
        order_box.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        order_box.columnconfigure(0, weight=1)
        self.tab_order_list = self._create_work_listbox(order_box, height=6, exportselection=False)
        self.tab_order_list.grid(row=0, column=0, rowspan=3, sticky="ew")
        for name in self.tab_order:
            self.tab_order_list.insert(END, name)
        ttk.Button(order_box, text="上移", command=lambda: self._move_tab_order_item(-1)).grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 4))
        ttk.Button(order_box, text="下移", command=lambda: self._move_tab_order_item(1)).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Button(order_box, text="默认顺序", command=self._reset_tab_order_list).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))

        user_preset_box = ttk.LabelFrame(box, text="用户预设管理", padding=12)
        user_preset_box.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        user_preset_box.columnconfigure(0, weight=1)
        self.user_preset_list = self._create_work_listbox(user_preset_box, height=6, exportselection=False)
        self.user_preset_list.grid(row=0, column=0, rowspan=3, sticky="ew")
        preset_actions = ttk.Frame(user_preset_box)
        preset_actions.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(8, 0))
        ttk.Button(preset_actions, text="导入", command=self.import_video_settings).grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(preset_actions, text="导出", command=self.export_selected_user_video_preset).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(preset_actions, text="删除", command=self.delete_selected_user_video_preset).grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Button(preset_actions, text="上移", command=lambda: self.move_selected_user_video_preset(-1)).grid(row=3, column=0, sticky="ew", pady=4)
        ttk.Button(preset_actions, text="下移", command=lambda: self.move_selected_user_video_preset(1)).grid(row=4, column=0, sticky="ew", pady=(4, 0))
        self._refresh_user_preset_listbox()

        features = ttk.LabelFrame(box, text="功能设置", padding=12)
        features.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        features.columnconfigure(1, weight=1)
        ttk.Label(features, text="预览播放器").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(features, textvariable=self.default_player).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=5)
        ttk.Button(features, text="选择…", command=self.choose_default_player).grid(row=0, column=2, pady=5)
        ttk.Label(features, text="为空时调用系统默认播放器。", style="Hint.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))
        ttk.Checkbutton(features, text="高级模式显示所有编码器和进阶参数", variable=self.advanced_encoders, command=self.refresh_encoder_choices).grid(row=2, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="启用文件拖入（需要 tkinterdnd2 支持）", variable=self.enable_drag_drop, command=self._setup_drag_drop).grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="覆盖前提醒", variable=self.confirm_overwrite).grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="导出前二次确认视频设置", variable=self.confirm_export_settings).grid(row=5, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="任务完成后打开输出目录", variable=self.auto_open_output).grid(row=6, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="启动时恢复上次退出页面", variable=self.restore_last_page_on_startup).grid(row=7, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="任务结束提示音", variable=self.play_finish_sound).grid(row=8, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Checkbutton(features, text="任务全部完成后自动关机", variable=self.shutdown_when_finished).grid(row=9, column=0, columnspan=3, sticky="w", pady=5)
        ttk.Label(features, text="导出文件名格式").grid(row=10, column=0, sticky="w", pady=5)
        ttk.Combobox(features, textvariable=self.export_filename_format, values=["原名_标签", "标签_原名", "仅原名"], state="readonly").grid(row=10, column=1, columnspan=2, sticky="ew", pady=5)

        device = ttk.LabelFrame(box, text="编码器偏好", padding=12)
        device.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        device.columnconfigure(1, weight=1)
        ttk.Label(device, text="编码器优先级").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(device, textvariable=self.preferred_device, values=["优先 GPU", "优先 CPU"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)

        codec = ttk.LabelFrame(box, text="x264 设置", padding=12)
        codec.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        codec.columnconfigure(1, weight=1)
        ttk.Label(codec, text="优先级").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(codec, textvariable=self.x264_priority, values=["低", "正常", "高"], state="readonly").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(codec, text="线程数量").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Spinbox(codec, from_=0, to=64, increment=1, textvariable=self.x264_threads).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(codec, text="自定义命令行").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(codec, textvariable=self.x264_command).grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(codec, text="线程 0 表示由 x264 自动决定；自定义命令可用于覆盖当前视频页命令。", style="Hint.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        actions = ttk.Frame(box)
        actions.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        actions.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(actions, text="还原默认设置", command=self.restore_default_settings).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="查看日志", command=self.show_log_window).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(actions, text="删除日志", command=self.clear_log).grid(row=0, column=2, sticky="ew", padx=(6, 0))
        ttk.Button(box, text="应用并保存", style="Accent.TButton", command=apply_and_close).grid(row=7, column=0, sticky="ew", pady=(14, 0))
        window.protocol("WM_DELETE_WINDOW", close_settings_by_x)
        self._bind_scroll_to_widget_tree(shell, canvas, bind_keys=True)
        self._bind_scroll_keys(window, canvas)

    def _settings_window_snapshot(self):
        tab_order = list(self.tab_order)
        if hasattr(self, "tab_order_list"):
            try:
                tab_order = [self.tab_order_list.get(index) for index in range(self.tab_order_list.size())]
            except Exception:
                tab_order = list(self.tab_order)
        return {
            "interface_language": self.interface_language.get(),
            "interface_size": self.interface_size.get(),
            "tray_mode": self.tray_mode.get(),
            "tab_order": tab_order,
            "user_video_presets": self._settings_snapshot_presets(),
            "default_player": self.default_player.get(),
            "advanced_encoders": self.advanced_encoders.get(),
            "enable_drag_drop": self.enable_drag_drop.get(),
            "confirm_overwrite": self.confirm_overwrite.get(),
            "confirm_export_settings": self.confirm_export_settings.get(),
            "auto_open_output": self.auto_open_output.get(),
            "restore_last_page_on_startup": self.restore_last_page_on_startup.get(),
            "play_finish_sound": self.play_finish_sound.get(),
            "shutdown_when_finished": self.shutdown_when_finished.get(),
            "export_filename_format": self.export_filename_format.get(),
            "preferred_device": self.preferred_device.get(),
            "x264_priority": self.x264_priority.get(),
            "x264_threads": self.x264_threads.get(),
            "x264_command": self.x264_command.get(),
        }

    def _settings_snapshot_presets(self):
        return json.dumps(self.user_video_presets, ensure_ascii=False, sort_keys=True)

    def _apply_preferred_encoder(self):
        self.encoder_name.set(self._preferred_video_encoder_name(prefer_gpu=self.preferred_device.get() != "优先 CPU"))
        self.refresh_encoder_choices()

    def _apply_app_settings(self):
        if hasattr(self, "tab_order_list"):
            self.tab_order = [self.tab_order_list.get(index) for index in range(self.tab_order_list.size())]
            self._apply_tab_order()
        self._apply_preferred_encoder()
        self._apply_theme(self.theme_mode.get(), persist=False)
        self._save_app_settings()
        self._log("设置已保存。")

    def _move_tab_order_item(self, direction):
        if not hasattr(self, "tab_order_list"):
            return
        selection = self.tab_order_list.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = max(0, min(self.tab_order_list.size() - 1, index + direction))
        if index == new_index:
            return
        value = self.tab_order_list.get(index)
        self.tab_order_list.delete(index)
        self.tab_order_list.insert(new_index, value)
        self.tab_order_list.selection_set(new_index)

    def _reset_tab_order_list(self):
        if not hasattr(self, "tab_order_list"):
            return
        default_order = ["视频", "音频", "常用", "字幕", "AVS", "反挤压", "封装", "复古", "Lut调色", "批量压缩", "MediaInfo", "任务管理"]
        self.tab_order_list.delete(0, END)
        for name in default_order:
            self.tab_order_list.insert(END, name)

    def choose_default_player(self):
        if self._is_macos():
            path = filedialog.askdirectory(title="选择预览播放器（请选择 .app 应用）")
            if path and not path.lower().endswith(".app"):
                messagebox.showwarning("选择无效", "macOS 请直接选择播放器的 .app 应用。")
                return
        else:
            filetypes = [("程序", "*.exe"), ("所有文件", "*.*")] if os.name == "nt" else [("所有文件", "*.*")]
            path = filedialog.askopenfilename(title="选择预览播放器", filetypes=filetypes)
        if path:
            self.default_player.set(path)

    def restore_default_settings(self):
        if not messagebox.askyesno("还原默认设置", "确认还原界面、功能和 x264 设置为默认值？"):
            return
        self.interface_language.set("中文")
        self.interface_size.set("小")
        self.tray_mode.set(True)
        self.x264_priority.set("正常")
        self.x264_threads.set(0)
        self.x264_command.set("")
        self.default_player.set("")
        self.export_filename_format.set("原名_标签")
        self.preferred_device.set("优先 GPU")
        self.enable_drag_drop.set(True)
        self.confirm_overwrite.set(True)
        self.confirm_export_settings.set(False)
        self.auto_open_output.set(False)
        self.shutdown_when_finished.set(False)
        self.play_finish_sound.set(True)
        self.restore_last_page_on_startup.set(True)
        self.advanced_encoders.set(False)
        self.auto_fallback_cpu_h264.set(True)
        self.common_channel_copy_mode.set("左复制到右")
        self.theme_mode.set("日间模式")
        self.refresh_encoder_choices()
        self._apply_theme(self.theme_mode.get(), persist=False)
        self._save_app_settings()
        self._log("已还原默认设置。")

    def show_log_window(self):
        metrics = self._ui_metrics()
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title("运行日志")
        self._set_window_geometry(window, "760x460")
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = Text(frame, wrap="word", background=self.COLORS["entry_bg"], foreground=self.COLORS["text"], font=("Microsoft YaHei UI", metrics["font"]))
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)
        lines = [self.log.get(index) for index in range(self.log.size())] if hasattr(self, "log") else []
        text.insert("1.0", "\n".join(lines) if lines else "暂无日志。")
        text.configure(state="disabled")

    def clear_log(self):
        if messagebox.askyesno("删除日志", "确认清空当前运行日志？"):
            if hasattr(self, "log"):
                self.log.delete(0, END)
            self._log("日志已清空。")

    def _save_app_settings(self):
        window_geometry, window_state = self._window_geometry_snapshot()
        last_active_tab = ""
        if hasattr(self, "notebook"):
            try:
                tab_id = self.notebook.select()
                if tab_id:
                    last_active_tab = self.notebook.tab(tab_id, "text")
            except Exception:
                last_active_tab = ""
        data = {
            "theme_mode": self.theme_mode.get(),
            "first_run_guide_completed": self.first_run_guide_completed,
            "interface_language": self.interface_language.get(),
            "interface_size": self.interface_size.get(),
            "tray_mode": self.tray_mode.get(),
            "user_video_presets": self.user_video_presets,
            "x264_priority": self.x264_priority.get(),
            "x264_threads": self.x264_threads.get(),
            "x264_command": self.x264_command.get(),
            "default_player": self.default_player.get(),
            "export_filename_format": self.export_filename_format.get(),
            "preferred_device": self.preferred_device.get(),
            "enable_drag_drop": self.enable_drag_drop.get(),
            "confirm_overwrite": self.confirm_overwrite.get(),
            "confirm_export_settings": self.confirm_export_settings.get(),
            "auto_open_output": self.auto_open_output.get(),
            "shutdown_when_finished": self.shutdown_when_finished.get(),
            "play_finish_sound": self.play_finish_sound.get(),
            "restore_last_page_on_startup": self.restore_last_page_on_startup.get(),
            "advanced_encoders": self.advanced_encoders.get(),
            "auto_fallback_cpu_h264": self.auto_fallback_cpu_h264.get(),
            "last_active_tab": last_active_tab,
            "tab_order": self.tab_order,
            "audio_output_mode": self.audio_output_mode.get(),
            "audio_output_dir": self.audio_output_dir.get(),
            "audio_overwrite_source": self.audio_overwrite_source.get(),
            "video_settings": self._video_settings_dict(),
            "output_dir": self.output_dir.get(),
            "audio_encoder_name": self.audio_encoder_name.get(),
            "audio_page_bitrate": self.audio_page_bitrate.get(),
            "audio_sample_rate": self.audio_sample_rate.get(),
            "audio_channels": self.audio_channels.get(),
            "audio_normalize": self.audio_normalize.get(),
            "common_output_dir": self.common_output_dir.get(),
            "common_trim_start": self.common_trim_start.get(),
            "common_trim_end": self.common_trim_end.get(),
            "common_trim_encoder": self.common_trim_encoder.get(),
            "common_trim_muxer": self.common_trim_muxer.get(),
            "common_channel_copy_mode": self.common_channel_copy_mode.get(),
            "subtitle_output_dir": self.subtitle_output_dir.get(),
            "subtitle_output_format": self.subtitle_output_format.get(),
            "avs_video_path": self.avs_video_path.get(),
            "avs_subtitle_path": self.avs_subtitle_path.get(),
            "avs_output_path": self.avs_output_path.get(),
            "avs_enable_addborders": self.avs_enable_addborders.get(),
            "avs_border_left": self.avs_border_left.get(),
            "avs_border_top": self.avs_border_top.get(),
            "avs_border_right": self.avs_border_right.get(),
            "avs_border_bottom": self.avs_border_bottom.get(),
            "avs_enable_crop": self.avs_enable_crop.get(),
            "avs_crop_left": self.avs_crop_left.get(),
            "avs_crop_top": self.avs_crop_top.get(),
            "avs_crop_right": self.avs_crop_right.get(),
            "avs_crop_bottom": self.avs_crop_bottom.get(),
            "avs_enable_trim": self.avs_enable_trim.get(),
            "avs_trim_start": self.avs_trim_start.get(),
            "avs_trim_end": self.avs_trim_end.get(),
            "avs_enable_brightness": self.avs_enable_brightness.get(),
            "avs_brightness": self.avs_brightness.get(),
            "avs_enable_sharpen": self.avs_enable_sharpen.get(),
            "avs_sharpen_amount": self.avs_sharpen_amount.get(),
            "avs_enable_denoise": self.avs_enable_denoise.get(),
            "avs_denoise_strength": self.avs_denoise_strength.get(),
            "anamorphic_output_dir": self.anamorphic_output_dir.get(),
            "anamorphic_factor": self.anamorphic_factor.get(),
            "anamorphic_mode": self.anamorphic_mode.get(),
            "anamorphic_target_aspect": self.anamorphic_target_aspect.get(),
            "anamorphic_resolution": self.anamorphic_resolution.get(),
            "anamorphic_encoder_name": self.anamorphic_encoder_name.get(),
            "anamorphic_keep_audio": self.anamorphic_keep_audio.get(),
            "anamorphic_auto_crop": self.anamorphic_auto_crop.get(),
            "mux_output_dir": self.mux_output_dir.get(),
            "mux_merge_name": self.mux_merge_name.get(),
            "mux_merge_format": self.mux_merge_format.get(),
            "mux_convert_format": self.mux_convert_format.get(),
            "mux_audio_mode": self.mux_audio_mode.get(),
            "mux_audio_bitrate": self.mux_audio_bitrate.get(),
            "batch_input_dir": self.batch_input_dir.get(),
            "batch_output_dir": self.batch_output_dir.get(),
            "batch_preset_name": self.batch_preset_name.get(),
            "batch_keep_tree": self.batch_keep_tree.get(),
            "batch_include_audio": self.batch_include_audio.get(),
            "batch_vertical_mode": self.batch_vertical_mode.get(),
            "queue_parallel_jobs": self.queue_parallel_jobs.get(),
            "retro_output_dir": self.retro_output_dir.get(),
            "retro_format_name": self.retro_format_name.get(),
            "retro_resolution_name": self.retro_resolution_name.get(),
            "retro_bitrate": self.retro_bitrate.get(),
            "retro_audio_bitrate": self.retro_audio_bitrate.get(),
            "retro_deinterlace": self.retro_deinterlace.get(),
            "retro_denoise": self.retro_denoise.get(),
            "retro_remux_format": self.retro_remux_format.get(),
            "retro_remux_audio": self.retro_remux_audio.get(),
            "screenshot_dir": self.screenshot_dir.get(),
            "lut_page_video": self.lut_page_video.get(),
            "lut_page_folder": self.lut_page_folder.get(),
            "lut_page_output": self.lut_page_output.get(),
            "lut_page_time": self.lut_page_time.get(),
            "media_compare_frame_time": self.media_compare_frame_time.get(),
            "media_compare_generate_frames_on_export": self.media_compare_generate_frames_on_export.get(),
            "main_window_geometry": window_geometry,
            "main_window_state": window_state,
        }
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._sync_all_user_preset_backups()
        except Exception as exc:
            self._log(f"保存应用设置失败：{exc}")

    def _load_app_settings(self):
        source_path = self.settings_path
        if not source_path.exists():
            legacy_path = self.base_dir / "data" / "app_settings.json"
            if legacy_path.exists():
                source_path = legacy_path
            else:
                return
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._log(f"读取应用设置失败：{exc}")
            data = {}
        data = self._normalize_loaded_settings_data(data)
        self.theme_mode.set("黑暗模式" if data.get("theme_mode") == "黑暗模式" else "日间模式")
        self.first_run_guide_completed = bool(data.get("first_run_guide_completed", False))
        if not self._guide_enabled():
            self.first_run_guide_completed = True
        mapping = {
            "interface_language": self.interface_language,
            "interface_size": self.interface_size,
            "tray_mode": self.tray_mode,
            "x264_priority": self.x264_priority,
            "x264_threads": self.x264_threads,
            "x264_command": self.x264_command,
            "default_player": self.default_player,
            "export_filename_format": self.export_filename_format,
            "preferred_device": self.preferred_device,
            "enable_drag_drop": self.enable_drag_drop,
            "confirm_overwrite": self.confirm_overwrite,
            "confirm_export_settings": self.confirm_export_settings,
            "auto_open_output": self.auto_open_output,
            "shutdown_when_finished": self.shutdown_when_finished,
            "play_finish_sound": self.play_finish_sound,
            "restore_last_page_on_startup": self.restore_last_page_on_startup,
            "advanced_encoders": self.advanced_encoders,
            "auto_fallback_cpu_h264": self.auto_fallback_cpu_h264,
            "audio_output_mode": self.audio_output_mode,
            "audio_output_dir": self.audio_output_dir,
            "audio_overwrite_source": self.audio_overwrite_source,
            "output_dir": self.output_dir,
            "audio_encoder_name": self.audio_encoder_name,
            "audio_page_bitrate": self.audio_page_bitrate,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_channels": self.audio_channels,
            "audio_normalize": self.audio_normalize,
            "common_output_dir": self.common_output_dir,
            "common_trim_start": self.common_trim_start,
            "common_trim_end": self.common_trim_end,
            "common_trim_encoder": self.common_trim_encoder,
            "common_trim_muxer": self.common_trim_muxer,
            "common_channel_copy_mode": self.common_channel_copy_mode,
            "subtitle_output_dir": self.subtitle_output_dir,
            "subtitle_output_format": self.subtitle_output_format,
            "avs_video_path": self.avs_video_path,
            "avs_subtitle_path": self.avs_subtitle_path,
            "avs_output_path": self.avs_output_path,
            "avs_enable_addborders": self.avs_enable_addborders,
            "avs_border_left": self.avs_border_left,
            "avs_border_top": self.avs_border_top,
            "avs_border_right": self.avs_border_right,
            "avs_border_bottom": self.avs_border_bottom,
            "avs_enable_crop": self.avs_enable_crop,
            "avs_crop_left": self.avs_crop_left,
            "avs_crop_top": self.avs_crop_top,
            "avs_crop_right": self.avs_crop_right,
            "avs_crop_bottom": self.avs_crop_bottom,
            "avs_enable_trim": self.avs_enable_trim,
            "avs_trim_start": self.avs_trim_start,
            "avs_trim_end": self.avs_trim_end,
            "avs_enable_brightness": self.avs_enable_brightness,
            "avs_brightness": self.avs_brightness,
            "avs_enable_sharpen": self.avs_enable_sharpen,
            "avs_sharpen_amount": self.avs_sharpen_amount,
            "avs_enable_denoise": self.avs_enable_denoise,
            "avs_denoise_strength": self.avs_denoise_strength,
            "anamorphic_output_dir": self.anamorphic_output_dir,
            "anamorphic_factor": self.anamorphic_factor,
            "anamorphic_mode": self.anamorphic_mode,
            "anamorphic_target_aspect": self.anamorphic_target_aspect,
            "anamorphic_resolution": self.anamorphic_resolution,
            "anamorphic_encoder_name": self.anamorphic_encoder_name,
            "anamorphic_keep_audio": self.anamorphic_keep_audio,
            "anamorphic_auto_crop": self.anamorphic_auto_crop,
            "mux_output_dir": self.mux_output_dir,
            "mux_merge_name": self.mux_merge_name,
            "mux_merge_format": self.mux_merge_format,
            "mux_convert_format": self.mux_convert_format,
            "mux_audio_mode": self.mux_audio_mode,
            "mux_audio_bitrate": self.mux_audio_bitrate,
            "batch_input_dir": self.batch_input_dir,
            "batch_output_dir": self.batch_output_dir,
            "batch_preset_name": self.batch_preset_name,
            "batch_keep_tree": self.batch_keep_tree,
            "batch_include_audio": self.batch_include_audio,
            "batch_vertical_mode": self.batch_vertical_mode,
            "queue_parallel_jobs": self.queue_parallel_jobs,
            "retro_output_dir": self.retro_output_dir,
            "retro_format_name": self.retro_format_name,
            "retro_resolution_name": self.retro_resolution_name,
            "retro_bitrate": self.retro_bitrate,
            "retro_audio_bitrate": self.retro_audio_bitrate,
            "retro_deinterlace": self.retro_deinterlace,
            "retro_denoise": self.retro_denoise,
            "retro_remux_format": self.retro_remux_format,
            "retro_remux_audio": self.retro_remux_audio,
            "screenshot_dir": self.screenshot_dir,
            "lut_page_video": self.lut_page_video,
            "lut_page_folder": self.lut_page_folder,
            "lut_page_output": self.lut_page_output,
            "lut_page_time": self.lut_page_time,
            "media_compare_frame_time": self.media_compare_frame_time,
            "media_compare_generate_frames_on_export": self.media_compare_generate_frames_on_export,
        }
        for key, variable in mapping.items():
            if key in data:
                variable.set(data[key])
        if isinstance(data.get("video_settings"), dict):
            self._apply_video_settings_dict(data["video_settings"])
        self.user_video_presets = self._normalize_user_video_presets(data.get("user_video_presets"))
        if not self.user_video_presets:
            self.user_video_presets = self._load_user_preset_backups()
        if isinstance(data.get("tab_order"), list):
            valid = [name for name in data["tab_order"] if name in self.tab_frames]
            missing = [name for name in self.tab_order if name not in valid]
            self.tab_order = valid + missing
            self._apply_tab_order()
        if self.restore_last_page_on_startup.get():
            last_active_tab = str(data.get("last_active_tab", "")).strip()
            if last_active_tab and last_active_tab in self.tab_frames:
                self.notebook.select(self.tab_frames[last_active_tab])
        self._normalize_audio_selector_values()
        self._apply_saved_main_window_settings(data)
        self.refresh_encoder_choices()

    def _normalize_loaded_settings_data(self, data):
        if not isinstance(data, dict):
            return {}
        fixed = {}
        for key, value in data.items():
            fixed_key = self._fix_mojibake_text(key)
            fixed[fixed_key] = self._fix_mojibake_value(value)
        if isinstance(fixed.get("tab_order"), list):
            fixed["tab_order"] = [self._fix_mojibake_text(item) for item in fixed["tab_order"]]
        if isinstance(fixed.get("video_settings"), dict):
            video_settings = {}
            for key, value in fixed["video_settings"].items():
                video_settings[self._fix_mojibake_text(key)] = self._fix_mojibake_value(value)
            fixed["video_settings"] = video_settings
        if isinstance(fixed.get("user_video_presets"), list):
            normalized_presets = []
            for item in fixed["user_video_presets"]:
                if not isinstance(item, dict):
                    continue
                name = self._fix_mojibake_text(item.get("name", ""))
                settings = item.get("settings")
                if isinstance(settings, dict):
                    settings = {self._fix_mojibake_text(k): self._fix_mojibake_value(v) for k, v in settings.items()}
                normalized_presets.append({"name": name, "settings": settings})
            fixed["user_video_presets"] = normalized_presets
        return fixed

    def _fix_mojibake_value(self, value):
        if isinstance(value, str):
            return self._fix_mojibake_text(value)
        if isinstance(value, list):
            return [self._fix_mojibake_value(item) for item in value]
        if isinstance(value, dict):
            return {self._fix_mojibake_text(key): self._fix_mojibake_value(item) for key, item in value.items()}
        return value

    def _fix_mojibake_text(self, text):
        if not isinstance(text, str):
            return text
        fixed = text.strip()
        for broken, corrected in self.MOJIBAKE_TEXT_MAP.items():
            if broken in fixed:
                fixed = fixed.replace(broken, corrected)
        return fixed

    def _normalize_audio_selector_values(self):
        sample_rate = self.audio_sample_rate.get().strip()
        channels = self.audio_channels.get().strip()
        if sample_rate == "":
            self.audio_sample_rate.set("自动")
        elif sample_rate not in {"自动", "44100", "48000", "96000"}:
            self.audio_sample_rate.set("48000")
        if channels == "":
            self.audio_channels.set("自动")
        elif channels not in {"自动", "1", "2", "6"}:
            self.audio_channels.set("2")

    def _on_main_close(self):
        if self._has_running_tasks():
            confirm = messagebox.askyesno(
                "确认退出",
                "当前仍有任务在运行。\n关闭窗口会终止正在进行的任务。\n\n确定继续退出吗？",
            )
            if not confirm:
                return
            self.stop_requested = True
            for job in self.active_ffmpeg_jobs.values():
                job["cancel"] = True
                process = job.get("process")
                if process and process.poll() is None:
                    try:
                        process.terminate()
                    except Exception:
                        pass
        self._save_app_settings()
        if self.tray_mode.get():
            self.root.withdraw()
            self._log("托盘模式已启用：窗口已隐藏，任务会继续在后台运行。")
            return
        self.root.destroy()

    def _has_running_tasks(self):
        active_worker_alive = any(worker.is_alive() for worker in self.active_workers.values())
        active_process_alive = any(
            (job.get("process") is not None and job.get("process").poll() is None)
            for job in self.active_ffmpeg_jobs.values()
        )
        return active_worker_alive or active_process_alive

    def _setup_drag_drop(self):
        if not self.enable_drag_drop.get():
            return
        try:
            from tkinterdnd2 import DND_FILES
        except Exception:
            self.messages.put(("log", "拖入增强未启用：如需文件拖拽，请安装 tkinterdnd2。"))
            return
        for widget, target in (
            (self.file_list, "video"),
            (getattr(self, "audio_file_list", None), "audio"),
            (getattr(self, "retro_file_list", None), "retro"),
            (getattr(self, "media_info_text", None), "mediainfo"),
        ):
            if not widget:
                continue
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", lambda event, kind=target: self._handle_drop(event.data, kind))
            except Exception as exc:
                self.messages.put(("log", f"拖入绑定失败：{exc}"))

    def _handle_drop(self, data, kind):
        paths = self.root.tk.splitlist(data)
        if kind == "audio":
            self._add_audio_paths(paths)
        elif kind == "retro":
            self._add_retro_paths(paths)
        elif kind == "mediainfo":
            self._set_mediainfo_path(paths)
        else:
            self._add_paths(paths)

    def open_player_preview(self):
        source = self._preview_source()
        if not source:
            messagebox.showwarning("没有视频", "请先添加视频，最好在列表中选中一个要预览的视频。")
            return
        try:
            source_path = Path(source)
            player = self.default_player.get().strip()
            if player:
                if self._is_macos():
                    player_path = Path(player).expanduser()
                    if player.lower().endswith(".app") or player_path.is_dir() or ("/" not in player and not player_path.exists()):
                        subprocess.Popen(["open", "-a", player, str(source_path)])
                    else:
                        subprocess.Popen([str(player_path), str(source_path)])
                else:
                    subprocess.Popen([player, str(source_path)], creationflags=self._command_creationflags())
            elif os.name == "nt":
                os.startfile(str(source_path))
            elif self._is_macos():
                subprocess.Popen(["open", str(source_path)])
            else:
                subprocess.Popen(["xdg-open", str(source_path)])
        except Exception as exc:
            messagebox.showerror("播放失败", f"无法调用系统播放器：{exc}")
        return
        self.preview_source_path = Path(source)
        self.preview_duration = ffmpeg.duration_seconds(self.preview_source_path)
        self.preview_seconds.set(0.0)
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.lift()
            self.render_preview_frame()
            return
        self.preview_window = Toplevel(self.root)
        self._set_window_icon(self.preview_window)
        self.preview_window.title(f"播放预览 - {self.preview_source_path.name}")
        self._set_window_geometry(self.preview_window, "1040x720")
        self.preview_window.columnconfigure(0, weight=1)
        self.preview_window.rowconfigure(0, weight=1)
        self.preview_window.protocol("WM_DELETE_WINDOW", self.close_player_preview)
        self.preview_window.bind("<space>", lambda event: self.toggle_preview_playback())
        self.preview_window.bind("<Left>", lambda event: self.seek_preview(-5))
        self.preview_window.bind("<Right>", lambda event: self.seek_preview(5))
        self.preview_window.bind("<Control-Left>", lambda event: self.seek_preview(-30))
        self.preview_window.bind("<Control-Right>", lambda event: self.seek_preview(30))
        self.preview_window.bind("<Home>", lambda event: self.seek_preview_to(0))
        self.preview_window.bind("<End>", lambda event: self.seek_preview_to(self.preview_duration))
        self.preview_window.bind("<Key-s>", lambda event: self.save_current_screenshot())
        self.preview_window.bind("<Key-o>", lambda event: self.choose_screenshot_dir())

        body = ttk.Frame(self.preview_window, padding=12)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.player_image_label = ttk.Label(body, text="正在生成预览帧...", anchor="center")
        self.player_image_label.grid(row=0, column=0, sticky="nsew")

        controls = ttk.Frame(body)
        controls.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        controls.columnconfigure(4, weight=1)
        ttk.Button(controls, text="后退 5s", command=lambda: self.seek_preview(-5)).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(controls, text="播放/暂停", command=self.toggle_preview_playback).grid(row=0, column=1, padx=6)
        ttk.Button(controls, text="前进 5s", command=lambda: self.seek_preview(5)).grid(row=0, column=2, padx=6)
        ttk.Button(controls, text="截图", command=self.save_current_screenshot).grid(row=0, column=3, padx=6)
        self.preview_time_label = ttk.Label(controls, text="00:00 / 00:00")
        self.preview_time_label.grid(row=0, column=4, sticky="e")

        slider = ttk.Scale(
            body,
            from_=0,
            to=max(self.preview_duration, 1),
            orient=HORIZONTAL,
            variable=self.preview_seconds,
            command=self._on_preview_slider,
        )
        slider.grid(row=2, column=0, sticky="ew", pady=8)

        save_row = ttk.Frame(body)
        save_row.grid(row=3, column=0, sticky="ew")
        save_row.columnconfigure(1, weight=1)
        ttk.Label(save_row, text="截图目录").grid(row=0, column=0, sticky="w")
        ttk.Entry(save_row, textvariable=self.screenshot_dir).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(save_row, text="选择", command=self.choose_screenshot_dir).grid(row=0, column=2)
        ttk.Label(
            body,
            text="快捷键：空格播放/暂停，←/→ 跳 5 秒，Ctrl+←/→ 跳 30 秒，Home/End 到首尾，S 截图，O 选择截图目录。",
            style="Hint.TLabel",
        ).grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.render_preview_frame()

    def close_player_preview(self):
        self.preview_playing = False
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
            self.preview_after_id = None
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.destroy()
        self.preview_window = None

    def render_preview_frame(self):
        if not self.preview_source_path:
            return
        self.preview_frame_path.parent.mkdir(parents=True, exist_ok=True)
        if self.preview_frame_path.exists():
            try:
                self.preview_frame_path.unlink()
            except OSError:
                pass
        seconds = self._clamp_preview_time(self.preview_seconds.get())
        self.preview_seconds.set(seconds)
        output = ffmpeg.run_capture(ffmpeg.build_frame_command(self.preview_source_path, self.preview_frame_path, seconds, self._settings()))
        if self.preview_frame_path.exists() and self.preview_window and self.preview_window.winfo_exists():
            self.player_preview_image = PhotoImage(file=str(self.preview_frame_path))
            self.player_image_label.configure(image=self.player_preview_image, text="")
            self._update_preview_time_label()
        elif output:
            self._log("预览帧生成失败：" + output)

    def toggle_preview_playback(self):
        if not (self.preview_window and self.preview_window.winfo_exists()):
            return
        self.preview_playing = not self.preview_playing
        if self.preview_playing:
            self._tick_preview_playback()

    def _tick_preview_playback(self):
        if not self.preview_playing:
            return
        next_time = self.preview_seconds.get() + 1
        if self.preview_duration and next_time >= self.preview_duration:
            next_time = self.preview_duration
            self.preview_playing = False
        self.preview_seconds.set(self._clamp_preview_time(next_time))
        self.render_preview_frame()
        if self.preview_playing:
            self.preview_after_id = self.root.after(1000, self._tick_preview_playback)

    def seek_preview(self, delta):
        if not (self.preview_window and self.preview_window.winfo_exists()):
            return
        self.seek_preview_to(self.preview_seconds.get() + delta)

    def seek_preview_to(self, seconds):
        if not (self.preview_window and self.preview_window.winfo_exists()):
            return
        self.preview_seconds.set(self._clamp_preview_time(seconds))
        self.render_preview_frame()

    def _on_preview_slider(self, value):
        if not (self.preview_window and self.preview_window.winfo_exists()):
            return
        try:
            self.preview_seconds.set(self._clamp_preview_time(float(value)))
        except ValueError:
            return
        if not self.preview_playing:
            self.render_preview_frame()

    def choose_screenshot_dir(self):
        folder = filedialog.askdirectory(title="选择截图保存目录")
        if folder:
            self.screenshot_dir.set(folder)

    def save_current_screenshot(self):
        if not self.preview_source_path:
            messagebox.showwarning("没有预览视频", "请先打开播放预览窗口。")
            return
        screenshot_dir = Path(self.screenshot_dir.get()).resolve()
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        seconds = self._clamp_preview_time(self.preview_seconds.get())
        target = screenshot_dir / f"{self.preview_source_path.stem}_{int(seconds):06d}s_{timestamp}.jpg"
        output = ffmpeg.run_capture(ffmpeg.build_screenshot_command(self.preview_source_path, target, seconds, self._settings()))
        if target.exists():
            self._log(f"截图已保存：{target}")
        else:
            self._log("截图失败：" + output)

    def _clamp_preview_time(self, seconds):
        seconds = max(0.0, float(seconds))
        if self.preview_duration:
            return min(seconds, self.preview_duration)
        return seconds

    def _update_preview_time_label(self):
        if hasattr(self, "preview_time_label"):
            current = self._format_clock(self.preview_seconds.get())
            total = self._format_clock(self.preview_duration)
            self.preview_time_label.configure(text=f"{current} / {total}")

    def add_files(self):
        paths = filedialog.askopenfilenames(title="选择视频文件", filetypes=VIDEO_FILETYPES)
        self._add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if not folder:
            return
        paths = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in VIDEO_EXTENSIONS]
        self._add_paths(paths)

    def _add_paths(self, paths):
        existing = set(self.files)
        for path in self._expand_paths(paths, VIDEO_EXTENSIONS):
            full = str(path.resolve())
            if full not in existing:
                self.files.append(full)
                self.file_list.insert(END, full)
                existing.add(full)
        self._log(f"已添加 {len(self.files)} 个视频")

    def remove_selected(self):
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            del self.files[index]

    def clear_files(self):
        self.files.clear()
        self.file_list.delete(0, END)

    def choose_output_dir(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_dir.set(folder)

    def choose_common_trim_video(self):
        path = filedialog.askopenfilename(title="选择要截取的视频", filetypes=VIDEO_FILETYPES)
        if path:
            self.common_trim_video.set(path)

    def choose_common_output_dir(self):
        folder = filedialog.askdirectory(title="选择常用功能输出目录")
        if folder:
            self.common_output_dir.set(folder)

    def choose_subtitle_source(self):
        path = filedialog.askopenfilename(title="选择带字幕的视频文件", filetypes=VIDEO_FILETYPES)
        if path:
            self.subtitle_source.set(path)
            self.load_subtitle_tracks()

    def choose_subtitle_output_dir(self):
        folder = filedialog.askdirectory(title="选择字幕封装输出目录")
        if folder:
            self.subtitle_output_dir.set(folder)

    def choose_avs_video(self):
        path = filedialog.askopenfilename(title="选择 AVS 视频源", filetypes=VIDEO_FILETYPES + [("所有文件", "*.*")])
        if path:
            self.avs_video_path.set(path)

    def choose_avs_subtitle(self):
        path = filedialog.askopenfilename(title="选择 AVS 字幕文件", filetypes=[("字幕文件", "*.ass *.ssa *.srt *.vtt *.sub"), ("所有文件", "*.*")])
        if path:
            self.avs_subtitle_path.set(path)

    def choose_avs_output(self):
        folder = filedialog.askdirectory(title="选择 AVS 输出目录")
        if folder:
            self.avs_output_path.set(folder)

    def open_output_dir(self, variable):
        folder = variable.get().strip()
        if not folder:
            messagebox.showwarning("无法打开目录", "请先设置输出目录。")
            return
        try:
            path = Path(folder).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            self._open_folder(path)
        except Exception as exc:
            fallback = self._default_output_dir()
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                variable.set(str(fallback))
                messagebox.showwarning("输出目录已重置", f"系统找不到指定路径，已回退到：{fallback}")
                self._open_folder(fallback)
            except Exception:
                messagebox.showerror("打开目录失败", str(exc))

    def save_video_settings(self):
        default_name = f"用户预设 {len(self.user_video_presets) + 1}"
        name = simpledialog.askstring(
            "保存为用户预设",
            "请输入预设名称：",
            initialvalue=default_name,
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return
        existing = self._find_user_video_preset_index(name) >= 0
        if existing and not messagebox.askyesno("覆盖预设", f"用户预设“{name}”已存在，是否覆盖？"):
            return
        data = self._video_settings_dict()
        self._upsert_user_video_preset(name, data)
        try:
            self._write_user_preset_backup(name, data)
        except Exception as exc:
            self._log(f"写入用户预设备份失败：{exc}")
        self._refresh_user_preset_listbox(select_name=name)
        self._save_app_settings()
        self._log(f"用户预设已保存：{name}")

    def import_video_settings(self):
        path = filedialog.askopenfilename(title="导入压缩设置", filetypes=[("JSON 设置", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("文件内容不是有效设置对象。")
            suggested = Path(path).stem
            name = simpledialog.askstring("导入到用户预设", "请输入导入后的预设名称：", initialvalue=suggested)
            if not name:
                return
            name = name.strip()
            if not name:
                return
            existing = self._find_user_video_preset_index(name) >= 0
            if existing and not messagebox.askyesno("覆盖预设", f"用户预设“{name}”已存在，是否覆盖？"):
                return
            self._upsert_user_video_preset(name, data)
            try:
                self._write_user_preset_backup(name, data)
            except Exception as exc:
                self._log(f"写入用户预设备份失败：{exc}")
            self._refresh_user_preset_listbox(select_name=name)
            self._save_app_settings()
            self._log(f"用户预设已导入：{name}")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def export_selected_user_video_preset(self):
        if not hasattr(self, "user_preset_list"):
            return
        selection = self.user_preset_list.curselection()
        if not selection:
            messagebox.showwarning("没有选择", "请先在“用户预设管理”里选择一个预设。")
            return
        index = selection[0]
        preset = self.user_video_presets[index]
        path = filedialog.asksaveasfilename(
            title="导出用户预设",
            initialfile=f"{preset['name']}.json",
            defaultextension=".json",
            filetypes=[("JSON 设置", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        payload = dict(preset["settings"])
        payload["preset_title"] = preset["name"]
        try:
            Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            backup_path = self._write_user_preset_backup(preset["name"], preset["settings"])
            self._log(f"用户预设已导出：{path}")
            self._log(f"用户预设副本已保存：{backup_path}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def delete_selected_user_video_preset(self):
        if not hasattr(self, "user_preset_list"):
            return
        selection = self.user_preset_list.curselection()
        if not selection:
            messagebox.showwarning("没有选择", "请先在“用户预设管理”里选择一个预设。")
            return
        index = selection[0]
        name = self.user_video_presets[index]["name"]
        if not messagebox.askyesno("删除用户预设", f"确认删除用户预设“{name}”？"):
            return
        del self.user_video_presets[index]
        self._sync_all_user_preset_backups()
        self._refresh_user_preset_listbox()
        self._save_app_settings()
        self._log(f"已删除用户预设：{name}")

    def move_selected_user_video_preset(self, direction):
        if not hasattr(self, "user_preset_list"):
            return
        selection = self.user_preset_list.curselection()
        if not selection:
            messagebox.showwarning("没有选择", "请先在“用户预设管理”里选择一个预设。")
            return
        index = selection[0]
        target = max(0, min(len(self.user_video_presets) - 1, index + direction))
        if index == target:
            return
        item = self.user_video_presets.pop(index)
        self.user_video_presets.insert(target, item)
        self._sync_all_user_preset_backups()
        self._refresh_user_preset_listbox(select_index=target)
        self._save_app_settings()

    def _refresh_user_preset_listbox(self, select_name=None, select_index=None):
        if not hasattr(self, "user_preset_list"):
            return
        self.user_preset_list.delete(0, END)
        for item in self.user_video_presets:
            self.user_preset_list.insert(END, item["name"])
        if select_name:
            for index, item in enumerate(self.user_video_presets):
                if item["name"] == select_name:
                    select_index = index
                    break
        if select_index is not None and 0 <= select_index < len(self.user_video_presets):
            self.user_preset_list.selection_set(select_index)
            self.user_preset_list.activate(select_index)

    def load_video_preset(self):
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title("加载预设")
        self._set_window_geometry(window, "940x420")
        window.minsize(860, 340)
        box = ttk.Frame(window, padding=16)
        box.pack(fill="both", expand=True)
        box.columnconfigure(0, weight=3)
        box.columnconfigure(1, weight=2)
        box.columnconfigure(2, weight=3)
        box.rowconfigure(1, weight=1)

        ttk.Label(box, text="用户预设").grid(row=0, column=0, sticky="w")
        ttk.Label(box, text="主要参数预览").grid(row=0, column=1, sticky="w", padx=(8, 8))
        ttk.Label(box, text="内置预设").grid(row=0, column=2, sticky="w")

        user_box = ttk.Frame(box)
        user_box.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        user_box.columnconfigure(0, weight=1)
        user_box.rowconfigure(0, weight=1)
        user_list = self._create_work_listbox(user_box, exportselection=False)
        user_list.grid(row=0, column=0, sticky="nsew")
        for item in self.user_video_presets:
            user_list.insert(END, item["name"])
        if self.user_video_presets:
            user_list.selection_set(0)

        preview_box = ttk.Frame(box)
        preview_box.grid(row=1, column=1, sticky="nsew", padx=8)
        preview_box.columnconfigure(0, weight=1)
        preview_box.rowconfigure(0, weight=1)
        preview_text = Text(
            preview_box,
            wrap="word",
            height=12,
            width=28,
            background=self.COLORS["entry_bg"],
            foreground=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief="solid",
            borderwidth=1,
            font=("Microsoft YaHei UI", self._ui_metrics()["font"]),
            padx=10,
            pady=8,
        )
        preview_text.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(preview_box, orient="vertical", command=preview_text.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        preview_text.configure(yscrollcommand=preview_scroll.set, state="disabled")

        builtin_names = list(self._builtin_video_presets())
        builtin_box = ttk.Frame(box)
        builtin_box.grid(row=1, column=2, sticky="nsew", padx=(8, 0))
        builtin_box.columnconfigure(0, weight=1)
        builtin_box.rowconfigure(0, weight=1)
        builtin_list = self._create_work_listbox(builtin_box, exportselection=False)
        builtin_list.grid(row=0, column=0, sticky="nsew")
        for name in builtin_names:
            builtin_list.insert(END, name)
        if builtin_names:
            builtin_list.selection_set(0)

        actions = ttk.Frame(box)
        actions.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        actions.columnconfigure((0, 1), weight=1)

        def refresh_user_preview(_event=None):
            selection = user_list.curselection()
            if selection:
                preset = self.user_video_presets[selection[0]]
                text = self._format_preset_preview(preset["settings"])
            else:
                text = "暂无用户预设。"
            preview_text.configure(state="normal")
            preview_text.delete("1.0", END)
            preview_text.insert("1.0", text)
            preview_text.configure(state="disabled")

        user_list.bind("<<ListboxSelect>>", refresh_user_preview)
        refresh_user_preview()

        def apply_user_preset():
            selection = user_list.curselection()
            if not selection:
                messagebox.showwarning("没有选择", "请先选择一个用户预设。")
                return
            preset = self.user_video_presets[selection[0]]
            self._apply_video_settings_dict(preset["settings"])
            self._log(f"已加载用户预设：{preset['name']}")
            window.destroy()

        def apply_builtin_preset():
            selection = builtin_list.curselection()
            if not selection:
                messagebox.showwarning("没有选择", "请先选择一个内置预设。")
                return
            name = builtin_names[selection[0]]
            preset = self._builtin_video_presets()[name]
            self._apply_video_settings_dict(preset)
            self._log(f"已加载内置预设：{name}")
            window.destroy()

        ttk.Button(actions, text="加载用户预设", style="Accent.TButton", command=apply_user_preset).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="加载内置预设", command=apply_builtin_preset).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _format_preset_preview(self, settings):
        data = dict(settings or {})
        def value(key, default="未设置"):
            text = str(data.get(key, "")).strip()
            return text if text else default

        lines = [
            f"编码器：{value('encoder_name')}",
            f"预设速度：{value('preset_name', self.preset_name.get())}",
            f"质量模式：{value('quality_mode', 'CRF / 恒定质量')}",
            f"CRF/CQ：{value('cq_value', '23')}",
            f"目标码率：{value('bitrate')}",
            f"分辨率：{value('resolution_name')}",
            f"锐化：{value('sharpen_name', '关闭')}",
            f"音频：{value('audio_mode')}",
            f"音频码率：{value('audio_bitrate')}",
            f"容器：{value('muxer_name')}",
            f"输出倍速：{value('output_speed', '1.0')}x",
        ]
        effects = []
        if data.get("use_lut") and str(data.get("lut_path", "")).strip():
            effects.append(f"LUT：{data.get('lut_path')}")
        if value("sharpen_name", "关闭") != "关闭":
            effects.append(f"锐化：{value('sharpen_name')}")
        if str(data.get("hidden_watermark_enabled", "")).lower() in {"true", "1"} or data.get("hidden_watermark_enabled") is True:
            effects.append(f"隐藏水印：{value('hidden_watermark_mode', 'text')}")
        extra = str(data.get("extra_ffmpeg_args", "")).strip()
        if extra:
            effects.append(f"高级参数：{extra}")
        custom = str(data.get("custom_command", "")).strip()
        if value("quality_mode", "") == "自定义命令" and custom:
            effects.append(f"自定义命令：{custom}")
        lines.append("")
        lines.append("影响画面/声音的设置：")
        lines.extend(f"- {item}" for item in effects) if effects else lines.append("- 无额外效果设置")
        return "\n".join(lines)

    def _video_settings_dict(self):
        return {
            "encoder_name": self.encoder_name.get(),
            "advanced_encoders": self.advanced_encoders.get(),
            "preset_name": self.preset_name.get(),
            "resolution_name": self.resolution_name.get(),
            "sharpen_name": self.sharpen_name.get(),
            "custom_width": self.custom_width.get(),
            "custom_height": self.custom_height.get(),
            "quality_mode": self.quality_mode.get(),
            "cq_value": self.cq_value.get(),
            "bitrate": self.bitrate.get(),
            "custom_command": self.custom_command.get(),
            "audio_mode": self.audio_mode.get(),
            "audio_bitrate": self.audio_bitrate.get(),
            "muxer_name": self.muxer_name.get(),
            "output_speed": self.output_speed.get(),
            "create_thumbnail": self.create_thumbnail.get(),
            "thumbnail_only_selected": self.thumbnail_only_selected.get(),
            "thumbnail_time": self.thumbnail_time.get(),
            "parallel_jobs": self.parallel_jobs.get(),
            "extra_ffmpeg_args": self.extra_ffmpeg_args.get(),
            "use_lut": self.use_lut.get(),
            "lut_path": self.lut_path.get(),
            "hidden_watermark_enabled": self.hidden_watermark_enabled.get(),
            "hidden_watermark_mode": self.hidden_watermark_mode.get(),
            "hidden_watermark_text": self.hidden_watermark_text.get(),
            "hidden_watermark_image": self.hidden_watermark_image.get(),
            "file_conflict_action": self.file_conflict_action.get(),
        }

    def _apply_video_settings_dict(self, data):
        setters = {
            "encoder_name": self.encoder_name,
            "advanced_encoders": self.advanced_encoders,
            "preset_name": self.preset_name,
            "resolution_name": self.resolution_name,
            "sharpen_name": self.sharpen_name,
            "custom_width": self.custom_width,
            "custom_height": self.custom_height,
            "quality_mode": self.quality_mode,
            "cq_value": self.cq_value,
            "bitrate": self.bitrate,
            "custom_command": self.custom_command,
            "audio_mode": self.audio_mode,
            "audio_bitrate": self.audio_bitrate,
            "muxer_name": self.muxer_name,
            "output_speed": self.output_speed,
            "create_thumbnail": self.create_thumbnail,
            "thumbnail_only_selected": self.thumbnail_only_selected,
            "thumbnail_time": self.thumbnail_time,
            "parallel_jobs": self.parallel_jobs,
            "extra_ffmpeg_args": self.extra_ffmpeg_args,
            "use_lut": self.use_lut,
            "lut_path": self.lut_path,
            "hidden_watermark_enabled": self.hidden_watermark_enabled,
            "hidden_watermark_mode": self.hidden_watermark_mode,
            "hidden_watermark_text": self.hidden_watermark_text,
            "hidden_watermark_image": self.hidden_watermark_image,
            "file_conflict_action": self.file_conflict_action,
        }
        for key, variable in setters.items():
            if key in data:
                variable.set(data[key])
        self.refresh_encoder_choices()

    def choose_audio_output_dir(self):
        folder = filedialog.askdirectory(title="选择音频输出目录")
        if folder:
            self.audio_output_dir.set(folder)

    def choose_retro_output_dir(self):
        folder = filedialog.askdirectory(title="选择复古输出目录")
        if folder:
            self.retro_output_dir.set(folder)

    def choose_anamorphic_output_dir(self):
        folder = filedialog.askdirectory(title="选择变形视频输出目录")
        if folder:
            self.anamorphic_output_dir.set(folder)

    def choose_mux_output_dir(self):
        folder = filedialog.askdirectory(title="选择封装输出目录")
        if folder:
            self.mux_output_dir.set(folder)

    def choose_batch_input_dir(self):
        folder = filedialog.askdirectory(title="选择批量输入文件夹")
        if folder:
            self.batch_input_dir.set(folder)

    def choose_batch_output_dir(self):
        folder = filedialog.askdirectory(title="选择批量输出文件夹")
        if folder:
            self.batch_output_dir.set(folder)

    def choose_lut(self):
        path = filedialog.askopenfilename(title="选择 LUT 文件", filetypes=LUT_FILETYPES)
        if path:
            self.lut_path.set(path)
            self.use_lut.set(True)

    def choose_hidden_watermark_image(self):
        path = filedialog.askopenfilename(title="选择水印图片", filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.webp"), ("所有文件", "*.*")])
        if path:
            self.hidden_watermark_image.set(path)
            self.hidden_watermark_mode.set("image")
            self.hidden_watermark_enabled.set(True)

    def extract_hidden_watermark_from_file(self):
        path = filedialog.askopenfilename(title="选择要解析隐藏水印的视频", filetypes=VIDEO_FILETYPES + [("所有文件", "*.*")])
        if not path:
            return
        info = ffmpeg.probe_media_info(Path(path))
        payload = ffmpeg.extract_hidden_watermark_payload(info)
        if not payload:
            messagebox.showinfo("解析结果", "未检测到本软件嵌入的隐藏水印签名。")
            return
        lines = [f"文件：{Path(path).name}", "", f"签名：{payload}"]
        parts = payload.split(":")
        if len(parts) >= 4:
            mode = parts[3]
            if mode == "text" and len(parts) >= 5:
                lines += ["", "类型：文字", f"内容：{':'.join(parts[4:])}"]
            elif mode == "image":
                lines += ["", "类型：图片", f"标识：{':'.join(parts[4:])}"]
        messagebox.showinfo("解析结果", "\n".join(lines))

    def choose_lut_page_video(self):
        path = filedialog.askopenfilename(title="选择用于 LUT 对比的视频", filetypes=VIDEO_FILETYPES)
        if path:
            self.lut_page_video.set(path)

    def choose_lut_page_folder(self):
        folder = filedialog.askdirectory(title="选择 LUT 文件夹")
        if folder:
            self.lut_page_folder.set(folder)

    def choose_lut_page_output(self):
        folder = filedialog.askdirectory(title="选择 LUT 缩略图输出目录")
        if folder:
            self.lut_page_output.set(folder)

    def _schedule_avs_script_refresh(self, *_):
        text_widget = getattr(self, "avs_script_text", None)
        if text_widget and text_widget.winfo_exists() and self._avs_script_user_edited:
            return
        job = getattr(self, "_avs_script_refresh_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        try:
            self._avs_script_refresh_job = self.root.after(50, lambda: self.generate_avs_script(force=False))
        except Exception:
            self._avs_script_refresh_job = None

    def _avs_quote_path(self, raw_path):
        path = str(Path(raw_path).expanduser())
        return path.replace("\\", "/").replace('"', '\\"')

    def _on_avs_script_modified(self, _event=None):
        text_widget = getattr(self, "avs_script_text", None)
        if not text_widget or not text_widget.winfo_exists():
            return
        modified = bool(text_widget.edit_modified())
        if modified and not self._avs_script_updating:
            self._avs_script_user_edited = True
        try:
            text_widget.edit_modified(False)
        except Exception:
            pass

    def generate_avs_script(self, force=True):
        text_widget = getattr(self, "avs_script_text", None)
        if not text_widget or not text_widget.winfo_exists():
            return
        if not force and self._avs_script_user_edited:
            return
        video = self.avs_video_path.get().strip()
        subtitle = self.avs_subtitle_path.get().strip()
        lines = ["# 自动生成的 AVS 脚本", "# 你可以继续手工补充滤镜或源滤镜设置。"]
        if video:
            lines.append(f'video = "{self._avs_quote_path(video)}"')
            lines.append('v = FFVideoSource(video)')
        else:
            lines.append('# video = "请先选择视频文件"')
            lines.append("v = last")
        if self.avs_enable_addborders.get():
            lines.append(
                "v = AddBorders(v, {0}, {1}, {2}, {3})".format(
                    int(self.avs_border_left.get()),
                    int(self.avs_border_top.get()),
                    int(self.avs_border_right.get()),
                    int(self.avs_border_bottom.get()),
                )
            )
        if self.avs_enable_crop.get():
            lines.append(
                "v = Crop(v, {0}, {1}, -{2}, -{3})".format(
                    int(self.avs_crop_left.get()),
                    int(self.avs_crop_top.get()),
                    int(self.avs_crop_right.get()),
                    int(self.avs_crop_bottom.get()),
                )
            )
        if self.avs_enable_trim.get():
            start = max(0, int(self.avs_trim_start.get()))
            end = max(start, int(self.avs_trim_end.get()))
            lines.append(f"v = Trim(v, {start}, {end})")
        if self.avs_enable_brightness.get():
            bright = int(self.avs_brightness.get())
            lines.append(f"v = Tweak(v, bright={bright})")
        if self.avs_enable_sharpen.get():
            amount = max(0.0, float(self.avs_sharpen_amount.get()))
            lines.append(f"v = Sharpen(v, {amount:.2f})")
        if self.avs_enable_denoise.get():
            strength = max(1, int(self.avs_denoise_strength.get()))
            scenechange = min(40, max(8, strength * 2))
            lines.append(f"v = TemporalSoften(v, 2, {strength}, {strength}, {scenechange}, 2)")
        if subtitle:
            lines.append(f'# 字幕文件: "{self._avs_quote_path(subtitle)}"')
            lines.append("# 如需压制字幕，请在这里接入你常用的字幕滤镜。")
        lines.append("")
        lines.append("return v")
        self._avs_script_updating = True
        try:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", END)
            text_widget.insert("1.0", "\n".join(lines))
            text_widget.edit_modified(False)
            self._avs_script_user_edited = False
        finally:
            self._avs_script_updating = False

    def save_avs_script(self):
        if not self._avs_script_user_edited:
            self.generate_avs_script(force=True)
        video_name = Path(self.avs_video_path.get().strip()).stem if self.avs_video_path.get().strip() else "script"
        default_dir = self.avs_output_path.get().strip()
        initialdir = default_dir if default_dir else str(self._default_output_dir("avs"))
        path = filedialog.asksaveasfilename(
            title="保存 AVS 脚本",
            initialdir=initialdir,
            initialfile=f"{video_name}.avs",
            defaultextension=".avs",
            filetypes=[("AVS 脚本", "*.avs"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.avs_script_text.get("1.0", "end-1c"), encoding="utf-8")
            self._log(f"AVS 脚本已保存：{target}")
        except Exception as exc:
            messagebox.showerror("保存失败", f"保存 AVS 脚本失败：{exc}")

    def copy_avs_script(self):
        if not self._avs_script_user_edited:
            self.generate_avs_script(force=True)
        try:
            text = self.avs_script_text.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._log("AVS 脚本已复制到剪贴板。")
        except Exception as exc:
            messagebox.showerror("复制失败", f"复制 AVS 脚本失败：{exc}")

    def clear_avs_script(self):
        if not hasattr(self, "avs_script_text"):
            return
        self.avs_script_text.delete("1.0", END)
        self.avs_script_text.edit_modified(False)
        self._avs_script_user_edited = False

    def choose_mediainfo_file(self):
        path = filedialog.askopenfilename(title="选择媒体文件", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        if path:
            self.media_info_path.set(path)
            self.load_mediainfo()

    def choose_mediainfo_compare_a(self):
        path = filedialog.askopenfilename(title="选择对比文件 A", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        if path:
            self.media_compare_path_a.set(path)

    def choose_mediainfo_compare_b(self):
        path = filedialog.askopenfilename(title="选择对比文件 B", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        if path:
            self.media_compare_path_b.set(path)

    def _set_mediainfo_path(self, paths):
        for raw in paths:
            path = Path(raw)
            if path.is_file():
                self.media_info_path.set(str(path.resolve()))
                self.load_mediainfo()
                return

    def compare_mediainfo_files(self):
        path_a = Path(self.media_compare_path_a.get().strip())
        path_b = Path(self.media_compare_path_b.get().strip())
        if not path_a.exists() or not path_b.exists():
            messagebox.showwarning("文件不存在", "请先选择两个有效的对比文件。")
            return
        info_a = ffmpeg.probe_media_info(path_a)
        info_b = ffmpeg.probe_media_info(path_b)
        if not info_a or not info_b:
            messagebox.showwarning("读取失败", "至少有一个文件无法读取媒体信息，请确认 ffprobe 可用。")
            return
        rows = self._build_mediainfo_comparison_rows(path_a, info_a, path_b, info_b)
        self.media_compare_rows = list(rows)
        self._show_mediainfo_compare_window(path_a, path_b)

    def _show_mediainfo_compare_window(self, path_a, path_b):
        window = self.media_compare_window
        if not window or not window.winfo_exists():
            window = Toplevel(self.root)
            self.media_compare_window = window
            self._set_window_icon(window)
            window.title("MediaInfo 参数对比")
            self._set_window_geometry(window, "1160x700")
            window.minsize(980, 560)
            window.columnconfigure(0, weight=1)
            window.rowconfigure(1, weight=1)
            window.protocol("WM_DELETE_WINDOW", self._close_mediainfo_compare_window)

            toolbar = ttk.Frame(window, padding=(12, 10))
            toolbar.grid(row=0, column=0, sticky="ew")
            for col in range(6):
                toolbar.columnconfigure(col, weight=1)
            ttk.Button(toolbar, text="重新对比", style="Accent.TButton", command=self.compare_mediainfo_files).grid(row=0, column=0, sticky="ew", padx=(0, 6))
            ttk.Button(toolbar, text="交换 A/B", command=self._swap_mediainfo_compare_files).grid(row=0, column=1, sticky="ew", padx=6)
            ttk.Button(toolbar, text="导出表格", command=self.export_mediainfo_comparison).grid(row=0, column=2, sticky="ew", padx=6)
            ttk.Button(toolbar, text="生成 A/B 静态帧", command=self.export_mediainfo_compare_frames_manual).grid(row=0, column=3, sticky="ew", padx=6)
            ttk.Checkbutton(toolbar, text="仅显示不同项", variable=self.media_compare_show_diff_only, command=self._refresh_mediainfo_compare_popup_rows).grid(row=0, column=4, sticky="w", padx=(10, 6))
            ttk.Button(toolbar, text="关闭", command=self._close_mediainfo_compare_window).grid(row=0, column=5, sticky="ew", padx=(6, 0))

            table_wrap = ttk.Frame(window, padding=(12, 0, 12, 12))
            table_wrap.grid(row=1, column=0, sticky="nsew")
            table_wrap.columnconfigure(0, weight=1)
            table_wrap.rowconfigure(0, weight=1)
            columns = ("param", "left", "right", "status", "delta")
            tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
            tree.heading("param", text="参数")
            tree.heading("left", text="A")
            tree.heading("right", text="B")
            tree.heading("status", text="判定")
            tree.heading("delta", text="差值说明")
            tree.column("param", width=140, minwidth=110, anchor="w")
            tree.column("left", width=280, minwidth=220, anchor="w")
            tree.column("right", width=280, minwidth=220, anchor="w")
            tree.column("status", width=90, minwidth=70, anchor="center", stretch=False)
            tree.column("delta", width=260, minwidth=180, anchor="w")
            tree.grid(row=0, column=0, sticky="nsew")
            scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
            scroll.grid(row=0, column=1, sticky="ns")
            tree.configure(yscrollcommand=scroll.set)
            self.media_compare_popup_tree = tree

        self._update_mediainfo_compare_popup_headers(path_a, path_b)
        self._refresh_mediainfo_compare_popup_rows()
        window.lift()
        try:
            window.focus_force()
        except Exception:
            pass

    def _update_mediainfo_compare_popup_headers(self, path_a, path_b):
        tree = self.media_compare_popup_tree
        if not tree:
            return
        tree.heading("left", text=f"A：{path_a.name}")
        tree.heading("right", text=f"B：{path_b.name}")

    def _refresh_mediainfo_compare_popup_rows(self):
        tree = self.media_compare_popup_tree
        if not tree or not tree.winfo_exists():
            return
        for item in tree.get_children():
            tree.delete(item)
        rows = list(self.media_compare_rows)
        if self.media_compare_show_diff_only.get():
            rows = [row for row in rows if len(row) >= 4 and row[3] == "不同"]
        for index, row in enumerate(rows):
            tree.insert("", END, iid=f"cmp_{index}", values=row)

    def _swap_mediainfo_compare_files(self):
        a = self.media_compare_path_a.get()
        b = self.media_compare_path_b.get()
        self.media_compare_path_a.set(b)
        self.media_compare_path_b.set(a)
        self.compare_mediainfo_files()

    def export_mediainfo_compare_frames_manual(self):
        path_a = Path(self.media_compare_path_a.get().strip())
        path_b = Path(self.media_compare_path_b.get().strip())
        if not path_a.exists() or not path_b.exists():
            messagebox.showwarning("文件不存在", "请先选择两个有效的对比文件。")
            return
        folder = filedialog.askdirectory(title="选择静态帧导出目录")
        if not folder:
            return
        outputs = self._export_mediainfo_compare_frames(path_a, path_b, Path(folder))
        if outputs and all(path.exists() for path in outputs):
            messagebox.showinfo("导出完成", f"A/B 静态帧已生成：\n{outputs[0]}\n{outputs[1]}")

    def _close_mediainfo_compare_window(self):
        window = self.media_compare_window
        if window and window.winfo_exists():
            try:
                window.destroy()
            except Exception:
                pass
        self.media_compare_window = None
        self.media_compare_popup_tree = None

    def export_mediainfo_comparison(self):
        rows = list(getattr(self, "media_compare_rows", []))
        if not rows:
            messagebox.showwarning("没有对比结果", "请先点击“对比参数”生成结果后再导出。")
            return
        path_a = Path(self.media_compare_path_a.get().strip())
        path_b = Path(self.media_compare_path_b.get().strip())
        if not path_a.exists() or not path_b.exists():
            messagebox.showwarning("文件不存在", "请先选择两个有效的对比文件。")
            return
        default_name = f"mediainfo_compare_{path_a.stem}_vs_{path_b.stem}.csv"
        export_path = filedialog.asksaveasfilename(
            title="导出对比表格",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV 表格", "*.csv"), ("所有文件", "*.*")],
        )
        if not export_path:
            return
        target = Path(export_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerow(["参数", "A 文件", "B 文件", "判定", "差值说明"])
                writer.writerows(rows)
                writer.writerow([])
                writer.writerow(["A 文件路径", str(path_a)])
                writer.writerow(["B 文件路径", str(path_b)])
                writer.writerow(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            frame_outputs = []
            if self.media_compare_generate_frames_on_export.get():
                frame_outputs = self._export_mediainfo_compare_frames(path_a, path_b, target.parent)
            tips = [f"对比表格已导出：{target}"]
            if frame_outputs:
                tips.append(f"A/B 静态帧已生成：{frame_outputs[0].name}、{frame_outputs[1].name}")
            messagebox.showinfo("导出完成", "\n".join(tips))
            self._log(f"MediaInfo 对比表格已导出：{target}")
            if frame_outputs:
                self._log(f"MediaInfo 对比帧已生成：{frame_outputs[0]} | {frame_outputs[1]}")
        except Exception as exc:
            messagebox.showerror("导出失败", f"导出对比表格失败：{exc}")

    def _export_mediainfo_compare_frames(self, path_a, path_b, output_dir):
        seconds = max(0.0, self._safe_float(self.media_compare_frame_time.get()))
        timestamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_a = output_dir / f"{path_a.stem}_A_{seconds:.2f}s_{timestamp_tag}.jpg"
        frame_b = output_dir / f"{path_b.stem}_B_{seconds:.2f}s_{timestamp_tag}.jpg"
        output_a = ffmpeg.run_capture(ffmpeg.build_thumbnail_command(path_a, frame_a, seconds))
        output_b = ffmpeg.run_capture(ffmpeg.build_thumbnail_command(path_b, frame_b, seconds))
        missing = [str(path) for path in (frame_a, frame_b) if not path.exists()]
        if missing:
            messagebox.showwarning(
                "静态帧生成不完整",
                "导出表格已成功，但部分静态帧生成失败。\n\n"
                + "\n".join(missing)
                + ("\n\nffmpeg 输出：\n" + (output_a + "\n" + output_b).strip() if (output_a or output_b) else ""),
            )
        return [frame_a, frame_b]

    def add_audio_files(self):
        paths = filedialog.askopenfilenames(title="选择音频/视频文件", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        self._add_audio_paths(paths)

    def add_audio_folder(self):
        folder = filedialog.askdirectory(title="选择音频文件夹")
        if not folder:
            return
        valid_exts = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
        paths = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in valid_exts]
        self._add_audio_paths(paths)

    def _add_audio_paths(self, paths):
        existing = set(self.audio_files)
        before = len(self.audio_files)
        valid_exts = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
        for path in self._expand_paths(paths, valid_exts):
            full = str(path.resolve())
            if full not in existing:
                self.audio_files.append(full)
                self.audio_file_list.insert(END, full)
                existing.add(full)
        added = len(self.audio_files) - before
        if added > 0:
            self._log(f"已添加 {len(self.audio_files)} 个音频/视频")

    def _expand_paths(self, paths, extensions):
        expanded = []
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                expanded.extend(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in extensions)
            elif path.is_file() and path.suffix.lower() in extensions:
                expanded.append(path)
        return expanded

    def remove_selected_audio(self):
        for index in reversed(self.audio_file_list.curselection()):
            self.audio_file_list.delete(index)
            del self.audio_files[index]

    def clear_audio_files(self):
        self.audio_files.clear()
        self.audio_file_list.delete(0, END)

    def add_retro_files(self):
        paths = filedialog.askopenfilenames(title="选择古老素材文件", filetypes=VIDEO_FILETYPES)
        self._add_retro_paths(paths)

    def add_retro_folder(self):
        folder = filedialog.askdirectory(title="选择古老素材文件夹")
        if not folder:
            return
        self._add_retro_paths([folder])

    def _add_retro_paths(self, paths):
        existing = set(self.retro_files)
        for path in self._expand_paths(paths, VIDEO_EXTENSIONS):
            full = str(path.resolve())
            if full not in existing:
                self.retro_files.append(full)
                self.retro_file_list.insert(END, full)
                existing.add(full)
        self._log(f"已添加 {len(self.retro_files)} 个复古素材")

    def remove_selected_retro(self):
        for index in reversed(self.retro_file_list.curselection()):
            self.retro_file_list.delete(index)
            del self.retro_files[index]

    def clear_retro_files(self):
        self.retro_files.clear()
        self.retro_file_list.delete(0, END)

    def add_anamorphic_files(self):
        paths = filedialog.askopenfilenames(title="选择变形镜头视频", filetypes=VIDEO_FILETYPES)
        self._add_anamorphic_paths(paths)

    def add_anamorphic_folder(self):
        folder = filedialog.askdirectory(title="选择变形镜头视频文件夹")
        if folder:
            self._add_anamorphic_paths([folder])

    def _add_anamorphic_paths(self, paths):
        existing = set(self.anamorphic_files)
        for path in self._expand_paths(paths, VIDEO_EXTENSIONS):
            full = str(path.resolve())
            if full not in existing:
                self.anamorphic_files.append(full)
                self.anamorphic_file_list.insert(END, full)
                existing.add(full)
        self._log(f"已添加 {len(self.anamorphic_files)} 个变形镜头素材")

    def remove_selected_anamorphic(self):
        for index in reversed(self.anamorphic_file_list.curselection()):
            self.anamorphic_file_list.delete(index)
            del self.anamorphic_files[index]

    def clear_anamorphic_files(self):
        self.anamorphic_files.clear()
        self.anamorphic_file_list.delete(0, END)

    def add_mux_merge_files(self):
        paths = filedialog.askopenfilenames(title="选择要合并的文件", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        self._add_mux_paths(paths, self.mux_merge_files, self.mux_merge_list)

    def remove_selected_mux_merge(self):
        self._remove_selected_mux_paths(self.mux_merge_files, self.mux_merge_list)

    def clear_mux_merge_files(self):
        self.mux_merge_files.clear()
        self.mux_merge_list.delete(0, END)

    def add_mux_convert_files(self):
        paths = filedialog.askopenfilenames(title="选择要转换封装的文件", filetypes=VIDEO_FILETYPES + AUDIO_FILETYPES + [("所有文件", "*.*")])
        self._add_mux_paths(paths, self.mux_convert_files, self.mux_convert_list)

    def add_mux_convert_folder(self):
        folder = filedialog.askdirectory(title="选择封装转换文件夹")
        if folder:
            paths = [str(p) for p in Path(folder).rglob("*") if p.is_file() and (p.suffix.lower() in VIDEO_EXTENSIONS or p.suffix.lower() in AUDIO_EXTENSIONS)]
            self._add_mux_paths(paths, self.mux_convert_files, self.mux_convert_list)

    def remove_selected_mux_convert(self):
        self._remove_selected_mux_paths(self.mux_convert_files, self.mux_convert_list)

    def clear_mux_convert_files(self):
        self.mux_convert_files.clear()
        self.mux_convert_list.delete(0, END)

    def load_subtitle_tracks(self):
        source = Path(self.subtitle_source.get())
        if not source.exists():
            messagebox.showwarning("没有视频", "请先选择有效的视频文件。")
            return
        info = ffmpeg.probe_media_info(source)
        streams = info.get("streams", []) if info else []
        self.subtitle_tracks = []
        for item in self.subtitle_track_tree.get_children():
            self.subtitle_track_tree.delete(item)
        type_count = {"video": 0, "audio": 0, "subtitle": 0}
        for stream in streams:
            codec_type = stream.get("codec_type", "unknown")
            if codec_type not in type_count:
                continue
            type_count[codec_type] += 1
            tags = stream.get("tags", {}) or {}
            track = {
                "stream_index": stream.get("index"),
                "codec_type": codec_type,
                "codec": stream.get("codec_name") or "",
                "lang": tags.get("language") or "und",
                "title": tags.get("title") or f"{self._subtitle_type_label(codec_type)} {type_count[codec_type]}",
                "keep": True,
            }
            self.subtitle_tracks.append(track)
            self._insert_subtitle_track_row(len(self.subtitle_tracks) - 1, track)
        self._log(f"已读取轨道：视频 {type_count['video']}，音频 {type_count['audio']}，字幕 {type_count['subtitle']}")

    def _insert_subtitle_track_row(self, row_id, track):
        self.subtitle_track_tree.insert("", END, iid=str(row_id), values=(
            "是" if track["keep"] else "否",
            self._subtitle_type_label(track["codec_type"]),
            track["stream_index"],
            track["codec"],
            track["lang"],
            track["title"],
        ))

    def _subtitle_type_label(self, codec_type):
        return {"video": "视频", "audio": "音频", "subtitle": "字幕"}.get(codec_type, codec_type)

    def toggle_selected_subtitle_track(self):
        for item in self.subtitle_track_tree.selection():
            index = int(item)
            self.subtitle_tracks[index]["keep"] = not self.subtitle_tracks[index]["keep"]
            self.subtitle_track_tree.item(item, values=(
                "是" if self.subtitle_tracks[index]["keep"] else "否",
                self._subtitle_type_label(self.subtitle_tracks[index]["codec_type"]),
                self.subtitle_tracks[index]["stream_index"],
                self.subtitle_tracks[index]["codec"],
                self.subtitle_tracks[index]["lang"],
                self.subtitle_tracks[index]["title"],
            ))

    def import_subtitle_files(self):
        paths = filedialog.askopenfilenames(title="导入外部字幕", filetypes=[("字幕文件", "*.srt *.ass *.ssa *.vtt"), ("所有文件", "*.*")])
        existing = set(self.subtitle_external_files)
        for raw in paths:
            path = Path(raw)
            if path.is_file():
                full = str(path.resolve())
                if full not in existing:
                    self.subtitle_external_files.append(full)
                    self.external_subtitle_list.insert(END, full)
                    existing.add(full)

    def remove_selected_external_subtitle(self):
        for index in reversed(self.external_subtitle_list.curselection()):
            self.external_subtitle_list.delete(index)
            del self.subtitle_external_files[index]

    def _add_mux_paths(self, paths, target_list, listbox):
        existing = set(target_list)
        for raw in paths:
            path = Path(raw)
            if path.is_file():
                full = str(path.resolve())
                if full not in existing:
                    target_list.append(full)
                    listbox.insert(END, full)
                    existing.add(full)
        self._log(f"已添加 {len(target_list)} 个封装文件")

    def _remove_selected_mux_paths(self, target_list, listbox):
        for index in reversed(listbox.curselection()):
            listbox.delete(index)
            del target_list[index]

    def check_environment(self):
        self._guide_action_flags["checked_env"] = True
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title("环境检测与 Benchmark")
        self._set_window_geometry(window, "1280x720")
        window.minsize(1120, 620)
        self.environment_window = window
        self.environment_encoder_text = ""
        self._show_child_window_front(window)
        box = ttk.Frame(window, padding=14)
        box.pack(fill="both", expand=True)
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=3)
        box.rowconfigure(0, weight=1)

        info_box = ttk.LabelFrame(box, text="现有环境信息", padding=12)
        info_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        info_box.columnconfigure(0, weight=1)
        env_text = Text(info_box, height=12, width=42, wrap="char", bg=self.COLORS["entry_bg"], fg=self.COLORS["text"], relief="solid", borderwidth=1)
        env_text.grid(row=0, column=0, sticky="nsew")
        info_box.rowconfigure(0, weight=1)
        env_text.insert(END, "正在检测 FFmpeg、编码器和电脑配置...\n\n检测过程已放到后台执行，窗口可以正常拖动和操作。")
        env_text.configure(state="disabled")
        self.environment_info_text = env_text

        bench = ttk.LabelFrame(box, text="Benchmark", padding=12)
        bench.grid(row=0, column=1, sticky="nsew")
        bench.columnconfigure(1, weight=1)
        bench.columnconfigure(2, weight=0)
        bench.columnconfigure(3, weight=0)
        bench.rowconfigure(4, weight=1)

        video_path = StringVar(value="")
        ttk.Label(bench, text="测试视频").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(bench, textvariable=video_path).grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(bench, text="选择…", command=lambda: self._choose_benchmark_video(video_path, window)).grid(row=0, column=2, pady=(0, 8))

        def encoder_supported(name):
            encoder_key = ENCODERS.get(name, "")
            if not encoder_key:
                return False
            encoder_text = getattr(self, "environment_encoder_text", "")
            if not encoder_text:
                return True
            resolved_encoder, _ = ffmpeg.resolve_encoder(encoder_key)
            pattern = rf"(?<![a-z0-9_]){re.escape(resolved_encoder.lower())}(?![a-z0-9_])"
            return bool(re.search(pattern, encoder_text))

        encoder_box = ttk.Frame(bench)
        encoder_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        encoder_vars = {}
        default_encoders = [name for name in self._filtered_encoder_list(COMMON_ENCODERS) if name in ENCODERS]
        benchmark_candidates = self._filtered_encoder_list(list(ENCODERS))
        for index, name in enumerate(benchmark_candidates):
            var = BooleanVar(value=name in default_encoders)
            encoder_vars[name] = var
            ttk.Checkbutton(encoder_box, text=name, variable=var).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12), pady=3)

        nvidia_encoders = self._filtered_encoder_list([name for name, key in ENCODERS.items() if "nvenc" in key])
        amd_encoders = self._filtered_encoder_list([name for name, key in ENCODERS.items() if key.endswith("_amf")])
        intel_encoders = self._filtered_encoder_list([name for name, key in ENCODERS.items() if key.endswith("_qsv")])
        apple_encoders = self._filtered_encoder_list([name for name, key in ENCODERS.items() if key.endswith("_videotoolbox")])

        def apply_encoder_group(candidates):
            for var in encoder_vars.values():
                var.set(False)
            for name in candidates:
                if name in encoder_vars and encoder_supported(name):
                    encoder_vars[name].set(True)

        preset_row = ttk.Frame(bench)
        preset_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        ttk.Button(preset_row, text="N卡常用", command=lambda: apply_encoder_group(nvidia_encoders)).pack(side="left")
        ttk.Button(preset_row, text="A卡常用", command=lambda: apply_encoder_group(amd_encoders)).pack(side="left", padx=(6, 0))
        ttk.Button(preset_row, text="I卡常用", command=lambda: apply_encoder_group(intel_encoders)).pack(side="left", padx=(6, 0))
        ttk.Button(preset_row, text="Apple 常用", command=lambda: apply_encoder_group(apple_encoders)).pack(side="left", padx=(6, 0))
        ttk.Button(preset_row, text="全选", command=lambda: [var.set(True) for var in encoder_vars.values()]).pack(side="left", padx=(14, 0))
        ttk.Button(preset_row, text="清除", command=lambda: [var.set(False) for var in encoder_vars.values()]).pack(side="left", padx=(6, 0))

        action_row = ttk.Frame(bench)
        action_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        action_row.columnconfigure(0, weight=1)
        status = StringVar(value="等待开始")
        ttk.Label(action_row, textvariable=status, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        stop_button = ttk.Button(action_row, text="停止 Benchmark", command=lambda: self._stop_environment_benchmark(status))
        stop_button.grid(row=0, column=1, sticky="e", padx=(0, 8))
        ttk.Button(
            action_row,
            text="开始 Benchmark",
            style="Accent.TButton",
            command=lambda: self._start_environment_benchmark(video_path, encoder_vars, result_tree, status),
        ).grid(row=0, column=2, sticky="e")

        columns = ("encoder", "status", "size", "ratio", "elapsed")
        result_tree = ttk.Treeview(bench, columns=columns, show="headings", height=10)
        result_tree.heading("encoder", text="编码器")
        result_tree.heading("status", text="状态")
        result_tree.heading("size", text="压缩后大小")
        result_tree.heading("ratio", text="压缩率")
        result_tree.heading("elapsed", text="耗时")
        result_tree.column("encoder", width=360, minwidth=260, stretch=True)
        result_tree.column("status", width=130, minwidth=110, anchor="center", stretch=True)
        result_tree.column("size", width=130, minwidth=110, anchor="e", stretch=True)
        result_tree.column("ratio", width=110, minwidth=90, anchor="e", stretch=True)
        result_tree.column("elapsed", width=110, minwidth=90, anchor="e", stretch=True)
        result_tree.grid(row=4, column=0, columnspan=3, sticky="nsew")
        scrollbar = ttk.Scrollbar(bench, orient="vertical", command=result_tree.yview)
        scrollbar.grid(row=4, column=3, sticky="ns")
        result_tree.configure(yscrollcommand=scrollbar.set)
        threading.Thread(target=self._environment_detection_worker, daemon=True).start()

    def _show_child_window_front(self, window):
        try:
            window.transient(self.root)
            window.lift()
            window.focus_force()
            window.attributes("-topmost", True)
            window.after(250, lambda w=window: w.winfo_exists() and w.attributes("-topmost", False))
        except Exception:
            pass

    def _environment_detection_worker(self):
        try:
            info = ffmpeg.detect_environment()
            encoder_text = ffmpeg.run_capture([info.ffmpeg, "-hide_banner", "-encoders"]).lower() if info.ffmpeg else ""
            system_lines = self._system_profile_lines()
            if os.name == "nt":
                gpu_names = self._windows_cim_list("Win32_VideoController", "Name")
            elif self._is_macos():
                gpu_names = self._mac_gpu_names()
            else:
                gpu_names = []
            self.messages.put(("environment_update", (info, encoder_text, system_lines, gpu_names)))
        except Exception as exc:
            self.messages.put(("environment_update", (None, "", [f"检测失败：{exc}"], [])))

    def _apply_environment_update(self, payload):
        info, encoder_text, system_lines, gpu_names = payload
        self.environment_encoder_text = encoder_text or ""
        if gpu_names:
            self.detected_gpu_names = gpu_names
        text_widget = getattr(self, "environment_info_text", None)
        window = getattr(self, "environment_window", None)
        if not text_widget or not text_widget.winfo_exists():
            return
        if info is None or not info.ffmpeg:
            lines = ["未找到 ffmpeg。请安装 FFmpeg 6.0+ 并加入 PATH。", "", *system_lines]
            if window and window.winfo_exists():
                messagebox.showerror("环境检测", "未找到 ffmpeg。请安装 FFmpeg 6.0+ 并加入 PATH。", parent=window)
        else:
            gpu_summary = "、".join((gpu_names or self.detected_gpu_names)[:3]) if (gpu_names or self.detected_gpu_names) else "未读取到显卡名称"
            lines = [
                f"ffmpeg: {info.ffmpeg}",
                f"ffprobe: {info.ffprobe or '未找到，仍可压缩但进度估算会变弱'}",
                f"NVENC 编码器: {'可用' if info.has_nvenc else '未检测到'}",
                f"AMF 编码器: {'可用' if info.has_amf else '未检测到'}",
                f"Intel QSV 编码器: {'可用' if info.has_qsv else '未检测到'}",
                f"Apple VideoToolbox: {'可用' if info.has_videotoolbox else '未检测到'}",
                f"检测到显卡: {gpu_summary}",
                "",
                "电脑配置检查",
                *system_lines,
            ]
        text_widget.configure(state="normal")
        text_widget.delete("1.0", END)
        text_widget.insert("1.0", "\n".join(lines))
        text_widget.configure(state="disabled")
        if window and window.winfo_exists():
            self._show_child_window_front(window)

    def _choose_benchmark_video(self, variable, parent=None):
        path = filedialog.askopenfilename(title="选择 Benchmark 视频", filetypes=VIDEO_FILETYPES, parent=parent)
        if path:
            variable.set(path)
        if parent and parent.winfo_exists():
            self._show_child_window_front(parent)

    def _system_profile_lines(self):
        os_text = f"{platform.system()} {platform.release()}"
        version_text = platform.version()
        arch = platform.machine() or "未知"
        logical_cores = os.cpu_count() or 0
        if os.name == "nt":
            cpu_name = self._windows_cim_first("Win32_Processor", "Name")
            gpu_names = self._windows_cim_list("Win32_VideoController", "Name")
        elif self._is_macos():
            cpu_name = self._mac_cpu_name()
            gpu_names = self._mac_gpu_names()
        else:
            cpu_name = platform.processor()
            gpu_names = []
        cpu_name = cpu_name or "未知"
        memory_gb = self._total_memory_gb()
        lines = [
            f"系统: {os_text}",
            f"系统版本: {version_text}",
            f"架构: {arch}",
            f"CPU: {cpu_name}",
            f"逻辑核心数: {logical_cores if logical_cores else '未知'}",
            f"内存: {memory_gb:.1f} GB" if memory_gb > 0 else "内存: 未知",
        ]
        if gpu_names:
            for index, name in enumerate(gpu_names[:4], start=1):
                lines.append(f"GPU{index}: {name}")
            if len(gpu_names) > 4:
                lines.append(f"GPU: 其余 {len(gpu_names) - 4} 项未展开")
        else:
            lines.append("GPU: 未检测到（或系统未返回）")
        return lines

    def _mac_cpu_name(self):
        values = (
            self._read_command_lines(["sysctl", "-n", "machdep.cpu.brand_string"], timeout=2),
            self._read_command_lines(["sysctl", "-n", "hw.model"], timeout=2),
            self._read_command_lines(["uname", "-m"], timeout=2),
        )
        for lines in values:
            if lines:
                return lines[0]
        return platform.processor() or "Apple Silicon / Intel Mac"

    def _mac_gpu_names(self):
        lines = self._read_command_lines(["system_profiler", "SPDisplaysDataType", "-json"], timeout=6)
        if not lines:
            return []
        try:
            payload = json.loads("\n".join(lines))
        except Exception:
            return []
        results = []
        for item in payload.get("SPDisplaysDataType", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("sppci_model") or item.get("_name") or "").strip()
            if name:
                results.append(name)
        return results

    def _read_command_lines(self, command, timeout=4):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=self._command_creationflags(),
                timeout=timeout,
            )
        except Exception:
            return []
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def _total_memory_gb(self):
        if os.name == "nt":
            try:
                class MemoryStatusEx(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_uint32),
                        ("dwMemoryLoad", ctypes.c_uint32),
                        ("ullTotalPhys", ctypes.c_uint64),
                        ("ullAvailPhys", ctypes.c_uint64),
                        ("ullTotalPageFile", ctypes.c_uint64),
                        ("ullAvailPageFile", ctypes.c_uint64),
                        ("ullTotalVirtual", ctypes.c_uint64),
                        ("ullAvailVirtual", ctypes.c_uint64),
                        ("ullAvailExtendedVirtual", ctypes.c_uint64),
                    ]
                status = MemoryStatusEx()
                status.dwLength = ctypes.sizeof(MemoryStatusEx)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                    return status.ullTotalPhys / (1024 ** 3)
            except Exception:
                return 0.0
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            page_count = os.sysconf("SC_PHYS_PAGES")
            return (page_size * page_count) / (1024 ** 3)
        except Exception:
            pass
        return 0.0

    def _windows_cim_first(self, class_name, property_name):
        values = self._windows_cim_list(class_name, property_name)
        return values[0] if values else ""

    def _windows_cim_list(self, class_name, property_name):
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Get-CimInstance {class_name} | Select-Object -ExpandProperty {property_name}",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=self._command_creationflags(),
                timeout=4,
            )
        except Exception:
            return []
        if result.returncode != 0:
            return []
        values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        dedup = []
        seen = set()
        for value in values:
            if value not in seen:
                seen.add(value)
                dedup.append(value)
        return dedup

    def _start_environment_benchmark(self, video_path, encoder_vars, result_tree, status):
        source = Path(video_path.get())
        if not source.exists():
            messagebox.showwarning("没有视频", "请先选择一个用于 Benchmark 的视频文件。")
            return
        selected = [name for name, var in encoder_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("没有编码器", "请至少勾选一个编码器。")
            return
        for item in result_tree.get_children():
            result_tree.delete(item)
        for name in selected:
            result_tree.insert("", END, iid=name, values=(name, "等待中", "-", "-", "-"))
        status.set("Benchmark 运行中")
        self.benchmark_result_tree = result_tree
        self.benchmark_status = status
        self._start_worker("环境 Benchmark", self._environment_benchmark_worker, source, selected)

    def _stop_environment_benchmark(self, status):
        self.stop_requested = True
        status.set("正在停止 Benchmark")
        for job in self.active_ffmpeg_jobs.values():
            job["cancel"] = True
            process = job.get("process")
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass

    def _environment_benchmark_worker(self, source, selected):
        settings = self._settings()
        bench_dir = Path(self.output_dir.get()).resolve() / "benchmark"
        bench_dir.mkdir(parents=True, exist_ok=True)
        source_size = source.stat().st_size if source.exists() else 0
        for index, name in enumerate(selected, start=1):
            if self.stop_requested:
                break
            encoder_key = ENCODERS[name]
            tag = ENCODER_FILENAME_TAGS.get(encoder_key, re.sub(r"[^A-Za-z0-9]+", "_", encoder_key).strip("_"))
            safe_name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
            target = bench_dir / f"{source.stem}_benchmark_{index}_{tag}_{safe_name}.mkv"
            start = time.perf_counter()
            self.messages.put(("benchmark_update", (name, "运行中", "-", "-", "-")))
            cmd = ffmpeg.build_compress_command(source, target, settings, encoder_override=encoder_key, benchmark=True)
            ok = self._run_ffmpeg(cmd, source, show_job_window=False, benchmark_name=name)
            elapsed = time.perf_counter() - start
            if self.stop_requested:
                self.messages.put(("benchmark_update", (name, "已停止", "-", "-", self._format_seconds(elapsed))))
            elif ok and target.exists():
                target_size = target.stat().st_size
                saved_ratio = max(0, (1 - target_size / source_size) * 100) if source_size and target_size else 0
                self.messages.put(("benchmark_update", (
                    name,
                    "支持",
                    self._format_size(target_size),
                    f"{saved_ratio:.1f}%",
                    self._format_seconds(elapsed),
                )))
            else:
                self.messages.put(("benchmark_update", (name, "不支持", "-", "-", self._format_seconds(elapsed))))
            self.messages.put(("progress", index / len(selected) * 100))
        self.messages.put(("benchmark_done", "Benchmark 完成" if not self.stop_requested else "Benchmark 已停止"))

    def start_proxy_files(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.files:
            messagebox.showwarning("没有视频", "请先添加视频文件。")
            return
        self._start_worker("生成代理文件", self._proxy_worker)

    def start_compression(self):
        self._guide_action_flags["pressed_start"] = True
        if not self._confirm_overwrite_if_needed():
            return
        if not self.files:
            messagebox.showwarning("没有视频", "请先添加单个或批量视频。")
            return
        settings = self._settings()
        output_dir = Path(self.output_dir.get()).resolve()
        if not self._confirm_video_export_settings("开始导出", self.files, output_dir, settings):
            return
        self.export_record_context = self._build_export_record_context(len(self.files))
        self._start_worker("视频压缩", self._compress_worker)

    def _build_export_record_context(self, file_count):
        if file_count <= 10:
            return None
        if not messagebox.askyesno("保存导出记录", f"当前任务包含 {file_count} 个文件。\n是否保存导出记录（.log）用于追溯失败文件？"):
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = self._export_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"export_record_{stamp}.log"
        return {
            "path": path,
            "file_count": file_count,
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def add_current_video_to_queue(self):
        if not self.files:
            messagebox.showwarning("没有视频", "请先添加视频文件。")
            return
        files = self._selected_files() or list(self.files)
        settings = self._settings()
        output_dir = Path(self.output_dir.get()).resolve()
        if not self._confirm_video_export_settings("添加到任务队列", files, output_dir, settings):
            return
        task_id = self._create_task(self._describe_video_queue_task(files, output_dir))
        self.queued_tasks[task_id] = {
            "type": "video",
            "files": files,
            "settings": settings,
            "output_dir": output_dir,
            "conflict_action": self.file_conflict_action.get(),
        }
        self._update_task_status(task_id, "已加入队列")
        self.notebook.select(self.tasks_tab)

    def _describe_video_queue_task(self, files, output_dir):
        first = Path(files[0])
        if len(files) == 1:
            return f"压缩视频 {first} 到 {output_dir}"
        return f"压缩视频 {first} 等 {len(files)} 个文件到 {output_dir}"

    def start_selected_queued_tasks(self):
        selected = [item for item in self.task_tree.selection() if item in self.queued_tasks and self._task_status(item) != "运行中"]
        if not selected:
            messagebox.showwarning("没有待启动任务", "请先选择已加入队列的任务。")
            return
        self._start_worker("启动选中队列任务", self._queued_tasks_worker, selected)

    def start_all_queued_tasks(self):
        task_ids = [item for item in self.task_tree.get_children() if item in self.queued_tasks and self._task_status(item) != "运行中"]
        if not task_ids:
            messagebox.showwarning("没有待启动任务", "请先通过顶部“加入队列”添加任务。")
            return
        self._start_worker("启动全部队列任务", self._queued_tasks_worker, task_ids)

    def move_selected_task(self, direction):
        if not hasattr(self, "task_tree"):
            return
        selected = self.task_tree.selection()
        if not selected:
            return
        item = selected[0]
        siblings = list(self.task_tree.get_children())
        index = siblings.index(item)
        new_index = max(0, min(len(siblings) - 1, index + direction))
        if new_index == index:
            return
        self.task_tree.move(item, "", new_index)
        self.task_tree.selection_set(item)

    def _task_drag_start(self, event):
        if not hasattr(self, "task_tree"):
            return
        item = self.task_tree.identify_row(event.y)
        self.dragged_task = item if item in self.queued_tasks else None
        if self.dragged_task:
            self.task_tree.selection_set(self.dragged_task)

    def _task_drag_motion(self, event):
        item = getattr(self, "dragged_task", None)
        if not item or not self.task_tree.exists(item):
            return
        target = self.task_tree.identify_row(event.y)
        if not target or target == item:
            return
        values = self.task_tree.item(item, "values")
        target_values = self.task_tree.item(target, "values")
        if (values and values[1] == "运行中") or (target_values and target_values[1] == "运行中"):
            return
        siblings = list(self.task_tree.get_children())
        self.task_tree.move(item, "", siblings.index(target))
        self.task_tree.selection_set(item)

    def remove_selected_tasks(self):
        if not hasattr(self, "task_tree"):
            return
        for item in self.task_tree.selection():
            values = self.task_tree.item(item, "values")
            if values and values[1] == "运行中":
                continue
            self.queued_tasks.pop(item, None)
            self.task_tree.delete(item)

    def _task_status(self, item):
        if not hasattr(self, "task_tree") or not self.task_tree.exists(item):
            return ""
        values = self.task_tree.item(item, "values")
        return values[1] if len(values) > 1 else ""

    def start_thumbnail_batch(self):
        files = self._selected_files() if self.thumbnail_only_selected.get() else list(self.files)
        if not files:
            messagebox.showwarning("没有视频", "请先添加视频，或在列表中选中要生成缩略图的视频。")
            return
        self._start_worker("批量缩略图", self._thumbnail_worker, files)

    def start_lut_preview(self):
        source = self._preview_source()
        if not source:
            messagebox.showwarning("没有视频", "请先添加视频，最好在列表中选中一个要预览的视频。")
            return
        if self.use_lut.get() and not self.lut_path.get().strip():
            messagebox.showwarning("没有 LUT", "请先选择 LUT 文件。")
            return
        if self.use_lut.get() and not Path(self.lut_path.get()).exists():
            messagebox.showwarning("LUT 不存在", "当前 LUT 文件路径不存在，请重新选择。")
            return
        self._start_worker("LUT 预览", self._lut_preview_worker, Path(source))

    def start_benchmark(self):
        sample = self.base_dir / "test.mp4"
        if not sample.exists():
            messagebox.showwarning("缺少样本", f"未找到内置样本：{sample}")
            return
        self._start_worker("CPU/GPU Benchmark", self._benchmark_worker, sample)

    def start_audio_compression(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.audio_files:
            messagebox.showwarning("没有音频", "请先添加单个或批量音频文件。")
            return
        self._start_worker("音频压缩", self._audio_worker)

    def start_audio_reverse(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.audio_files:
            messagebox.showwarning("没有音频", "请先添加单个或批量音频文件。")
            return
        self._start_worker("音频倒放", self._audio_reverse_worker)

    def start_common_trim(self):
        source = Path(self.common_trim_video.get())
        if not source.exists():
            messagebox.showwarning("没有视频", "请先选择要截取的视频文件。")
            return
        if self._parse_time_seconds(self.common_trim_end.get()) <= self._parse_time_seconds(self.common_trim_start.get()):
            messagebox.showwarning("时间无效", "结束时间必须大于开始时间。")
            return
        self._start_worker("截取视频", self._common_trim_worker, source)

    def start_common_demux(self):
        source = Path(self.common_trim_video.get())
        if not source.exists():
            messagebox.showwarning("没有媒体", "请先在常用页面选择一个媒体文件。")
            return
        has_video, has_audio = self._common_stream_flags(source)
        if not has_video or not has_audio:
            messagebox.showwarning("流信息不足", "分离音视频需要同时包含视频流和音频流。")
            return
        self._start_worker("分离音视频", self._common_demux_worker, source)

    def start_common_channel_copy(self):
        source = Path(self.common_trim_video.get())
        if not source.exists():
            messagebox.showwarning("没有媒体", "请先在常用页面选择一个媒体文件。")
            return
        _, has_audio = self._common_stream_flags(source)
        if not has_audio:
            messagebox.showwarning("没有音频流", "当前文件没有可处理的音频流。")
            return
        self._start_worker("复制左右声道", self._common_channel_copy_worker, source)

    def _common_stream_flags(self, source):
        info = ffmpeg.probe_media_info(source) or {}
        streams = info.get("streams", [])
        has_video = any(stream.get("codec_type") == "video" for stream in streams)
        has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
        return has_video, has_audio

    def start_subtitle_mux(self):
        source = Path(self.subtitle_source.get())
        if not source.exists():
            messagebox.showwarning("没有视频", "请先选择视频文件。")
            return
        if not self.subtitle_tracks:
            self.load_subtitle_tracks()
        if not any(track["keep"] for track in self.subtitle_tracks) and not self.subtitle_external_files:
            messagebox.showwarning("没有轨道", "请至少保留一个原轨道或导入一个字幕文件。")
            return
        self._start_worker("字幕封装", self._subtitle_mux_worker, source)

    def start_subtitle_export(self):
        selected = self.subtitle_track_tree.selection()
        if not selected:
            messagebox.showwarning("没有字幕", "请先选中一个字幕轨道。")
            return
        track = self.subtitle_tracks[int(selected[0])]
        if track["codec_type"] != "subtitle":
            messagebox.showwarning("不是字幕轨道", "只能导出字幕轨道。")
            return
        self._start_worker("导出字幕", self._subtitle_export_worker, Path(self.subtitle_source.get()), track)

    def start_retro_processing(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.retro_files:
            messagebox.showwarning("没有素材", "请先添加古老素材文件。")
            return
        self._start_worker("复古处理", self._retro_worker)

    def start_anamorphic_processing(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.anamorphic_files:
            messagebox.showwarning("没有视频", "请先添加变形镜头拍摄的视频文件。")
            return
        self._start_worker("变形处理", self._anamorphic_worker)

    def start_anamorphic_preview(self):
        source = self.anamorphic_files[0] if self.anamorphic_files else ""
        if hasattr(self, "anamorphic_file_list") and self.anamorphic_file_list.curselection():
            source = self.anamorphic_files[self.anamorphic_file_list.curselection()[0]]
        if not source:
            messagebox.showwarning("没有视频", "请先添加或选中一个变形镜头视频。")
            return
        self._start_worker("变形预览帧", self._anamorphic_preview_worker, Path(source))

    def start_mux_merge(self):
        if len(self.mux_merge_files) < 2:
            messagebox.showwarning("文件不足", "请至少添加两个要合并的文件。")
            return
        self._start_worker("合并文件", self._mux_merge_worker)

    def start_mux_convert(self):
        if not self.mux_convert_files:
            messagebox.showwarning("没有文件", "请先添加要封装转换的文件。")
            return
        self._start_worker("封装转换", self._mux_convert_worker)

    def start_retro_remux(self):
        if not self._confirm_overwrite_if_needed():
            return
        if not self.retro_files:
            messagebox.showwarning("没有素材", "请先添加要封装转换的素材文件。")
            return
        self._start_worker("封装转换", self._retro_remux_worker)

    def start_batch_compression(self):
        if not self._confirm_overwrite_if_needed():
            return
        input_dir = Path(self.batch_input_dir.get())
        if not input_dir.exists():
            messagebox.showwarning("输入文件夹不存在", "请先选择有效的批量输入文件夹。")
            return
        self._start_worker("批量压缩", self._batch_worker)

    def start_lut_folder_preview(self):
        video = Path(self.lut_page_video.get())
        folder = Path(self.lut_page_folder.get())
        if not video.exists():
            messagebox.showwarning("没有视频", "请先选择用于预览的视频。")
            return
        if not folder.exists():
            messagebox.showwarning("没有 LUT 文件夹", "请先选择有效的 LUT 文件夹。")
            return
        self._start_worker("LUT 批量预览", self._lut_folder_preview_worker)

    def stop(self):
        self.stop_requested = True
        for job in self.active_ffmpeg_jobs.values():
            job["cancel"] = True
            process = job.get("process")
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass
        self._log("正在请求停止，所有正在运行的 ffmpeg 任务会尽快停止。")

    def _confirm_overwrite_if_needed(self):
        if not (self.file_conflict_action.get() == "覆盖" and self.confirm_overwrite.get()):
            return True
        return messagebox.askyesno("确认覆盖", "当前文件冲突策略为覆盖，已存在文件会被替换。是否继续？")

    def _confirm_video_export_settings(self, action_text, files, output_dir, settings):
        if not self.confirm_export_settings.get():
            return True
        summary = self._video_export_confirmation_text(action_text, files, output_dir, settings)
        return self._show_export_confirmation_dialog(action_text, summary)

    def _video_export_confirmation_text(self, action_text, files, output_dir, settings):
        file_count = len(files)
        preview_files = [str(Path(path)) for path in files[:8]]
        if file_count > len(preview_files):
            preview_files.append(f"... 另有 {file_count - len(preview_files)} 个文件")

        speed_value = self._normalized_speed_value(settings.output_speed)
        speed = self._format_speed_value(speed_value)
        effect_notes = []
        if settings.quality_mode == "自定义命令":
            effect_notes.append("自定义命令：将按命令内容导出，页面上的部分选项可能不会生效")
        if settings.resolution_name != "保持原分辨率":
            effect_notes.append(f"分辨率变更：{settings.resolution_name}")
        if settings.sharpen_name != "关闭":
            effect_notes.append(f"锐化滤镜：{settings.sharpen_name}")
        if settings.use_lut and settings.lut_path.strip():
            effect_notes.append(f"LUT 调色：{settings.lut_path.strip()}")
        if speed_value != 1.0:
            effect_notes.append(f"输出变速：{speed}x，音频会同步变速")
            if settings.audio_mode == "复制音频流":
                effect_notes.append("音频复制模式下变速会自动改为 AAC 重编码")
        if settings.hidden_watermark_enabled:
            effect_notes.append(f"隐藏水印：{settings.hidden_watermark_mode}")
        if settings.extra_ffmpeg_args.strip():
            effect_notes.append(f"高级参数：{settings.extra_ffmpeg_args.strip()}")

        lines = [
            f"即将{action_text}，请确认是否使用以下设置。",
            "",
            "输入文件",
            f"文件数量：{file_count}",
            *preview_files,
            "",
            "输出基础属性",
            f"输出目录：{output_dir}",
            f"文件名格式：{self.export_filename_format.get()}",
            f"文件冲突：{self.file_conflict_action.get()}",
            f"容器：{settings.muxer_name}",
            f"编码器：{settings.encoder_key}",
            f"速度/质量预设：{settings.preset_name}",
            f"质量模式：{settings.quality_mode}",
            f"CRF/CQ：{settings.cq_value}",
            f"目标码率：{settings.bitrate.strip() or '未设置'}",
            f"分辨率：{settings.resolution_name}",
            f"音频：{settings.audio_mode}",
            f"音频码率：{settings.audio_bitrate.strip() or '未设置'}",
            f"输出倍速：{speed}x",
            f"缩略图时间：{settings.thumbnail_time} 秒",
            "",
            "影响画面/声音效果的设置",
        ]
        if effect_notes:
            lines.extend(f"- {note}" for note in effect_notes)
        else:
            lines.append("- 未启用额外滤镜、变速、水印或高级参数")
        return "\n".join(lines)

    def _format_speed_value(self, value):
        speed = self._normalized_speed_value(value)
        return f"{speed:.3f}".rstrip("0").rstrip(".")

    def _normalized_speed_value(self, value):
        try:
            speed = float(value)
        except Exception:
            speed = 1.0
        if speed <= 0:
            speed = 1.0
        return speed

    def _show_export_confirmation_dialog(self, action_text, summary):
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title("确认导出设置")
        self._set_window_geometry(window, "680x560")
        window.minsize(560, 420)
        window.transient(self.root)
        window.grab_set()

        result = {"ok": False}
        frame = ttk.Frame(window, padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text="是否用以下设置继续？", font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        text = Text(frame, wrap="word", background=self.COLORS["entry_bg"], foreground=self.COLORS["text"], font=("Microsoft YaHei UI", 10), height=18)
        text.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)
        text.insert("1.0", summary)
        text.configure(state="disabled")

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure((0, 1), weight=1)

        def confirm():
            result["ok"] = True
            window.destroy()

        ttk.Button(actions, text=f"是，{action_text}", style="Accent.TButton", command=confirm).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="取消", command=window.destroy).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        window.bind("<Return>", lambda event: confirm())
        window.bind("<Escape>", lambda event: window.destroy())
        window.wait_window()
        return result["ok"]

    def _start_worker(self, task_name, target, *args):
        self.stop_requested = False
        self.progress.set(0)
        worker_id = f"worker_{time.time_ns()}"
        worker = threading.Thread(target=self._worker_wrapper, args=(None, target, args), daemon=True)
        self.active_workers[worker_id] = worker
        self.worker = worker
        worker.start()

    def _worker_wrapper(self, task_id, target, args):
        try:
            target(*args)
        except Exception as exc:
            self.messages.put(("log", f"任务异常：{exc}"))
        finally:
            for worker_id, worker in list(self.active_workers.items()):
                if worker is threading.current_thread():
                    self.active_workers.pop(worker_id, None)
                    break
            if not self.active_workers:
                self.root.after(0, self._on_all_workers_finished)

    def _on_all_workers_finished(self):
        if self.stop_requested:
            return
        if self.play_finish_sound.get():
            self._play_finish_sound()
        if self.shutdown_when_finished.get():
            self._schedule_shutdown()

    def _play_finish_sound(self):
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            try:
                self.root.bell()
            except Exception:
                pass

    def _schedule_shutdown(self):
        try:
            if os.name == "nt":
                self._log("任务全部完成，已执行关机指令：30 秒后自动关机。")
                subprocess.Popen(["shutdown", "/s", "/t", "30"], creationflags=self._command_creationflags())
            elif self._is_macos():
                self._log("任务全部完成，已请求 macOS 关机。若系统拦截，请检查自动化权限。")
                subprocess.Popen(["osascript", "-e", 'tell application "System Events" to shut down'])
            else:
                self._log("当前系统未实现自动关机。")
        except Exception as exc:
            self._log(f"执行关机失败：{exc}")

    def _create_task(self, task_name):
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        if hasattr(self, "task_tree"):
            self.task_tree.insert("", END, iid=task_id, values=(task_name, "等待中", "", ""))
        return task_id

    def _update_task_status(self, task_id, status):
        if not hasattr(self, "task_tree") or not self.task_tree.exists(task_id):
            return
        values = list(self.task_tree.item(task_id, "values"))
        if len(values) < 4:
            return
        values[1] = status
        if status == "运行中":
            values[2] = time.strftime("%H:%M:%S")
        if status in {"已完成", "已停止", "失败"}:
            values[3] = time.strftime("%H:%M:%S")
        self.task_tree.item(task_id, values=values)

    def clear_finished_tasks(self):
        if not hasattr(self, "task_tree"):
            return
        for item in self.task_tree.get_children():
            values = self.task_tree.item(item, "values")
            if values and values[1] in {"已完成", "已停止", "失败"}:
                self.queued_tasks.pop(item, None)
                self.task_tree.delete(item)

    def _queued_tasks_worker(self, task_ids):
        pending = [task_id for task_id in task_ids if task_id in self.queued_tasks and self._task_status(task_id) != "运行中"]
        total = len(pending)
        if not total:
            return
        max_workers = max(1, min(self.queue_parallel_jobs.get(), 4, total))
        self.messages.put(("log", f"队列启动：{total} 个任务，同时进行 {max_workers} 个"))
        done = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._run_queued_task, task_id, self.queued_tasks[task_id]): task_id
                for task_id in pending
            }
            for future in as_completed(futures):
                task_id = futures[future]
                done += 1
                try:
                    ok = future.result()
                    self.messages.put(("task", (task_id, "已完成" if ok else "失败")))
                    if ok:
                        self.queued_tasks.pop(task_id, None)
                except Exception as exc:
                    self.messages.put(("log", f"队列任务异常：{exc}"))
                    self.messages.put(("task", (task_id, "失败")))
                self.messages.put(("progress", done / total * 100))
                if self.stop_requested:
                    break
        self.messages.put(("status", "队列任务完成" if not self.stop_requested else "队列任务已停止"))

    def _run_queued_task(self, task_id, task):
        self.messages.put(("task", (task_id, "运行中")))
        if task["type"] != "video":
            return False
        output_dir = task["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        skipped = 0
        for source in task["files"]:
            if self.stop_requested:
                self.messages.put(("task", (task_id, "已停止")))
                return False
            source_path = Path(source)
            target = self._video_target_path(output_dir, source_path, task["settings"], task.get("conflict_action", "重命名"))
            if target is None:
                self.messages.put(("log", f"文件已存在，已跳过：{source_path.name}"))
                skipped += 1
                continue
            result = self._compress_one(source_path, target, task["settings"])
            if result:
                results.append(result)
        self._log_compression_summary(results)
        return (bool(results) or skipped > 0) and all(result.ok for result in results)

    def _settings(self):
        extra_args = self.extra_ffmpeg_args.get()
        if self.encoder_name.get() == "CPU H.264 / AVC (libx264)":
            x264_args = []
            if self.x264_threads.get() > 0:
                x264_args += ["-threads", str(self.x264_threads.get())]
            if self.x264_command.get().strip():
                x264_args += shlex.split(self.x264_command.get().strip(), posix=os.name != "nt")
            if x264_args:
                extra_args = " ".join([extra_args.strip(), *x264_args]).strip()
        return CompressionSettings(
            encoder_key=self.encoder_name.get(),
            preset_name=self.preset_name.get(),
            resolution_name=self.resolution_name.get(),
            sharpen_name=self.sharpen_name.get(),
            custom_width=self.custom_width.get(),
            custom_height=self.custom_height.get(),
            cq_value=self.cq_value.get(),
            bitrate=self.bitrate.get(),
            audio_mode=self.audio_mode.get(),
            audio_bitrate=self.audio_bitrate.get(),
            muxer_name=self.muxer_name.get(),
            output_speed=self.output_speed.get(),
            thumbnail_time=self.thumbnail_time.get(),
            overwrite=self.file_conflict_action.get() == "覆盖",
            use_lut=self.use_lut.get(),
            lut_path=self.lut_path.get(),
            extra_ffmpeg_args=extra_args,
            quality_mode=self.quality_mode.get(),
            custom_command=self.custom_command.get(),
            hidden_watermark_enabled=self.hidden_watermark_enabled.get(),
            hidden_watermark_mode=self.hidden_watermark_mode.get(),
            hidden_watermark_text=self.hidden_watermark_text.get(),
            hidden_watermark_image=self.hidden_watermark_image.get(),
        )

    def _audio_settings(self):
        sample_rate = self.audio_sample_rate.get().strip()
        channels = self.audio_channels.get().strip()
        if sample_rate == "自动":
            sample_rate = ""
        if channels == "自动":
            channels = ""
        return AudioSettings(
            encoder_name=self.audio_encoder_name.get(),
            bitrate=self.audio_page_bitrate.get(),
            sample_rate=sample_rate,
            channels=channels,
            overwrite=self.file_conflict_action.get() == "覆盖" or self.audio_overwrite_source.get(),
            normalize=self.audio_normalize.get(),
            output_mode=self.audio_output_mode.get(),
            overwrite_source=self.audio_overwrite_source.get(),
        )

    def _retro_settings(self):
        return RetroSettings(
            format_name=self.retro_format_name.get(),
            resolution_name=self.retro_resolution_name.get(),
            cq_value=self.cq_value.get(),
            bitrate=self.retro_bitrate.get(),
            audio_bitrate=self.retro_audio_bitrate.get(),
            deinterlace=self.retro_deinterlace.get(),
            denoise=self.retro_denoise.get(),
            overwrite=self.file_conflict_action.get() == "覆盖",
        )

    def _compress_worker(self):
        output_dir = Path(self.output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(self.files)
        done = 0
        skipped = []
        jobs = max(1, min(self.parallel_jobs.get(), 8, total))
        settings = self._settings()
        export_context = self.export_record_context
        self.messages.put(("multi_job_start", total if jobs > 1 else 0))
        self.messages.put(("log", f"并发任务数：{jobs}"))
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            futures = []
            for source in self.files:
                source_path = Path(source)
                target = self._video_target_path(output_dir, source_path, settings)
                if target is None:
                    done += 1
                    self.messages.put(("log", f"文件已存在，已跳过：{source_path.name}"))
                    skipped.append((source_path, "已跳过（文件已存在）"))
                    self.messages.put(("progress", done / total * 100))
                    continue
                job_id = f"video_{time.time_ns()}"
                futures.append(executor.submit(self._compress_one, source_path, target, settings, job_id))
            results = []
            for future in as_completed(futures):
                done += 1
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self._log_compression_result(result)
                except Exception as exc:
                    self.messages.put(("log", f"任务异常：{exc}"))
                self.messages.put(("progress", done / total * 100))
                if self.stop_requested:
                    break
        self._log_compression_summary(results)
        if export_context:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                self._write_export_record_log(export_context["path"], export_context["file_count"], export_context["started_at"], finished_at, results, skipped)
                self.messages.put(("log", f"导出记录已保存：{export_context['path']}"))
            except Exception as exc:
                self.messages.put(("log", f"保存导出记录失败：{exc}"))
        self.export_record_context = None
        self.messages.put(("status", "任务完成" if not self.stop_requested else "任务已停止"))
        self.messages.put(("multi_job_end", not self.stop_requested))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _compress_one(self, source_path, target, settings, job_id=None):
        if self.stop_requested:
            return None
        started_dt = datetime.now()
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        self.messages.put(("status", f"正在压缩：{source_path.name}"))
        ok = self._run_encode_job(source_path, target, settings, job_id=job_id)
        elapsed = time.perf_counter() - start
        ended_dt = datetime.now()
        target_size = target.stat().st_size if ok and target.exists() else 0
        if ok and self.create_thumbnail.get():
            self._create_thumbnail(target, settings.thumbnail_time)
        return CompressionResult(
            source=source_path,
            target=target,
            ok=ok,
            elapsed_seconds=elapsed,
            source_size=source_size,
            target_size=target_size,
            started_at=started_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ended_at=ended_dt.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _common_trim_worker(self, source_path):
        output_dir = Path(self.common_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = VIDEO_MUXERS[self.common_trim_muxer.get()]
        target = ffmpeg.unique_path(output_dir, source_path, suffix, self.file_conflict_action.get() == "覆盖", tag="trim")
        start_time = self.common_trim_start.get().strip()
        end_time = self.common_trim_end.get().strip()
        self.messages.put(("status", f"截取视频：{source_path.name}"))
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        ok = self._run_ffmpeg(self._build_common_trim_command(source_path, target, start_time, end_time), source_path)
        elapsed = time.perf_counter() - start
        target_size = target.stat().st_size if ok and target.exists() else 0
        result = CompressionResult(source_path, target, ok, elapsed, source_size, target_size)
        self._log_compression_result(result)
        self.messages.put(("status", "截取视频完成" if ok else "截取视频失败"))
        if ok and self.auto_open_output.get():
            self._open_folder(output_dir)

    def _common_demux_worker(self, source_path):
        output_dir = Path(self.common_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        overwrite = self.file_conflict_action.get() == "覆盖"
        video_suffix = source_path.suffix.lower() or ".mp4"
        video_target = ffmpeg.unique_path(output_dir, source_path, video_suffix, overwrite, tag="video_only")
        audio_target = ffmpeg.unique_path(output_dir, source_path, ".m4a", overwrite, tag="audio_only")
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        cmd_video = [
            ffmpeg_path,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-an",
            str(video_target),
        ]
        cmd_audio = [
            ffmpeg_path,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(audio_target),
        ]
        self.messages.put(("status", f"分离音视频：{source_path.name}"))
        ok_video = self._run_ffmpeg(cmd_video, source_path)
        ok_audio = self._run_ffmpeg(cmd_audio, source_path)
        if ok_video:
            self.messages.put(("log", f"视频流已导出：{video_target}"))
        if ok_audio:
            self.messages.put(("log", f"音频流已导出：{audio_target}"))
        self.messages.put(("status", "分离音视频完成" if ok_video and ok_audio else "分离音视频失败"))
        if (ok_video or ok_audio) and self.auto_open_output.get():
            self._open_folder(output_dir)

    def _common_channel_copy_worker(self, source_path):
        output_dir = Path(self.common_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        overwrite = self.file_conflict_action.get() == "覆盖"
        direction = self.common_channel_copy_mode.get()
        pan_expr = "stereo|c0=c0|c1=c0" if direction == "左复制到右" else "stereo|c0=c1|c1=c1"
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        is_video = source_path.suffix.lower() in VIDEO_EXTENSIONS
        if is_video:
            suffix = source_path.suffix.lower() or ".mp4"
            target = ffmpeg.unique_path(output_dir, source_path, suffix, overwrite, tag="audio_lr_copy")
            cmd = [
                ffmpeg_path,
                "-hide_banner",
                "-y" if overwrite else "-n",
                "-i",
                str(source_path),
                "-map",
                "0:v?",
                "-map",
                "0:a:0",
                "-c:v",
                "copy",
                "-af",
                f"pan={pan_expr}",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(target),
            ]
        else:
            target = ffmpeg.unique_path(output_dir, source_path, ".m4a", overwrite, tag="audio_lr_copy")
            cmd = [
                ffmpeg_path,
                "-hide_banner",
                "-y" if overwrite else "-n",
                "-i",
                str(source_path),
                "-af",
                f"pan={pan_expr}",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(target),
            ]
        self.messages.put(("status", f"复制左右声道：{source_path.name}"))
        ok = self._run_ffmpeg(cmd, source_path)
        if ok:
            self.messages.put(("log", f"声道复制完成：{target}"))
        self.messages.put(("status", "复制左右声道完成" if ok else "复制左右声道失败"))
        if ok and self.auto_open_output.get():
            self._open_folder(output_dir)

    def _build_common_trim_command(self, source_path, target, start_time, end_time):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        encoder_key = ENCODERS.get(self.common_trim_encoder.get(), "libx264")
        encoder, pix_fmt = ffmpeg.resolve_encoder(encoder_key)
        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-y" if self.file_conflict_action.get() == "覆盖" else "-n",
            "-ss",
            start_time,
            "-to",
            end_time,
            "-i",
            str(source_path),
            "-map",
            "0:v?",
            "-map",
            "0:a?",
            "-dn",
            "-c:v",
            encoder,
        ]
        if "nvenc" in encoder:
            cmd += ["-preset", "p5", "-rc", "vbr", "-cq", "23", "-b:v", "0"]
        elif encoder.endswith("_amf"):
            cmd += ["-quality", "balanced", "-rc", "cqp", "-qp_i", "23", "-qp_p", "23", "-qp_b", "23"]
        elif encoder == "libsvtav1":
            cmd += ["-preset", "6", "-crf", "28"]
        elif encoder == "libvpx-vp9":
            cmd += ["-crf", "30", "-b:v", "0", "-row-mt", "1"]
        elif encoder == "prores_ks":
            cmd += ["-profile:v", "3"]
        else:
            cmd += ["-preset", "medium", "-crf", "23"]
        if pix_fmt:
            cmd += ["-pix_fmt", pix_fmt]
        cmd += ["-c:a", "copy", "-map_metadata", "0", str(target)]
        return cmd

    def _video_target_path(self, output_dir, source_path, settings, action=None):
        action = action or self.file_conflict_action.get()
        naming_mode = {
            "原名_标签": "original_tag",
            "标签_原名": "tag_original",
            "仅原名": "original_only",
        }.get(self.export_filename_format.get(), "original_tag")
        base_target = ffmpeg.unique_video_output_path(output_dir, source_path, settings, True, naming_mode=naming_mode)
        if action == "跳过" and base_target.exists():
            return None
        if action == "覆盖":
            return base_target
        return ffmpeg.unique_video_output_path(output_dir, source_path, settings, False, naming_mode=naming_mode)

    def _run_encode_job(self, source_path, target, settings, job_id=None):
        if settings.quality_mode == "2PASS / 两遍码率":
            ok = self._run_two_pass(source_path, target, settings, job_id=job_id)
        else:
            ok = self._run_ffmpeg(ffmpeg.build_compress_command(source_path, target, settings), source_path, job_id=job_id)
        if ok:
            return True
        if not self._should_retry_with_cpu_h264(settings):
            return False
        return self._retry_encode_with_cpu_h264(source_path, target, settings, job_id=job_id)

    def _should_retry_with_cpu_h264(self, settings):
        if not self.auto_fallback_cpu_h264.get():
            return False
        if self.stop_requested:
            return False
        return settings.encoder_key != "CPU H.264 / AVC (libx264)"

    def _retry_encode_with_cpu_h264(self, source_path, target, settings, job_id=None):
        self.messages.put(("log", f"检测到编码失败，开始自动回退 CPU H.264：{source_path.name}"))
        if target.exists():
            try:
                target.unlink()
            except Exception as exc:
                self.messages.put(("log", f"清理失败的输出文件时出错：{exc}"))
        fallback_extra_args = settings.extra_ffmpeg_args
        if self.x264_threads.get() > 0 and "-threads" not in fallback_extra_args:
            fallback_extra_args = f"{fallback_extra_args} -threads {self.x264_threads.get()}".strip()
        if self.x264_command.get().strip():
            fallback_extra_args = f"{fallback_extra_args} {self.x264_command.get().strip()}".strip()
        fallback_settings = CompressionSettings(
            encoder_key="CPU H.264 / AVC (libx264)",
            preset_name=settings.preset_name,
            resolution_name=settings.resolution_name,
            sharpen_name=settings.sharpen_name,
            custom_width=settings.custom_width,
            custom_height=settings.custom_height,
            quality_mode="CRF / 恒定质量",
            cq_value=settings.cq_value,
            bitrate="",
            custom_command="",
            audio_mode=settings.audio_mode,
            audio_bitrate=settings.audio_bitrate,
            muxer_name=settings.muxer_name,
            output_speed=settings.output_speed,
            thumbnail_time=settings.thumbnail_time,
            overwrite=True,
            use_lut=settings.use_lut,
            lut_path=settings.lut_path,
            extra_ffmpeg_args=fallback_extra_args,
            hidden_watermark_enabled=settings.hidden_watermark_enabled,
            hidden_watermark_mode=settings.hidden_watermark_mode,
            hidden_watermark_text=settings.hidden_watermark_text,
            hidden_watermark_image=settings.hidden_watermark_image,
        )
        fallback_job_id = f"{job_id}_cpu_fallback" if job_id else None
        ok = self._run_ffmpeg(
            ffmpeg.build_compress_command(source_path, target, fallback_settings),
            source_path,
            job_id=fallback_job_id,
            title_suffix="自动回退 CPU H.264",
        )
        if ok:
            self.messages.put(("log", f"CPU H.264 回退编码成功：{source_path.name}"))
        else:
            self.messages.put(("log", f"CPU H.264 回退编码失败：{source_path.name}"))
            self.messages.put(("suggest_video_defaults", source_path.name))
        return ok

    def _run_two_pass(self, source_path, target, settings, job_id=None):
        temp = target.with_suffix(".passlog")
        base = ffmpeg.build_compress_command(source_path, target, settings)
        first = list(base[:-1]) + ["-pass", "1", "-an", "-f", "null", os.devnull]
        second = list(base[:-1]) + ["-pass", "2", str(target)]
        pass1_id = f"{job_id}_pass1" if job_id else None
        pass2_id = f"{job_id}_pass2" if job_id else None
        ok1 = self._run_ffmpeg(first, source_path, job_id=pass1_id, title_suffix="第 1 遍")
        ok2 = self._run_ffmpeg(second, source_path, job_id=pass2_id, title_suffix="第 2 遍") if ok1 else False
        try:
            if temp.exists():
                temp.unlink()
        except Exception:
            pass
        return ok1 and ok2

    def _thumbnail_worker(self, files):
        output_dir = Path(self.output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(files)
        thumbnail_time = self.thumbnail_time.get()
        for index, source in enumerate(files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            self.messages.put(("status", f"[{index}/{total}] 生成缩略图：{source_path.name}"))
            self._create_thumbnail(source_path, thumbnail_time, output_dir=output_dir)
            self.messages.put(("progress", index / total * 100))
        self.messages.put(("status", "缩略图任务完成" if not self.stop_requested else "缩略图任务已停止"))

    def _proxy_worker(self):
        output_dir = Path(self.output_dir.get()).resolve() / "proxy"
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(self.files)
        results = []
        for index, source in enumerate(self.files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            target = ffmpeg.unique_proxy_output_path(output_dir, source_path)
            start = time.perf_counter()
            self.messages.put(("status", f"[{index}/{total}] 生成代理文件：{source_path.name}"))
            ok = self._run_ffmpeg(ffmpeg.build_proxy_command(source_path, target), source_path)
            elapsed = time.perf_counter() - start
            results.append(CompressionResult(
                source=source_path,
                target=target,
                ok=ok,
                elapsed_seconds=elapsed,
                source_size=source_path.stat().st_size if source_path.exists() else 0,
                target_size=target.stat().st_size if ok and target.exists() else 0,
            ))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "代理文件完成" if not self.stop_requested else "代理文件已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _audio_worker(self):
        settings = self._audio_settings()
        total = len(self.audio_files)
        results = []
        last_output_dir = Path(self.audio_output_dir.get()).resolve()
        for index, source in enumerate(self.audio_files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            output_dir = source_path.parent if settings.output_mode == "和源文件同一目录" else Path(self.audio_output_dir.get()).resolve()
            last_output_dir = output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            target = ffmpeg.unique_audio_output_path(output_dir, source_path, settings)
            self.messages.put(("status", f"[{index}/{total}] 正在压缩音频：{source_path.name}"))
            results.append(self._convert_audio_one(source_path, target, settings))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "音频任务完成" if not self.stop_requested else "音频任务已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(last_output_dir)

    def _convert_audio_one(self, source_path, target, settings):
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        ok = self._run_ffmpeg(ffmpeg.build_audio_command(source_path, target, settings), source_path)
        elapsed = time.perf_counter() - start
        target_size = target.stat().st_size if ok and target.exists() else 0
        result = CompressionResult(source_path, target, ok, elapsed, source_size, target_size)
        self._log_compression_result(result)
        return result

    def _audio_reverse_worker(self):
        settings = self._audio_settings()
        total = len(self.audio_files)
        results = []
        last_output_dir = Path(self.audio_output_dir.get()).resolve()
        for index, source in enumerate(self.audio_files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            output_dir = source_path.parent if settings.output_mode == "和源文件同一目录" else Path(self.audio_output_dir.get()).resolve()
            last_output_dir = output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            _, suffix = AUDIO_ENCODERS[settings.encoder_name]
            target = ffmpeg.unique_path(output_dir, source_path, suffix, settings.overwrite, tag="reverse")
            self.messages.put(("status", f"[{index}/{total}] 倒放音频：{source_path.name}"))
            results.append(self._reverse_audio_one(source_path, target, settings))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "音频倒放完成" if not self.stop_requested else "音频倒放已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(last_output_dir)

    def _reverse_audio_one(self, source_path, target, settings):
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        ok = self._run_ffmpeg(self._build_audio_reverse_command(source_path, target, settings), source_path)
        elapsed = time.perf_counter() - start
        target_size = target.stat().st_size if ok and target.exists() else 0
        result = CompressionResult(source_path, target, ok, elapsed, source_size, target_size)
        self._log_compression_result(result)
        return result

    def _build_audio_reverse_command(self, source_path, target, settings):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        encoder, _ = AUDIO_ENCODERS[settings.encoder_name]
        filters = ["areverse"]
        if settings.normalize:
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        cmd = [ffmpeg_path, "-hide_banner", "-y" if settings.overwrite else "-n", "-i", str(source_path), "-vn", "-af", ",".join(filters), "-c:a", encoder]
        if settings.bitrate.strip() and encoder not in {"flac", "pcm_s16le"}:
            cmd += ["-b:a", settings.bitrate.strip()]
        if settings.sample_rate.strip():
            cmd += ["-ar", settings.sample_rate.strip()]
        if settings.channels.strip():
            cmd += ["-ac", settings.channels.strip()]
        cmd += [str(target)]
        return cmd

    def _retro_worker(self):
        output_dir = Path(self.retro_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        settings = self._retro_settings()
        total = len(self.retro_files)
        results = []
        for index, source in enumerate(self.retro_files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            target = ffmpeg.unique_retro_output_path(output_dir, source_path, settings)
            self.messages.put(("status", f"[{index}/{total}] 复古处理：{source_path.name}"))
            results.append(self._retro_one(source_path, target, settings))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "复古处理完成" if not self.stop_requested else "复古处理已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _retro_one(self, source_path, target, settings):
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        ok = self._run_ffmpeg(ffmpeg.build_retro_command(source_path, target, settings), source_path)
        elapsed = time.perf_counter() - start
        target_size = target.stat().st_size if ok and target.exists() else 0
        result = CompressionResult(source_path, target, ok, elapsed, source_size, target_size)
        self._log_compression_result(result)
        return result

    def _anamorphic_worker(self):
        output_dir = Path(self.anamorphic_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(self.anamorphic_files)
        results = []
        for index, source in enumerate(self.anamorphic_files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            target = self._anamorphic_target_path(output_dir, source_path)
            self.messages.put(("status", f"[{index}/{total}] 变形处理：{source_path.name}"))
            results.append(self._anamorphic_one(source_path, target))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "变形处理完成" if not self.stop_requested else "变形处理已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _anamorphic_one(self, source_path, target):
        start = time.perf_counter()
        source_size = source_path.stat().st_size if source_path.exists() else 0
        ok = self._run_ffmpeg(self._build_anamorphic_command(source_path, target), source_path)
        elapsed = time.perf_counter() - start
        target_size = target.stat().st_size if ok and target.exists() else 0
        result = CompressionResult(source_path, target, ok, elapsed, source_size, target_size)
        self._log_compression_result(result)
        return result

    def _mux_merge_worker(self):
        output_dir = Path(self.mux_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = VIDEO_MUXERS[self.mux_merge_format.get()]
        target = self._mux_merge_target_path(output_dir, suffix)
        list_path = output_dir / "_mux_concat_list.txt"
        list_text = "\n".join(f"file '{self._escape_concat_path(path)}'" for path in self.mux_merge_files)
        list_path.write_text(list_text, encoding="utf-8")
        try:
            self.messages.put(("status", "正在合并文件"))
            ok = self._run_ffmpeg(self._build_mux_merge_command(list_path, target), Path(self.mux_merge_files[0]))
            self.messages.put(("log", f"合并完成：{target}" if ok and target.exists() else "合并失败：请确认文件编码、分辨率、帧率和流结构兼容。"))
        finally:
            try:
                list_path.unlink()
            except Exception:
                pass

    def _mux_convert_worker(self):
        output_dir = Path(self.mux_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = VIDEO_MUXERS[self.mux_convert_format.get()]
        total = len(self.mux_convert_files)
        for index, raw in enumerate(self.mux_convert_files, start=1):
            if self.stop_requested:
                break
            source = Path(raw)
            target = ffmpeg.unique_path(output_dir, source, suffix, self.file_conflict_action.get() == "覆盖", tag="mux")
            self.messages.put(("status", f"[{index}/{total}] 封装转换：{source.name}"))
            ok = self._run_ffmpeg(self._build_mux_convert_command(source, target), source)
            self.messages.put(("log", f"封装完成：{target.name}" if ok and target.exists() else f"封装失败：{source.name}"))
            self.messages.put(("progress", index / total * 100))
        self.messages.put(("status", "封装转换完成" if not self.stop_requested else "封装转换已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _build_mux_merge_command(self, list_path, target):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        return [
            ffmpeg_path,
            "-hide_banner",
            "-y" if self.file_conflict_action.get() == "覆盖" else "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            "-map_metadata",
            "0",
            str(target),
        ]

    def _build_mux_convert_command(self, source, target):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [ffmpeg_path, "-hide_banner", "-y" if self.file_conflict_action.get() == "覆盖" else "-n", "-i", str(source), "-map", "0", "-c:v", "copy"]
        mode = self.mux_audio_mode.get()
        if mode == "复制音频":
            cmd += ["-c:a", "copy"]
        elif mode == "移除音频":
            cmd += ["-an"]
        else:
            audio_encoder = {
                "AAC 编码": "aac",
                "MP3 编码": "libmp3lame",
                "Opus 编码": "libopus",
                "FLAC 无损": "flac",
                "WAV PCM": "pcm_s16le",
            }.get(mode, "aac")
            cmd += ["-c:a", audio_encoder]
            if mode not in {"FLAC 无损", "WAV PCM"} and self.mux_audio_bitrate.get().strip():
                cmd += ["-b:a", self.mux_audio_bitrate.get().strip()]
        cmd += ["-map_metadata", "0", str(target)]
        return cmd

    def _mux_merge_target_path(self, output_dir, suffix):
        name = self.mux_merge_name.get().strip() or "merged"
        target = output_dir / f"{name}{suffix}"
        if self.file_conflict_action.get() == "覆盖" or not target.exists():
            return target
        counter = 1
        while True:
            candidate = output_dir / f"{name}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _escape_concat_path(self, path):
        return str(Path(path).resolve()).replace("\\", "/").replace("'", r"'\''")

    def _subtitle_mux_worker(self, source):
        output_dir = Path(self.subtitle_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = VIDEO_MUXERS[self.subtitle_output_format.get()]
        target = ffmpeg.unique_path(output_dir, source, suffix, self.file_conflict_action.get() == "覆盖", tag="subtitles")
        self.messages.put(("status", f"保存字幕封装：{source.name}"))
        ok = self._run_ffmpeg(self._build_subtitle_mux_command(source, target), source)
        self.messages.put(("log", f"字幕封装完成：{target}" if ok and target.exists() else "字幕封装失败"))
        if ok and self.auto_open_output.get():
            self._open_folder(output_dir)

    def _subtitle_export_worker(self, source, track):
        output_dir = Path(self.subtitle_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        lang = re.sub(r"[^A-Za-z0-9_-]+", "_", track.get("lang") or "und")
        target = output_dir / f"{source.stem}_subtitle_{track['stream_index']}_{lang}.srt"
        counter = 1
        while target.exists() and self.file_conflict_action.get() != "覆盖":
            target = output_dir / f"{source.stem}_subtitle_{track['stream_index']}_{lang}_{counter}.srt"
            counter += 1
        self.messages.put(("status", f"导出字幕：{source.name}"))
        ok = self._run_ffmpeg(self._build_subtitle_export_command(source, track["stream_index"], target), source)
        self.messages.put(("log", f"字幕已导出：{target}" if ok and target.exists() else "字幕导出失败：图形字幕可能无法直接导出为 SRT。"))

    def _build_subtitle_mux_command(self, source, target):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [ffmpeg_path, "-hide_banner", "-y" if self.file_conflict_action.get() == "覆盖" else "-n", "-i", str(source)]
        for subtitle in self.subtitle_external_files:
            cmd += ["-i", subtitle]
        for track in self.subtitle_tracks:
            if track["keep"]:
                cmd += ["-map", f"0:{track['stream_index']}"]
        for index, _ in enumerate(self.subtitle_external_files, start=1):
            cmd += ["-map", f"{index}:0"]
        cmd += ["-c", "copy"]
        suffix = target.suffix.lower()
        if suffix in {".mp4", ".mov", ".m4v"}:
            cmd += ["-c:s", "mov_text"]
        cmd += ["-map_metadata", "0", str(target)]
        return cmd

    def _build_subtitle_export_command(self, source, stream_index, target):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        return [
            ffmpeg_path,
            "-hide_banner",
            "-y" if self.file_conflict_action.get() == "覆盖" else "-n",
            "-i",
            str(source),
            "-map",
            f"0:{stream_index}",
            str(target),
        ]

    def _anamorphic_preview_worker(self, source_path):
        output_dir = Path(self.anamorphic_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / f"{source_path.stem}_anamorphic_preview.jpg"
        cmd = self._build_anamorphic_command(source_path, target, preview=True)
        self.messages.put(("status", f"生成变形预览帧：{source_path.name}"))
        ok = self._run_ffmpeg(cmd, source_path)
        if ok and target.exists():
            self.messages.put(("log", f"变形预览帧已生成：{target}"))
            self.messages.put(("anamorphic_preview", str(target)))
        else:
            self.messages.put(("log", "变形预览帧生成失败"))

    def _anamorphic_target_path(self, output_dir, source_path):
        suffix = source_path.suffix if source_path.suffix.lower() in VIDEO_EXTENSIONS else ".mp4"
        return ffmpeg.unique_path(output_dir, source_path, suffix, self.file_conflict_action.get() == "覆盖", tag="anamorphic")

    def _build_anamorphic_command(self, source_path, target, preview=False):
        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
        factor = self._float_or_default(self.anamorphic_factor.get(), 1.33)
        filters = [f"scale=trunc(iw*{factor:.4f}/2)*2:trunc(ih/2)*2"]
        if self.anamorphic_auto_crop.get():
            filters.append("unsharp=5:5:0.6:3:3:0.0")
        mode = self.anamorphic_mode.get()
        aspect = self._aspect_value(self.anamorphic_target_aspect.get())
        if mode == "裁切到目标画幅":
            filters.append(f"crop='trunc(min(iw,ih*{aspect:.6f})/2)*2':'trunc(min(ih,iw/{aspect:.6f})/2)*2'")
        elif mode == "加黑边适配目标画幅":
            filters.append(f"pad='trunc(max(iw,ih*{aspect:.6f})/2)*2':'trunc(max(ih,iw/{aspect:.6f})/2)*2':(ow-iw)/2:(oh-ih)/2:black")
        width = self._anamorphic_output_width()
        if width:
            filters.append(f"scale={width}:trunc(ow/a/2)*2")
        else:
            filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
        cmd = [ffmpeg_path, "-hide_banner", "-y", "-i", str(source_path), "-vf", ",".join(filters)]
        if preview:
            cmd += ["-frames:v", "1", "-q:v", "2", str(target)]
            return cmd
        encoder = ENCODERS.get(self.anamorphic_encoder_name.get(), "libx264")
        resolved_encoder, pix_fmt = ffmpeg.resolve_encoder(encoder)
        cmd += ["-c:v", resolved_encoder]
        if "nvenc" in resolved_encoder:
            cmd += ["-preset", "p5", "-rc", "vbr", "-cq", "23", "-b:v", "0"]
        elif resolved_encoder.endswith("_amf"):
            cmd += ["-quality", "balanced", "-rc", "cqp", "-qp_i", "23", "-qp_p", "23", "-qp_b", "23"]
        elif resolved_encoder.endswith("_videotoolbox"):
            cmd += ["-q:v", ffmpeg.videotoolbox_quality_value(23)]
            if resolved_encoder.startswith("hevc_") and Path(target).suffix.lower() in {".mov", ".mp4", ".m4v"}:
                cmd += ["-tag:v", "hvc1"]
        elif resolved_encoder == "prores_ks":
            cmd += ["-profile:v", "3"]
        elif resolved_encoder == "libsvtav1":
            cmd += ["-preset", "6", "-crf", "28"]
        elif resolved_encoder == "libvpx-vp9":
            cmd += ["-crf", "30", "-b:v", "0", "-row-mt", "1"]
        else:
            cmd += ["-preset", "medium", "-crf", "23"]
        if pix_fmt:
            cmd += ["-pix_fmt", pix_fmt]
        cmd += ["-c:a", "copy"] if self.anamorphic_keep_audio.get() else ["-an"]
        cmd += ["-map_metadata", "0", str(target)]
        return cmd

    def _anamorphic_output_width(self):
        mapping = {
            "4K 宽 3840": 3840,
            "2K 宽 2048": 2048,
            "1080p 宽 1920": 1920,
            "720p 宽 1280": 1280,
        }
        return mapping.get(self.anamorphic_resolution.get())

    def _aspect_value(self, text):
        if ":" in text:
            left, right = text.split(":", 1)
            return self._float_or_default(left, 2.39) / max(self._float_or_default(right, 1), 0.01)
        return self._float_or_default(text.replace(":1", ""), 2.39)

    def _float_or_default(self, value, default):
        try:
            return float(str(value).strip())
        except Exception:
            return default

    def _retro_remux_worker(self):
        total = len(self.retro_files)
        suffix = VIDEO_MUXERS[self.retro_remux_format.get()]
        audio_mode = "aac" if self.retro_remux_audio.get() == "AAC 重新编码" else "copy"
        results = []
        for index, source in enumerate(self.retro_files, start=1):
            if self.stop_requested:
                break
            source_path = Path(source)
            target = self._remux_target_path(source_path.parent, source_path, suffix)
            if target is None:
                self.messages.put(("log", f"文件已存在，已跳过：{source_path.name}"))
                continue
            self.messages.put(("status", f"[{index}/{total}] 封装转换：{source_path.name}"))
            start = time.perf_counter()
            ok = self._run_ffmpeg(ffmpeg.build_remux_command(source_path, target, audio_mode=audio_mode, overwrite=self.file_conflict_action.get() == "覆盖"), source_path)
            elapsed = time.perf_counter() - start
            results.append(CompressionResult(
                source=source_path,
                target=target,
                ok=ok,
                elapsed_seconds=elapsed,
                source_size=source_path.stat().st_size if source_path.exists() else 0,
                target_size=target.stat().st_size if ok and target.exists() else 0,
            ))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary(results)
        self.messages.put(("status", "封装转换完成" if not self.stop_requested else "封装转换已停止"))

    def _remux_target_path(self, output_dir, source_path, suffix):
        target = output_dir / f"{source_path.stem}_remux{suffix}"
        action = self.file_conflict_action.get()
        if action == "跳过" and target.exists():
            return None
        if action == "覆盖" or not target.exists():
            return target
        counter = 2
        while True:
            candidate = output_dir / f"{source_path.stem}_remux_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _lut_folder_preview_worker(self):
        video = Path(self.lut_page_video.get()).resolve()
        folder = Path(self.lut_page_folder.get()).resolve()
        output_dir = Path(self.lut_page_output.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        lut_files = [
            p for p in folder.rglob("*")
            if p.suffix.lower() in {".cube", ".3dl", ".dat", ".m3d"}
        ]
        self.messages.put(("lut_clear", ""))
        total = len(lut_files)
        if not total:
            self.messages.put(("log", "LUT 文件夹中没有找到可用 LUT 文件。"))
            return
        for index, lut in enumerate(lut_files, start=1):
            if self.stop_requested:
                break
            target = output_dir / f"{video.stem}_{lut.stem}.png"
            self.messages.put(("status", f"[{index}/{total}] 生成 LUT 缩略图：{lut.name}"))
            output = ffmpeg.run_capture(ffmpeg.build_lut_thumbnail_command(video, target, self.lut_page_time.get(), lut))
            if target.exists():
                self.messages.put(("lut_item", (lut.name, str(target))))
            else:
                self.messages.put(("log", f"LUT 缩略图失败：{lut.name} {output}"))
            self.messages.put(("progress", index / total * 100))
        self.messages.put(("status", "LUT 批量缩略图完成"))

    def _batch_worker(self):
        input_dir = Path(self.batch_input_dir.get()).resolve()
        output_dir = Path(self.batch_output_dir.get()).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        preset = BATCH_PRESETS[self.batch_preset_name.get()]
        settings = self._batch_video_settings(preset)
        audio_settings = AudioSettings(
            encoder_name="AAC (.m4a)",
            bitrate=preset["audio_bitrate"],
            sample_rate="48000",
            channels="2",
            overwrite=self.file_conflict_action.get() == "覆盖",
            normalize=False,
            output_mode="自定义",
            overwrite_source=False,
        )
        candidates = [
            p for p in input_dir.rglob("*")
            if p.is_file() and (p.suffix.lower() in VIDEO_EXTENSIONS or (self.batch_include_audio.get() and p.suffix.lower() in AUDIO_EXTENSIONS))
        ]
        total = len(candidates)
        if not total:
            self.messages.put(("log", "批量扫描没有找到可处理的媒体文件。"))
            return
        results = []
        for index, source_path in enumerate(candidates, start=1):
            if self.stop_requested:
                break
            target_dir = self._batch_target_dir(input_dir, output_dir, source_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            self.messages.put(("status", f"[{index}/{total}] 批量处理：{source_path.name}"))
            if source_path.suffix.lower() in VIDEO_EXTENSIONS:
                target = self._video_target_path(target_dir, source_path, settings)
                if target is None:
                    self.messages.put(("log", f"文件已存在，已跳过：{source_path.name}"))
                    self.messages.put(("progress", index / total * 100))
                    continue
                results.append(self._compress_one(source_path, target, settings))
            else:
                target = ffmpeg.unique_audio_output_path(target_dir, source_path, audio_settings)
                results.append(self._convert_audio_one(source_path, target, audio_settings))
            self.messages.put(("progress", index / total * 100))
        self._log_compression_summary([r for r in results if r])
        self.messages.put(("status", "批量压缩完成" if not self.stop_requested else "批量压缩已停止"))
        if self.auto_open_output.get() and not self.stop_requested:
            self._open_folder(output_dir)

    def _batch_video_settings(self, preset):
        resolution_name = preset["resolution"]
        if self.batch_vertical_mode.get():
            vertical_map = {
                "2160p / 4K": "竖屏 4K 2160x3840",
                "1440p / 2K": "竖屏 1440x2560",
                "1080p": "竖屏 1080x1920",
                "720p": "竖屏 720x1280",
            }
            resolution_name = vertical_map.get(resolution_name, resolution_name)
        return CompressionSettings(
            encoder_key=self._resolve_platform_encoder(preset["encoder"]),
            preset_name=self.preset_name.get(),
            resolution_name=resolution_name,
            sharpen_name=self.sharpen_name.get(),
            custom_width=self.custom_width.get(),
            custom_height=self.custom_height.get(),
            quality_mode="CRF / 恒定质量",
            cq_value=preset["cq"],
            bitrate="",
            custom_command="",
            audio_mode=preset["audio"],
            audio_bitrate=preset["audio_bitrate"],
            muxer_name=preset["muxer"],
            output_speed=self.output_speed.get(),
            thumbnail_time=self.thumbnail_time.get(),
            overwrite=self.file_conflict_action.get() == "覆盖",
            use_lut=self.use_lut.get(),
            lut_path=self.lut_path.get(),
            extra_ffmpeg_args=self.extra_ffmpeg_args.get(),
            hidden_watermark_enabled=self.hidden_watermark_enabled.get(),
            hidden_watermark_mode=self.hidden_watermark_mode.get(),
            hidden_watermark_text=self.hidden_watermark_text.get(),
            hidden_watermark_image=self.hidden_watermark_image.get(),
        )

    def _batch_target_dir(self, input_dir, output_dir, source_path):
        if not self.batch_keep_tree.get():
            return output_dir
        return output_dir / source_path.parent.relative_to(input_dir)

    def _lut_preview_worker(self, source_path):
        settings = self._settings()
        self.preview_path.parent.mkdir(parents=True, exist_ok=True)
        if self.preview_path.exists():
            self.preview_path.unlink()
        cmd = ffmpeg.build_preview_command(source_path, self.preview_path, settings)
        self.messages.put(("status", f"生成 LUT 预览：{source_path.name}"))
        output = ffmpeg.run_capture(cmd)
        if self.preview_path.exists():
            self.messages.put(("preview", str(self.preview_path)))
            self.messages.put(("log", f"LUT 预览已生成：{self.preview_path}"))
        else:
            self.messages.put(("log", "LUT 预览生成失败：" + output))
        self.messages.put(("status", "LUT 预览完成"))

    def _benchmark_worker(self, sample):
        settings = self._settings()
        bench_dir = Path(self.output_dir.get()).resolve() / "benchmark"
        bench_dir.mkdir(parents=True, exist_ok=True)
        jobs = [
            ("GPU H.265", "hevc_nvenc", bench_dir / "benchmark_gpu_h265.mp4"),
            ("AMD H.265", "hevc_amf", bench_dir / "benchmark_amd_h265.mp4"),
            ("Intel H.265", "hevc_qsv", bench_dir / "benchmark_intel_h265.mp4"),
            ("CPU H.265", "libx265", bench_dir / "benchmark_cpu_h265.mp4"),
        ]
        results = []
        for i, (name, encoder, target) in enumerate(jobs, start=1):
            if self.stop_requested:
                break
            start = time.perf_counter()
            cmd = ffmpeg.build_compress_command(sample, target, settings, encoder_override=encoder, benchmark=True)
            self.messages.put(("status", f"Benchmark {name} 运行中"))
            ok = self._run_ffmpeg(cmd, sample)
            elapsed = time.perf_counter() - start
            size = target.stat().st_size / 1024 / 1024 if target.exists() else 0
            results.append(f"{name}: {'成功' if ok else '失败'}，{elapsed:.1f}s，{size:.1f} MB")
            self.messages.put(("progress", i / len(jobs) * 100))
        self.messages.put(("log", "Benchmark 结果：" + " | ".join(results)))
        self.messages.put(("status", "Benchmark 完成"))

    def _run_ffmpeg(self, cmd, source, job_id=None, title_suffix="", show_job_window=True, benchmark_name=None):
        job_id = job_id or f"ffmpeg_{time.time_ns()}"
        duration = ffmpeg.duration_seconds(source)
        if "-progress" not in cmd and len(cmd) > 2:
            cmd = list(cmd[:-1]) + ["-progress", "pipe:1", "-nostats", cmd[-1]]
        title = Path(source).name
        if title_suffix:
            title = f"{title} - {title_suffix}"
        command_text = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
        if show_job_window:
            self.messages.put(("job_start", (job_id, title)))
        self.messages.put(("log", command_text))
        if show_job_window:
            self.messages.put(("job_log", (job_id, command_text)))
        try:
            creationflags = self._command_creationflags()
            if os.name == "nt" and "libx264" in [str(part) for part in cmd]:
                priority_flags = {"低": 0x00004000, "高": 0x00000080}
                creationflags |= priority_flags.get(self.x264_priority.get(), 0)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
            )
            self.active_ffmpeg_jobs[job_id] = {"process": process, "cancel": False}
            if job_id in self.cancelled_ffmpeg_jobs:
                self.active_ffmpeg_jobs[job_id]["cancel"] = True
            for line in process.stdout:
                job = self.active_ffmpeg_jobs.get(job_id, {})
                if self.stop_requested or job.get("cancel"):
                    process.terminate()
                    if show_job_window:
                        self.messages.put(("job_log", (job_id, "已请求停止此任务。")))
                        self.messages.put(("job_done", (job_id, False)))
                    return False
                line = line.strip()
                if line:
                    self.messages.put(("log", line))
                    if show_job_window:
                        self.messages.put(("job_log", (job_id, line)))
                    seconds = self._parse_ffmpeg_progress_seconds(line) or ffmpeg.parse_time(line)
                    if seconds and duration:
                        progress = min(seconds / duration * 100, 99)
                        self.messages.put(("subprogress", progress))
                        if show_job_window:
                            self.messages.put(("job_progress", (job_id, progress)))
                        if benchmark_name:
                            self.messages.put(("benchmark_update", (benchmark_name, f"运行中 {progress:.0f}%", "-", "-", "-")))
            code = process.wait()
            if code != 0:
                self.messages.put(("log", f"ffmpeg 退出码：{code}"))
                self.messages.put(("log", "编码失败提示：如果当前使用的是显卡硬件编码器，请换用 CPU H.264 / AVC (libx264) 后再次尝试。"))
                if show_job_window:
                    self.messages.put(("job_log", (job_id, f"ffmpeg 退出码：{code}")))
                    self.messages.put(("job_log", (job_id, "编码失败提示：如果当前使用的是显卡硬件编码器，请换用 CPU H.264 / AVC (libx264) 后再次尝试。")))
            if show_job_window:
                self.messages.put(("job_progress", (job_id, 100 if code == 0 else 0)))
                self.messages.put(("job_done", (job_id, code == 0)))
            return code == 0
        except FileNotFoundError:
            self.messages.put(("log", "未找到 ffmpeg，请安装并加入 PATH。"))
            if show_job_window:
                self.messages.put(("job_log", (job_id, "未找到 ffmpeg，请安装并加入 PATH。")))
                self.messages.put(("job_done", (job_id, False)))
            return False
        except Exception as exc:
            self.messages.put(("log", f"任务失败：{exc}"))
            self.messages.put(("log", "编码失败提示：如果当前使用的是显卡硬件编码器，请换用 CPU H.264 / AVC (libx264) 后再次尝试。"))
            if show_job_window:
                self.messages.put(("job_log", (job_id, f"任务失败：{exc}")))
                self.messages.put(("job_log", (job_id, "编码失败提示：如果当前使用的是显卡硬件编码器，请换用 CPU H.264 / AVC (libx264) 后再次尝试。")))
                self.messages.put(("job_done", (job_id, False)))
            return False
        finally:
            self.cancelled_ffmpeg_jobs.discard(job_id)
            self.active_ffmpeg_jobs.pop(job_id, None)

    def _parse_ffmpeg_progress_seconds(self, line):
        if line.startswith("out_time_ms="):
            try:
                return int(line.split("=", 1)[1]) / 1_000_000
            except Exception:
                return 0
        if line.startswith("out_time="):
            return ffmpeg.parse_time("time=" + line.split("=", 1)[1])
        return 0

    def _parse_time_seconds(self, value):
        text = str(value).strip()
        if not text:
            return 0
        if ":" not in text:
            try:
                return float(text)
            except Exception:
                return 0
        parts = text.split(":")
        try:
            numbers = [float(part) for part in parts]
        except Exception:
            return 0
        seconds = 0
        for number in numbers:
            seconds = seconds * 60 + number
        return seconds

    def _create_thumbnail(self, video_path, thumbnail_time, output_dir=None):
        thumb = (output_dir / f"{video_path.stem}.jpg") if output_dir else video_path.with_suffix(".jpg")
        self.messages.put(("status", f"生成缩略图：{thumb.name}"))
        ffmpeg.run_capture(ffmpeg.build_thumbnail_command(video_path, thumb, thumbnail_time))
        self.messages.put(("log", f"缩略图已生成：{thumb}"))

    def _log_compression_result(self, result: CompressionResult):
        if not result.ok:
            self.messages.put(("log", f"压缩失败：{result.source.name}，用时 {self._format_seconds(result.elapsed_seconds)}"))
            self.messages.put(("log", "建议换用 CPU H.264 / AVC (libx264) 编码器再次尝试。"))
            return
        self.messages.put((
            "log",
            (
                f"压缩完成：{result.source.name} -> {result.target.name} | "
                f"用时 {self._format_seconds(result.elapsed_seconds)} | "
                f"原大小 {self._format_size(result.source_size)} | "
                f"压后 {self._format_size(result.target_size)} | "
                f"压缩率 {result.saved_ratio:.1f}%"
            ),
        ))

    def _log_compression_summary(self, results):
        if len(results) <= 1:
            return
        finished = [result for result in results if result.ok]
        if not finished:
            self.messages.put(("log", "本次没有成功完成的压缩任务。"))
            return
        elapsed = sum(result.elapsed_seconds for result in finished)
        source_size = sum(result.source_size for result in finished)
        target_size = sum(result.target_size for result in finished)
        saved_ratio = max(0, (1 - target_size / source_size) * 100) if source_size and target_size else 0
        self.messages.put((
            "log",
            (
                f"批量汇总：成功 {len(finished)}/{len(results)} 个 | "
                f"总用时 {self._format_seconds(elapsed)} | "
                f"原大小 {self._format_size(source_size)} | "
                f"压后 {self._format_size(target_size)} | "
                f"总体压缩率 {saved_ratio:.1f}%"
            ),
        ))

    def _write_export_record_log(self, path, selected_count, started_at, finished_at, results, skipped):
        lines = [
            "MaruRebuild Export Record",
            f"任务开始时间: {started_at}",
            f"任务结束时间: {finished_at}",
            f"选择文件数: {selected_count}",
            f"成功/失败结果数: {len(results)}",
            f"跳过文件数: {len(skipped)}",
            "",
            "明细:",
        ]
        for result in results:
            status = "成功" if result.ok else "失败"
            target_folder = str(result.target.parent if result.target else "")
            size_text = self._format_size(result.target_size) if result.ok else "-"
            ratio_text = f"{result.saved_ratio:.1f}%" if result.ok else "-"
            start_text = result.started_at or "-"
            end_text = result.ended_at or "-"
            lines.append(
                (
                    f"[{status}] 原文件名: {result.source.name} | "
                    f"保存文件夹: {target_folder} | "
                    f"开始时间: {start_text} | "
                    f"结束时间: {end_text} | "
                    f"耗时: {self._format_seconds(result.elapsed_seconds)} | "
                    f"保存大小: {size_text} | "
                    f"压缩率: {ratio_text}"
                )
            )
        for source_path, reason in skipped:
            lines.append(
                (
                    f"[跳过] 原文件名: {source_path.name} | "
                    f"保存文件夹: - | 开始时间: - | 结束时间: - | 耗时: - | 保存大小: - | 压缩率: - | 原因: {reason}"
                )
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")

    def _selected_files(self):
        return [self.files[index] for index in self.file_list.curselection()]

    def _open_folder(self, folder):
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", str(folder)], creationflags=self._command_creationflags())
            elif self._is_macos():
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            self.messages.put(("log", f"打开输出目录失败：{exc}"))

    def _poll_resources(self):
        cpu = self._cpu_usage_percent()
        self._ensure_gpu_usage_poll()
        gpu = self._last_gpu_usage
        cpu_text = "--" if cpu is None else f"{cpu:.0f}"
        gpu_text = "--" if gpu is None else f"{gpu:.0f}"
        self.resource_status.set(f"CPU {cpu_text}%  |  GPU {gpu_text}%")
        self._append_resource_history(cpu, gpu)
        self._draw_resource_chart()
        self.root.after(1500, self._poll_resources)

    def _ensure_gpu_usage_poll(self):
        if self._gpu_poll_running:
            return
        self._gpu_poll_running = True
        threading.Thread(target=self._gpu_usage_worker, daemon=True).start()

    def _gpu_usage_worker(self):
        try:
            self._last_gpu_usage = self._gpu_usage_percent()
        finally:
            self._gpu_poll_running = False

    def _append_resource_history(self, cpu, gpu):
        self.cpu_history.append(0 if cpu is None else max(0, min(100, cpu)))
        self.gpu_history.append(0 if gpu is None else max(0, min(100, gpu)))
        self.cpu_history = self.cpu_history[-40:]
        self.gpu_history = self.gpu_history[-40:]

    def _draw_resource_chart(self):
        if not hasattr(self, "resource_canvas"):
            return
        colors = self.COLORS
        canvas = self.resource_canvas
        canvas.delete("all")
        width = int(canvas["width"])
        height = int(canvas["height"])
        canvas.create_text(8, 10, text="CPU", anchor="w", fill=colors["sparkline_cpu_label"], font=("Microsoft YaHei UI", 8, "bold"))
        canvas.create_text(8, 30, text="GPU", anchor="w", fill=colors["sparkline_gpu_label"], font=("Microsoft YaHei UI", 8, "bold"))
        self._draw_sparkline(canvas, self.cpu_history, 42, 6, width - 8, 20, colors["sparkline_cpu_line"])
        self._draw_sparkline(canvas, self.gpu_history, 42, 26, width - 8, 40, colors["sparkline_gpu_line"])

    def _draw_sparkline(self, canvas, values, x1, y1, x2, y2, color):
        canvas.create_rectangle(x1, y1, x2, y2, outline=self.COLORS["sparkline_border"], fill=self.COLORS["sparkline_bg"])
        if len(values) < 2:
            return
        step = (x2 - x1) / max(1, len(values) - 1)
        points = []
        for index, value in enumerate(values):
            x = x1 + index * step
            y = y2 - (value / 100) * (y2 - y1)
            points.extend((x, y))
        canvas.create_line(*points, fill=color, width=2, smooth=True)

    def _cpu_usage_percent(self):
        if os.name != "nt":
            if self._is_macos():
                lines = self._read_command_lines(["ps", "-A", "-o", "%cpu"], timeout=2)
                values = []
                for line in lines:
                    try:
                        values.append(float(line))
                    except Exception:
                        continue
                if not values:
                    return None
                cores = max(os.cpu_count() or 1, 1)
                return max(0, min(100, sum(values) / cores))
            return None

        class FileTime(ctypes.Structure):
            _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

        idle = FileTime()
        kernel = FileTime()
        user = FileTime()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        idle_value = (idle.dwHighDateTime << 32) | idle.dwLowDateTime
        kernel_value = (kernel.dwHighDateTime << 32) | kernel.dwLowDateTime
        user_value = (user.dwHighDateTime << 32) | user.dwLowDateTime
        current = (idle_value, kernel_value + user_value)
        previous = self._last_cpu_times
        self._last_cpu_times = current
        if not previous:
            return None
        idle_delta = current[0] - previous[0]
        total_delta = current[1] - previous[1]
        if total_delta <= 0:
            return None
        return max(0, min(100, (1 - idle_delta / total_delta) * 100))

    def _gpu_usage_percent(self):
        if os.name != "nt":
            return None
        commands = [
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$samples = Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -ErrorAction SilentlyContinue; "
                "$sum = ($samples | Where-Object {$_.Name -match 'engtype_(3D|Compute|VideoEncode|VideoDecode|Copy)'} | Measure-Object UtilizationPercentage -Sum).Sum; "
                "if ($null -eq $sum) {''} else {$sum}",
            ],
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$samples = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples; "
                "$sum = ($samples | Where-Object {$_.InstanceName -match 'engtype_(3d|compute|videoencode|videodecode|copy)'} | Measure-Object CookedValue -Sum).Sum; "
                "if ($null -eq $sum) {''} else {$sum}",
            ],
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
        ]
        for command in commands:
            try:
                output = subprocess.check_output(
                    command,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=1,
                    creationflags=self._command_creationflags(),
                )
                values = [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", output)]
                if values:
                    return max(0, min(100, sum(values)))
            except Exception:
                continue
        return None

    def _poll_messages(self):
        processed = 0
        while processed < 80:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break
            processed += 1
            if kind == "log":
                if not self.multi_job_mode:
                    self._log(payload)
            elif kind == "status":
                if not self.multi_job_mode:
                    self.current_task.set(payload)
                    self._log(payload)
            elif kind == "progress":
                self.progress.set(payload)
            elif kind == "subprogress":
                if not self.multi_job_mode:
                    self.progress.set(payload)
                    self.current_task.set(f"当前文件进度：{payload:.0f}%")
            elif kind == "multi_job_start":
                self._start_multi_job_mode(payload)
            elif kind == "multi_job_end":
                self._end_multi_job_mode(payload)
            elif kind == "job_start":
                job_id, title = payload
                self._create_job_window(job_id, title)
            elif kind == "job_log":
                job_id, text = payload
                self._append_job_log(job_id, text)
            elif kind == "job_progress":
                job_id, value = payload
                self._update_job_progress(job_id, value)
            elif kind == "job_done":
                job_id, ok = payload
                self._finish_job_window(job_id, ok)
            elif kind == "benchmark_update":
                self._update_benchmark_result(payload)
            elif kind == "benchmark_done":
                self._finish_benchmark(payload)
            elif kind == "environment_update":
                self._apply_environment_update(payload)
            elif kind == "preview":
                self._show_preview(payload)
            elif kind == "anamorphic_preview":
                self._show_anamorphic_preview(payload)
            elif kind == "task":
                task_id, status = payload
                self._update_task_status(task_id, status)
            elif kind == "lut_clear":
                self._clear_lut_thumbnails()
            elif kind == "lut_item":
                name, path = payload
                self._add_lut_thumbnail(name, path)
            elif kind == "suggest_video_defaults":
                self._prompt_restore_video_defaults(payload)
        delay = 30 if not self.messages.empty() else 120
        self.root.after(delay, self._poll_messages)

    def _log(self, text):
        self.log.insert(END, text)
        self.log.yview_moveto(1)

    def _prompt_restore_video_defaults(self, source_name):
        if self._restore_video_defaults_prompt_open:
            return
        self._restore_video_defaults_prompt_open = True
        try:
            message = (
                f"{source_name} 使用 CPU H.264 兜底仍然导出失败。\n\n"
                "这可能是当前压缩参数、滤镜、音频模式或自定义 x264 参数导致的。\n"
                "是否恢复视频压缩默认设置后再尝试？"
            )
            if messagebox.askyesno("导出失败", message):
                self._restore_video_compression_defaults()
                self._save_app_settings()
                self._log("已恢复视频压缩默认设置。")
        finally:
            self._restore_video_defaults_prompt_open = False

    def _restore_video_compression_defaults(self):
        self.encoder_name.set(self._preferred_video_encoder_name(prefer_gpu=True))
        self.advanced_encoders.set(False)
        self.preset_name.set("高速")
        self.resolution_name.set("保持原分辨率")
        self.sharpen_name.set("关闭")
        self.custom_width.set(1920)
        self.custom_height.set(1080)
        self.quality_mode.set("CRF / 恒定质量")
        self.cq_value.set(23)
        self.bitrate.set("")
        self.custom_command.set('-y -i "{input}" -c:v libx264 -crf 23 -c:a copy "{output}"')
        self.audio_mode.set("复制音频流")
        self.audio_bitrate.set("160k")
        self.muxer_name.set("MP4 (.mp4)")
        self.output_speed.set(1.0)
        self.extra_ffmpeg_args.set("")
        self.use_lut.set(False)
        self.lut_path.set("")
        self.hidden_watermark_enabled.set(False)
        self.hidden_watermark_mode.set("text")
        self.hidden_watermark_text.set("")
        self.hidden_watermark_image.set("")
        self.x264_threads.set(0)
        self.x264_command.set("")
        self.auto_fallback_cpu_h264.set(True)
        self.refresh_encoder_choices()

    def _start_multi_job_mode(self, total):
        self.multi_job_mode = total > 1
        self.multi_job_total = total
        self.multi_job_finished = 0
        if self.multi_job_mode:
            self.current_task.set(f"正在编码：0/{total}")
            self.progress.set(0)
            self._log(f"正在编码：共 {total} 个任务")

    def _end_multi_job_mode(self, completed):
        if self.multi_job_mode:
            text = "停止编码" if completed else "停止编码：任务已停止"
            self.current_task.set(text)
            self._log(text)
        self.multi_job_mode = False
        self.multi_job_total = 0
        self.multi_job_finished = 0

    def _update_benchmark_result(self, payload):
        name, status, size, ratio, elapsed = payload
        tree = getattr(self, "benchmark_result_tree", None)
        if not tree:
            return
        try:
            if tree.exists(name):
                tree.item(name, values=(name, status, size, ratio, elapsed))
        except Exception:
            pass

    def _finish_benchmark(self, text):
        status = getattr(self, "benchmark_status", None)
        if status:
            try:
                status.set(text)
            except Exception:
                pass
        self.current_task.set(text)
        self._log(text)

    def _create_job_window(self, job_id, title):
        if job_id in self.job_windows:
            return
        window = Toplevel(self.root)
        self._set_window_icon(window)
        window.title(f"任务进度 - {title}")
        self._set_window_geometry(window, "760x360")
        window.minsize(520, 260)
        box = ttk.Frame(window, padding=12)
        box.pack(fill="both", expand=True)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(2, weight=1)
        status = StringVar(value=f"运行中：{title}")
        progress = DoubleVar(value=0)
        ttk.Label(box, textvariable=status, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Progressbar(box, variable=progress, maximum=100).grid(row=1, column=0, sticky="ew", pady=(8, 10))
        log = Text(box, height=10, wrap="word", bg=self.COLORS["entry_bg"], fg=self.COLORS["text"], relief="solid", borderwidth=1)
        log.grid(row=2, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=log.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        log.configure(yscrollcommand=scrollbar.set, state="disabled")
        window.protocol("WM_DELETE_WINDOW", lambda: self._cancel_job_window(job_id))
        self.job_windows[job_id] = {
            "window": window,
            "status": status,
            "progress": progress,
            "log": log,
            "closed": False,
        }

    def _append_job_log(self, job_id, text):
        info = self.job_windows.get(job_id)
        if not info:
            return
        log = info["log"]
        log.configure(state="normal")
        log.insert(END, text + "\n")
        log.see(END)
        log.configure(state="disabled")

    def _update_job_progress(self, job_id, value):
        info = self.job_windows.get(job_id)
        if not info:
            return
        info["progress"].set(value)
        info["status"].set(f"当前文件进度：{value:.0f}%")

    def _finish_job_window(self, job_id, ok):
        info = self.job_windows.get(job_id)
        is_file_done = not job_id.endswith("_pass1")
        if self.multi_job_mode and is_file_done:
            self.multi_job_finished += 1
            total = max(1, self.multi_job_total)
            self.progress.set(min(self.multi_job_finished / total * 100, 100))
            self.current_task.set(f"正在编码：{self.multi_job_finished}/{total}")
        if not info or info.get("closed"):
            return
        info["progress"].set(100 if ok else info["progress"].get())
        info["done"] = True
        info["ok"] = ok
        self._append_job_log(job_id, "任务完成。" if ok else "任务已停止或失败。")
        if ok:
            self._countdown_close_job_window(job_id, 3)
        else:
            info["status"].set("已停止或失败")

    def _countdown_close_job_window(self, job_id, seconds):
        info = self.job_windows.get(job_id)
        if not info or info.get("closed"):
            return
        if seconds <= 0:
            try:
                info["window"].destroy()
            except Exception:
                pass
            self.job_windows.pop(job_id, None)
            return
        info["status"].set(f"已完成，{seconds} 秒后自动关闭")
        info["window"].after(1000, lambda: self._countdown_close_job_window(job_id, seconds - 1))

    def _cancel_job_window(self, job_id):
        info = self.job_windows.get(job_id)
        was_done = bool(info and info.get("done"))
        if info:
            info["closed"] = True
            try:
                info["window"].destroy()
            except Exception:
                pass
            self.job_windows.pop(job_id, None)
        job = self.active_ffmpeg_jobs.get(job_id)
        if job:
            job["cancel"] = True
            process = job.get("process")
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass
        elif not was_done:
            self.cancelled_ffmpeg_jobs.add(job_id)

    def _show_preview(self, path):
        self.preview_image = PhotoImage(file=path)
        self.preview_label.configure(image=self.preview_image, text="")

    def _show_anamorphic_preview(self, path):
        if not self.anamorphic_preview_window or not self.anamorphic_preview_window.winfo_exists():
            self.anamorphic_preview_window = Toplevel(self.root)
            self._set_window_icon(self.anamorphic_preview_window)
            self.anamorphic_preview_window.title("变形预览帧")
            self._set_window_geometry(self.anamorphic_preview_window, "960x540")
            self.anamorphic_preview_window.columnconfigure(0, weight=1)
            self.anamorphic_preview_window.rowconfigure(0, weight=1)
            self.anamorphic_preview_label = ttk.Label(self.anamorphic_preview_window, anchor="center")
            self.anamorphic_preview_label.grid(row=0, column=0, sticky="nsew")
        self.anamorphic_preview_image = PhotoImage(file=path)
        self.anamorphic_preview_label.configure(image=self.anamorphic_preview_image, text="")
        self.anamorphic_preview_window.lift()

    def _preview_source(self):
        selected = self._selected_files()
        if selected:
            return selected[0]
        if self.files:
            return self.files[0]
        return ""

    def _clear_lut_thumbnails(self):
        self.lut_preview_images.clear()
        self.lut_thumb_images.clear()
        if hasattr(self, "lut_result_strip"):
            for child in self.lut_result_strip.winfo_children():
                child.destroy()
        self._hide_lut_tooltip()

    def _add_lut_thumbnail(self, name, path):
        if not hasattr(self, "lut_result_strip"):
            return
        self.lut_preview_images[name] = path
        try:
            image = PhotoImage(file=path)
        except Exception:
            return
        image = self._fit_lut_thumbnail_image(image)
        self.lut_thumb_images[name] = image
        item = ttk.Frame(self.lut_result_strip, padding=(8, 8))
        item.pack(side="left", padx=(0, 8), pady=6)
        label = ttk.Label(item, image=image)
        label.pack()
        short_name = Path(name).stem
        ttk.Label(item, text=short_name[:16], style="Hint.TLabel").pack(pady=(5, 0))
        for widget in (item, label):
            widget.bind("<Enter>", lambda event, text=name: self._schedule_lut_tooltip(event, text))
            widget.bind("<Leave>", lambda event: self._hide_lut_tooltip())

    def _fit_lut_thumbnail_image(self, image, max_width=320, max_height=180):
        try:
            width = max(int(image.width()), 1)
            height = max(int(image.height()), 1)
        except Exception:
            return image
        scale = max(width / max_width, height / max_height, 1)
        if scale <= 1:
            return image
        factor = max(1, int(scale + 0.999))
        try:
            return image.subsample(factor, factor)
        except Exception:
            return image

    def _schedule_lut_tooltip(self, event, text):
        self._hide_lut_tooltip()
        x = event.x_root + 12
        y = event.y_root + 12
        self.lut_tooltip_after = self.root.after(1000, lambda: self._show_lut_tooltip(text, x, y))

    def _show_lut_tooltip(self, text, x, y):
        metrics = self._ui_metrics()
        self._hide_lut_tooltip(cancel_after=False)
        tip = Toplevel(self.root)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        ttk.Label(tip, text=text, padding=metrics["entry_pad"], relief="solid").pack()
        self.lut_tooltip = tip

    def _hide_lut_tooltip(self, cancel_after=True):
        if cancel_after and self.lut_tooltip_after:
            self.root.after_cancel(self.lut_tooltip_after)
            self.lut_tooltip_after = None
        if self.lut_tooltip:
            self.lut_tooltip.destroy()
            self.lut_tooltip = None

    def load_mediainfo(self):
        path = Path(self.media_info_path.get())
        if not path.exists():
            messagebox.showwarning("文件不存在", "请先选择有效的媒体文件。")
            return
        info = ffmpeg.probe_media_info(path)
        self._update_mediainfo_indicators(info or {})
        text = self._format_mediainfo(path, info) if info else "未能读取媒体信息。请确认 ffprobe 可用。"
        self.media_info_text.configure(state="normal")
        self.media_info_text.delete("1.0", END)
        self.media_info_text.insert("1.0", text)
        self.media_info_text.configure(state="disabled")

    def _update_mediainfo_indicators(self, info):
        if not hasattr(self, "media_feature_labels"):
            return
        features = self._extract_mediainfo_features(info)
        for name, label in self.media_feature_labels.items():
            on = bool(features.get(name))
            label.configure(text=f"{'●' if on else '○'} {name}", foreground="#16a34a" if on else "#9ca3af")

    def _extract_mediainfo_features(self, info):
        streams = info.get("streams", []) if isinstance(info, dict) else []
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        primary_video = video_streams[0] if video_streams else {}
        width = self._safe_int(primary_video.get("width"))
        height = self._safe_int(primary_video.get("height"))
        fps_text = self._fps_text(primary_video.get("avg_frame_rate") or primary_video.get("r_frame_rate"))
        fps_match = re.search(r"([0-9]+(?:\.[0-9]+)?)fps", fps_text)
        fps = float(fps_match.group(1)) if fps_match else 0.0
        bits = self._safe_int(primary_video.get("bits_per_raw_sample") or primary_video.get("bits_per_sample"))
        pix_fmt = str(primary_video.get("pix_fmt") or "").lower()
        transfer = str(primary_video.get("color_transfer") or "").lower()
        primaries = str(primary_video.get("color_primaries") or "").lower()
        hdr = transfer in {"smpte2084", "arib-std-b67"} or ("bt2020" in primaries and ("10" in pix_fmt or bits >= 10))
        is_dolby = any(
            str(stream.get("codec_name") or "").lower() in {"ac3", "eac3", "truehd"}
            or "dolby" in str(stream.get("codec_long_name") or "").lower()
            for stream in audio_streams
        )
        has_51 = any(
            self._safe_int(stream.get("channels")) >= 6
            or "5.1" in str(stream.get("channel_layout") or "").lower()
            for stream in audio_streams
        )
        return {
            "杜比音效": is_dolby,
            "5.1声道": has_51,
            "HDR": hdr,
            "10-bit": bits >= 10 or "10" in pix_fmt,
            "4K": width >= 3840 or height >= 2160,
            "高帧率": fps >= 50.0,
            "多音轨": len(audio_streams) >= 2,
        }

    def _format_mediainfo(self, path, info):
        fmt = info.get("format", {})
        streams = info.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
        duration = self._safe_float(fmt.get("duration"))
        bitrate = self._safe_int(fmt.get("bit_rate"))
        size = self._safe_int(fmt.get("size"))
        lines = [
            f"文件名：{path.name}",
            f"封装格式：{fmt.get('format_long_name') or fmt.get('format_name') or '未知'}",
            "",
            "整体参数",
            "",
            f"    文件体积：{self._format_size(size)}",
            f"    视频时长：{duration:.3f} 秒" if duration else "    视频时长：未知",
            f"    整体码率：{self._format_bitrate(bitrate)}",
        ]
        created = fmt.get("tags", {}).get("creation_time") or video.get("tags", {}).get("creation_time")
        if created:
            lines.append(f"    录制编码时间：{created}")
        if video:
            width = video.get("width")
            height = video.get("height")
            fps = self._fps_text(video.get("avg_frame_rate") or video.get("r_frame_rate"))
            frames = video.get("nb_frames")
            v_bitrate = self._safe_int(video.get("bit_rate"))
            profile = video.get("profile")
            level = video.get("level")
            level_text = f"@L{level / 30:.1f}" if isinstance(level, int) and level else ""
            lines += [
                "",
                "视频流",
                "",
                f"    编码格式：{self._codec_name(video)}{f'，{profile}{level_text} 规格' if profile else ''}",
                f"    分辨率：{self._resolution_label(width, height)}",
                f"    帧率：{fps}，{video.get('field_order') or '逐行扫描'}",
                f"    色彩规格：{self._color_text(video)}",
                f"    视频码率：{self._format_bitrate(v_bitrate)}",
                f"    总帧数：{frames or '未知'} 帧",
            ]
        if audio:
            a_bitrate = self._safe_int(audio.get("bit_rate"))
            lines += [
                "",
                "音频流",
                "",
                f"    编码格式：{self._codec_name(audio)}",
                f"    码率：{self._format_bitrate(a_bitrate)}",
                f"    采样率：{self._sample_rate_text(audio)}，{self._channels_text(audio)}",
            ]
        return "\n".join(lines)

    def _build_mediainfo_comparison_rows(self, path_a, info_a, path_b, info_b):
        left = self._mediainfo_snapshot(path_a, info_a)
        right = self._mediainfo_snapshot(path_b, info_b)
        metrics = [
            ("container", "封装格式"),
            ("size", "文件大小"),
            ("duration", "时长"),
            ("bitrate", "整体码率"),
            ("video_codec", "视频编码"),
            ("resolution", "分辨率"),
            ("fps", "帧率"),
            ("bit_depth", "位深"),
            ("pixel_format", "像素格式"),
            ("hdr", "HDR"),
            ("video_bitrate", "视频码率"),
            ("audio_codec", "音频编码"),
            ("audio_tracks", "音轨数量"),
            ("audio_channels", "音频声道"),
            ("audio_sample_rate", "采样率"),
            ("audio_bitrate", "音频码率"),
        ]
        rows = []
        for key, label in metrics:
            left_raw = left.get(key)
            right_raw = right.get(key)
            left_text = self._compare_value_text(key, left_raw)
            right_text = self._compare_value_text(key, right_raw)
            same = self._compare_equal(left_raw, right_raw)
            verdict = "相同" if same else "不同"
            delta_text = "-"
            if not same and isinstance(left_raw, (int, float)) and isinstance(right_raw, (int, float)):
                delta = right_raw - left_raw
                if key == "duration":
                    delta_text = f"{delta:+.3f}s"
                elif key in {"bitrate", "video_bitrate", "audio_bitrate"}:
                    delta_text = f"{self._format_bitrate(abs(int(delta)))}{'↑' if delta > 0 else '↓'}"
                elif key == "fps":
                    delta_text = f"{delta:+.3f}"
            rows.append((label, left_text, right_text, verdict, delta_text))
        return rows

    def _mediainfo_snapshot(self, path, info):
        fmt = info.get("format", {}) if isinstance(info, dict) else {}
        streams = info.get("streams", []) if isinstance(info, dict) else []
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        video = video_streams[0] if video_streams else {}
        audio = audio_streams[0] if audio_streams else {}
        features = self._extract_mediainfo_features(info or {})
        duration = self._safe_float(fmt.get("duration"))
        bitrate = self._safe_int(fmt.get("bit_rate"))
        width = self._safe_int(video.get("width"))
        height = self._safe_int(video.get("height"))
        fps = self._fps_value(video.get("avg_frame_rate") or video.get("r_frame_rate"))
        bits = self._safe_int(video.get("bits_per_raw_sample") or video.get("bits_per_sample"))
        return {
            "path": str(path),
            "container": fmt.get("format_long_name") or fmt.get("format_name") or "未知",
            "size": self._safe_int(fmt.get("size")),
            "duration": duration,
            "bitrate": bitrate,
            "video_codec": self._codec_name(video),
            "resolution": (width, height),
            "fps": fps,
            "bit_depth": bits,
            "pixel_format": str(video.get("pix_fmt") or "未知"),
            "hdr": bool(features.get("HDR")),
            "video_bitrate": self._safe_int(video.get("bit_rate")),
            "audio_codec": self._codec_name(audio),
            "audio_tracks": len(audio_streams),
            "audio_channels": self._safe_int(audio.get("channels")),
            "audio_sample_rate": self._safe_int(audio.get("sample_rate")),
            "audio_bitrate": self._safe_int(audio.get("bit_rate")),
        }

    def _compare_value_text(self, key, value):
        if key == "size":
            return self._format_size(value) if value else "未知"
        if key == "duration":
            return f"{value:.3f}s" if value else "未知"
        if key in {"bitrate", "video_bitrate", "audio_bitrate"}:
            return self._format_bitrate(int(value)) if value else "未知"
        if key == "resolution":
            width, height = value if isinstance(value, tuple) else (0, 0)
            return f"{width}x{height}" if width and height else "未知"
        if key == "fps":
            return f"{value:.3f}fps" if value else "未知"
        if key == "bit_depth":
            return f"{value}bit" if value else "未知"
        if key == "hdr":
            return "是" if value else "否"
        if key == "audio_tracks":
            return f"{value} 条" if value else "0 条"
        if key == "audio_channels":
            return f"{value} 声道" if value else "未知"
        if key == "audio_sample_rate":
            return f"{value}Hz" if value else "未知"
        if value is None:
            return "未知"
        text = str(value).strip()
        return text if text else "未知"

    def _compare_equal(self, left, right):
        if isinstance(left, tuple) and isinstance(right, tuple):
            return left == right
        if isinstance(left, float) or isinstance(right, float):
            return abs(float(left or 0) - float(right or 0)) < 0.005
        return left == right

    def _codec_name(self, stream):
        name = stream.get("codec_long_name") or stream.get("codec_name") or "未知"
        codec = stream.get("codec_name", "")
        if codec == "hevc":
            return "HEVC (H.265)"
        if codec == "h264":
            return "AVC (H.264)"
        if codec == "aac":
            return "AAC-LC 有损压缩"
        return name

    def _resolution_label(self, width, height):
        if not width or not height:
            return "未知"
        ratio = "16:9" if round(width / height, 2) == 1.78 else f"{width}:{height}"
        prefix = "4K " if width >= 3840 or height >= 2160 else ""
        return f"{prefix}{width}×{height}，画幅 {ratio}"

    def _color_text(self, stream):
        bits = stream.get("bits_per_raw_sample") or stream.get("bits_per_sample")
        pix_fmt = stream.get("pix_fmt") or "未知采样"
        space = stream.get("color_space") or "未知矩阵"
        range_text = "全色域" if stream.get("color_range") == "pc" else "有限色域"
        return f"{bits or '未知'}bit 位深、{pix_fmt}、{range_text}、{space} 矩阵"

    def _sample_rate_text(self, stream):
        sample_rate = self._safe_int(stream.get("sample_rate"))
        return f"{sample_rate / 1000:.0f}kHz" if sample_rate else "未知采样率"

    def _channels_text(self, stream):
        channels = stream.get("channels")
        layout = stream.get("channel_layout")
        if channels == 2:
            return "双声道立体声"
        return layout or (f"{channels} 声道" if channels else "未知声道")

    def _fps_text(self, value):
        fps = self._fps_value(value)
        if fps > 0:
            return f"恒定 {fps:.2f}fps"
        return "帧率未知"

    def _fps_value(self, value):
        try:
            num, den = value.split("/")
            den_val = float(den)
            if den_val == 0:
                return 0.0
            return float(num) / den_val
        except Exception:
            return 0.0

    def _format_bitrate(self, value):
        if not value:
            return "未知"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}Mbps"
        return f"{value / 1000:.0f}Kbps"

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except Exception:
            return 0

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except Exception:
            return 0.0

    @staticmethod
    def _format_size(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024
        return f"{value:.1f} TB"

    @staticmethod
    def _format_seconds(seconds):
        seconds = int(round(seconds))
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}小时{minutes}分{sec}秒"
        if minutes:
            return f"{minutes}分{sec}秒"
        return f"{sec}秒"

    @staticmethod
    def _format_clock(seconds):
        seconds = int(max(0, round(seconds)))
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}"
        return f"{minutes:02d}:{sec:02d}"


def run_app():
    try:
        try:
            from tkinterdnd2 import TkinterDnD
            root = TkinterDnD.Tk()
        except Exception:
            root = Tk()
        root.withdraw()
        root.update_idletasks()
        VideoCompressorApp(root)
        root.update_idletasks()
        root.deiconify()
        root.mainloop()
    except Exception:
        crash_log = Path.cwd() / "crash.log"
        crash_log.write_text(traceback.format_exc(), encoding="utf-8")
        raise
