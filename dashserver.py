#! /usr/local/opt/python-3.9.4/bin/python3.9
"""
This application serves as a way of maniuplating a pandas dataframe for each user to update the work outs saved.
The graphs will then update dynamically.


To do:
    - serve figures with various options (raw numbers, weighted by body weight)
    - accept Apple Health XML to update weight
"""
# first party
import os
from pathlib import Path
import pdb
import logging
from typing import Optional
import sys


# third party
import dash
from dash import Dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import pandas as pd

app = Dash("Funcitonal Fitness", )
stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(__name__+".log", mode="a+")
logging.basicConfig(format='%(asctime)s - %(module)s.%(funcName)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG, handlers=[file_handler, stream_handler])
logger = logging.getLogger(__file__)

app.layout = html.Div([
    html.Button("Add Row", id='add-row-button', n_clicks=0),
    html.Button("Add Column", id='add-column-button', n_clicks=0),
    html.Button("Save", id='save-button', n_clicks=0),
    dash_table.DataTable(
        id='exercise-table',
        sort_action="native",
        filter_action='native',
    ),
    dcc.Store(id='exercise-data'),
    html.Div(id='hidden-div', hidden=True)

])

# read in file, if it doesnt exist, make it


def make_dataframe(file_name: Path):
    """
    Fetches the local dataframe for the user if it exists, else create a new one.

    Args:
        file_name (Path): Path dataframe *should* exist at.

    Returns:
        pd.DataFrame: Loaded DataFrame for that user. 
    """

    logger.info("Making DataFrame")
    if file_name.exists():
        logger.info(f"Reading DataFrame from file {file_name}")
        df = pd.read_csv(file_name, index_col=0)

    else:
        logger.info(f"Creating DataFrame and saving to file {file_name}")
        df = pd.DataFrame()
        df['Date'] = []
        df['Exercise'] = []
        df['Weight'] = []
        df['Sets'] = []
        df['Reps'] = []
        df['Volume'] = []
        df['Muscle Group'] = []

        df.to_csv(file_name)
    return df


# update dataframe depending on button press
@app.callback(Output('exercise-data', 'data'),
              [Input('add-column-button', 'n_clicks'),
               Input('add-row-button', 'n_clicks')],
              [State('exercise-data', 'data')])
def update_dataframe(col_but: int, row_but: int, data: Optional[str]):

    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id']
    logger.info(f"Update_DataFrame triggered by {trigger}")

    # load in DataFrame if it doesnt already exist.
    if data is None:
        df = make_dataframe(Path("user.csv"))
    # data already exists, load it in.
    else:
        df = pd.read_json(data)

    # parse context of this callback
    if trigger == 'add-column-button.n_clicks':
        df['New Column'] = [None] * len(df)
        logger.info("Added new column.")
    elif trigger == 'add-row-button.n_clicks':
        df = df.append(pd.Series(dtype='object'), ignore_index=True)
        logger.info("Added new row.")
    else:
        logger.error("Triggered by unforseen context.")

    # send to dcc.Store as json.
    return df.to_json()


@app.callback([Output('exercise-table', 'columns'),
               Output('exercise-table', 'data')],
              [Input('exercise-data', 'data')], prevent_initial_call=True)
def update_datatable(raw_df: str):
    df = pd.read_json(raw_df)

    if df.empty:
        raise dash.exceptions.PreventUpdate

    columns = [{'name': col, 'id': col, 'renamable': True,
                'editable': True} for col in df.columns]
    data = df.values if df.empty else df.to_dict('records')

    logger.info(
        f"Updating datatable w/ len(col) = {len(columns)} and len(data) = {len(data)}")

    return columns, data


@app.callback(Output('hidden-div', 'children'),
              [Input('save-button', 'n_clicks')],
              [State('exercise-table', 'data')], prevent_initial_call=True)
def save_datatable(save_nClicks: int, data_table: str):
    logger.info("Saving DataTable to file.")
    df = pd.DataFrame(data_table)
    df.to_csv(Path('user.csv'))
    return True


app.run_server(host="0.0.0.0", port="8050", debug=True)
