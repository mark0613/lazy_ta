from .base import BASE_PROMPT, EX_PROMPT

# base

PROBLEM_DESCRIPTION = """
Write a program that converts a mixed text-and-digit phone number into its numeric equivalent. Each alphabetic character should be translated into the corresponding telephone keypad digit according to this table:
Digit	Letters
2	ABC
3	DEF
4	GHI
5	JKL
6	MNO
7	PQRS
8	TUV
9	WXYZ

If the input contains non-alphabetic characters (digits, hyphens, or spaces), leave them unchanged. You may assume that all letters entered by the user are uppercase.
Input Example
```
Enter a phone number: +1-855-TRY-NOW
```
Output Example
```
Numeric form: +1-855-879-669
```

Hint
• You can process the string character by character.
• Use an if-else or switch statement to convert letters.
• Characters outside A-Z range should be printed as-is.
"""

SCORE_INSTRUCTIONS = """
總共 30 分，具體評分標準如下：
- 輸入格式 (6 分): 能正確讀取並處理使用者輸入，主要抓讀取方式錯誤或無法處理測試案例的情況
- 正確處理空格 (6 分): 能正確處理輸入中的多個空格
- 保留其他符號 (6 分): 能正確保留輸入中的非字母數字符號，如加號、連字號等
- 轉換邏輯 (12 分): 能正確將字母轉換為對應的數字

PS.
- 以 6 分為一個檔次，意思是數學邏輯部分錯誤，你要酌扣分數，就是 6、12 分這樣，不能只扣 1、2 分
- 不考慮 output prefix (Numeric form:)，有寫沒寫都可以，所以如果你發現未通過的的測資僅是因為這個問題，請直接給他滿分
"""

EXTRA_INSTRUCTIONS = """
無
"""

# ex

EX_PROBLEM_DESCRIPTION = (
    PROBLEM_DESCRIPTION
    + """
--- extra ---
Allow lowercase input as well, by converting each letter to uppercase before mapping.
""".strip()
)


EX_EXTRA_INSTRUCTIONS = EXTRA_INSTRUCTIONS

# prompt for P2, P2_ex

P2_PROMPT = (
    BASE_PROMPT.replace('{problem_description}', PROBLEM_DESCRIPTION.strip())
    .replace('{score_instructions}', SCORE_INSTRUCTIONS.strip())
    .replace('{extra_instructions}', EXTRA_INSTRUCTIONS.strip())
)

P2_EX_PROMPT = EX_PROMPT.replace('{problem_description}', EX_PROBLEM_DESCRIPTION.strip()).replace(
    '{extra_instructions}', EX_EXTRA_INSTRUCTIONS.strip()
)
