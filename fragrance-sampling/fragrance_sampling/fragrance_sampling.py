import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# dracula:
color_scheme = {
    "bg": "#282A36",
    "fg": "#F8F8F2",
    "red": "#FF5555",
    "green": "#50FA7B",
    "hl": "#8BE9FD",
}


app = Dash(__name__)
app.layout = html.Div(
    [
        html.H1("fragrance sampling"),
        dcc.Interval(
            id="load_interval",
            n_intervals=0,
            max_intervals=0,  # <-- only run once
            interval=1,
        ),
        html.H4("KPIs"),
        html.Div(id="kpis"),
        html.H4("Orders"),
        dcc.Graph(id="order_cost_plot"),
        dcc.Graph(id="order_amount_plot"),
        dcc.Graph(id="order_rating_plot"),
        dcc.Graph(id="house_rating_plot"),
        dcc.Graph(id="fragrances_house_plot"),
        dcc.Graph(id="hist_plot"),
        dcc.Store(id="df"),
    ],
    style={
        "padding": "50px 50px 50px 100px",
        "backgroundColor": color_scheme["bg"],
        "color": color_scheme["fg"],
    },
)


@app.callback(Output("df", "data"), Input("load_interval", "n_intervals"))
def load_data(n_intervals):
    df = pd.read_csv(
        "fragrance_sampling/fragrance_sampling_data.csv",
        sep=";",
        encoding="UTF-8",
        decimal=",",
    )

    for date_col in ["order_date", "arrival_date", "shipping_date"]:
        df[date_col] = pd.to_datetime(df[date_col], format="%d.%m.%y")

    df["sample_cost_ml"] = df["sample_cost"] / df["sample_ml"]
    df["bottle_cost_ml"] = df["bottle_cost"] / df["bottle_ml"]

    return df.to_json(date_format="iso", orient="split")


@app.callback(
    Output("kpis", "children"),
    Input("df", "data"),
)
def calculate_kpis(df):

    df = pd.read_json(df, orient="split")

    kpis = {
        "Unique Fragrances": df[["house", "fragrance"]].drop_duplicates().shape[0],
        "Unique Houses": df["house"].drop_duplicates().shape[0],
        "Total ML (Samples)": df["sample_ml"].sum(),
        "Total ML (Bottles)": df["bottle_ml"].sum(),
        "Total Cost (Sampling)": df["sample_cost"].sum(),
        "Total Cost (Bottles)": df["bottle_cost"].sum(),
        "Average Cost / ML (Sampling)": df["sample_cost_ml"].mean(),
        "Average Cost / ML (Bottles)": df["bottle_cost_ml"].mean(),
    }

    div_list = []
    for k, v in kpis.items():
        div_list.append(html.Div([f"{k}: {v:.2f}"]))

    return html.Div(div_list)


def style_chart(fig, style):
    if style == "vbar":
        fig.update_xaxes(showgrid=False, gridcolor=color_scheme["fg"], zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor=color_scheme["fg"], zeroline=False)

    elif style == "bar":
        fig.update_xaxes(showgrid=True, gridcolor=color_scheme["fg"], zeroline=False)
        fig.update_yaxes(showgrid=False, gridcolor=color_scheme["fg"], zeroline=False)

    fig.update_layout(
        font_color=color_scheme["fg"],
        title_font_color=color_scheme["fg"],
        legend_title_font_color=color_scheme["fg"],
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
    )

    fig.update_traces(marker_color=color_scheme["hl"])

    return fig


@app.callback(
    Output("order_cost_plot", "figure"),
    Output("order_amount_plot", "figure"),
    Output("order_rating_plot", "figure"),
    Output("house_rating_plot", "figure"),
    Output("fragrances_house_plot", "figure"),
    Output("hist_plot", "figure"),
    Input("df", "data"),
)
def plot(df):
    df = pd.read_json(df, orient="split")

    order_cost_data = df.groupby(["order_date"], as_index=False).sum("sample_cost")
    order_cost_plot = px.bar(
        order_cost_data, x="order_date", y="sample_cost", title="Cost per Order"
    )
    order_cost_plot = style_chart(order_cost_plot, "vbar")
    order_cost_plot.update_layout(yaxis_ticksuffix="€", yaxis_tickformat=",.")

    order_amount_data = df.groupby(["order_date"], as_index=False).sum("amount")
    order_amount_plot = px.bar(
        order_amount_data, x="order_date", y="amount", title="Fragrances per Order"
    )
    order_amount_plot = style_chart(order_amount_plot, "vbar")

    order_rating_data = df.groupby(["order_date"], as_index=False).mean("rating")
    order_rating_plot = px.bar(
        order_rating_data,
        x="order_date",
        y="rating",
        title="Rating per Order",
        range_y=[0, 5.5],
    )
    order_rating_plot = style_chart(order_rating_plot, "vbar")

    house_rating_data = (
        df.groupby(["house"], as_index=False).mean("rating").sort_values("rating")
    )
    house_rating_plot = px.bar(
        house_rating_data,
        x="rating",
        y="house",
        range_x=[0, 5.5],
        orientation="h",
        title="Average Rating per House",
    )
    house_rating_plot = style_chart(house_rating_plot, "bar")

    fragrances_house_data = (
        df.groupby(["house"], as_index=False).size().sort_values("size")
    )
    fragrances_house_plot = px.bar(
        fragrances_house_data,
        x="size",
        y="house",
        title="Fragrances per House",
        orientation="h",
    )
    fragrances_house_plot = style_chart(fragrances_house_plot, "bar")

    hist_data = df.groupby(["rating"], as_index=False).size()
    hist_plot = px.bar(hist_data, x="rating", y="size", title="Rating Distribution")
    hist_plot = style_chart(hist_plot, "vbar")

    return (
        order_cost_plot,
        order_amount_plot,
        order_rating_plot,
        house_rating_plot,
        fragrances_house_plot,
        hist_plot,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
