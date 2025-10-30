# Lazy TA
懶惰的 TA 不想改上機考? 你這懶蟲 🫵🐛 ，試試看 LLM 自動批改腳本

!!!你應該檢查 LLM 批改結果，而不是完全相信，當你使用這個腳本，表示你知道這一點並同意自行負責。


## 功能特色
- **自動編譯與測試**: 支援 C/C++ 檔案的自動編譯和測試案例執行
- **智慧評分**: 使用 LLM 對部分通過的程式進行智慧評分
- **平行處理**: 支援多執行緒平行批改，提升效率
- **接續批改**: 自動跳過已批改的學生，支援中斷後繼續
- **多格式報告**: 生成 CSV、Excel、詳細日誌、摘要報告

## 系統需求
- Python 3.11
- gcc / g++ compiler
- [uv](https://github.com/astral-sh/uv)


## 快速開始
### 1. 環境設定
複製 `.env.example` 為 `.env` 並填入必要資訊:

### 2. 檔案結構
按格式將學生程式碼放入 `source_codes/` 目錄:
```
lazy_ta/
├── source_codes/          # 學生程式碼
│   ├── 112550019/
│   │   ├── 112550019_p1.c
│   │   ├── 112550019_p2.cpp
│   │   └── ...
│   └── A123456/
│       └── ...
└── results/               # 批改結果 (自動生成)
```

### 3. 安裝依賴
```bash
uv sync --no-dev
```

### 4. 執行批改
```bash
uv run main.py grade --workers 4
```

### 5. 查看結果
批改完成後，結果會存放在 `results/` 目錄中。


## 輸出檔案
批改完成後會在 `results/` 目錄生成以下檔案:
```
results/
├── grades.csv              # CSV 成績表
├── grades.xlsx             # Excel 成績表 (含多個工作表)
├── summary.txt             # 摘要報告
├── grading.log             # 批改日誌
├── detailed_logs/          # 詳細日誌
│   ├── 112550019.txt
│   ├── A123456.txt
│   └── ...
└── grading_progress.jsonl  # 批改進度檔
```


## 環境變數說明
| 變數 | 說明 | 預設值 |
|------|------|--------|
| `GOOGLE_API_KEY` | Gemini API Key | *必填* |
| `GCC_PATH` | gcc 路徑 | `/usr/bin/gcc` |
| `GPP_PATH` | g++ 路徑 | `/usr/bin/g++` |
| `COMPILE_TIMEOUT` | 編譯超時 (秒) | `10` |
| `TEST_TIMEOUT` | 測試超時 (秒) | `5` |
| `MEMORY_LIMIT_MB` | 記憶體限制 (MB) | `256` |
| `LLM_MODEL` | LLM 模型 | `gemini-2.5-flash` |


## CLI 指令說明
### `grade` - 完整批改流程 (預設指令)

執行編譯、測試、評分、生成報告的完整流程。

```bash
uv run main.py grade [OPTIONS]
```

**選項:**

- `--workers, -w`: 平行處理的 worker 數量 (預設 1)
- `--student, -s`: 指定批改的學號 (多個學號用逗號分隔)

**範例:**
```bash
uv run main.py grade                    # 批改所有未處理的學生
uv run main.py grade --workers 4        # 使用 4 個 worker 平行處理
uv run main.py grade --student 110550099,A123456  # 批改多位指定學生
```

### `build` - 只編譯程式碼
只執行編譯階段，不進行測試和評分，適合用於快速檢查學生程式是否能編譯。

```bash
uv run main.py build [OPTIONS]
```

**選項:**

- `--workers, -w`: 平行處理的 worker 數量 (預設 1)
- `--student, -s`: 指定編譯的學號 (多個學號用逗號分隔)

**範例:**
```bash
uv run main.py build                    # 編譯所有學生的程式
uv run main.py build --workers 8        # 使用 8 個 worker 快速編譯
uv run main.py build --student 110550099  # 只編譯特定學號
```

### `report` - 從進度檔生成報告
從現有的 `grading_progress.jsonl` 和 `grades.csv` 生成報告，不執行編譯、測試或評分。適合用於重新生成報告或修改報告格式後更新。

```bash
uv run main.py report
```

**範例:**
```bash
uv run main.py report  # 從進度檔重新生成所有報告
```

## `source_codes/` 目錄結構說明
```
├── {學號}/
|     ├── {學號}_p{題號}.c
|     └── {學號}_p{題號}_ex.c
...
```


## 授權
MIT License
