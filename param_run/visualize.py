# -*- coding: utf-8 -*-

import sys
import pathlib
import shutil
import json
import csv

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def visualize_output(config_file, floor_area, model_id):
    """"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    root_dir = pathlib.Path.cwd().joinpath('sim')
    output_dir = root_dir.joinpath('output')
    base_csv = '{}.csv'.format(config['BaseModel'].strip('.osm'))
    df_csv = '{}.csv'.format(config['DFModel'].strip('.osm'))
    design = pathlib.Path.cwd().joinpath(
        config['InputDirectory'], config['Design']
    )

    # Initializaiton
    vis = PlotDFOutput(
        root_dir, output_dir, base_csv, df_csv, design, floor_area, model_id
    )

    # Visualization
    switcher = {
        'Regplot': vis.generate_regplot,
        'Regplots': vis.generate_regplots,
        'TSplot': vis.generate_tsplot,
        'TSplots': vis.generate_tsplots,
        'Boxplot': vis.generate_boxplot
    }

    try:
        plots = config['Plots']
    except KeyError:
        plots = ['Regplot', 'Regplots', 'TSplot', 'TSplots', 'Boxplot']
    for p in plots:
        switcher.get(p, vis.generate_regplot)()
    if 'TSplots' in plots:
        vis.generate_tsplots(plot_type='band')
        vis.generate_tsplots(plot_type='box-sep')


def read_eplus_output(csv_file):
    """"""
    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
    df.rename(
        columns={
            'Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)':
                'oat',
            'Electricity:Facility [J](TimeStep)': 'bldg'
        },
        inplace=True
    )
    df.oat = df.oat * 1.8 + 32  # convert to F
    df.bldg = df.bldg / 900000  # convert to kW
    return df


class PlotDFOutput(object):
    """"""
    def __init__(
            self, root_dir, output_dir,
            base_csv='', df_csv='', dsg_csv='', floor_area=None, model_id=''):
        self.root_dir = root_dir
        self.output_dir = output_dir
        self.base_csv = base_csv
        self.df_csv = df_csv
        self.design = pd.read_csv(dsg_csv)
        self.floor_area = floor_area
        self.model_id = model_id

    def add_df_output(self, base_csv=None, df_csv=None):
        """"""
        base_csv = self.base_csv if base_csv is None else base_csv
        df_csv = self.df_csv if df_csv is None else df_csv

        # Read base and df eplus csv files
        base = read_eplus_output(self.output_dir.joinpath(base_csv))
        df = read_eplus_output(self.output_dir.joinpath(df_csv))

        base['_'.join([self.model_id, 'bldg'])] = df.bldg
        base['_'.join([self.model_id, 'shed_pct'])] = (
            (base.bldg - df.bldg) / base.bldg
        )
        base['_'.join([self.model_id, 'shed_W_ft2'])] = (
            (base.bldg - df.bldg) * 1000 / self.floor_area
        )

        # print(base[self.model_id+'_'+'shed_W_ft2'].max())

        return base

    def add_df_outputs(self):
        """"""
        # Read base and df eplus csv files of each instance
        outputs = []
        n, m = self.design.shape
        for i in range(n):
            output = self.add_df_output(
                '{}_Inst_{}.csv'.format(self.base_csv.split('.')[0], i+1),
                '{}_Inst_{}.csv'.format(self.df_csv.split('.')[0], i+1),
            )
            # TEMPORARY: Add feature
            for j in range(m):
                output[self.design.columns[j]] = self.design.iloc[i, j]
            outputs.append(output)

        return outputs

    # Regression plot
    def generate_regplot(self):
        """"""
        df = self.add_df_output().resample('H').mean()

        # Subset of data on weekdays in summer months
        df_wk_sm = df.loc[df.index.weekday < 5].loc['2017-5-1':'2017-10-31']
        df_wk_sm = df_wk_sm.loc[
            (df_wk_sm.index.hour > 10) & (df_wk_sm.index.hour <= 16)
        ]
        # print(df_wk_sm.head())

        # Plot
        df_plot = df_wk_sm.copy()
        df_plot['hour'] = df_plot.index.hour
        df_plot['hour'] = df_plot['hour'].apply(
            lambda x: '{}:00~{}:00'.format(x, x+1)
        )
        df_plot['oat_range'] = df_plot.oat.apply(
            lambda x: 'OAT > 75F' if x > 75 else 'OAT <= 75F'
        )

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        # All hours
        gm = sns.lmplot(
            x='oat', y='_'.join([self.model_id, 'shed_W_ft2']),
            hue='oat_range', data=df_plot,
            height=3, aspect=5/3, ci=None, legend=False, truncate=True
        )
        gm.set_xlabels('Outside Air Temperature, °F')
        gm.set_ylabels('Demand Shed Intensity (w/ft2)')
        gm.ax.legend(loc=2)

        # Each hour
        g = sns.lmplot(
            x='oat', y='_'.join([self.model_id, 'shed_W_ft2']),
            col='hour', col_wrap=3, hue='oat_range', data=df_plot,
            height=3, aspect=5/3, ci=None, legend=False, truncate=True
        )
        # g.despine(trim=True)
        g.set_titles('{col_name}')
        g.set_xlabels('Outside Air Temperature, °F')
        g.set_ylabels('Demand Shed Intensity (w/ft2)')
        for ax in g.axes:
            ax.legend(loc=2)

        output_path = self.root_dir.joinpath('plot')
        gm.fig.savefig(
            output_path.joinpath('{}-reg.png'.format(self.model_id)),
            dpi=300, bbox_inches='tight'
        )
        g.fig.savefig(
            output_path.joinpath('{}-reg-hour.png'.format(self.model_id)),
            dpi=300, bbox_inches='tight'
        )

    def generate_regplots(self):
        """"""
        df = pd.concat([d.resample('H').mean() for d in self.add_df_outputs()])

        # Subset of data on weekdays in summer months
        df_wk_sm = df.loc[df.index.weekday < 5].loc['2017-5-1':'2017-10-31']
        df_wk_sm = df_wk_sm.loc[
            (df_wk_sm.index.hour > 10) & (df_wk_sm.index.hour <= 16)
        ]

        # Plot
        df_plot = df_wk_sm.copy()
        df_plot['hour'] = df_plot.index.hour
        df_plot['hour'] = df_plot['hour'].apply(
            lambda x: '{}:00~{}:00'.format(x, x+1)
        )
        df_plot['oat_range'] = df_plot.oat.apply(
            lambda x: 'OAT > 75F' if x > 75 else 'OAT <= 75F'
        )

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        for i in range(self.design.shape[1]):
            param = self.design.columns[i]
            response = '_'.join([self.model_id, 'shed_W_ft2'])
            df_plot_inst = df_plot[
                [response, 'oat', 'oat_range', 'hour', param]
            ]

            df_plot_inst.insert(
                loc=0, column='cat',
                value=(
                    '{} = '.format(param)
                    + df_plot_inst[param].map(str) + ', '
                    + df_plot_inst['oat_range']
                )
            )

            # All hours
            gm = sns.lmplot(
                x='oat', y=response, hue='cat',
                data=df_plot_inst, height=3, aspect=5/3,
                ci=None, legend=False, truncate=True
            )
            gm.set_xlabels('Outside Air Temperature, °F')
            gm.set_ylabels('Demand Shed Intensity (w/ft2)')
            gm.ax.legend(loc=2)

            # Each hour
            g = sns.lmplot(
                x='oat', y=response, col='hour', col_wrap=3, hue='cat',
                data=df_plot_inst, height=3, aspect=5/3,
                ci=None, legend=False, truncate=True
            )
            # g.despine(trim=True)
            g.set_titles('{col_name}')
            g.set_xlabels('Outside Air Temperature, °F')
            g.set_ylabels('Demand Shed Intensity (w/ft2)')
            for ax in g.axes:
                ax.legend(loc=2)

            output_path = self.root_dir.joinpath('plot')
            gm.fig.savefig(
                output_path.joinpath(
                    '{}-regs-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )
            g.fig.savefig(
                output_path.joinpath(
                    '{}-regs-hour-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )

    # Box-plot
    def generate_tsplot(self, plot_type=None):
        """"""
        plot_type = 'box' if plot_type is None else plot_type

        df = self.add_df_output().resample('H').mean()

        # Subset of data on weekdays in summer months
        df_wk_sm = df.loc[df.index.weekday < 5].loc['2017-5-1':'2017-10-31']

        # print(df_wk_sm.head())

        # Plot
        df_plot = df_wk_sm.copy()
        df_plot['hour'] = df_plot.index.hour
        df_plot_ts = pd.pivot_table(
            df_plot, values='_'.join([self.model_id, 'shed_W_ft2']),
            index=df_plot.index.date, columns='hour'
        )

        # print(df_plot_bx.head())

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        fig = plt.figure(figsize=(5, 3), facecolor='w', edgecolor='k')
        ax = fig.add_subplot(111)

        ax.plot(range(1, 25), df_plot_ts.mean(), '-ro', label='Average')
        if plot_type == 'band':
            ax.fill_between(
                range(1, 25),
                df_plot_ts.quantile(0.025, axis=0),
                df_plot_ts.quantile(0.975, axis=0),
                alpha=0.5, label='95% CI'
            )
        else:
            df_plot_ts.boxplot(ax=ax)

        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Demand Shed Intensity (w/ft2)')
        ax.legend()

        output_path = self.root_dir.joinpath('plot')
        fig.savefig(
            output_path.joinpath(
                '{}-tsplot-{}.png'.format(self.model_id, plot_type)
            ),
            dpi=300, bbox_inches='tight'
        )

    def generate_tsplots(self, plot_type=None):
        """"""
        plot_type = 'box' if plot_type is None else plot_type

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        for j in range(self.design.shape[1]):
            param = self.design.columns[j]

            dfs = self.add_df_outputs()
            if plot_type == 'box-sep':
                fig = plt.figure(figsize=(8, 3), facecolor='w', edgecolor='k')
                ax = fig.add_subplot(111)
                df_m = pd.DataFrame(columns=dfs[0].columns)
                for d in dfs:
                    df = d.resample('H').mean()
                    df_wk_sm = (
                        df.loc[df.index.weekday < 5]
                        .loc['2017-5-1':'2017-10-31']
                    )
                    df_m = df_m.append(df_wk_sm)

                value = '_'.join([self.model_id, 'shed_W_ft2'])
                df_plot_ts = df_m.loc[:, [value, param]]
                df_plot_ts['hour'] = df_plot_ts.index.hour
                df_plot_ts.index = df_plot_ts.index.date

                sns.boxplot(
                    x='hour', y=value, hue=param, data=df_plot_ts, ax=ax,
                    linewidth=0.5,
                    flierprops=dict(
                        marker='o', markerfacecolor='none',
                        markersize=2, markeredgewidth=0.5
                    )
                )

                handles, _ = ax.get_legend_handles_labels()
                ax.legend(
                    handles,
                    [
                        '{} = {}'.format(param, v)
                        for v in self.design.iloc[:, j]
                    ]
                )

            else:
                fig = plt.figure(figsize=(5, 3), facecolor='w', edgecolor='k')
                ax = fig.add_subplot(111)
                for i, d in enumerate(dfs):
                    df = d.resample('H').mean()
                    df_wk_sm = (
                        df.loc[df.index.weekday < 5]
                        .loc['2017-5-1':'2017-10-31']
                    )

                    # Plot
                    df_plot = df_wk_sm.copy()
                    df_plot['hour'] = df_plot.index.hour
                    df_plot_ts = pd.pivot_table(
                        df_plot,
                        values='_'.join([self.model_id, 'shed_W_ft2']),
                        index=df_plot.index.date, columns='hour'
                    )

                    color = sns.color_palette()[i]
                    ax.plot(
                        range(1, 25), df_plot_ts.mean(axis=0), color=color,
                        label='{} = {}'.format(param, self.design.iloc[i, j])
                    )
                    if plot_type == 'band':
                        ax.fill_between(
                            range(1, 25),
                            df_plot_ts.quantile(0.025, axis=0),
                            df_plot_ts.quantile(0.975, axis=0),
                            color=color, alpha=0.5
                        )
                    else:
                        box = df_plot_ts.boxplot(
                            ax=ax, patch_artist=True, return_type='dict'
                        )
                        plt.setp(box['boxes'], color=color, alpha=0.5)
                        for item in ['whiskers', 'fliers', 'medians', 'caps']:
                            plt.setp(box[item], color=color)
                        plt.setp(box["fliers"], markeredgecolor=color)

                    ax.legend()

            ax.set_xlabel('Hour of Day')
            ax.set_ylabel('Demand Shed Intensity (w/ft2)')

            output_path = self.root_dir.joinpath('plot')
            fig.savefig(
                output_path.joinpath(
                    '{}-tsplots-{}-{}.png'.format(
                        self.model_id, plot_type, param.lower()
                    )
                ),
                dpi=300, bbox_inches='tight'
            )

    def generate_boxplot(self):
        """"""
        df = pd.concat([d.resample('H').mean() for d in self.add_df_outputs()])

        # Subset of data on weekdays in summer months
        df_wk_sm = df.loc[df.index.weekday < 5].loc['2017-5-1':'2017-10-31']
        df_wk_sm = df_wk_sm.loc[
            (df_wk_sm.index.hour > 10) & (df_wk_sm.index.hour <= 16)
        ]

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        for i in range(self.design.shape[1]):
            param = self.design.columns[i]
            df_plot_bx_par = pd.pivot_table(
                df_wk_sm, values='_'.join([self.model_id, 'shed_W_ft2']),
                index=df_wk_sm.index, columns=param
            )

            fig = plt.figure(figsize=(5, 3), facecolor='w', edgecolor='k')
            ax = fig.add_subplot(111)
            g = df_plot_bx_par.boxplot(ax=ax)
            ax.set_xlabel(param)
            ax.set_ylabel('Demand Shed Intensity (w/ft2)')

            output_path = self.root_dir.joinpath('plot')
            fig.savefig(
                output_path.joinpath(
                    '{}-boxplot-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )

        # TEMPORARY
        df_wk_sm.to_csv(output_path.joinpath('data_output.csv'))


if __name__ == "__main__":
    """"""
    config = sys.argv[1]
    floor_area = float(sys.argv[2])
    model_id = sys.argv[3]
    visualize_output(config, floor_area, model_id)
