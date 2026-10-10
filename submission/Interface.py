"""Interactive review of anonymization proposed by Gemini.

Run from anywhere with:
    py submission/validation_gui.py

Expected project layout:
    raw_data/document_to_anonymize.txt
    submission/submission.txt

Review the proposed masks, then save directly to submission/submission.txt.
Uses only the Python standard library (tkinter).
"""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORIGINAL = ROOT / "raw_data" / "document_to_anonymize.txt"
DEFAULT_PROPOSAL = ROOT / "submission" / "submission.txt"
DEFAULT_EXPORT = ROOT / "submission" / "submission.txt"
TOKEN_PATTERN = re.compile(r"\S+")


def tokens_by_line(text):
    """Return per-line (token, absolute_start, absolute_end)."""
    result, offset = [], 0
    for line in text.splitlines(keepends=True):
        result.append([(m.group(), offset + m.start(), offset + m.end())
                       for m in TOKEN_PATTERN.finditer(line)])
        offset += len(line)
    if not result and text:
        result = [[(m.group(), m.start(), m.end()) for m in TOKEN_PATTERN.finditer(text)]]
    return result


def proposed_masks(original, proposed):
    """Infer masking from a Gemini full-text output, conservatively.

    We align nonblank lines by order. If a line's token count differs,
    no automatic flags are generated for that line (review it manually).
    Returns (set of token spans, warnings).
    """
    original_lines = [line for line in tokens_by_line(original) if line]
    proposed_lines = [line for line in tokens_by_line(proposed) if line]
    masks = set()
    warnings = []
    if len(original_lines) != len(proposed_lines):
        warnings.append(f"Linhas com texto: original={len(original_lines)}, Gemini={len(proposed_lines)}. "
                        "Revê com atenção as sugestões.")
    for i, (orig_line, prop_line) in enumerate(zip(original_lines, proposed_lines), start=1):
        if len(orig_line) != len(prop_line):
            warnings.append(f"Linha {i}: número de palavras diferente "
                            f"({len(orig_line)} vs. {len(prop_line)}); sem marcação automática.")
            continue
        for (_, start, end), (proposed_word, _, _) in zip(orig_line, prop_line):
            # Identify '*' as a whole token or surrounded only by punctuation.
            if proposed_word.strip('.,;:!?()[]{}\"\'') == '*':
                masks.add((start, end))
    return masks, warnings


class ReviewApp:
    def __init__(self, root):
        self.root = root
        root.title("Revisão de anonimização — NOS")
        root.geometry("1080x740")
        self.original = ""
        self.spans = []
        self.masked = set()
        self.initial_masked = set()
        self.issues = []
        self.mouse_start = None

        bar = ttk.Frame(root, padding=10)
        bar.pack(fill="x")
        ttk.Button(bar, text="Guardar", command=self.export).pack(side="left", padx=3)

        ttk.Label(root, text="Clica numa palavra para marcar/desmarcar. Arrasta para selecionar várias palavras de uma vez. "
                  "As palavras sublinhadas a vermelho serão substituídas por *.", padding=(12, 0)).pack(anchor="w")
        text_frame = ttk.Frame(root, padding=10)
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, wrap="word", undo=False,
                            font=("Consolas", 12), padx=12, pady=12)
        self.text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scroll.set)
        self.text.tag_configure("masked", underline=True, foreground="#b91c1c",
                                background="#fee2e2")
        self.text.bind("<Key>", lambda e: "break" if e.keysym not in ("Left", "Right", "Up", "Down", "Prior", "Next", "Home", "End") else None)
        self.text.bind("<ButtonPress-1>", self.start_mouse_selection)
        self.text.bind("<ButtonRelease-1>", self.finish_mouse_selection)

        self.status = ttk.Label(root, text="Abre o documento original para começar.", padding=10)
        self.status.pack(anchor="w")

        if DEFAULT_ORIGINAL.exists():
            self.open_original(DEFAULT_ORIGINAL)
        if DEFAULT_PROPOSAL.exists() and self.original:
            self.open_proposal(DEFAULT_PROPOSAL)

    def load_original(self):
        path = filedialog.askopenfilename(title="TXT original", filetypes=[("Ficheiros TXT", "*.txt")])
        if path:
            self.open_original(Path(path))

    
    def save_comparison_results(self):
        # Censuras removidas manualmente pelo utilizador
        removed = self.initial_masked - self.masked

        # Censuras adicionadas manualmente pelo utilizador
        added = self.masked - self.initial_masked

        def get_context(span):
            start, end = span

            # Encontrar o início da linha original
            line_start = self.original.rfind("\n", 0, start) + 1

            # Encontrar o fim da linha original
            line_end = self.original.find("\n", end)

            if line_end == -1:
                line_end = len(self.original)

            # Reconstruir a linha com a palavra assinalada
            return (
                self.original[line_start:start]
                + "*"
                + self.original[start:end]
                + "*"
                + self.original[end:line_end]
            )

        # Criar o conteúdo do ficheiro
        lines = ["Removed:"]

        for span in sorted(removed):
            lines.append(get_context(span))

        lines.append("")
        lines.append("Added:")

        for span in sorted(added):
            lines.append(get_context(span))

        # Caminho do ficheiro de resultados
        path = ROOT / "submission" / "comparisions_results.txt"

        # Criar a pasta, caso não exista
        path.parent.mkdir(parents=True, exist_ok=True)

        # Criar ou substituir o ficheiro
        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8"
        )


    def open_original(self, path):
        self.original = path.read_text(encoding="utf-8-sig")
        self.spans = [(start, end) for line in tokens_by_line(self.original)
                      for _, start, end in line]
        self.masked.clear()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", self.original)
        self.refresh()
        self.status.configure(text=f"Original: {path.name} | {len(self.spans)} palavras")

    def load_proposal(self):
        if not self.original:
            messagebox.showwarning("Falta original", "Abre primeiro o TXT original.")
            return
        path = filedialog.askopenfilename(title="TXT anonimizado pelo Gemini",
                                           filetypes=[("Ficheiros TXT", "*.txt")])
        if path:
            self.open_proposal(Path(path))

    def open_proposal(self, path):
        candidate = path.read_text(encoding="utf-8-sig")
        self.masked, self.issues = proposed_masks(self.original, candidate)

        # Guardar as censuras originais do Gemini
        self.initial_masked = self.masked.copy()

        self.refresh()
        self.status.configure(text=f"Proposta: {path.name} | {len(self.masked)} palavras marcadas | "
                             f"{len(self.issues)} avisos de alinhamento")
        if self.issues:
            messagebox.showwarning("Revisão necessária",
                                   "Algumas linhas não puderam ser alinhadas automaticamente.\n\n"
                                   + "\n".join(self.issues[:7])
                                   + ("\n..." if len(self.issues) > 7 else ""))

    def to_tk_index(self, offset):
        return f"1.0+{offset}c"

    def refresh(self):
        self.text.tag_remove("masked", "1.0", "end")
        for start, end in self.masked:
            self.text.tag_add("masked", self.to_tk_index(start), self.to_tk_index(end))

    def start_mouse_selection(self, event):
        self.mouse_start = self.text.index(f"@{event.x},{event.y}")

    def finish_mouse_selection(self, event):
        if not self.original or self.mouse_start is None:
            return
        start_index = self.mouse_start
        end_index = self.text.index(f"@{event.x},{event.y}")
        self.mouse_start = None
        # The default tkinter mouse handler finishes updating the selection
        # after this callback; defer our action until then.
        self.root.after_idle(lambda: self.toggle_at_range(start_index, end_index))

    def toggle_at_range(self, begin_index, end_index):
        first = self.text.count("1.0", begin_index, "chars")[0]
        last = self.text.count("1.0", end_index, "chars")[0]
        if first > last:
            first, last = last, first
        if first == last:
            # A single click affects only the token under the cursor.
            affected = [(a, b) for a, b in self.spans if a <= first < b]
        else:
            # Dragging affects all tokens overlapping the selected range.
            affected = [(a, b) for a, b in self.spans if a < last and b > first]
        if not affected:
            return
        # When everything is already masked, unmask; otherwise mask the set.
        if all(span in self.masked for span in affected):
            self.masked.difference_update(affected)
        else:
            self.masked.update(affected)
        self.text.tag_remove("sel", "1.0", "end")
        self.refresh()
        self.status.configure(text=f"{len(self.masked)} palavras marcadas para anonimização")

    def set_selection(self, value):
        try:
            begin = self.text.count("1.0", "sel.first", "chars")[0]
            end = self.text.count("1.0", "sel.last", "chars")[0]
        except tk.TclError:
            messagebox.showinfo("Seleciona texto", "Seleciona uma ou várias palavras com o rato.")
            return
        affected = [(a, b) for a, b in self.spans if a < end and b > begin]
        if value:
            self.masked.update(affected)
        else:
            self.masked.difference_update(affected)
        self.refresh()
        self.status.configure(text=f"{len(self.masked)} palavras marcadas para anonimização")

    def export(self):
        if not self.original:
            messagebox.showwarning("Falta original", "Abre o TXT original.")
            return
        # Guardar diretamente no ficheiro oficial, sem abrir qualquer janela.
        path = DEFAULT_EXPORT
        # Reconstruct from the exact original text, replacing only marked tokens.
        pieces = []
        last = 0
        for start, end in sorted(self.masked):
            pieces.append(self.original[last:start])
            token = self.original[start:end]
            # Keep punctuation that surrounds a masked word.
            leading = re.match(r"^[([{\"']*", token).group()
            trailing = re.search(r"[,.;:!?)}\]\"']*$", token).group()
            if len(leading) + len(trailing) >= len(token):
                pieces.append("*")
            else:
                pieces.append(leading + "*" + trailing)
            last = end
        pieces.append(self.original[last:])
        result = "".join(pieces)
        result = "\n".join(line for line in result.splitlines() if line.strip())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Erro ao guardar", str(exc))
            return
        # Fechar a interface assim que o ficheiro for guardado com sucesso.
        # Sem janela ou notificacao de confirmacao.
        # Guardar as alterações manuais
        try:
            self.save_comparison_results()
        except OSError as exc:
            messagebox.showerror(
                "Erro ao guardar comparações",
                str(exc)
            )
            return

        # Fechar a interface
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()
