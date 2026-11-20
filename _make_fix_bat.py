# -*- coding: utf-8 -*-
"""在桌面生成「修复网关计划任务」批处理（CRLF 换行）"""
from pathlib import Path

BAT = Path(r"C:\Users\Administrator\Desktop\修复Hermes网关计划任务.bat")

CONTENT = r'''@echo off
chcp 65001 >nul
title 修复 Hermes 网关计划任务
echo ==================================================
echo   修复 Hermes 网关计划任务
echo   把旧的 S4U 模板换成新模板（防止所有定时任务一起失效）
echo ==================================================
echo.

set "HERMES=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe"
if not exist "%HERMES%" set "HERMES=hermes"

echo [1/3] 重新注册计划任务...
"%HERMES%" gateway install
echo.

echo [2/3] 启动网关...
"%HERMES%" gateway start
echo.

echo [3/3] 检查定时任务状态...
"%HERMES%" cron status
echo.
echo ==================================================
echo   修复完成的标准：
echo   1. 出现 "Scheduled Task registered"
echo   2. 不再出现 "predates the current template (S4U)"
echo   3. cron status 显示 Gateway is running
echo ==================================================
echo.
echo 按任意键关闭本窗口...
pause >nul
'''

# .bat 必须用 CRLF
BAT.write_text(CONTENT.replace("\n", "\r\n"), encoding="utf-8", newline="")
print(f"✓ 已生成: {BAT}")
print(f"  大小: {BAT.stat().st_size} 字节")
print(f"  行数: {len(CONTENT.splitlines())}")

# 验证能读回
back = BAT.read_text(encoding="utf-8")
print(f"  校验: {'✓ 内容完整' if 'gateway install' in back and 'cron status' in back else '✗ 内容异常'}")
print(f"  hermes 路径: {'✓ 绝对路径已写入' if 'hermes.exe' in back else '✗ 缺失'}")
