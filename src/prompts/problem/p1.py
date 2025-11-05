from .base import BASE_PROMPT, EX_PROMPT

# base

PROBLEM_DESCRIPTION = """
Write a program that calculates the balance of a savings account after the first, second, and third months:
Input Example:
```
Enter initial deposit: 10000.00
Enter annual interest rate: 4.0
Enter monthly withdrawal: 350.00
```
Output Example:
```
Balance after first month:  $9683.33
Balance after second month: $9365.61
Balance after third month:  $9046.83
```

Display each balance with two digits after the decimal point.
Hint
♦ The monthly interest rate equals the annual rate divided by 12, then by 100.
For example, 4% annual → 0.003333 monthly.

♦ Each month, the balance increases by balance * monthly_interest_rate
and decreases by the withdrawal amount.
"""

SCORE_INSTRUCTIONS = """
總共 30 分，具體評分標準如下：
1. 輸入格式 (6 分): 能正確讀取並處理使用者輸入，主要抓讀取方式錯誤或無法處理測試案例的情況
2. 數學邏輯 (18 分): 計算每月餘額的邏輯正確
3. 輸出格式 (6 分): 必須使用 first, second, third 來表示月份否則該項目 0 分。其他如空格對齊、$ 符號、多於空格等格式上的小問題不扣分

PS. 以 6 分為一個檔次，意思是數學邏輯部分錯誤，當你要酌扣分數，就是 6、12、18、24 分這樣，不能只扣 1、2 分
"""

EXTRA_INSTRUCTIONS = """
- 輸出格式必須和 Output Example 一致，只能用 first, second, third 來表示月份，否則扣他 6 分
- 輸出的空格數量不算 typo，只有明顯的拼字錯誤才算 typo
"""

# ex

EX_PROBLEM_DESCRIPTION = (
    PROBLEM_DESCRIPTION
    + """
--- extra ---
Modify your program so the user can enter how many months to calculate.
Use a for loop to compute and print the balance after each month.
""".strip()
)


EX_EXTRA_INSTRUCTIONS = (
    EXTRA_INSTRUCTIONS
    + """
- 輸入順序不是唯一，因為題目沒有給 example，所以如果有學生的輸入的項目都對，只是順序不同造成測試 case 失敗，請視為正確，不要扣分
- 前三筆只能是 first, second, third，之後的筆數請用數字表示 (e.g., 4th month, 5th month, etc.)，如果沒有照這個規則，直接 0 分
- 輸出的空格數量不算 typo，只有明顯的拼字錯誤才算 typo
"""
)


# prompt for P1, P1_ex

P1_PROMPT = (
    BASE_PROMPT.replace('{problem_description}', PROBLEM_DESCRIPTION.strip())
    .replace('{score_instructions}', SCORE_INSTRUCTIONS.strip())
    .replace('{extra_instructions}', EXTRA_INSTRUCTIONS.strip())
)

P1_EX_PROMPT = EX_PROMPT.replace('{problem_description}', EX_PROBLEM_DESCRIPTION.strip()).replace(
    '{extra_instructions}', EX_EXTRA_INSTRUCTIONS.strip()
)
