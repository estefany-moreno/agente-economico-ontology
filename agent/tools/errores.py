"""
Errores "seguros" de las tools: su mensaje se le muestra al LLM y al usuario.

Solo los mensajes de ErrorDeFuente llegan al modelo. Cualquier otra excepcion
se reporta solo por su tipo, porque su texto puede traer datos internos
(p. ej. la URL de INEGI lleva el token en la ruta).
"""


class ErrorDeFuente(RuntimeError):
    """Fallo esperado al consultar una fuente externa (Sheets, INEGI, Banxico)."""
