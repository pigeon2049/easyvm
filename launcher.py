import sys
from PyQt5.QtWidgets import QApplication
from core.qemu_engine import qemu_engine
from ui.qemu_downloader_dialog import QemuDownloaderDialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 全局美化样式表
    global_style = """
        /* 全局字体和颜色 */
        * {
            font-family: "Microsoft YaHei UI", "Segoe UI", Arial, sans-serif;
            font-size: 13px;
        }
        
        /* 工具提示样式 */
        QToolTip {
            background-color: #2c3e50;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        /* 消息框样式 */
        QMessageBox {
            background-color: #f5f7fa;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #3498db;
            color: white;
            border: 2px solid #2980b9;
            padding: 10px 24px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #5dade2;
            border: 2px solid #3498db;
        }
        QMessageBox QPushButton:pressed {
            background-color: #2874a6;
            border: 2px solid #21618c;
        }
        
        /* 滚动条全局样式 */
        QScrollBar:horizontal {
            border: none;
            background: #f5f7fa;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #bdc3c7;
            border-radius: 5px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #95a5a6;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        
        /* 菜单样式 */
        QMenu {
            background-color: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 5px;
        }
        QMenu::item {
            padding: 8px 25px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
        QMenu::separator {
            height: 2px;
            background: #e0e0e0;
            margin: 5px 10px;
        }
    """
    
    app.setStyleSheet(global_style)
    
    # 核心体验点:启动时检验系统级依赖
    if not qemu_engine.is_qemu_installed():
        dlg = QemuDownloaderDialog()
        dlg.exec_()
        # 无论成功失败都强制进入主控制面板

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()