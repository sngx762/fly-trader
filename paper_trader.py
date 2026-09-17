"""
Симулятор портфеля (Paper Trader) для исполнения ордеров и расчета P&L с поддержкой плеча (leverage).
"""

import config


class PaperTrader:
    """Симулятор портфеля для оценки эффективности торговой стратегии агента."""

    def __init__(self, balance: float = config.INITIAL_BALANCE):
        self.cash = balance
        self.position = 0.0  # 0 - нет позиции, лонг с плечом
        self.entry_price = 0.0
        self.last_price = 0.0
        self.equity_curve = [balance]
        self.trades = []

    def update_price(self, price: float) -> float:
        """Обновление текущей цены и расчет текущего эквити."""
        self.last_price = price
        equity = self.cash
        if self.position > 0:
            equity = self.cash + self.position * price - (self.position * self.entry_price * (config.LEVERAGE - 1.0)) if config.LEVERAGE > 1 else self.cash + self.position * price
        # Correct equity calculation for leveraged paper trade:
        # Borrowed amount = self.entry_price * self.position * (LEVERAGE - 1) / LEVERAGE ... simpler:
        # Equity = cash + current position value - borrowed cash
        if self.position > 0:
            position_value = self.position * price
            borrowed_cash = (self.entry_price * self.position) * ((config.LEVERAGE - 1.0) / config.LEVERAGE) if config.LEVERAGE > 1 else 0.0
            # Wait, when buying with leverage L, cash used = C, borrowed = C * (L-1). Total position size = C * L / price.
            # So borrowed cash = C * (L-1) = position * price * (L-1) / L.
            # Equity = cash (0) + position * price - borrowed_cash = position * price * (1 - (L-1)/L) = position * price / L?
            # Let's check: when position is opened, cash = 0, position = C * L / price.
            # If price changes to price_new, equity = position * price_new - borrowed_cash = (C * L / price) * price_new - C * (L - 1) = C * L * (price_new / price) - C * L + C = C + C * L * (price_new / price - 1).
            # That correctly reflects leveraged return!
            borrowed = (self.entry_price * self.position / config.LEVERAGE) * (config.LEVERAGE - 1.0) if config.LEVERAGE > 1 else 0.0
            equity = self.cash + self.position * price - borrowed
        else:
            equity = self.cash
        self.equity_curve.append(equity)
        return equity

    def execute(self, action: int, price: float) -> float:
        """Исполнение торгового действия (0: hold, 1: buy, 2: sell) и возврат изменения equity."""
        self.last_price = price
        prev_equity = self.get_equity()
        pnl_delta = 0.0

        if action == 1 and self.position == 0:
            buy_amount = self.cash * config.LEVERAGE
            self.position = (buy_amount * config.MAX_POSITION) / price
            self.cash = 0.0
            self.entry_price = price
            self.trades.append({"type": "BUY", "price": price})

        elif action == 2 and self.position > 0:
            revenue = self.position * price
            borrowed = (self.entry_price * self.position / config.LEVERAGE) * (config.LEVERAGE - 1.0) if config.LEVERAGE > 1 else 0.0
            net_revenue = revenue - borrowed
            pnl = net_revenue - (self.cash if self.cash > 0 else 0) # profit relative to starting cash before this trade
            # Or simply pnl = net_revenue - initial invested cash for this trade
            invested_cash = (self.entry_price * self.position) / config.LEVERAGE
            pnl = net_revenue - invested_cash
            pnl_delta = pnl
            self.cash = net_revenue
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
            borrowed = (self.entry_price * self.position / config.LEVERAGE) * (config.LEVERAGE - 1.0) if config.LEVERAGE > 1 else 0.0
            return self.cash + self.position * self.last_price - borrowed
        return self.cash
