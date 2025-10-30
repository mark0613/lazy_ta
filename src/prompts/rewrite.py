COMMENT_PROMPT = """
You are a C/C++ code processing tool. Your task is to comment out printf/cout statements that prompt users for input before scanf/cin.

CRITICAL RULES:
1. Only comment out printf/cout that prompt users for input (appear before scanf/cin)
2. Keep everything else EXACTLY the same:
   - Do NOT fix any syntax errors
   - Do NOT change any logic
   - Do NOT modify other printf/cout (like output statements)
   - Do NOT add or remove any lines
   - Do NOT reformat the code
3. Comment method: Add // before the line (on the same line, do not create new line)
4. Return the complete modified code directly, without any explanation or markdown format

Example:
Input:
```c
#include <stdio.h>
int main() {{
    int a, b;
    printf("Enter two numbers: ");
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}}
```

Output:
```c
#include <stdio.h>
int main() {{
    int a, b;
    // printf("Enter two numbers: ");
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}}
```

Code to process:
{source_code}

Return the complete modified code:
"""
