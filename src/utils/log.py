import logging
import sys
from pathlib import Path


def setup_logging(level: str = 'INFO'):
    """
    設定日誌系統

    Args:
        level: 日誌等級 (FATAL, ERROR, WARNING, INFO)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 建立日誌格式
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 設定根 logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('results/grading.log', encoding='utf-8'),
        ],
    )

    # 建立 results 目錄
    Path('results').mkdir(exist_ok=True)
