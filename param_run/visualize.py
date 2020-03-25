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

from SALib.analyze import morris as morris_analyze
from SALib.plotting import morris as morris_plot


def visualize_output(config_file):
    """"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    root_dir = pathlib.Path.cwd().joinpath('sim')
    output_dir = root_dir.joinpath('output')
    result_dir = root_dir.joinpath('result')
    plot_dir = root_dir.joinpath('plot')
    model_id = config['ModelID']
    base_csv = '{}.csv'.format(config['BaseModel'].strip('.osm'))
    df_csv = '{}.csv'.format(config['DFModel'].strip('.osm'))
    design_type = config['DesignType']
    design = pathlib.Path.cwd().joinpath(
        config['InputDirectory'], config['Design']
    )
    floor_area = config['FloorArea']

    # Initializaiton
    vis = PlotDFOutput(
        model_id, root_dir, output_dir, result_dir, plot_dir,
        base_csv, df_csv, design, design_type, floor_area
    )

    # Extract and export data
    vis.extract_data()

    # Visualization
    if design_type.lower() == 'param':
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
    elif design_type.lower() == 'mcs':
        labels = [d['label'] for d in config['Parameters']]
        vis.generate_histograms(labels)
    elif design_type.lower() == 'sa':
        names = [d['name'] for d in config['Parameters']]
        problem = config['Problem']
        design_cdf = pathlib.Path.cwd().joinpath(
            config['InputDirectory'],
            config['Design'].replace('.csv', '_cdf.csv')
        )
        vis.generate_sa_plots(names, problem, design_cdf)
    else:
        print("Error: Unknown analysis type")


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
            self,  model_id, root_dir, output_dir, result_dir, plot_dir,
            base_csv='', df_csv='', dsg_csv='',
            dsg_type=None, floor_area=None):
        self.root_dir = root_dir
        self.output_dir = output_dir
        self.result_dir = result_dir
        self.plot_dir = plot_dir
        self.base_csv = base_csv
        self.df_csv = df_csv
        self.design = pd.read_csv(dsg_csv)
        self.design_type = dsg_type
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

    def extract_data(self):
        """"""
        # Reference case
        df_ref = self.add_df_output().resample('H').mean()

        # Subset of data on weekdays in summer months
        df_ref_wk_sm = (
            df_ref.loc[df_ref.index.weekday < 5].loc['2017-5-1':'2017-10-31']
        )
        df_ref_wk_sm_evt = df_ref_wk_sm.loc[
            (df_ref_wk_sm.index.hour > 10) & (df_ref_wk_sm.index.hour <= 16)
        ]
        self.df_ref = df_ref_wk_sm
        self.df_ref_evt = df_ref_wk_sm_evt

        # Analysis design
        df_dsg = [d.resample('H').mean() for d in self.add_df_outputs()]

        # Subset of data on weekdays in summer months
        df_dsg_wk_sm = [
            d.loc[d.index.weekday < 5].loc['2017-5-1':'2017-10-31']
            for d in df_dsg
        ]

        df_dsg_wk_sm_evt = [
            d.loc[(d.index.hour > 10) & (d.index.hour <= 16)]
            for d in df_dsg_wk_sm
        ]
        self.df_dsg = df_dsg_wk_sm
        self.df_dsg_evt = df_dsg_wk_sm_evt

        # Export data
        self.df_ref_evt.to_csv(
            self.result_dir.joinpath('{}_Ref.csv'.format(self.model_id))
        )
        pd.concat(self.df_dsg_evt).to_csv(
            self.result_dir.joinpath(
                '{}_{}.csv'.format(self.model_id, self.design_type)
            )
        )

    # Regression plot
    def generate_regplot(self):
        """"""
        # Plot
        df_plot = self.df_ref_evt.copy()
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

        gm.fig.savefig(
            self.plot_dir.joinpath('{}-reg.png'.format(self.model_id)),
            dpi=300, bbox_inches='tight'
        )
        g.fig.savefig(
            self.plot_dir.joinpath('{}-reg-hour.png'.format(self.model_id)),
            dpi=300, bbox_inches='tight'
        )

    def generate_regplots(self):
        """"""
        # Plot
        df_plot = pd.concat(self.df_dsg_evt)
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

        for param in self.design.columns:
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

            gm.fig.savefig(
                self.plot_dir.joinpath(
                    '{}-regs-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )
            g.fig.savefig(
                self.plot_dir.joinpath(
                    '{}-regs-hour-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )

    # Box-plot
    def generate_tsplot(self, plot_type=None):
        """"""
        plot_type = 'box' if plot_type is None else plot_type

        # Plot
        df_plot = self.df_ref.copy()
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
                df_plot_ts.quantile(0.05, axis=0),
                df_plot_ts.quantile(0.95, axis=0),
                alpha=0.5, label='95% CI'
            )
        else:
            df_plot_ts.boxplot(ax=ax)

        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Demand Shed Intensity (w/ft2)')
        ax.legend()

        fig.savefig(
            self.plot_dir.joinpath(
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

            if plot_type == 'box-sep':
                fig = plt.figure(figsize=(8, 3), facecolor='w', edgecolor='k')
                ax = fig.add_subplot(111)
                df_wk_sm = pd.concat(self.df_dsg)
                value = '_'.join([self.model_id, 'shed_W_ft2'])
                df_plot_ts = df_wk_sm.loc[:, [value, param]]
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
                for i, df_wk_sm in enumerate(self.df_dsg):

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
                            df_plot_ts.quantile(0.05, axis=0),
                            df_plot_ts.quantile(0.95, axis=0),
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

            fig.savefig(
                self.plot_dir.joinpath(
                    '{}-tsplots-{}-{}.png'.format(
                        self.model_id, plot_type, param.lower()
                    )
                ),
                dpi=300, bbox_inches='tight'
            )

    def generate_boxplot(self):
        """"""
        # Subset of data on weekdays in summer months
        df_wk_sm = pd.concat(self.df_dsg_evt)

        sns.set_style('ticks')
        sns.set_context('paper', rc={"lines.linewidth": 2})
        sns.set_palette('colorblind')

        for param in self.design.columns:
            df_plot_bx_par = pd.pivot_table(
                df_wk_sm, values='_'.join([self.model_id, 'shed_W_ft2']),
                index=df_wk_sm.index, columns=param
            )

            fig = plt.figure(figsize=(5, 3), facecolor='w', edgecolor='k')
            ax = fig.add_subplot(111)
            g = df_plot_bx_par.boxplot(ax=ax, showmeans=True)
            ax.set_xlabel(param)
            ax.set_ylabel('Demand Shed Intensity (w/ft2)')

            fig.savefig(
                self.plot_dir.joinpath(
                    '{}-boxplot-{}.png'.format(self.model_id, param.lower())
                ),
                dpi=300, bbox_inches='tight'
            )

    def generate_histograms(self, labels):
        """"""
        sns.set_style('ticks')
        sns.set_context("paper", rc={"lines.linewidth": 2})

        # Parameters
        for i, param in enumerate(self.design.columns):
            fig = plt.figure(figsize=(4, 3))
            ax = fig.add_subplot(111)
            ax.hist(
                self.design.loc[:, param].values,
                alpha=0.8, density=True
            )
            ax.set_xlabel(labels[i])
            ax.set_ylabel('Probability density')
            plt.savefig(
                self.plot_dir.joinpath(
                    '{}-histogram-{}.png'.format(self.model_id, param)
                ),
                dpi=300, bbox_inches='tight'
            )

        # Output
        df_wk_sm_avg = pd.concat(
            [d.mean(axis=0) for d in self.df_dsg_evt], axis=1
        ).transpose()
        out = df_wk_sm_avg.loc[
            :, '_'.join([self.model_id, 'shed_W_ft2'])
        ].values

        fig = plt.figure(figsize=(5, 3))
        ax = fig.add_subplot(111)
        ax.hist(out, alpha=0.8, density=True)
        ax.set_xlabel('Hourly Average Demand Shed Intensity [W/ft2]')
        ax.set_ylabel('Probability Density')

        fig.savefig(
            self.plot_dir.joinpath(
                '{}-histogram.png'.format(self.model_id)
            ),
            dpi=300, bbox_inches='tight'
        )

        # Export data
        df_wk_sm_avg.to_csv(
            self.result_dir.joinpath(
                '{}_{}_Output.csv'.format(self.model_id, self.design_type)
            )
        )

    def generate_sa_plots(self, names, setting, design_file):
        """"""
        # Plot functions
        def plot_morris_cov(sa, name, outdir):
            """Plot result of sensitivity analysis using Morris method."""
            if np.isnan(sa['sigma']).any():
                # Remove sigma to trigger the use of 'mu_star_conf'in y axis
                # by SALib
                sa_plot = sa.copy()
                sa_plot['sigma'] = None
                Y = sa['mu_star_conf']
            else:
                sa_plot = sa
                Y = sa['sigma']

            fig, ax = plt.subplots(figsize=(6, 5))
            morris_plot.covariance_plot(ax, sa_plot, {})

            # TEMPORARY
            ax.set_ylim(0, 0.001)
            ax.set_xlabel(r'$\mu^\star$ [W/ft2]')
            ax.set_ylabel(r'$\sigma$ [W/ft2]')

            x_offset = ax.get_xlim()[1] * 0.01
            y_offset = ax.get_ylim()[1] * 0.01
            for i in range(len(sa['names'])):
                plt.annotate(
                    sa['names'][i],
                    (sa['mu_star'][i] + x_offset, Y[i] + y_offset)
                )
            plt.savefig(
                outdir.joinpath('{}-morris_covplot.png'.format(name)),
                dpi=300, bbox_inches='tight'
            )
            plt.close()

        def plot_morris_bar(sa, name, outdir):
            """Plot result of sensitivity analysis using Morris method."""
            # Use short variable name in plots
            sa_copy = sa.copy()

            fig, ax = plt.subplots(figsize=(6, 5))
            morris_plot.horizontal_bar_plot(ax, sa_copy, {})
            plt.savefig(
                outdir.joinpath('{}-morris_barplot.png'.format(name)),
                dpi=300, bbox_inches='tight'
            )
            plt.close()

        def plot_morris_bar_sign(sa, name, outdir):
            """Plot result of sensitivity analysis using Morris method."""
            # Use short variable name in plots
            sa_copy = sa.copy()
            sa_copy['mu_star'] = sa_copy['mu']

            fig, ax = plt.subplots(figsize=(6, 5))
            morris_plot.horizontal_bar_plot(ax, sa_copy, {})
            ax.plot([0, 0], [ax.get_ylim()[0], ax.get_ylim()[1]], 'k--')
            ax.set_xlabel(r'$\mu$ [W/ft2]')
            plt.savefig(
                outdir.joinpath('{}-morris_barplot-sign.png'.format(name)),
                dpi=300, bbox_inches='tight'
            )
            plt.close()

        # Result
        df_wk_sm_avg = pd.concat(
            [d.mean(axis=0) for d in self.df_dsg_evt], axis=1
        ).transpose()
        out = df_wk_sm_avg.loc[
            :, '_'.join([self.model_id, 'shed_W_ft2'])
        ].values

        # Analyze result
        design = pd.read_csv(design_file).values
        p = design.shape[1]
        problem = {
            'num_vars': p,
            'names': names,
            'bounds': np.tile(np.array([1e-3, 1 - 1e-3]), (p, 1))
        }
        sa = morris_analyze.analyze(
            problem, X=design, Y=out, num_levels=setting['levels']
        )

        # Generate plots
        plot_morris_cov(sa, self.model_id, self.plot_dir)
        plot_morris_bar(sa, self.model_id, self.plot_dir)
        plot_morris_bar_sign(sa, self.model_id, self.plot_dir)

        # Export result
        df_wk_sm_avg.to_csv(
            self.result_dir.joinpath(
                '{}_{}_Output.csv'.format(self.model_id, self.design_type)
            )
        )
        pd.DataFrame(sa).to_csv(
            self.result_dir.joinpath(
                '{}_{}_Morris.csv'.format(self.model_id, self.design_type)
            )
        )


if __name__ == "__main__":
    """"""
    config = sys.argv[1]
    visualize_output(config)
