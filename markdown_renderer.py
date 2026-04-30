import tkinter as tk
from tkinter import font


class MarkdownRenderer:
    """
    Lightweight Markdown → Tkinter Text renderer.
    Supports:
        - #, ##, ### headers
        - **bold**
        - *italic*
        - - bullet lists
        - > blockquotes
        - ``` code blocks ```
        - normal paragraphs
    """

    def __init__(self, text_widget: tk.Text):
        self.text = text_widget
        self._setup_tags()

    # ---------------- TAG SETUP ----------------

    def _setup_tags(self):
        """Define text formatting tags."""
        self.text.tag_configure("h1", font=("Segoe UI", 16, "bold"))
        self.text.tag_configure("h2", font=("Segoe UI", 14, "bold"))
        self.text.tag_configure("h3", font=("Segoe UI", 12, "bold"))

        self.text.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        self.text.tag_configure("italic", font=("Segoe UI", 10, "italic"))

        self.text.tag_configure("bullet", lmargin1=20, lmargin2=40)
        self.text.tag_configure("blockquote", lmargin1=20, foreground="#555555")

        self.text.tag_configure(
            "codeblock",
            font=("Consolas", 10),
            background="#EEECE6",
            lmargin1=20,
            lmargin2=20,
            spacing1=4,
            spacing3=4,
        )

    # ---------------- PUBLIC RENDER METHOD ----------------

    def render(self, markdown_text: str):
        """Render markdown into the Text widget."""
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)

        if not markdown_text:
            self.text.config(state="disabled")
            return

        lines = markdown_text.split("\n")
        in_code_block = False
        code_buffer = []

        for line in lines:
            stripped = line.strip()

            # ---------------- CODE BLOCKS ----------------
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_buffer = []
                else:
                    # End code block
                    self._insert_code_block("\n".join(code_buffer))
                    in_code_block = False
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            # ---------------- HEADERS ----------------
            if stripped.startswith("### "):
                self._insert_header(stripped[4:], "h3")
                continue
            if stripped.startswith("## "):
                self._insert_header(stripped[3:], "h2")
                continue
            if stripped.startswith("# "):
                self._insert_header(stripped[2:], "h1")
                continue

            # ---------------- BLOCKQUOTE ----------------
            if stripped.startswith(">"):
                self._insert_blockquote(stripped[1:].strip())
                continue

            # ---------------- BULLET LIST ----------------
            if stripped.startswith("- "):
                self._insert_bullet(stripped[2:])
                continue

            # ---------------- NORMAL PARAGRAPH ----------------
            self._insert_paragraph(stripped)

        self.text.config(state="disabled")

    # ---------------- INSERT HELPERS ----------------

    def _insert_header(self, text, tag):
        self.text.insert(tk.END, text + "\n", tag)
        self.text.insert(tk.END, "\n")

    def _insert_blockquote(self, text):
        self.text.insert(tk.END, text + "\n", "blockquote")

    def _insert_bullet(self, text):
        self.text.insert(tk.END, "• " + text + "\n", "bullet")

    def _insert_paragraph(self, text):
        if not text:
            self.text.insert(tk.END, "\n")
            return

        # Inline bold + italic
        text = self._apply_inline_styles(text)
        self.text.insert(tk.END, text + "\n")

    def _insert_code_block(self, code_text):
        self.text.insert(tk.END, code_text + "\n", "codeblock")
        self.text.insert(tk.END, "\n")

    # ---------------- INLINE STYLES ----------------

    def _apply_inline_styles(self, text):
        """
        Inserts text with inline bold/italic tags.
        Returns plain text with tag ranges applied.
        """
        i = 0
        while True:
            start = text.find("**", i)
            if start == -1:
                break
            end = text.find("**", start + 2)
            if end == -1:
                break

            bold_text = text[start + 2:end]
            self._apply_tag_to_range(text, start, end + 2, "bold")
            i = end + 2

        i = 0
        while True:
            start = text.find("*", i)
            if start == -1:
                break
            end = text.find("*", start + 1)
            if end == -1:
                break

            italic_text = text[start + 1:end]
            self._apply_tag_to_range(text, start, end + 1, "italic")
            i = end + 1

        return text.replace("**", "").replace("*", "")

    def _apply_tag_to_range(self, full_text, start, end, tag):
        """
        Apply a tag to a range in the Text widget.
        """
        widget_index_start = self.text.index(tk.END)
        self.text.insert(tk.END, full_text[:start])
        tag_start = self.text.index(tk.END)

        self.text.insert(tk.END, full_text[start:end])
        tag_end = self.text.index(tk.END)

        self.text.insert(tk.END, full_text[end:])

        self.text.tag_add(tag, tag_start, tag_end)