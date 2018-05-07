import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import ws_listener
import threading
import argparse

import datastorage
import params


def create_app():
    app = dash.Dash('KatieDJ-app')

    app.layout = html.Div([
        html.Div([
            html.H2('Katie DJ - Data Broadcast')
        ], className='banner'),
        html.Div([
            html.Div([
                html.H3('Traffic time series')
            ], className='Title'),
            html.Div([
                dcc.Graph(id='traffic-data'),
            ], className='twelve columns wind-speed'),
            dcc.Interval(id='traffic-data-update', interval=5000, n_intervals=0)
        ], className='row wind-speed-row')
    ])
    external_css = [
        "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
        "https://cdn.rawgit.com/plotly/dash-app-stylesheets/737dc4ab11f7a1a8d6b5645d26f69133d97062ae/dash-wind-streaming.css",
        "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
         "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i",
    ]
    for css in external_css:
        app.css.append_css({"external_url": css})
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--storage',
                        action='store',
                        required=False,
                        dest='storage',
                        default=None,
                        help='Path to storage file (sqlite)')
    args = parser.parse_args()
    data_store = datastorage.DataObj(storage=args.storage)
    arguments = {'ping_timeout': 5,
                 'reply_timeout': 10,
                 'sleep_time': 5}
    client = ws_listener.WSClient(
                    params.URL, **arguments)
    client.register(data_store)
    wst = threading.Thread(
        target=ws_listener.start_ws_client, args=(client,))
    wst.daemon = True
    wst.start()
    app = create_app()

    @app.callback(Output('traffic-data', 'figure'), [Input('traffic-data-update', 'n_intervals')])
    def get_new_data(interval):
        traces = []
        for k, val in data_store.lines.items():
            traces.append(
                go.Scatter(
                    y=val,
                    mode='lines',
                    name='Road {}'.format(k)
                )
            )
        layout = go.Layout(
            xaxis=dict(title='Time [steps from start]'),
            yaxis=dict(title='Number of vehicles')
        )
        return go.Figure(data=traces, layout=layout)
    
    app.run_server()
