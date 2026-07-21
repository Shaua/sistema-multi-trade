import os
import json
import asyncio
import time
import urllib.request

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Rate Limit Global do Gemini
_last_gemini_call_time = 0.0
GEMINI_RATE_LIMIT_DELAY = 4.5  # segundos

GEMINI_API_KEYS_RAW = os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", "dummy_key_for_testing"))
GEMINI_API_KEYS = [k.strip() for k in GEMINI_API_KEYS_RAW.split(",") if k.strip()]

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

class AIEngine:
    def __init__(self):
        self.clients = []
        self.current_client_index = 0
        try:
            if HAS_GENAI and GEMINI_API_KEYS and GEMINI_API_KEYS[0] != "dummy_key_for_testing":
                for key in GEMINI_API_KEYS:
                    self.clients.append(genai.Client(api_key=key))
            else:
                self.clients = []
        except Exception as e:
            print(f"Aviso: Não foi possível inicializar os clientes Gemini: {e}")
            self.clients = []

    def _get_current_client(self):
        if not self.clients:
            return None
        return self.clients[self.current_client_index]

    def _rotate_client(self):
        if self.clients:
            self.current_client_index = (self.current_client_index + 1) % len(self.clients)
            print(f"[AIEngine] Alternando para a chave do índice {self.current_client_index}.")

    async def _wait_for_global_rate_limit(self):
        global _last_gemini_call_time
        now = time.time()
        elapsed = now - _last_gemini_call_time
        if elapsed < GEMINI_RATE_LIMIT_DELAY:
            sleep_time = GEMINI_RATE_LIMIT_DELAY - elapsed
            await asyncio.sleep(sleep_time)
        _last_gemini_call_time = time.time()

    async def _call_groq(self, prompt: str) -> dict:
        if not GROQ_API_KEY:
            raise Exception("GROQ_API_KEY não configurada.")
        
        def make_req():
            url = "https://api.groq.com/openai/v1/chat/completions"
            data = json.dumps({
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))

        res = await asyncio.to_thread(make_req)
        content = res['choices'][0]['message']['content']
        return json.loads(content)

    async def _call_openrouter(self, prompt: str) -> dict:
        if not OPENROUTER_API_KEY:
            raise Exception("OPENROUTER_API_KEY não configurada.")
        
        def make_req():
            url = "https://openrouter.ai/api/v1/chat/completions"
            data = json.dumps({
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))

        res = await asyncio.to_thread(make_req)
        content = res['choices'][0]['message']['content']
        return json.loads(content)

    async def analyze_trade_signal(self, asset: str, strategy: str, signal: str, market_context: dict) -> dict:
        prompt = f"""
        Você é um Arquiteto de Sistemas Quantitativos e Analista Chefe de um Hedge Fund.
        Avalie o seguinte sinal gerado por nossos algoritmos automatizados:
        
        Ativo: {asset}
        Estratégia: {strategy}
        Sinal (Direção): {signal}
        Contexto de Mercado: {json.dumps(market_context)}
        
        Sua tarefa é aprovar ou vetar este sinal e explicar detalhadamente o racional da operação.
        
        REGRAS CRÍTICAS:
        1. AVALIE APENAS com base nos dados fornecidos no 'Contexto de Mercado'. NÃO invente nem assuma valores de indicadores que não foram fornecidos (ex: ADX, RSI, MACD, etc, se não estiverem no json).
        2. Se a sua análise técnica baseada exclusivamente no contexto fornecido indicar uma ação CONTRÁRIA ao Sinal ou apontar LATERALIZAÇÃO extrema sem tendência, você DEVE VETAR a operação. 
        3. Para vetar, defina o 'grau_confianca' como 0.0 e preencha obrigatoriamente 'motivo_entrada' 
        com a inconsistência encontrada no contexto fornecido.
        4. Se o sinal fizer sentido com o contexto fornecido (ex: rompimento com aumento de volume, pullback na tendência), APROVE a operação com 'grau_confianca' acima de 0.65.
        
        Retorne estritamente um JSON no seguinte formato:
        {{
            "motivo_entrada": "Explicação técnica detalhada e fundamentada baseada apenas nos dados fornecidos",
            "motivo_saida": "Condição técnica para fechamento",
            "nivel_risco": "Baixo, Moderado ou Alto",
            "grau_confianca": 0.85
        }}
        O grau de confiança deve ser numérico entre 0.0 e 1.0 (sendo 0.0 para rejeitar e acima de 0.70 para aprovar).
        """

        # 1. Tenta Gemini (com rate limit estrito global)
        if self.clients:
            max_attempts = len(self.clients)
            attempts = 0
            while attempts < max_attempts:
                client = self._get_current_client()
                try:
                    await self._wait_for_global_rate_limit()
                    response = await asyncio.to_thread(
                        client.models.generate_content,
                        model='gemini-flash-latest',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )
                    return json.loads(response.text)
                except Exception as e:
                    error_str = str(e)
                    attempts += 1
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        print(f"[Gemini] Rate Limit (429) na chave {self.current_client_index}. Tentativas: {attempts}/{max_attempts}")
                    else:
                        print(f"[Gemini] Erro na chave {self.current_client_index}: {e}. Tentativas: {attempts}/{max_attempts}")
                    self._rotate_client()

        # 2. Tenta Groq se configurado e Gemini falhou ou não tem chaves
        if GROQ_API_KEY:
            try:
                print("[Groq] Iniciando análise via fallback Groq...")
                return await self._call_groq(prompt)
            except Exception as e:
                print(f"[Groq] Falha no fallback: {e}")

        # 3. Tenta OpenRouter se configurado e anteriores falharam
        if OPENROUTER_API_KEY:
            try:
                print("[OpenRouter] Iniciando análise via fallback OpenRouter...")
                return await self._call_openrouter(prompt)
            except Exception as e:
                print(f"[OpenRouter] Falha no fallback: {e}")

        # 4. Fallback Mock de Falha se todos falharem (Evitar entradas cegas)
        print("Aviso: Todas as APIs de IA falharam ou não estão disponíveis. Bloqueando operação via fallback.")
        return {
            "motivo_entrada": "Sinal bloqueado por fallback. Erro ao contatar provedores de IA.",
            "motivo_saida": "N/A",
            "nivel_risco": "Alto",
            "grau_confianca": 0.0
        }

    async def generate_morning_report(self, portfolio_state: dict) -> str:
        return f"Relatório Matinal (08:00) gerado pela IA. Status: {portfolio_state['status']}"

    async def generate_evening_report(self, daily_performance: dict) -> str:
        return f"Relatório Noturno (20:00) gerado pela IA. PnL do dia: {daily_performance['pnl']}"

ai_engine = AIEngine()
