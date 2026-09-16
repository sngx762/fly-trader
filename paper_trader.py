"""
Симулятор портфеля (Paper Trader) для исполнения ордеров и расчета P&L.
"""

import config


class PaperTrader:
    """Симулятор портфеля для оценки эффективности торговой стратегии агента."""

    def __init__(self, balance: float = config.INITIAL_BALANCE):
        self.cash = balance
        self.position = 0.0  # 0 - нет позиции, 1 - лонг
        self.entry_price = 0.0
        self.last_price = 0.0
        self.equity_curve = [balance]
        self.trades = []

    def update_price(self, price: float) -> float:
        """Обновление текущей цены и расчет текущего эквити."""
        self.last_price = price
        equity = self.cash
        if self.position > 0:
            equity = self.cash + self.position * price
        self.equity_curve.append(equity)
        return equity

    def execute(self, action: int, price: float) -> float:
        """Исполнение торгового действия (0: hold, 1: buy, 2: sell) и возврат изменения equity."""
        self.last_price = price
        prev_equity = self.get_equity()
        pnl_delta = 0.0

        if action == 1 and self.position == 0:
            self.position = (self.cash * config.MAX_POSITION) / price
            self.cash = 0.0
            self.entry_price = price
            self.trades.append({"type": "BUY", "price": price})

        elif action == 2 and self.position > 0:
            revenue = self.position * price
            pnl = revenue - (self.position * self.entry_price)
            pnl_delta = pnl
            self.cash += revenue
            self.position = 0.0
            self.trades.append({"type": "SELL", "price": price, "pnl": pnl})

        current_equity = self.get_equity()
        if prev_equity > 0:
            equity_change = current_equity - prev_equity
        else:
            equity_change = 0.0

        return pnl_delta if pnl_delta != 0.0 else equity_change

    def get_equity(self) -> float:
        """Текущий размер капитала (equity)."""
        if self.position > 0:
            return self.cash + self.position * self.last_price
        return self.cash
