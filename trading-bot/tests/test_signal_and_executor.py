import os
import tempfile

from src.signal_generator import SignalGenerator, Signal, SignalContext
from src.executor import OrderExecutor


def test_signal_generator_opens_long_on_low_zscore():
    sg = SignalGenerator(beta=1.0, intercept=0.0, entry=2.0, exit_=0.5, stoploss=4.0)
    # spread = 100 - 1.0*110 = -10 ; mean=0, std=5 -> zscore = -2.0 -> LONG
    ctx = sg.next(price_a=100.0, price_b=110.0, mean=0.0, std=5.0)
    assert ctx.signal == Signal.LONG
    assert sg.current_position == 1


def test_signal_generator_closes_on_reversion():
    sg = SignalGenerator(beta=1.0, intercept=0.0, entry=2.0, exit_=0.5, stoploss=4.0)
    sg.next(price_a=100.0, price_b=110.0, mean=0.0, std=5.0)  # ouvre long
    ctx = sg.next(price_a=100.0, price_b=100.0, mean=0.0, std=5.0)  # spread proche de 0
    assert ctx.signal == Signal.CLOSE
    assert sg.current_position == 0


def test_signal_generator_stoploss_triggers_close():
    sg = SignalGenerator(beta=1.0, intercept=0.0, entry=2.0, exit_=0.5, stoploss=4.0)
    sg.next(price_a=100.0, price_b=110.0, mean=0.0, std=5.0)  # ouvre long (z=-2.0)
    ctx = sg.next(price_a=50.0, price_b=110.0, mean=0.0, std=5.0)  # spread s'effondre encore plus (z <= -4)
    assert ctx.signal == Signal.CLOSE


def test_signal_generator_holds_when_no_condition_met():
    sg = SignalGenerator(beta=1.0, intercept=0.0, entry=2.0, exit_=0.5, stoploss=4.0)
    ctx = sg.next(price_a=100.0, price_b=100.0, mean=0.0, std=5.0)  # zscore ~ 0
    assert ctx.signal == Signal.HOLD
    assert sg.current_position == 0


def test_executor_simulation_round_trip_computes_pnl():
    with tempfile.TemporaryDirectory() as tmp:
        log_path = os.path.join(tmp, "executions.csv")
        executor = OrderExecutor(log_path=log_path)
        executor._last_trade_ts = 0

        open_ctx = SignalContext(price_a=100.0, price_b=10.0, spread=0.0, zscore=-2.5,
                                  signal=Signal.LONG, current_position=1)
        open_result = executor.execute(open_ctx)
        assert open_result is not None
        assert open_result.pnl == 0.0

        executor._last_trade_ts = 0  # ignore le délai minimum pour le test
        close_ctx = SignalContext(price_a=110.0, price_b=10.0, spread=0.0, zscore=0.1,
                                   signal=Signal.CLOSE, current_position=0)
        close_result = executor.execute(close_ctx)

        assert close_result is not None
        # qty_a = 100/100 = 1.0 ; PnL = 1.0 * (110-100) - qty_b * (10-10) = 10.0
        assert abs(close_result.pnl - 10.0) < 1e-6
        assert os.path.exists(log_path)


def test_executor_respects_minimum_delay_between_trades():
    with tempfile.TemporaryDirectory() as tmp:
        executor = OrderExecutor(log_path=os.path.join(tmp, "executions.csv"))
        ctx = SignalContext(price_a=100.0, price_b=10.0, spread=0.0, zscore=-2.5,
                             signal=Signal.LONG, current_position=1)
        first = executor.execute(ctx)
        second = executor.execute(ctx)  # immédiatement après -> doit être ignoré

        assert first is not None
        assert second is None
