import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QSpinBox, QPushButton, QProgressBar, QMessageBox, QLabel)
from core.downloader import DownloadThread
from core.qemu_engine import qemu_engine
from core.config import config_manager

OS_OPTIONS = {
    "Alpine Linux (清华源默认, 极速)": "https://mirrors.tuna.tsinghua.edu.cn/alpine/latest-stable/releases/x86/alpine-extended-3.23.3-x86.iso",
    "Ubuntu Live Server (清华源)": "https://mirrors.tuna.tsinghua.edu.cn/ubuntu-releases/questing/ubuntu-25.10-live-server-amd64.iso",
    "Debian Netinst (清华源)": "https://mirrors.tuna.tsinghua.edu.cn/debian-cd/current/amd64/iso-cd/debian-13.4.0-amd64-netinst.iso"
}

class CreateVmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建虚拟机")
        self.setFixedSize(450, 300)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit("MyVM")
        form_layout.addRow("虚拟机名称:", self.name_edit)
        
        self.os_combo = QComboBox()
        self.os_combo.addItems(list(OS_OPTIONS.keys()))
        form_layout.addRow("操作系统选择:", self.os_combo)
        
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setValue(1024)
        self.ram_spin.setSuffix(" MB")
        form_layout.addRow("内存分配:", self.ram_spin)
        
        self.disk_spin = QSpinBox()
        self.disk_spin.setRange(1, 1000)
        self.disk_spin.setValue(20)
        self.disk_spin.setSuffix(" GB")
        form_layout.addRow("磁盘大小:", self.disk_spin)
        
        layout.addLayout(form_layout)
        
        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.create_btn = QPushButton("开始创建并下载镜像")
        self.create_btn.clicked.connect(self.start_creation)
        layout.addWidget(self.create_btn)
        
        self.vm_id = None

    def start_creation(self):
        name = self.name_edit.text()
        os_name = self.os_combo.currentText()
        url = OS_OPTIONS[os_name]
        ram = self.ram_spin.value()
        disk = self.disk_spin.value()
        
        if not name:
            QMessageBox.warning(self, "警告", "名称为空，请填写名称。")
            return
            
        self.create_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_label.setText("正在配置虚拟磁盘环境...")
        
        # 写入数据库记录
        vm_info = config_manager.add_vm(name, os_name, ram, disk)
        self.vm_id = vm_info['id']
        disk_path = vm_info['disk_path']
        
        # 调用核心引擎申请 qcow2 磁盘
        try:
            qemu_engine.create_disk(disk_path, disk)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"虚拟磁盘生成失败:\n{e}")
            self.reject()
            return
            
        # 增加缓存机制：检查本地是否有已下载的 ISO
        ISO_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'iso_cache')
        if not os.path.exists(ISO_CACHE_DIR):
            os.makedirs(ISO_CACHE_DIR)
            
        iso_name = url.split('/')[-1]
        cached_iso_path = os.path.join(ISO_CACHE_DIR, iso_name)
        
        if os.path.exists(cached_iso_path) and os.path.getsize(cached_iso_path) > 1024 * 1024:
            self.progress_bar.show()
            self.progress_bar.setValue(100)
            self.progress_label.setText("已找到本地镜像缓存，跳过下载！")
            self.on_download_finished(cached_iso_path)
            return

        # 并发下载操作系统 ISO 镜像
        self.progress_label.setText("首次部署此系统，正在下载安装介质...")
        self.thread = DownloadThread(url, cached_iso_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        self.thread.start()

    def on_download_finished(self, path):
        config_manager.update_vm(self.vm_id, {"iso_path": path})
        QMessageBox.information(self, "环境就绪", "虚拟机创建成功，启动后会自动引导安装介质。")
        self.accept()

    def on_download_error(self, err):
        QMessageBox.warning(self, "下载失败", f"镜像数据下载超时或失败: {err}\n配置已基本生成，请尝试手动更换有效 ISO 启动。")
        self.reject()
