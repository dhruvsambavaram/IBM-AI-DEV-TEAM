"""
orchestration/preflight_guard.py — Pre-Flight Python AST & Syntax Verification Gate
Intercepts LLM generated diffs BEFORE Testing/Review to prevent broken syntax from propagating.
"""

from __future__ import annotations

import ast


def validate_python_code(source_code: str) -> tuple[bool, str | None]:
    """
    Validate pure Python source code using Python's native AST parser.
    Returns: (is_valid, error_message)
    """
    try:
        ast.parse(source_code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"AST Parse Error: {str(e)}"


def extract_added_python_code(code_diff: str) -> list[str]:
    """
    Extracts newly added/modified lines from a unified diff hunk, grouped by Python file.
    Returns a list of strings, where each string is the combined added code for one Python file.
    """
    python_blocks = []
    current_file_is_python = False
    current_lines = []

    for line in code_diff.splitlines():
        if line.startswith("+++"):
            if current_file_is_python and current_lines:
                python_blocks.append("\n".join(current_lines))
            current_lines = []
            
            filepath = line[3:].strip()
            if filepath.startswith("b/"):
                filepath = filepath[2:]
            
            current_file_is_python = filepath.endswith(".py")
            continue

        if current_file_is_python:
            if line.startswith("+") and not line.startswith("+++"):
                current_lines.append(line[1:])
    
    if current_file_is_python and current_lines:
        python_blocks.append("\n".join(current_lines))
        
    return python_blocks


def preflight_diff_check(code_diff: str, original_file_content: str = "") -> dict:
    """
    Perform a complete pre-flight structural & AST syntax verification on a code diff.
    Returns: {
        "passed": bool,
        "syntax_clean": bool,
        "diff_structured": bool,
        "error": str | None,
    }
    """
    if not code_diff or not code_diff.strip():
        return {
            "passed": False,
            "syntax_clean": False,
            "diff_structured": False,
            "error": "Empty code diff provided",
        }

    # Verify standard unified diff markers
    has_headers = ("---" in code_diff and "+++" in code_diff) or "@@" in code_diff
    if not has_headers and not code_diff.startswith("diff --git"):
        return {
            "passed": False,
            "syntax_clean": False,
            "diff_structured": False,
            "error": "Malformed diff: missing standard unified diff hunk markers (---, +++, @@)",
        }

    python_blocks = extract_added_python_code(code_diff)

    import textwrap
    
    syntax_clean = True
    syntax_err = None

    # Check each modified Python file for syntax errors
    for added_code in python_blocks:
        if not added_code.strip():
            continue
            
        dedented = textwrap.dedent(added_code)
        parsed_ok = False

        # 1. Direct AST parse on dedented code
        try:
            ast.parse(dedented)
            parsed_ok = True
        except SyntaxError as e:
            syntax_err = f"SyntaxError in generated code patch at line {e.lineno}: {e.msg}"

        # 2. If direct parse failed, check if statements are valid inside a function or block context
        if not parsed_ok:
            for wrapper in (
                "def _dummy_context():\n" + textwrap.indent(dedented, "    "),
                "try:\n    pass\n" + textwrap.indent(dedented, "    "),
                "if True:\n    pass\n" + textwrap.indent(dedented, "    "),
            ):
                try:
                    ast.parse(wrapper)
                    parsed_ok = True
                    syntax_err = None
                    break
                except SyntaxError:
                    continue
        
        if not parsed_ok:
            syntax_clean = False
            break

    return {
        "passed": syntax_clean,
        "syntax_clean": syntax_clean,
        "diff_structured": True,
        "error": syntax_err,
    }
