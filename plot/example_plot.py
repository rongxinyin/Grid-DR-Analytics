import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("Office_Cases.csv")

fig = go.Figure(data=
go.Parcoords(
    line=dict(color = df['BldgType'],
              colorscale = [[1,'lightgray'],[0.5,'blue'],[0.5,'red']]),
    dimensions=list([
        dict(range=[1, 5],
             # constraintrange = [1,2], # change this range by dragging the pink line
             tickvals=[1, 2, 3, 4, 5],
             label='Building Type', values=df['BldgType'],
             ticktext=['Small Retail', 'Medium-Large Retail','Small Office', 'Medium Office', 'Large Office']),
        dict(range=[1, 5],
             tickvals=[1, 2, 3, 4, 5],
             label='Building Vintage', values=df['BldgVint'],
             ticktext=['Pre-1980', '1980-2004', '90.1-2004', '90.1-2010', '90.1-2016']),
        dict(range=[1, 5],
             tickvals=[1, 2, 3, 4, 5],
             label='Climate Zone', values=df['BldgLoc'],
             ticktext=['2A (Hot-Humid)', '2B (Hot-Dry)', '3A (Warm-Humid)', '3B (Warm-Dry)', '4A (Mixed–Humid)']),
        dict(range=[1, 5],
             tickvals=[2, 4],
             label='Construction', values=df['BldgConst'],
             ticktext=['Mass Wall', 'Steel-framed']),
        dict(range=[1, 5],
             tickvals=[1, 2, 3, 4, 5],
             label='Tstat', values=df['Tstat'],
             ticktext=['72', '73', '74', '74', '76'])
    ])
)
)
fig.show()
