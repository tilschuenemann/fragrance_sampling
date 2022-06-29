import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px


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
    ]
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

    order_amount_data = df.groupby(["order_date"], as_index=False).sum("amount")
    order_amount_plot = px.bar(
        order_amount_data, x="order_date", y="amount", title="Fragrances per Order"
    )

    order_rating_data = df.groupby(["order_date"], as_index=False).mean("rating")
    order_rating_plot = px.bar(
        order_rating_data, x="order_date", y="rating", title="Rating per Order"
    )

    house_rating_data = (
        df.groupby(["house"], as_index=False).mean("rating").sort_values("rating")
    )
    house_rating_plot = px.bar(
        house_rating_data,
        x="rating",
        y="house",
        orientation="h",
        title="Average Rating per House",
    )

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

    hist_data = df.groupby(["rating"], as_index=False).size()
    hist_plot = px.histogram(
        hist_data, x="rating", y="size", title="Rating Distribution"
    )

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
