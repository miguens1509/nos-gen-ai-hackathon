import os
import requests


# Obtém a chave da API guardada na variável de ambiente
API_KEY = os.getenv("GEMINI_API_KEY")

# URL da API do Gemini
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-3.8-flash:generateContent?key={API_KEY}"
)


def generate_content(prompt_text: str, temperature: float) -> dict:
    """
    Gera conteúdo através da API do Gemini.

    Args:
        prompt_text (str): Texto enviado ao Gemini.
        temperature (float): Controla a aleatoriedade da resposta.

    Returns:
        dict: Resposta da API em formato JSON.
    """

    headers = {
        "Content-Type": "application/json"
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
            "temperature": temperature
        }
    }

    # Envia o pedido para o Gemini
    response = requests.post(API_URL, headers=headers, json=body)

    # Devolve a resposta completa em formato JSON
    return response.json()


def anonymize(text: str) -> str:
    """
    Envia um documento para o Gemini para ser anonimizado.
    """

    # Lê as instruções de anonimização
    with open("submission/prompt.txt", "r", encoding="utf-8") as file:
        prompt = file.read()

    # Junta as instruções ao documento que queremos anonimizar
    prompt_text = f"{prompt}\n\nDocument:\n{text}"

    # Chama a função baseada diretamente no tutorial
    output = generate_content(prompt_text, 0.0)

    # Obtém apenas o texto da resposta do Gemini,
    # exatamente como é feito no tutorial
    response_text = output["candidates"][0]["content"]["parts"][0]["text"]

    return response_text

