"""One error type for every US01 step.

The message names the step and the cause. It never includes row content.
"""


class ErroUS01(Exception):
    def __init__(self, codigo: str, passo: str, causa: str):
        self.codigo = codigo
        self.passo = passo
        self.causa = causa
        super().__init__(
            f"Falha no passo {passo} ({codigo}). Causa: {causa}. A bronze não foi alterada."
        )
