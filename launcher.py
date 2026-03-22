import sys
from PyQt5.QtWidgets import QApplication
from core.qemu_engine import qemu_engine
from ui.qemu_downloader_dialog import QemuDownloaderDialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 核心体验点：启动时检验系统级依赖
    if not qemu_engine.is_qemu_installed():
        dlg = QemuDownloaderDialog()
        dlg.exec_()
        # 无论成功失败都强制进入主控制面板

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()