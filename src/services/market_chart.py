import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.technical_indicators import add_technical_indicators


MA_COLUMNS = {
    "MA5": ("ma5", "#FBBF24"),
    "MA10": ("ma10", "#60A5FA"),
    "MA20": ("ma20", "#A78BFA"),
    "MA60": ("ma60", "#22D3EE"),
}


def create_market_chart(
    history: pd.DataFrame,
    selected_ma: list[str],
    *,
    price_axis_title: str,
    up_color: str,
    down_color: str,
    skip_weekends: bool = False,
) -> go.Figure:
    """Build a candlestick chart with optional moving averages, volume, and MACD."""
    chart_data = add_technical_indicators(
        history.rename(columns={"date": "trade_date"})
    )
    chart_x = pd.to_datetime(chart_data["trade_date"])
    tick_step = max(1, len(chart_x) // 10)
    tick_values = chart_x.iloc[::tick_step]
    tick_text = tick_values.dt.strftime("%m/%d")
    chart_fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.58, 0.22, 0.20],
        subplot_titles=("K 线与均线", "成交量", "MACD"),
    )
    chart_fig.add_trace(
        go.Candlestick(
            x=chart_x,
            open=chart_data["open"],
            high=chart_data["high"],
            low=chart_data["low"],
            close=chart_data["close"],
            name="K 线",
            increasing_line_color=up_color,
            increasing_fillcolor=up_color,
            decreasing_line_color=down_color,
            decreasing_fillcolor=down_color,
        ),
        row=1,
        col=1,
    )
    for name in selected_ma:
        column, color = MA_COLUMNS[name]
        chart_fig.add_trace(
            go.Scatter(
                x=chart_x,
                y=chart_data[column],
                name=name,
                line={"color": color},
            ),
            row=1,
            col=1,
        )
    chart_fig.add_trace(
        go.Bar(
            x=chart_x,
            y=chart_data["volume"],
            name="成交量",
            marker_color=[
                up_color if close >= open_price else down_color
                for open_price, close in zip(
                    chart_data["open"], chart_data["close"]
                )
            ],
        ),
        row=2,
        col=1,
    )
    chart_fig.add_trace(
        go.Bar(
            x=chart_x,
            y=chart_data["macd"],
            name="MACD 柱",
            marker_color=[
                up_color if value >= 0 else down_color
                for value in chart_data["macd"].fillna(0)
            ],
        ),
        row=3,
        col=1,
    )
    for column, name, color in (
        ("dif", "DIF", "#FBBF24"),
        ("dea", "DEA", "#60A5FA"),
    ):
        chart_fig.add_trace(
            go.Scatter(
                x=chart_x,
                y=chart_data[column],
                name=name,
                line={"color": color},
            ),
            row=3,
            col=1,
        )
    chart_fig.update_layout(
        height=700,
        template="plotly_dark",
        dragmode="pan",
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
        xaxis_rangeslider_visible=False,
    )
    chart_fig.update_xaxes(
        type="date",
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_text,
        tickangle=0,
        rangeslider_visible=False,
        row=3,
        col=1,
    )
    if skip_weekends:
        chart_fig.update_xaxes(
            rangebreaks=[{"bounds": ["sat", "mon"]}],
            row=3,
            col=1,
        )
    chart_fig.update_yaxes(title_text=price_axis_title, row=1, col=1)
    chart_fig.update_yaxes(title_text="成交量", row=2, col=1)
    chart_fig.update_yaxes(title_text="MACD", row=3, col=1)
    return chart_fig
