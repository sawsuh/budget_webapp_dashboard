from dash import Dash, html, dcc, callback, Output, Input, dash_table
from dash.dash_table.Format import Format, Scheme
import pandas as pd
import dash_bootstrap_components as dbc

df = pd.read_csv("finances.csv")


def get_weeks(df_in):
    df_out = df_in.copy()
    df_out["date"] = pd.to_datetime(df_out["date"], format="%d/%m/%Y")
    df_out["week_first"] = df_out["date"].dt.to_period("W").dt.start_time
    df_out["week"] = df_out["week_first"].dt.strftime("%d/%m/%Y")

    weeks_out = df_out["week_first"].unique()
    weeks_out = weeks_out[weeks_out.argsort()][::-1].strftime("%d/%m/%Y")
    return (df_out, weeks_out)


df_weekly, weeks = get_weeks(df)
first_weeks = weeks[:5]


def summarise_weekly(df_in, weeks_in):
    df_out = (
        df_in.groupby(["categorisation", "week"])["amount"]
        .sum()
        .unstack()[weeks_in]
        .reset_index("categorisation")
    )
    return pd.concat(
        [
            df_out,
            pd.DataFrame(
                {
                    **{"categorisation": ["TOTAL"]},
                    **{
                        i: [df_out[i].sum()]
                        for i in list(df_out.columns)
                        if i != "categorisation"
                    },
                }
            ),
        ]
    ).round(2)


df_weekly_summary = summarise_weekly(df_weekly, first_weeks)


def table_display_helper(df_in):
    return [
        {
            **{"name": i, "id": i},
            **(
                {}
                if i == "categorisation"
                else {
                    "type": "numeric",
                    "format": Format(precision=2, scheme=Scheme.fixed),
                }
            ),
        }
        for i in df_in.columns
    ]


app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1(children="Weekly sums", style={"textAlign": "left"}))),
        dbc.Row(
            dbc.Col(
                dbc.Table.from_dataframe(
                    df_weekly_summary,
                    striped=True,
                    bordered=True,
                    hover=True,
                )
            )
        ),
        dbc.Row(
            dbc.Col(html.H1(children="Specific week", style={"textAlign": "left"}))
        ),
        dbc.Row(dbc.Col(dcc.Dropdown(weeks, weeks[0], id="dropdown-week"))),
        dbc.Row(dbc.Col(html.Div(id="graph-content"))),
        dbc.Row(dbc.Col(html.H1(children="Transactions", style={"textAlign": "left"}))),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(list(df["categorisation"].unique()), id="dropdown-cat")
            )
        ),
        dbc.Row(dbc.Col(html.Div(id="cat_filter"))),
    ]
)


@callback(Output("graph-content", "children"), Input("dropdown-week", "value"))
def week_table(week):
    dat = summarise_weekly(df_weekly, week)
    return html.Div(
        [dbc.Table.from_dataframe(dat, striped=True, bordered=True, hover=True)]
    )


@callback(Output("cat_filter", "children"), Input("dropdown-cat", "value"))
def cat_table(cat):
    return html.Div(
        [
            dbc.Table.from_dataframe(
                df[df["categorisation"] == cat] if cat else df,
                striped=True,
                bordered=True,
                hover=True,
            )
        ]
    )


if __name__ == "__main__":
    app.run(debug=True)
