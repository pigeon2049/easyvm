import os
import subprocess
import threading
import time

QEMU_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qemu')
QEMU_EXE = os.path.join(QEMU_DIR, 'qemu-system-x86_64.exe')
QEMU_IMG = os.path.join(QEMU_DIR, 'qemu-img.exe')

class QemuEngine:
    def __init__(self):
        self.running_processes = {}

    def is_qemu_installed(self):
        if os.path.exists(QEMU_EXE):
            return True
        try:
            subprocess.run(["qemu-system-x86_64", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except FileNotFoundError:
            return False

    def create_disk(self, disk_path, size_gb):
        qemu_img_cmd = QEMU_IMG if os.path.exists(QEMU_IMG) else "qemu-img"
        
        cmd = [qemu_img_cmd, 'create', '-f', 'qcow2', disk_path, f"{size_gb}G"]
        
        creationflags = subprocess.CREATE_NO_WINDOW
        
        subprocess.run(cmd, creationflags=creationflags, check=True)

    def resize_disk(self, disk_path, new_size_gb):
        qemu_img_cmd = QEMU_IMG if os.path.exists(QEMU_IMG) else "qemu-img"
        cmd = [qemu_img_cmd, 'resize', disk_path, f"{new_size_gb}G"]
        creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.run(cmd, creationflags=creationflags, check=True)

    def start_vm(self, vm_config, on_exit_callback=None):
        vm_id = vm_config['id']
        ram = vm_config.get('ram_mb', 1024)
        disk_path = vm_config['disk_path']
        iso_path = vm_config.get('iso_path', '')
        
        qemu_exe_cmd = QEMU_EXE if os.path.exists(QEMU_EXE) else "qemu-system-x86_64"

        cmd = [
            qemu_exe_cmd,
            '-m', str(ram),
            '-smp', '2',
            '-drive', f"file={disk_path},format=qcow2,if=virtio",
            '-netdev', 'user,id=n1',
            '-device', f"virtio-net,netdev=n1,mac={vm_config['mac_address']}",
            '-vga', 'qxl'
        ]

        # 如果指定了 ISO 且文件存在，则挂载光驱并设置为对应优先级启动顺序
        boot_from_iso = vm_config.get('boot_from_iso', True)
        if iso_path and os.path.exists(iso_path):
            cmd.extend(['-cdrom', iso_path])
            if boot_from_iso:
                cmd.extend(['-boot', 'd']) # 首先从光盘引导 (首次装机)
            else:
                cmd.extend(['-boot', 'cd']) # 主硬盘设为最高引导，光盘作为第二顺位 (辅助挂载层)
        else:
            cmd.extend(['-boot', 'c'])
        
        whpx_cmd = cmd + ['-accel', 'whpx']
        tcg_cmd = cmd + ['-accel', 'tcg']
        
        def run_process():
            creationflags = subprocess.CREATE_NO_WINDOW
            
            proc = None
            try:
                # 尝试开启 WHPX
                proc = subprocess.Popen(whpx_cmd, creationflags=creationflags, stderr=subprocess.PIPE)
                
                try:
                    _, err = proc.communicate(timeout=1.5)
                    if proc.returncode != 0:
                        # WHPX 失败，降级为 TCG
                        error_msg = err.decode('utf-8', errors='ignore') if err else 'Unknown'
                        print(f"[{vm_id}] WHPX failed, falling back to TCG. Error: {error_msg}")
                        proc = subprocess.Popen(tcg_cmd, creationflags=creationflags)
                        self.running_processes[vm_id] = proc
                        proc.wait()
                except subprocess.TimeoutExpired:
                    # WHPX 启动成功，仍在运行
                    self.running_processes[vm_id] = proc
                    proc.wait()
            except Exception as e:
                print(f"Error starting VM: {e}")
            finally:
                if vm_id in self.running_processes:
                    del self.running_processes[vm_id]
                if on_exit_callback:
                    on_exit_callback(vm_id)

        t = threading.Thread(target=run_process, daemon=True)
        t.start()

    def stop_vm(self, vm_id):
        if vm_id in self.running_processes:
            proc = self.running_processes[vm_id]
            proc.terminate()
            del self.running_processes[vm_id]

qemu_engine = QemuEngine()
