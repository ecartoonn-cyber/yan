"""
版本控制模块 - Git提交和历史备份管理
"""
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import (
    PROJECT_ROOT,
    BACKUPS_DIR,
    MAX_BACKUPS,
    ensure_dirs,
)


class VersionControl:
    """版本管理器"""
    
    def __init__(self):
        self.git_dir = PROJECT_ROOT / ".git"
        ensure_dirs()
    
    def create_backup(self, source_file: Path, prefix: str = "backup") -> Optional[Path]:
        """创建带时间戳的备份文件"""
        if not source_file.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{prefix}_{timestamp}{source_file.suffix}"
        backup_path = BACKUPS_DIR / backup_name
        
        shutil.copy2(source_file, backup_path)
        self._cleanup_old_backups(prefix)
        return backup_path
    
    def _cleanup_old_backups(self, prefix: str):
        """清理旧备份，只保留最近MAX_BACKUPS个"""
        backups = sorted(
            BACKUPS_DIR.glob(f"{prefix}_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()
    
    def git_commit(self, message: str) -> bool:
        """执行Git提交"""
        if not self.git_dir.exists():
            return False
        
        try:
            # 添加所有更改
            subprocess.run(
                ["git", "add", "-A"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                check=True
            )
            # 提交
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=PROJECT_ROOT,
                capture_output=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    
    def git_push(self) -> bool:
        """推送到远程仓库"""
        if not self.git_dir.exists():
            return False
        
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=PROJECT_ROOT,
                capture_output=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    
    def create_version(self, files: list[Path], message: str = None) -> dict:
        """
        创建完整版本记录
        返回: {"backups": [...], "git_committed": bool, "git_pushed": bool}
        """
        result = {
            "backups": [],
            "git_committed": False,
            "git_pushed": False
        }
        
        # 创建备份
        for file_path in files:
            if file_path.exists():
                backup = self.create_backup(
                    file_path, 
                    prefix=file_path.stem
                )
                if backup:
                    result["backups"].append(str(backup))
        
        # Git提交
        if message is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"数据更新 {timestamp}"
        
        result["git_committed"] = self.git_commit(message)
        
        return result


# 全局实例
version_control = VersionControl()
