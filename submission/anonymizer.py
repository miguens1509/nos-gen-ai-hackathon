"""Anonymize a PDF and improve the prompt using saved review corrections."""
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = BASE_DIR / "submission"
PROMPT_PATH = SUBMISSION_DIR / "prompt.txt"
COMPARISON_PATH = SUBMISSION_DIR / "comparisions_results.txt"
load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"


def generate_content(prompt_text: str) -> dict:
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY nao definida no ambiente ou no ficheiro .env.")
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"thinkingConfig": {"thinkingLevel": "low"}},
            },
            timeout=(10, 60),
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("O Gemini excedeu o tempo de espera. Este erro nao confirma uma chave invalida.") from None
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Nao foi possivel estabelecer ligacao a API Gemini.") from None
    if not response.ok:
        detail = response.text.replace(API_KEY, "[REDACTED]")
        raise RuntimeError(f"Erro da API Gemini ({response.status_code}): {detail}")
    return response.json()


def response_text(output: dict) -> str:
    candidates = output.get("candidates") or []
    if not candidates:
        raise RuntimeError("O Gemini nao devolveu candidatos de texto.")
    candidate = candidates[0]
    if candidate.get("finishReason") not in (None, "STOP"):
        raise RuntimeError(f"Resposta incompleta: {candidate.get('finishReason')}")
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(part["text"] for part in parts
                   if isinstance(part.get("text"), str) and not part.get("thought"))
    if not text.strip():
        raise RuntimeError("O Gemini devolveu uma resposta vazia.")
    return text


def anonymize(text: str) -> str:
    """Send a document to Gemini and return its anonymized version."""
    with open(
        "submission/prompt.txt",
        "r",
        encoding="utf-8"
    ) as file:
        prompt = file.read()

    prompt_text = f"{prompt}\n\nDocument:\n{text}"
    output = generate_content(prompt_text)

    if "candidates" not in output:
        raise RuntimeError(f"O Gemini nao devolveu texto: {output}")

    response_text = (
        output["candidates"][0]["content"]["parts"][0]["text"]
    )
    return response_text


def improve_prompt() -> None:
    if not COMPARISON_PATH.exists():
        return
    corrections = COMPARISON_PATH.read_text(encoding="utf-8").strip()
    if not corrections:
        print("Nenhuma alteracao manual encontrada. O prompt original foi mantido.")
        return
    current_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    request = f"""You are improving an anonymization prompt.

CURRENT PROMPT:
{current_prompt}

USER CORRECTIONS:
{corrections}

Rewrite the CURRENT PROMPT incorporating the corrections.
Rules:
- Preserve the instructions that were already correct.
- Fix the mistakes identified by the user.
- Return ONLY the improved prompt.
- Do not include explanations or Markdown formatting.
"""
    improved = response_text(generate_content(request))
    PROMPT_PATH.write_text(improved, encoding="utf-8")
    print("Prompt atualizado com sucesso!")


def main() -> None:
    import fitz
    import tkinter as tk
    if __package__:
        from .Interface import ReviewApp
    else:
        from Interface import ReviewApp

    pdf_path = BASE_DIR / "raw_data" / "document_to_anonymize.pdf"
    with fitz.open(pdf_path) as document:
        text = "".join(page.get_text() for page in document)
    pdf_path.with_suffix(".txt").write_text(text, encoding="utf-8")

    print("A iniciar anonimizacao...", flush=True)
    start = time.perf_counter()
    result = anonymize(text)
    (SUBMISSION_DIR / "submission.txt").write_text(result, encoding="utf-8")
    print(f"Documento anonimizado em {time.perf_counter() - start:.2f} segundos")

    # Feedback must belong to this review, rather than a previous run.
    COMPARISON_PATH.write_text("", encoding="utf-8")
    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()
    improve_prompt()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(f"Erro: {exc}") from None
