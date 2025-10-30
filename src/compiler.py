import logging
import subprocess
from pathlib import Path

from src import config

from .utils.file import get_executable_path

logger = logging.getLogger(__name__)


def check_compiler_availability() -> bool:
    gcc_path = config.GCC_PATH
    gpp_path = config.GPP_PATH

    # 測試 gcc 是否可用
    try:
        subprocess.run([gcc_path, '--version'], capture_output=True, check=True)
        logger.info('GCC 可用')
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.error(f'錯誤: 找不到 gcc 編譯器: {gcc_path}')

    # 測試 g++ 是否可用
    try:
        subprocess.run([gpp_path, '--version'], capture_output=True, check=True)
        logger.info('G++ 可用')
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.error(f'錯誤: 找不到 g++ 編譯器: {gpp_path}')

    return False


def validate_file_extension(source_file: Path) -> bool:
    """
    驗證檔案副檔名是否為 .c 或 .cpp
    """
    return source_file.suffix in {'.c', '.cpp'}


def compile_code(source_file: Path, timeout: int = 5) -> tuple[bool, str]:
    """
    編譯 C/C++ 程式碼

    Returns:
        (成功與否, 錯誤訊息)
    """
    if not validate_file_extension(source_file):
        raise ValueError('不支援的檔案類型')

    gcc_path = config.GCC_PATH
    gpp_path = config.GPP_PATH

    extension = source_file.suffix
    compiler = gcc_path if extension == '.c' else gpp_path

    source = str(source_file.resolve())
    output_file = get_executable_path(source_file.with_suffix(''))
    output = str(output_file.resolve())

    compile_cmd = [
        compiler,
        source,
        '-o',
        output,
    ]

    try:
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 無法解碼的字元用 � 替換
            timeout=timeout,
        )

        if result.returncode == 0 and output_file.exists():
            return True, ''
        else:
            return False, result.stderr or result.stdout

    except subprocess.TimeoutExpired:
        return False, f'編譯超時（超過 {timeout} 秒）'
    except Exception as e:
        return False, f'編譯錯誤: {str(e)}'
