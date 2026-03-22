from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer
from core.config import config_manager
from core.qemu_engine import qemu_engine
from ui.create_vm_dialog import CreateVmDialog
from ui.edit_vm_dialog import EditVmDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简易虚拟机控制台")
        self.resize(800, 400)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # 顶部工具区
        toolbar = QHBoxLayout()
        self.btn_new = QPushButton("新建虚拟机")
        self.btn_new.setStyleSheet("background-color: #0078D7; color: white; padding: 5px;")
        
        self.btn_start = QPushButton("启动 (Start)")
        self.btn_stop = QPushButton("关闭 (Stop)")
        self.btn_eject = QPushButton("光驱控制选项 (Eject/Mount)")
        self.btn_del = QPushButton("删除 (Delete)")
        
        self.btn_new.clicked.connect(self.on_new_vm)
        self.btn_start.clicked.connect(self.on_start_vm)
        self.btn_stop.clicked.connect(self.on_stop_vm)
        self.btn_eject.clicked.connect(self.on_toggle_iso)
        self.btn_del.clicked.connect(self.on_delete_vm)
        
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_start)
        toolbar.addWidget(self.btn_stop)
        toolbar.addWidget(self.btn_eject)
        toolbar.addWidget(self.btn_del)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 主机展示看板
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["主机名称", "系统类型", "已分配内存(MB)", "当前状态", "UID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnHidden(4, True) # 隐藏内部ID列
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
        # 使用 QTimer 周期性同步后台引擎真实运行状态
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_table)
        self.timer.start(1500)
        
        self.refresh_table()

    def refresh_table(self):
        vms = config_manager.get_all_vms()
        self.table.setRowCount(len(vms))
        
        for row, vm in enumerate(vms):
            self.table.setItem(row, 0, QTableWidgetItem(vm['name']))
            self.table.setItem(row, 1, QTableWidgetItem(vm['os_type']))
            self.table.setItem(row, 2, QTableWidgetItem(str(vm['ram_mb'])))
            
            # 核对底层进程映射池，若PID存在表示绝对在运行
            is_running = vm['id'] in qemu_engine.running_processes
            status = "运行中" if is_running else "已停止"
            self.table.setItem(row, 3, QTableWidgetItem(status))
            
            self.table.setItem(row, 4, QTableWidgetItem(vm['id']))

    def on_item_double_clicked(self, item):
        row = item.row()
        vm_id = self.table.item(row, 4).text()
        
        if vm_id in qemu_engine.running_processes:
            QMessageBox.warning(self, "提示", "虚拟机正在运行，为避免数据损坏，请先将其关闭后再尝试修改配置。")
            return
            
        vm_config = config_manager.vms.get(vm_id)
        if not vm_config:
            return
            
        dlg = EditVmDialog(vm_config, self)
        if dlg.exec_():
            self.refresh_table()

    def get_selected_vm_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.table.item(rows[0].row(), 4).text()

    def on_new_vm(self):
        dlg = CreateVmDialog(self)
        if dlg.exec_():
            self.refresh_table()

    def on_start_vm(self):
        vm_id = self.get_selected_vm_id()
        if not vm_id: 
            return QMessageBox.information(self, "提示", "请先选择需要启动的虚拟机")
        
        if vm_id in qemu_engine.running_processes:
            return QMessageBox.information(self, "提示", "无法执行：系统已经在运行中。")
            
        vm_config = config_manager.vms[vm_id]
        
        def on_exit(vid):
            config_manager.update_vm(vid, {'status': '已停止'})
            
        config_manager.update_vm(vm_id, {'status': '运行中'})
        qemu_engine.start_vm(vm_config, on_exit_callback=on_exit)
        self.refresh_table()

    def on_stop_vm(self):
        vm_id = self.get_selected_vm_id()
        if not vm_id: 
            return
        
        if vm_id in qemu_engine.running_processes:
            # 暴力结束进程，真实环境中可以发送 ACPI 关闭信号
            qemu_engine.stop_vm(vm_id)
            config_manager.update_vm(vm_id, {'status': '已停止'})
            self.refresh_table()
        else:
            QMessageBox.information(self, "提示", "虚拟机处于停止状态，无法触发关闭。")

    def on_delete_vm(self):
        vm_id = self.get_selected_vm_id()
        if not vm_id: return
        
        reply = QMessageBox.question(self, "彻底删除", "确定要无情删除该虚拟环境及关联数据吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if vm_id in qemu_engine.running_processes:
                qemu_engine.stop_vm(vm_id)
            config_manager.delete_vm(vm_id)
            self.refresh_table()

    def on_selection_changed(self):
        vm_id = self.get_selected_vm_id()
        if not vm_id:
            self.btn_eject.setText("光驱选项 (无选取对象)")
            return
        vm = config_manager.vms.get(vm_id)
        if vm and vm.get('iso_path'):
            self.btn_eject.setText("分离此安装盘 (Eject ISO)")
        else:
            self.btn_eject.setText("为它挂载光盘 (Mount ISO)")

    def on_toggle_iso(self):
        vm_id = self.get_selected_vm_id()
        if not vm_id: 
            return QMessageBox.information(self, "提示", "请先选择需要操作的虚拟机。")
        
        vm = config_manager.vms.get(vm_id)
        if not vm: return
        
        if vm.get('iso_path'):
            config_manager.update_vm(vm_id, {'iso_path': ''})
            self.on_selection_changed()
            if vm_id in qemu_engine.running_processes:
                QMessageBox.information(self, "分离成功", "系统盘已剥离配置！\n由于当前的虚拟机正在运行，它将在您下次重启机器时将光盘彻底拔出。届时将直接从本地主虚拟硬盘引导。")
            else:
                QMessageBox.information(self, "分离成功", "安装光盘已弹出！\n下一次启动该机器时，将直接从原生主硬盘极速引导。")
        else:
            iso_path, _ = QFileDialog.getOpenFileName(self, "选择系统或辅助工具镜像 (ISO)", "", "ISO 镜像文件 (*.iso);;所有镜像文件 (*)")
            if iso_path:
                config_manager.update_vm(vm_id, {'iso_path': iso_path, 'boot_from_iso': False})
                self.on_selection_changed()
                if vm_id in qemu_engine.running_processes:
                    QMessageBox.information(self, "挂载就绪", "ISO 镜像成功置入光驱舱。\n因为虚拟机正开启，请完全关闭它再重新启动后以便识别这个光盘。引导系统依然从主硬盘优先启动。")
                else:
                    QMessageBox.information(self, "挂载成功", "光盘配置成功！\n下次运行启动时这枚光盘可供底层读取。我们已经向内核设置了『硬盘优先启动级』，请随时放心启动跑系统吧。")
