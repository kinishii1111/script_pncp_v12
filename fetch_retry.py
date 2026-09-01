"""
fetch_retry.py
Responsabilidade: executar requisições HTTP GET com retry e backoff exponencial.
Não conhece paginação, não conhece persistência, não conhece regras da API PNCP.
"""
import json
import sys
import time
from typing import Optional, Tuple

import requests

# Uma sessão: keep-alive. Recriar GET a cada página estoura o 429.
_SESSION = requests.Session()
_SESSION.headers.update(
    {"Accept": "application/json", "User-Agent": "pncp-find/1"}
)
# pausa entre páginas depois de um 429 (o coletor lê isso)
pausa_sugerida = 0.5


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


class HttpRetryClient:
    """Executa requisições HTTP GET com retry e backoff exponencial."""

    def __init__(
        self,
        max_tentativas: int = 4,
        backoff_inicial: float = 1.0,
        timeout: int = 45,
    ) -> None:
        """
        Inicializa o cliente HTTP.

        Args:
            max_tentativas: Número máximo de tentativas por requisição.
            backoff_inicial: Tempo inicial de espera entre tentativas (segundos).
            timeout: Timeout em segundos para cada requisição.
        """
        self.max_tentativas = max_tentativas
        self.backoff_inicial = backoff_inicial
        self.timeout = timeout
        self._headers = {'accept': '*/*'}

    def get(
        self, url: str, params: dict
    ) -> Optional[Tuple[list, Optional[int]]]:
        """
        Executa um GET com retry e backoff exponencial.

        Args:
            url: URL completa da requisição.
            params: Parâmetros de query string.

        Returns:
            Tupla (dados, total_paginas) em caso de sucesso,
            ([], None) para respostas sem conteúdo,
            ou None em caso de erro fatal.
        """
        tentativas = 0
        backoff = self.backoff_inicial

        while tentativas < self.max_tentativas:
            try:
                resposta = _SESSION.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                # 200 OK: sucesso
                if resposta.status_code == 200:
                    return self._processar_200(resposta)

                # 204 No Content: fim da paginação
                if resposta.status_code == 204:
                    return ([], None)

                # 400/422: erro nos parâmetros, não adianta tentar de novo
                if resposta.status_code in [400, 422]:
                    _log(
                        f"Erro de cliente {resposta.status_code}:"
                        f" {resposta.text}"
                    )
                    return None

                # 429: rate limit do PNCP — espera mais que o backoff padrão
                if resposta.status_code == 429:
                    global pausa_sugerida
                    espera = max(20.0, backoff)
                    pausa_sugerida = 1.2
                    _log(
                        f"429 — espera {espera:.0f}s (não paralelizar; pausa páginas→{pausa_sugerida}s)"
                    )
                    time.sleep(espera)
                    tentativas += 1
                    backoff = min(backoff * 2, 60)
                    continue

                # 500+: erro de servidor, tenta de novo
                _log(
                    f"Erro {resposta.status_code}."
                    f" Tentando novamente em {backoff}s..."
                )

            except requests.exceptions.RequestException as e:
                _log(f"Erro de conexão: {e}. Tentando novamente em {backoff}s...")
            except json.JSONDecodeError:
                _log("Erro ao decodificar JSON. Retornando None.")
                return None

            time.sleep(backoff)
            tentativas += 1
            backoff *= 2  # backoff exponencial

        _log("Número máximo de tentativas atingido. Falha ao buscar dados.")
        return None

    def _processar_200(
        self, resposta: requests.Response
    ) -> Tuple[list, Optional[int]]:
        """
        Extrai dados e total de páginas de uma resposta 200 OK.

        Args:
            resposta: Objeto Response com status 200.

        Returns:
            Tupla (dados, total_paginas) ou ([], None) se formato inesperado.
        """
        dados_resposta = resposta.json()

        if isinstance(dados_resposta, dict) and 'data' in dados_resposta:
            dados = dados_resposta.get('data', [])
            total_paginas = dados_resposta.get('totalPaginas')
            return (dados, total_paginas)

        _log("Resposta 200 OK, mas JSON em formato inesperado.")
        return ([], None)


# --- Fachada: preserva compatibilidade com pncp_client.py e código existente ---

def fetch_com_retry(
    url: str,
    params: dict,
    max_tentativas: int = 5,
    backoff_inicial: float = 1.0,
) -> Optional[Tuple[list, Optional[int]]]:
    """
    Fachada que preserva a assinatura original.
    Instancia HttpRetryClient e executa a requisição.

    Args:
        url: URL completa da requisição.
        params: Parâmetros de query string.
        max_tentativas: Número máximo de tentativas.
        backoff_inicial: Tempo inicial de espera entre tentativas.

    Returns:
        Tupla (dados, total_paginas), ([], None) ou None.
    """
    cliente = HttpRetryClient(
        max_tentativas=max_tentativas,
        backoff_inicial=backoff_inicial,
    )
    return cliente.get(url, params)
