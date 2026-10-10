import os
import time
import requests
from dotenv import load_dotenv
from pathlib import Path
import tkinter as tk
from Interface import ReviewApp
from pdf_to_text import *
from Interface import *
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis de ambiente do ficheiro
load_dotenv(BASE_DIR / ".env")

# Obter a chave API
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada no ficheiro .env")

# URL da API do Gemini
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.8-flash:generateContent"
)


def generate_content(prompt_text: str) -> dict:
    """
    Gera conteúdo através da API do Gemini.

    Args:
        prompt_text (str): Texto enviado ao Gemini.

    Returns:
        dict: Resposta da API em formato JSON.
    """

    # Confirma que existe uma chave de API
    if not API_KEY:
        raise ValueError("A variável GEMINI_API_KEY não está definida.")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {

            # Reduz o raciocínio interno para acelerar a resposta
            "thinkingConfig": {
                "thinkingLevel": "low"
            }
        }
    }

    # Envia o pedido para a API do Gemini
    response = requests.post(
        API_URL,
        headers=headers,
        json=body
    )

    # Verifica se a API devolveu algum erro HTTP
    if not response.ok:
        raise RuntimeError(
            f"Erro da API Gemini ({response.status_code}): "
            f"{response.text}"
        )

    # Devolve a resposta em formato JSON
    return response.json()


def anonymize(text: str) -> str:
    """
    Envia o texto de um documento para o Gemini e
    devolve a versão anonimizada.
    """

    # Lê as instruções de anonimização
    with open(
        "submission/prompt.txt",
        "r",
        encoding="utf-8"
    ) as file:
        prompt = file.read()

    # Junta as instruções ao documento original
    prompt_text = f"{prompt}\n\nDocument:\n{text}"

    # Envia o documento para o Gemini
    output = generate_content(prompt_text)

    # Verifica se o Gemini devolveu conteúdo
    if "candidates" not in output:
        raise RuntimeError(
            f"O Gemini não devolveu texto: {output}"
        )

    # Extrai apenas o texto gerado pelo Gemini
    response_text = (
        output["candidates"][0]["content"]["parts"][0]["text"]
    )

    return response_text


# Executa a anonimização do documento real
if __name__ == "__main__":
    path_to_pdf = "../nos-gen-ai-hackathon/raw_data/document_to_anonymize.pdf"
    extracted_text = extract_text_from_pdf(path_to_pdf)
    print(extracted_text)

    txt_path = path_to_pdf.replace(".pdf", ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    print(f"✅ Text extracted and saved to: {txt_path}")

    # Lê o texto extraído do PDF
    with open(
        "raw_data/document_to_anonymize.txt",
        "r",
        encoding="utf-8"
    ) as file:
        texto_documento = file.read()

    print("A iniciar anonimização...")

    # Regista o instante inicial
    inicio = time.perf_counter()

    # Envia o documento para o Gemini
    resultado = anonymize(texto_documento)

    # Calcula o tempo de processamento
    fim = time.perf_counter()

    # Guarda a resposta do Gemini no ficheiro de submissão
    with open(
        "submission/submission.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(resultado)


    print("Documento anonimizado com sucesso!")
    print(f"Tempo de processamento: {fim - inicio:.2f} segundos")

    root = tk.Tk()
    ReviewApp(root)
    root.mainloop()
    