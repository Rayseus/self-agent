"""测试公共配置：将 backend/ 加入 sys.path，使 `from app...` 可被解析。

同时提供占位环境变量，避免导入 app.config 时因缺失 GEMINI_API_KEY 等触发校验失败。
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
