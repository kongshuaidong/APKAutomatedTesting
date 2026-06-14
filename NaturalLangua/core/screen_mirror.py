# ============================================================
# 【设备层】screen_mirror.py
# 职责：启动/停止手机实时投屏
# 依赖工具：scrcpy（开源投屏工具，非 Python 库）
#   - 原理：在手机上部署一个服务端 APK，通过 ADB socket 传输视频流，
#     PC 端用 SDL 渲染窗口实时显示，延迟通常 < 50ms
#   - 项目地址：https://github.com/Genymobile/scrcpy
# ============================================================

import subprocess
import shutil
from utils.logger import logger
from config import SCRCPY_PATH


class ScreenMirror:
    """手机屏幕实时投屏控制器"""

    def __init__(self, device_serial: str = None):
        self.device_serial = device_serial          # 指定投屏的设备序列号（多设备时需要）
        self.process: subprocess.Popen = None       # scrcpy 子进程句柄

    def _check_scrcpy(self) -> bool:
        """检查 scrcpy 可执行文件是否存在，防止因未安装而报错"""
        if shutil.which(SCRCPY_PATH):   # 在系统 PATH 中查找
            return True
        try:
            # 如果 PATH 里没有，尝试直接执行配置的路径
            result = subprocess.run(
                [SCRCPY_PATH, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def start(
        self,
        window_title: str = "Phone Screen - NL Automation",
        max_size: int = 900,        # 投屏窗口最大边长（像素），越大越清晰但越耗性能
        bit_rate: str = "4M",       # 视频码率，越高越清晰，建议 2M~8M
        always_on_top: bool = False,
        no_audio: bool = True,      # 默认关闭音频，避免声音干扰
    ):
        """
        启动投屏：用 subprocess 拉起 scrcpy 进程，窗口在单独的 GUI 窗口中显示。
        scrcpy 在后台运行，不阻塞主程序。
        """
        if not self._check_scrcpy():
            raise RuntimeError(
                f"scrcpy not found at '{SCRCPY_PATH}'.\n"
                "  • Windows: https://github.com/Genymobile/scrcpy/releases\n"
                "  • Or set SCRCPY_PATH in your .env file."
            )

        if self.is_running():
            logger.warning("Screen mirroring is already running.")
            return

        # 构建 scrcpy 命令行参数
        cmd = [SCRCPY_PATH]

        if self.device_serial:
            cmd += ["-s", self.device_serial]   # 多设备时指定目标设备

        cmd += [
            "--window-title", window_title,
            "--max-size", str(max_size),
            "--video-bit-rate", bit_rate,
        ]

        if no_audio:
            cmd += ["--no-audio"]

        if always_on_top:
            cmd += ["--always-on-top"]

        logger.info(f"Starting scrcpy: {' '.join(cmd)}")

        # 用 Popen 非阻塞启动，stdout/stderr 丢弃避免干扰主程序输出
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Screen mirroring started (scrcpy window should appear).")

    def stop(self):
        """终止 scrcpy 进程，关闭投屏窗口"""
        if self.process and self.is_running():
            self.process.terminate()        # 先尝试优雅退出
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()         # 超时则强制杀进程
            logger.info("Screen mirroring stopped.")
        self.process = None

    def is_running(self) -> bool:
        """检查 scrcpy 进程是否仍在运行（poll() 返回 None 表示进程未结束）"""
        return self.process is not None and self.process.poll() is None
