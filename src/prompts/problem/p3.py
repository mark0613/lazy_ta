from .base import BASE_PROMPT, EX_PROMPT

# base
PROBLEM_DESCRIPTION = """
(a) Write a program that reads a sentence from the user and then prints the reversed sentence.
• Read the sentence one character at a time using getchar().
• Store each character in an array.
• Stop reading when the array is full or when the user enters a newline ('\n').
• After the input ends, print the sentence in reverse order.
Input Example
```
Enter a sentence: Keep calm and code in C.
```
Output Example
```
Reversal: .C ni edoc dna mlac peeK
```

(b) Revise your program from Part (a) to use a pointer instead of an integer variable to keep track of the current position in the array.
"""

A_SCORE_INSTRUCTIONS = """
總共 12.5 分，具體評分標準如下：
- 輸入格式 (2.5 分): 能正確讀取並處理使用者輸入，主要抓讀取方式錯誤或無法處理測試案例的情況。但這題有個規定，必須使用 getchar，如果不是用這個的請直接這個項目給他 0 分
- 正確處理空格 (2.5 分): 能正確處理輸入中的多個空格
- 儲存到 array (2.5 分): 按照題目要求正確儲存輸入到陣列中
- 邏輯 (2.5 分): 能正確實現字元反轉的邏輯
- 輸出格式 (2.5 分): 必須輸出題目所要求的 prefix (Reversal:)，而且能正確顯示反轉後的訊息
"""

B_SCORE_INSTRUCTIONS = """
總共 17.5 分，具體評分標準如下：
- 輸入格式 (2.5 分): 能正確讀取並處理使用者輸入，主要抓讀取方式錯誤或無法處理測試案例的情況。但這題有個規定，必須使用 getchar，如果不是用這個的請直接這個項目給他 0 分
- 正確處理空格 (2.5 分): 能正確處理輸入中的多個空格
- 儲存到 array (2.5 分): 按照題目要求正確儲存輸入到陣列中
- 邏輯 (2.5 分): 能正確實現字元反轉的邏輯
- pointer (5 分): 針對 (b) 部分，能正確使用 pointer 來追蹤陣列位置
- 輸出格式 (2.5 分): 必須輸出題目所要求的 prefix (Reversal:)，而且能正確顯示反轉後的訊息
"""

EXTRA_INSTRUCTIONS = """
- 仔細檢查編號這題到底是 P3_a 還是 P3_b，如果是 P3_b 記得關注他是否滿足題目要求的 pointer 使用
"""

# ex

EX_PROBLEM_DESCRIPTION = (
    PROBLEM_DESCRIPTION
    + """
--- extra ---
Modify your program (either using index or pointer) so that it reverses each individual word in the sentence, but keeps the words in their original order.
Input Example
```
Enter a sentence: Hello World from C
```
Output Example
```
Reversal by word: olleH dlroW morf C
```
""".strip()
)


EX_EXTRA_INSTRUCTIONS = """
- 不用在乎原題目的 (a) 或 (b) 作法，只要能達成反轉每個單字的要求即可
"""

# prompt for P3_a, P3_b, P3_ex

P3_A_PROMPT = (
    BASE_PROMPT.replace('{problem_description}', PROBLEM_DESCRIPTION.strip())
    .replace('{score_instructions}', A_SCORE_INSTRUCTIONS.strip())
    .replace('{extra_instructions}', EXTRA_INSTRUCTIONS.strip())
)

P3_B_PROMPT = (
    BASE_PROMPT.replace('{problem_description}', PROBLEM_DESCRIPTION.strip())
    .replace('{score_instructions}', B_SCORE_INSTRUCTIONS.strip())
    .replace('{extra_instructions}', EXTRA_INSTRUCTIONS.strip())
)

P3_EX_PROMPT = EX_PROMPT.replace('{problem_description}', EX_PROBLEM_DESCRIPTION.strip()).replace(
    '{extra_instructions}', EX_EXTRA_INSTRUCTIONS.strip()
)
