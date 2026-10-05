import pandas as pd

from src.services.market_chart import create_market_chart


def test_market_chart_includes_selected_moving_averages_volume_and_macd():
    history = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=80, freq="D"),
        "open": [100 + index for index in range(80)],
        "high": [102 + index for index in range(80)],
        "low": [99 + index for index in range(80)],
        "close": [101 + index for index in range(80)],
        "volume": [1_000 + index for index in range(80)],
    })

    figure = create_market_chart(
        history,
        ["MA5", "MA20"],
        price_axis_title="价格（USD）",
        up_color="#34d399",
        down_color="#fb7185",
        skip_weekends=True,
    )

    trace_names = [trace.name for trace in figure.data]
    assert trace_names == [
        "K 线", "MA5", "MA20", "成交量", "MACD 柱", "DIF", "DEA",
    ]
    assert len(figure.layout.annotations) == 3
    assert list(figure.layout.xaxis3.ticktext)[:2] == ["01/01", "01/09"]
    assert figure.layout.xaxis3.tickangle == 0
    assert figure.layout.xaxis3.rangebreaks[0].bounds == ("sat", "mon")
