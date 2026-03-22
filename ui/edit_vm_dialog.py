from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox, QPushButton, QMessageBox)
from core.qemu_engine import qemu_engine
from core.config import config_manager

class EditVmDialog(QDialog):
    def __init__(self, vm_info, parent=None):
        super().__init__(parent)
        self.vm_info = vm_info
        self.setWindowTitle(f"编辑 {vm_info['name']}")
        self.setFixedSize(350, 200)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setValue(int(vm_info.get('ram_mb', 1024)))
        self.ram_spin.setSuffix(" MB")
        form_layout.addRow("内存大小:", self.ram_spin)

        self.disk_spin = QSpinBox()
        self.disk_spin.setRange(1, 4000)
        self.disk_spin.setValue(int(vm_info.get('disk_size_gb', 20)))
        self.disk_spin.setSuffix(" GB")
        form_layout.addRow("磁盘大小 (只增不减):", self.disk_spin)

        layout.addLayout(form_layout)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_changes)
        layout.addWidget(self.save_btn)

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
