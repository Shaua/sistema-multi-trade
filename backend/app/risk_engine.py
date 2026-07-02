import math
from typing import List, Dict

class RiskEngine:
    def __init__(self, max_risk_per_trade: float = 0.01):
        """
        :param max_risk_per_trade: Risco máximo por trade (ex: 0.01 para 1%)
        """
        self.max_risk_per_trade = max_risk_per_trade

        # Matriz de correlação simplificada (0 a 1)
        self.correlation_matrix = {
            "US100": {"SPX500": 0.85, "BTC/USD": 0.4, "XAU/USD": 0.1, "WTI": 0.2},
            "SPX500": {"US100": 0.85, "BTC/USD": 0.35, "XAU/USD": 0.15, "WTI": 0.25},
            "BTC/USD": {"US100": 0.4, "SPX500": 0.35, "XAU/USD": 0.2, "WTI": 0.1},
            "XAU/USD": {"US100": 0.1, "SPX500": 0.15, "BTC/USD": 0.2, "WTI": 0.3},
            "WTI": {"US100": 0.2, "SPX500": 0.25, "BTC/USD": 0.1, "XAU/USD": 0.3},
        }

    def calculate_position_size(self, account_balance: float, atr: float, multiplier: float = 1.0) -> float:
        """
        Calcula o tamanho da posição com base no ATR e saldo da conta.
        Quanto maior a volatilidade (ATR), menor o lote.
        """
        risk_amount = account_balance * self.max_risk_per_trade
        # Simplificação: Stop Loss baseado em 1.5x ATR
        stop_loss_points = atr * 1.5
        
        if stop_loss_points <= 0:
            return 0.0

        # position_size = Risco Financeiro / (Distância do Stop em pontos * Multiplicador do Contrato)
        position_size = risk_amount / (stop_loss_points * multiplier)
        return round(position_size, 4)

    def check_drawdown_protection(self, max_drawdown: float) -> str:
        """
        Retorna o nível de proteção atual baseado no drawdown da conta.
        """
        if max_drawdown >= 0.15:
            return "LEVEL_3_PROTECTION" # Pausa total
        elif max_drawdown >= 0.10:
            return "LEVEL_2_PROTECTION" # Pausa temporária
        elif max_drawdown >= 0.05:
            return "LEVEL_1_PROTECTION" # Redução de lote
        
        return "NORMAL"

    def check_correlation_exposure(self, new_asset: str, open_positions: List[str]) -> float:
        """
        Calcula um fator de redução (0 a 1) com base na correlação com posições abertas.
        Se já temos uma posição em US100 e queremos abrir em SPX500, reduzimos o lote.
        """
        reduction_factor = 1.0
        
        for pos_asset in open_positions:
            if new_asset in self.correlation_matrix and pos_asset in self.correlation_matrix[new_asset]:
                correlation = self.correlation_matrix[new_asset][pos_asset]
                if correlation > 0.7:
                    # Alta correlação, reduz posição pela metade
                    reduction_factor *= 0.5
                elif correlation > 0.5:
                    # Correlação média, reduz em 20%
                    reduction_factor *= 0.8
                    
        return reduction_factor
