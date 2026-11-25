import platform
import psutil
from datetime import datetime


class SystemMonitor:
    def __init__(self):
        psutil.cpu_percent(interval=None)
        self.last_net = psutil.net_io_counters()
        self.last_disk = psutil.disk_io_counters() if psutil.disk_io_counters() else None
        self.last_time = datetime.now()

    def collect(self):
        now = datetime.now()
        elapsed = max((now - self.last_time).total_seconds(), 0.1)

        cpu = psutil.cpu_percent(interval=0.2)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(psutil.disk_partitions()[0].mountpoint)

        net = psutil.net_io_counters()
        sent_kbps = max(0, net.bytes_sent - self.last_net.bytes_sent) / 1024 / elapsed
        recv_kbps = max(0, net.bytes_recv - self.last_net.bytes_recv) / 1024 / elapsed

        disk_read_kbps = 0.0
        disk_write_kbps = 0.0
        current_disk = psutil.disk_io_counters() if psutil.disk_io_counters() else None
        if self.last_disk and current_disk:
            disk_read_kbps = max(0, current_disk.read_bytes - self.last_disk.read_bytes) / 1024 / elapsed
            disk_write_kbps = max(0, current_disk.write_bytes - self.last_disk.write_bytes) / 1024 / elapsed

        process_list = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                process_list.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "cpu_percent": round(info["cpu_percent"] or 0, 1),
                    "memory_percent": round(info["memory_percent"] or 0, 1),
                    "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        top_cpu = sorted(process_list, key=lambda p: p["cpu_percent"], reverse=True)[:10]
        top_memory = sorted(process_list, key=lambda p: p["memory_mb"], reverse=True)[:10]

        metrics = {
            "timestamp": now,
            "cpu_percent": round(cpu, 1),
            "memory_percent": round(memory.percent, 1),
            "memory_used_gb": round(memory.used / (1024 ** 3), 2),
            "memory_total_gb": round(memory.total / (1024 ** 3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024 ** 3), 2),
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "network_sent_kbps": round(sent_kbps, 2),
            "network_recv_kbps": round(recv_kbps, 2),
            "disk_read_kbps": round(disk_read_kbps, 2),
            "disk_write_kbps": round(disk_write_kbps, 2),
            "process_count": len(process_list),
            "top_cpu_processes": top_cpu,
            "top_memory_processes": top_memory,
            "platform": platform.platform(),
            "hostname": platform.node(),
        }

        self.last_net = net
        self.last_disk = current_disk
        self.last_time = now
        return metrics
