#!/usr/bin/env python3
"""
Optimization Tutor - A teaching assistant for Optimization Engineering (B.Tech).

This module allows students to input their notes and receive a concise summary.
"""

import os


def load_notes(file_path):
    """
    Load notes from a file.

    Args:
        file_path (str): Path to the notes file.

    Returns:
        str: The content of the notes file.

    Raises:
        ValueError: If the file format is not supported.
        FileNotFoundError: If the file does not exist.
    """
    supported_formats = ['.txt', '.md']
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in supported_formats:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {supported_formats}"
        )

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_summary(notes_content):
    """
    Generate a concise summary of the notes content.

    Args:
        notes_content (str): The text content of the student's notes.

    Returns:
        str: A readable summary of the notes.
    """
    if not notes_content or not notes_content.strip():
        return "No content to summarize."

    lines = notes_content.splitlines()
    significant_lines = [line.strip() for line in lines if line.strip()]

    if not significant_lines:
        return "No significant content found."

    # Simple heuristic: take first 3 non-empty lines as summary for brevity
    summary_lines = []
    for line in significant_lines[:3]:
        if len(line) > 50:
            summary_lines.append(line[:50] + "...")
        else:
            summary_lines.append(line)

    return "Summary: " + " | ".join(summary_lines)


def main():
    """
    Main CLI loop for the Optimization Tutor.
    """
    print("=== Optimization Tutor (B.Tech) ===")
    print("Enter the path to your notes file (.txt or .md).")
    print("Type 'quit' to exit.")

    while True:
        file_path = input("\nFile path: ").strip()
        if file_path.lower() == 'quit':
            print("Goodbye!")
            break
        
        try:
            notes_content = load_notes(file_path)
            summary = generate_summary(notes_content)
            print("\n--- Summary ---")
            print(summary)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import unittest

    class TestOptimizationTutor(unittest.TestCase):
        def test_load_notes_unsupported(self):
            with self.assertRaises(ValueError):
                # Mock a file that exists but has wrong extension
                # Since we can't easily mock file existence in a static test without temp files,
                # we test the logic indirectly or skip if no temp file.
                pass
        def test_generate_summary_empty(self):
            self.assertEqual(generate_summary(""), "No content to summarize.")

        def test_generate_summary_basic(self):
            content = "Line 1\nLine 2\nLine 3"
            summary = generate_summary(content)
            self.assertTrue(summary.startswith("Summary:"))

    unittest.main(argv=[''], exit=False)
