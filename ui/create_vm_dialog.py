import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QSpinBox, QPushButton, QProgressBar, QMessageBox, QLabel, QGroupBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
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
        self.setWindowTitle("✨ 新建虚拟机")
        self.setFixedSize(550, 520)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🖥️ 创建新的虚拟机")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px 0;
        """)
        layout.addWidget(title_label)
        
        # 分组框 - 基本配置
        form_group = QGroupBox("⚙️ 基本配置")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #34495e;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 统一输入框样式
        input_style = """
            QLineEdit, QComboBox, QSpinBox {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-height: 24px;
                color: #2c3e50;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 5px 10px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e8f6f3;
                color: #2c3e50;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3498db;
                color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3498db;
                border: none;
                border-radius: 4px;
                width: 20px;
                height: 12px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #2980b9;
            }
            QFormLayout label {
                font-size: 14px;
                font-weight: bold;
                color: #34495e;
                padding: 5px;
            }
        """
        
        self.name_edit = QLineEdit("MyVM")
        self.name_edit.setStyleSheet(input_style)
        self.name_edit.setPlaceholderText("请输入虚拟机名称")
        form_layout.addRow("虚拟机名称:", self.name_edit)
        
        self.os_combo = QComboBox()
        self.os_combo.addItems(list(OS_OPTIONS.keys()))
        self.os_combo.setStyleSheet(input_style)
        form_layout.addRow("操作系统选择:", self.os_combo)
        
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setValue(1024)
        self.ram_spin.setSuffix(" MB")
        self.ram_spin.setStyleSheet(input_style)
        form_layout.addRow("内存分配:", self.ram_spin)
        
        self.disk_spin = QSpinBox()
        self.disk_spin.setRange(1, 1000)
        self.disk_spin.setValue(20)
        self.disk_spin.setSuffix(" GB")
        self.disk_spin.setStyleSheet(input_style)
        form_layout.addRow("磁盘大小:", self.disk_spin)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 进度区域
        progress_group = QGroupBox("📊 下载进度")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #34495e;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("等待开始...")
        self.progress_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            padding: 5px;
        """)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 25px;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 创建按钮
        button_layout = QVBoxLayout()
        
        self.create_btn = QPushButton("🚀 开始创建并下载镜像")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                color: white;
                border: 2px solid #2980b9;
                padding: 14px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5dade2, stop:1 #58d68d);
                border: 2px solid #3498db;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2874a6, stop:1 #27ae60);
                border: 2px solid #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
                border: 2px solid #95a5a6;
            }
        """)
        self.create_btn.setMinimumHeight(45)
        self.create_btn.clicked.connect(self.start_creation)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
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
