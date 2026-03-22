import json
import os
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CONFIG_FILE = os.path.join(DATA_DIR, 'vms.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class ConfigManager:
    def __init__(self):
        self.vms = self.load()

    def load(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.vms, f, indent=4)

    def add_vm(self, name, os_type, ram_mb, disk_size_gb):
        vm_id = str(uuid.uuid4())
        vm_dir = os.path.join(DATA_DIR, vm_id)
        if not os.path.exists(vm_dir):
            os.makedirs(vm_dir)
            
        disk_path = os.path.join(vm_dir, "disk.qcow2")
        
        self.vms[vm_id] = {
            "id": vm_id,
            "name": name,
            "os_type": os_type,
            "ram_mb": ram_mb,
            "disk_size_gb": disk_size_gb,
            "disk_path": disk_path,
            "iso_path": "", # 将在下载完成后更新
            "mac_address": f"52:54:00:{os.urandom(3).hex(':', 1)}",
            "status": "已停止"
        }
        self.save()
        return self.vms[vm_id]

    def update_vm(self, vm_id, data):
        if vm_id in self.vms:
            self.vms[vm_id].update(data)
            self.save()

    def delete_vm(self, vm_id):
        if vm_id in self.vms:
            del self.vms[vm_id]
            self.save()

    def get_all_vms(self):
        return list(self.vms.values())

config_manager = ConfigManager()
