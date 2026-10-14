"""
Punto de entrada del agente economico.

Uso (desde la raiz del repo, con environment activo y .env cargado):
    python -m agent.main "como va la inflacion?"
    python -m agent.main          # lee la pregunta por stdin
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from agent.graph import build_agent


def main() -> None:
    # Cargar placeholders/secretos desde .env (nunca hardcodear tokens)
    load_dotenv()

    # Pregunta: argumento CLI o stdin
    if len(sys.argv) > 1:
        pregunta = " ".join(sys.argv[1:]).strip()
    else:
        pregunta = input("Pregunta: ").strip()
    if not pregunta:
        print("No se indico ninguna pregunta.")
        sys.exit(1)

    # create_agent -> grafo LangGraph; invoke con mensajes tipo chat
    agent = build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": pregunta}]})

    # Ultimo mensaje del asistente (respuesta final al usuario)
    messages = result.get("messages") or []
    if not messages:
        print(result)
        return
    ultimo = messages[-1]
    # .text une los bloques de contenido (Gemini devuelve una lista, no un str)
    print(getattr(ultimo, "text", None) or str(ultimo))


if __name__ == "__main__":
    main()
