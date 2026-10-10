import difflib
import re
from pathlib import Path


def comparar_documentos(original, anonimizado):
    # Separar o texto em linhas
    linhas_original = original.splitlines()
    linhas_final = anonimizado.splitlines()

    # Comparar as linhas dos dois documentos
    diff_linhas = difflib.SequenceMatcher(
        None, linhas_original, linhas_final, autojunk=False
    )

    for tipo, i1, i2, j1, j2 in diff_linhas.get_opcodes():

        if tipo == "equal":
            continue

        # Comparar as linhas alteradas
        for linha_original, linha_final in zip(
            linhas_original[i1:i2], linhas_final[j1:j2]
        ):
            # Separar palavras, preservando espaços
            tokens_original = re.findall(r"\S+|\s+", linha_original)
            tokens_final = re.findall(r"\S+|\s+", linha_final)

            diff = difflib.SequenceMatcher(
                None, tokens_original, tokens_final, autojunk=False
            )

            for operacao, a1, a2, b1, b2 in diff.get_opcodes():

                if operacao == "equal":
                    continue

                # Destacar o texto original que foi alterado
                inicio = sum(len(t) for t in tokens_original[:a1])
                fim = sum(len(t) for t in tokens_original[:a2])

                contexto = (
                    linha_original[:inicio]
                    + "*"
                    + linha_original[inicio:fim]
                    + "*"
                    + linha_original[fim:]
                )

                print(f"\nLinha {i1 + 1}:")
                print(contexto)
                f = open("submission/comparison_results.txt", "a", encoding="utf-8")
                while True:
                    resposta = input(
                        "Anonimização correta? (y/n): "
                    ).strip().lower()
                    if resposta == "y":
                        break

                    elif resposta == "n":

                        f.write(f"Linha {i1 + 1}: {contexto}\n")
                        
                        break

                    print("Introduz apenas y ou n.")
                f.close()


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Ler o texto original
    caminho_original = (
        BASE_DIR / "raw_data" / "document_to_anonymize.txt"
    )

    with open(caminho_original, encoding="utf-8") as f:
        original = f.read()

    # Ler o texto anonimizado
    caminho_final = BASE_DIR / "submission" / "submission.txt"

    with open(caminho_final, encoding="utf-8") as f:
        anonimizado = f.read()

    # Iniciar comparação
    comparar_documentos(original, anonimizado)