# NOS Gen-AI Hackathon — Anonimização de documentos

Solução de anonimização de documentos com a API Gemini e revisão humana através de uma interface gráfica em Tkinter. O sistema substitui palavras sensíveis por `*` e utiliza as correções do revisor para melhorar as instruções de anonimização.

## Como funciona

1. Extrai o texto de `raw_data/document_to_anonymize.pdf` e guarda-o em `raw_data/document_to_anonymize.txt`.
2. Envia o texto e as instruções de `submission/prompt.txt` ao Gemini.
3. Guarda a proposta em `submission/submission.txt` e abre a interface de revisão.
4. O utilizador adiciona ou remove máscaras e clica em **Guardar**. A interface guarda o documento revisto e as correções manuais.
5. Se existirem correções, uma segunda chamada envia o prompt atual, o documento original e o feedback ao Gemini. Esta chamada pede regras lógicas gerais que previnam os erros, sem acrescentar exemplos específicos, e atualiza `submission/prompt.txt`.

O prompt atualizado é usado na execução seguinte. A segunda chamada não volta a anonimizar o documento da execução atual.

## Requisitos

- Python 3 com Tkinter disponível.
- Ligação à Internet e uma chave da API Gemini com acesso ao modelo configurado em `submission/anonymizer.py`.
- Um PDF com texto extraível; o fluxo atual não inclui OCR para documentos digitalizados.

## Instalação

Abre um terminal na raiz deste repositório, a pasta `nos-gen-ai-hackathon`.

Em Windows / PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install requests python-dotenv PyMuPDF
```

Cria um ficheiro `.env` na raiz do repositório:

```dotenv
GEMINI_API_KEY=a_tua_chave
```

Podes obter uma chave no [Google AI Studio](https://aistudio.google.com/). Não publiques a chave nem o ficheiro `.env`. Se `GEMINI_API_KEY` já estiver definida no ambiente, essa variável tem prioridade sobre o valor no ficheiro.

## Execução

Coloca o PDF em `raw_data/document_to_anonymize.pdf` e verifica as instruções em `submission/prompt.txt`.

A partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe submission/anonymizer.py
```

É necessário executar a partir desta pasta porque a função `anonymize` lê `submission/prompt.txt` através de um caminho relativo.

### Revisão manual

- As palavras marcadas a vermelho serão substituídas por `*`.
- Clica numa palavra para adicionar ou remover a máscara.
- Arrasta o rato para marcar ou desmarcar várias palavras.
- Clica em **Guardar** para exportar o resultado, registar as correções e fechar a janela.

A interface preserva a pontuação exterior das palavras mascaradas e remove linhas vazias na exportação. Se apresentar avisos de alinhamento entre o original e a proposta, revê essas linhas manualmente.

O ficheiro de correções é esvaziado antes de cada revisão. Fechar a janela sem guardar não exporta as alterações manuais nem desencadeia a melhoria do prompt; a proposta inicial permanece em `submission.txt`.

Para abrir apenas a interface, usando os ficheiros existentes:

```powershell
.\.venv\Scripts\python.exe submission/Interface.py
```

Este comando não chama a API nem atualiza automaticamente o prompt.

## Ficheiros principais

| Ficheiro | Função |
| --- | --- |
| `submission/anonymizer.py` | Extração, chamadas à API, revisão e melhoria do prompt. |
| `submission/Interface.py` | Interface gráfica para rever as máscaras e guardar correções. |
| `submission/prompt.txt` | Instruções de anonimização, atualizadas após uma revisão com correções. |
| `submission/submission.txt` | Proposta do Gemini ou resultado final após guardar a revisão. |
| `submission/comparisions_results.txt` | Feedback manual: informação indevidamente mascarada e informação que deveria ter sido mascarada. |
| `raw_data/document_to_anonymize.pdf` | Documento de entrada. |
| `raw_data/document_to_anonymize.txt` | Texto original extraído do PDF. |
| `submission/pdf_to_text.py` | Utilitário separado de extração; não é necessário executá-lo no fluxo principal. |

## Resolução de problemas

- **Chave não definida:** verifica `GEMINI_API_KEY` no `.env` ou no ambiente.
- **Prompt não encontrado:** executa o comando na raiz do repositório.
- **PDF não encontrado:** confirma o nome e a localização do ficheiro de entrada.
- **Tempo de espera excedido:** a chamada configura 10 segundos para ligação e 60 segundos de espera de leitura. Um timeout não confirma que a chave seja inválida; verifica a ligação e tenta novamente.
- **Erro HTTP da API:** consulta o código e a mensagem apresentados no terminal para identificar problemas de acesso, quota ou modelo.
- **Tkinter indisponível:** usa uma instalação de Python que inclua suporte para Tkinter e um ambiente com interface gráfica.

O documento original é enviado ao Gemini na primeira chamada e, quando existem correções, também na segunda. O texto original e o feedback são guardados localmente.

## Submissão no hackathon

Consulta as [regras de submissão](submission/README.md) e os [critérios de avaliação](tutorials/problem_and_eval.md).

As regras pedem o resultado em `submission/submission.txt`, o prompt exato usado para o gerar em `submission/prompt.txt` e o código desenvolvido. Como a melhoria automática substitui o prompt depois de gerar o resultado, conserva uma cópia do prompt usado na execução final e confirma a correspondência antes de submeter. O resultado guardado pela interface pode incluir correções humanas; verifica também a sua compatibilidade com as regras de submissão.

## Recursos

- [Tutorial de Git](tutorials/git_tutorial.md)
- [Tutorial de Gemini](tutorials/gemini_tutorial.md)
- [Conversão de PDF para texto](tutorials/pdf__to__txt.ipynb)
- [Licença](LICENSE)
