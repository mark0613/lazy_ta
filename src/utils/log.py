import logging
import sys


def setup_logging(level: str = 'INFO'):
    """
    設定日誌系統

    Args:
        level: 日誌等級 (FATAL, ERROR, WARNING, INFO, DEBUG)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 建立日誌格式
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Console handler - 使用指定的 level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Console.log handler - 記錄所有 INFO 以上的日誌
    console_file_handler = logging.FileHandler('results/console.log', encoding='utf-8')
    console_file_handler.setLevel(logging.INFO)
    console_file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Debug.log handler - 記錄所有 DEBUG 以上的日誌
    debug_file_handler = logging.FileHandler('results/debug.log', encoding='utf-8')
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # 設定根 logger
    logging.basicConfig(
        level=logging.DEBUG,  # 根 logger 設為 DEBUG,讓所有訊息都能被處理
        format=log_format,
        datefmt=date_format,
        handlers=[
            console_handler,
            console_file_handler,
            debug_file_handler,
        ],
    )
