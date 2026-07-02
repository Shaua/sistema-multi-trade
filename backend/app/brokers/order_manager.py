import asyncio
from .broker_factory import broker_factory

class OrderManager:
    def __init__(self):
        pass

    async def execute_trade(self, asset: str, signal: str, volume: float, stop_loss_price: float):
        """
        Abre uma nova posição no mercado e posiciona o stop loss.
        """
        print(f"--- INIT EXECUTION: {asset} ---")
        broker = broker_factory.get_broker(asset)
        
        # 1. Executar ordem a mercado
        side = "BUY" if signal == "LONG" else "SELL"
        order_res = await broker.place_market_order(asset, side, volume)
        
        # 2. Posicionar Stop Loss (somente se stop_loss_price > 0)
        if stop_loss_price and stop_loss_price > 0:
            stop_side = "SELL" if signal == "LONG" else "BUY"
            await broker.place_stop_loss(asset, stop_side, stop_loss_price, volume)
        
        print(f"--- EXECUTION COMPLETE: {asset} ---")
        return order_res

    async def close_position(self, asset: str, direction: str, volume: float):
        """
        Fecha uma posição existente com ordem a mercado, sem criar novo stop loss.
        direction = direção da posição aberta ('LONG' ou 'SHORT')
        """
        print(f"--- CLOSING POSITION: {asset} {direction} ---")
        broker = broker_factory.get_broker(asset)
        
        # Para fechar: se estava LONG, vende; se estava SHORT, compra
        close_side = "SELL" if direction == "LONG" else "BUY"
        order_res = await broker.place_market_order(asset, close_side, volume)
        
        print(f"--- POSITION CLOSED: {asset} ---")
        return order_res

order_manager = OrderManager()
