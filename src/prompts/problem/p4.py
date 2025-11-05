from .base import BASE_PROMPT, EX_PROMPT

# base
PROBLEM_DESCRIPTION = """
One of the earliest encryption techniques, known as the Caesar cipher, shifts each letter in a message by a fixed number of positions in the alphabet.
When the shift passes 'Z' or 'z', it wraps around to the beginning of the alphabet.
Your task:
Write a program that encrypts a message entered by the user using a Caesar cipher.
• The user enters the message to be encrypted and a shift amount between 1 and 25.
• Only alphabetic characters are shifted; all other characters (spaces, punctuation, digits) remain unchanged.
• Uppercase letters stay uppercase, and lowercase letters stay lowercase.
Input Example 1
```
Enter a message to be encrypted: Meet me at the park at nine.
Enter shift amount (1-25): 5
```
Output Example 1
```
Encrypted message: Rjjy rj fy ymj ufwp fy snsj.
```

Input Example 2 (Decryption):
```
Enter a message to be encrypted: Rjjy rj fy ymj ufwp fy snsj.
Enter shift amount (1-25): 21
```
Output Example 1
```
Encrypted message: Meet me at the park at nine.
```
"""

SCORE_INSTRUCTIONS = """
總共 30 分，具體評分標準如下：
- 輸入格式 (6 分): 能正確讀取並處理使用者輸入，主要抓讀取方式錯誤或無法處理測試案例的情況
- 正確處理空格 (12 分): 能正確處理輸入中的空格
- 溢位後是否有記得調整 (12 分): 能正確處理字母溢位的情況

PS.
- 以 6 分為一個檔次，意思是數學邏輯部分錯誤，你要酌扣分數，就是 6、12 分這樣，不能只扣 1、2 分
- 不考慮 output prefix (Encrypted message:)，有寫沒寫都可以，所以如果你發現未通過的的測資僅是因為這個問題，請直接給他滿分
- 輸出的空格數量不算 typo，只有明顯的拼字錯誤才算 typo
"""

EXTRA_INSTRUCTIONS = """
無
"""

# ex

EX_PROBLEM_DESCRIPTION = (
    PROBLEM_DESCRIPTION
    + """
--- extra ---
Allow the user to choose whether to encrypt or decrypt the message.
If the user selects Decrypt, the program should automatically use 26 - shift as the effective shift amount.
Input Example:
```
Enter E to encrypt or D to decrypt: D
Enter a message: Rjjy rj fy ymj ufwp fy snsj.
Enter shift amount (1-25): 5
```
Output Example:
```
Decrypted message: Meet me at the park at nine.
```
""".strip()
)


EX_EXTRA_INSTRUCTIONS = (
    EXTRA_INSTRUCTIONS
    + """
- 請注意輸出前綴會因加密或解密而不同，分別為 Encrypted message: 或 Decrypted message: ，如果沒寫就是 0 分
- 輸出的空格數量不算 typo，只有明顯的拼字錯誤才算 typo
""".strip()
)

# prompt for P4, P4_ex

P4_PROMPT = (
    BASE_PROMPT.replace('{problem_description}', PROBLEM_DESCRIPTION.strip())
    .replace('{score_instructions}', SCORE_INSTRUCTIONS.strip())
    .replace('{extra_instructions}', EXTRA_INSTRUCTIONS.strip())
)

P4_EX_PROMPT = EX_PROMPT.replace('{problem_description}', EX_PROBLEM_DESCRIPTION.strip()).replace(
    '{extra_instructions}', EX_EXTRA_INSTRUCTIONS.strip()
)
