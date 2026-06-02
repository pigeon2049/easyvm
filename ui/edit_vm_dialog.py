from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox, QPushButton, QMessageBox, QLabel, QGroupBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from core.qemu_engine import qemu_engine
from core.config import config_manager

class EditVmDialog(QDialog):
    def __init__(self, vm_info, parent=None):
        super().__init__(parent)
        self.vm_info = vm_info
        self.setWindowTitle(f"✏️ 编辑 {vm_info['name']}")
        self.setFixedSize(500, 380)
        
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
        title_label = QLabel(f"⚙️ 编辑虚拟机配置 - {vm_info['name']}")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px 0;
        """)
        layout.addWidget(title_label)
        
        # 分组框
        form_group = QGroupBox("🔧 资源配置")
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
            QSpinBox {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-height: 24px;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
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
        """
        
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setValue(int(vm_info.get('ram_mb', 1024)))
        self.ram_spin.setSuffix(" MB")
        self.ram_spin.setStyleSheet(input_style)
        form_layout.addRow("内存大小:", self.ram_spin)
        
        self.disk_spin = QSpinBox()
        self.disk_spin.setRange(1, 4000)
        self.disk_spin.setValue(int(vm_info.get('disk_size_gb', 20)))
        self.disk_spin.setSuffix(" GB")
        self.disk_spin.setStyleSheet(input_style)
        form_layout.addRow("磁盘大小 (只增不减):", self.disk_spin)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # 按钮区域
        button_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setStyleSheet("""
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
        """)
        self.save_btn.setMinimumHeight(45)
        self.save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)

    def save_changes(self):
        new_ram = self.ram_spin.value()
        new_disk = self.disk_spin.value()
        old_disk = int(self.vm_info.get('disk_size_gb', 20))

        if new_disk < old_disk:
            QMessageBox.warning(self, "无效操作", "磁盘大小不能缩小，只能扩大。")
            self.disk_spin.setValue(old_disk)
            return

        updates = {'ram_mb': new_ram}
        
        if new_disk > old_disk:
            disk_path = self.vm_info['disk_path']
            try:
                qemu_engine.resize_disk(disk_path, new_disk)
                updates['disk_size_gb'] = new_disk
                QMessageBox.information(self, "成功", "磁盘扩容成功！\n请注意：由于底层磁盘已无损扩容，需要您在系统内部使用内置的分区工具和文件系统调整工具将新的空间挂载出来。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"虚拟磁盘扩容失败:\n{e}")
                return

        config_manager.update_vm(self.vm_info['id'], updates)
        self.accept()
