import os
import glob
import traceback
import vpk
from typing import List, Dict, Set


class VPKConflictChecker:
    def __init__(self, match_keys: List[str]):
        # 将匹配路径转换为 bytes 并按长度降序排序以提高匹配效率
        self.match_keys = sorted(
            [key.encode("utf-8") for key in match_keys],
            key=lambda x: len(x),
            reverse=True
        )
        self.official_files: Set[bytes] = set()
        self.conflict_files: Dict[str, int] = {}
        self.total_addons = 0
        self.total_conflict = 0

    def should_file_check(self, filepath: bytes) -> bool:
        """检查文件路径是否需要被检测（bytes 类型比较）"""
        return any(filepath.startswith(path) for path in self.match_keys)

    def read_official_vpk(self, vpk_path: str):
        """读取官方VPK文件并记录需要监控的文件路径"""
        print("--------------------------------------------------------------")
        print(f"扫描官方VPK: {vpk_path}")
        package = vpk.open(vpk_path, path_enc=None)
        new_files = []

        for file_path in package:
            if file_path not in self.official_files and self.should_file_check(file_path):
                self.official_files.add(file_path)
                new_files.append(file_path)
                print(f"\t{file_path}")
        print(f"\t发现 {len(new_files)} 个需要监控的新文件")


    def scan_official_vpk_dir(self, search_root: str):
        """扫描官方VPK目录结构"""
        # 典型目录结构：游戏根目录/left4dead2/[pak01_dir.vpk]
        for root_file in os.listdir(search_root):
            dir_path = os.path.join(search_root, root_file)
            if not os.path.isdir(dir_path):
                continue
            for child_file in os.listdir(dir_path):
                vpk_file = os.path.join(dir_path, child_file)
                if not vpk_file.endswith("pak01_dir.vpk"):
                    continue
                if not os.path.isfile(vpk_file):
                    continue
                self.read_official_vpk(vpk_file)

    def check_custom_vpk(self, vpk_path: str):
        """检查单个MOD VPK文件"""
        print(f"> 正在检查: {os.path.basename(vpk_path)}")
        self.total_addons += 1
        conflicts = 0
        mod_package = vpk.open(vpk_path, path_enc=None)
        for file_path in mod_package:
            if file_path in self.official_files:
                print(f"\t* 冲突发现: {file_path}")
                conflicts += 1

        if conflicts > 0:
            self.total_conflict += conflicts
            self.conflict_files[vpk_path] = conflicts
            print(f"\t* 发现 {conflicts} 个冲突")


    def scan_mods_directory(self, search_root: str):
        """扫描MOD目录"""
        print("==============================================================")
        mod_paths = [
            os.path.join(search_root, "left4dead2", "addons"),
            os.path.join(search_root, "left4dead2", "addons", "workshop")
        ]

        for base_path in mod_paths:
            if not os.path.exists(base_path):
                print(f"预设的MOD目录不存在: {base_path}")
                continue

            print(f"扫描MOD目录: {base_path}")
            for vpk_file in os.listdir(base_path):
                vpk_file = os.path.join(base_path, vpk_file)
                if os.path.isfile(vpk_file) and vpk_file.endswith(".vpk"):
                    self.check_custom_vpk(vpk_file)

    def generate_report(self):
        """生成最终报告"""
        print("\n" + "=" * 60)
        print("冲突检测报告")
        print(f"官方文件库: {len(self.official_files)} 个监控文件")
        print(f"扫描MOD数量: {self.total_addons} 个")
        print(f"发现冲突MOD: {len(self.conflict_files)} 个")
        print(f"总冲突文件: {self.total_conflict} 个\n")

        if self.conflict_files:
            print("冲突文件列表:")
            for path, count in self.conflict_files.items():
                print(f"- [{count} 冲突] {path}")
        else:
            print("未发现任何文件冲突!")


if __name__ == '__main__':
    # 配置参数
    GAME_ROOT = "D:\\SteamLibrary\\steamapps\\common\\Left 4 Dead 2"
    MONITOR_PATHS = [
            "scripts/vscripts/tankrun.nuc",
            "scripts/vscripts/",
            "scripts/melee/",
            # "scripts/",
            # "models/",
    ]

    # 初始化检测器
    checker = VPKConflictChecker(MONITOR_PATHS)

    # 第一阶段：扫描官方文件
    print("正在扫描官方VPK文件...")
    checker.scan_official_vpk_dir(GAME_ROOT)

    # 第二阶段：扫描MOD文件
    print("\n正在扫描MOD文件...")
    checker.scan_mods_directory(GAME_ROOT)

    # 生成报告
    checker.generate_report()