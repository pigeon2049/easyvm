import os
import subprocess
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from core.downloader import DownloadThread

QEMU_INSTALLER_URL = "https://qemu.weilnetz.de/w64/2026/qemu-w64-setup-20260318.exe"

class QemuDownloaderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("依赖缺失 - 下载 QEMU")
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout(self)
        self.label = QLabel("未检测到系统安装 QEMU 环境。\n开始为您自动下载并部署，请稍候...")
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.installer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qemu_setup.exe')
        
        self.thread = DownloadThread(QEMU_INSTALLER_URL, self.installer_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        
        self.thread.start()

    def on_download_finished(self, path):
        self.label.setText("下载完成，正在静默安装 QEMU 到默认目录...")
        self.progress_bar.setRange(0, 0) # 加载动画
        
        # 静默安装
        qemu_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qemu')
        try:
            cmd = [self.installer_path, '/S', f'/D={qemu_dir}']
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "安装完成", "虚拟机核心引擎已就绪！")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "安装失败", f"QEMU 部署失败：{e}\n请手动安装。")
            self.reject()

    def on_download_error(self, err):
        QMessageBox.warning(self, "下载失败", f"无法自动安装依赖，原因：{err}\n应用可继续运行，但启动虚拟机将报错。")
        self.reject()
