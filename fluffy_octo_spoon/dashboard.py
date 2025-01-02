from pathlib import Path

import dash  # type: ignore [import-untyped]
import pandas as pd
import plotly.express as px  # type: ignore [import-untyped]
from dash import dcc, html
from dash.dependencies import Input, Output  # type: ignore [import-untyped]

# Define the path to the classified transactions CSV file
classified_transactions_csv = Path.cwd() / "data/classified/classified_transactions.csv"

# Read the classified transactions CSV file
df = pd.read_csv(classified_transactions_csv, delimiter=";", encoding="utf-8")

# Preprocess the data
df["Buchungsdatum"] = pd.to_datetime(df["Buchungsdatum"], format="%Y-%m-%d")  # "%d.%m.%y")
df["Monat"] = df["Buchungsdatum"].dt.to_period("M").astype(str)  # Convert Period to string
df["Kategorie"] = df["Kategorie"].fillna("Sonstiges")

# Calculate the monthly sums for each category
monthly_category_sums = df.groupby(["Monat", "Kategorie"])["Einzelbetrag"].sum().abs().reset_index()

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Swiss Bank Transaction Dashboard"),
        dcc.Graph(id="bar-chart"),
        html.Label("Group by:"),
        dcc.RadioItems(
            id="group-by",
            options=[
                {"label": "Category and Month", "value": "both"},
                {"label": "Category", "value": "category"},
                {"label": "Month", "value": "month"},
            ],
            value="both",
            inline=True,
        ),
    ]
)


@app.callback(Output("bar-chart", "figure"), [Input("group-by", "value")])
def update_bar_chart(group_by):
    """Callback Function to update data using dashboard"""
    if group_by == "both":
        fig = px.bar(
            monthly_category_sums,
            x="Monat",
            y="Einzelbetrag",
            color="Kategorie",
            title="Monthly Transactions by Category",
            barmode="group",  # Use 'group' to show each category as a separate bar
        )
    elif group_by == "category":
        fig = px.bar(
            monthly_category_sums,
            x="Kategorie",
            y="Einzelbetrag",
            title="Total Transactions by Category",
            barmode="group",
        )
    else:  # group_by == 'month'
        fig = px.bar(
            monthly_category_sums.groupby("Monat").sum().reset_index(),
            x="Monat",
            y="Einzelbetrag",
            title="Total Transactions by Month",
            barmode="group",
        )
    return fig


def main():
    """Run server"""
    app.run_server(debug=True)


if __name__ == "__main__":
    main()
