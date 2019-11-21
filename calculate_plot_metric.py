import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pathlib
import shutil
import seaborn as sns


def read_eplus_output(csv_file):
    df = pd.read_csv(csv_file)
    rng = pd.date_range('1/1/2017 0:00', '12/31/2017 23:45', freq='15min')
    df.index = rng
    df['date'] = rng
    df.rename(columns={'Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)': 'oat',
                       'Electricity:Facility [J](TimeStep)': 'bldg'},
              inplace=True)
    df.oat = df.oat * 1.8 + 32  # convert to F
    df.bldg = df.bldg / 900000  # convert to kW
    # print(df.head())
    df['year'] = df.date.apply(lambda x: x.strftime('%Y'))
    df['time'] = df.date.apply(lambda x: x.strftime('%H:%M'))
    df['month'] = df.date.apply(lambda x: x.strftime('%m'))
    df['day'] = df.date.apply(lambda x: x.strftime('%d'))
    df['hour'] = df.date.apply(lambda x: x.strftime('%H'))
    df['minute'] = df.date.apply(lambda x: x.strftime('%M'))
    df['weekday'] = df.date.apply(lambda x: x.strftime('%w'))
    df['month'] = df.month.astype(int)
    df['weekday'] = df.weekday.astype(int)
    df['hour'] = df.hour.astype(int)
    # print(df.columns)
    return df[['date', 'year', 'time', 'month', 'day', 'hour', 'minute', 'weekday', 'oat', 'bldg']]

class PlotDFOutput(object):
    def __init__(self, floor_area, base_csv='', df_csv='', model_id=''):
        self.floor_area = floor_area
        self.base_csv = base_csv
        self.df_csv = df_csv
        self.model_id = model_id
        self.root_path = pathlib.Path.cwd()

    def add_df_output(self):
        # read base and df eplus csv files
        base_input = self.root_path.joinpath('eplus_output', self.base_csv)
        # print(base_input)
        base = read_eplus_output(base_input)

        df_input = self.root_path.joinpath('eplus_output', self.df_csv)
        df = read_eplus_output(df_input)

        base[self.model_id + '_' + 'bldg'] = df.bldg
        base[self.model_id+'_'+'shed_pct'] = (base.bldg - df.bldg) / base.bldg
        base[self.model_id+'_'+'shed_W_ft2'] = (base.bldg - df.bldg) * 1000 / self.floor_area

        return base

    def generate_plot(self):
        df = self.add_df_output()
        # Subset of data on weekdays in summer months
        df_wk = df[(df['weekday'] > 0) & (df['weekday'] < 6) & (df['month'] <= 10) & (df['month'] > 4)]
        df_wk = df_wk.resample('60min').mean()
        print(df_wk.head())

        # plot
        sns.set_style('ticks')
        sns.set_context("talk", rc={"lines.linewidth": 2})
        fig, axes = plt.subplots(2, 3, figsize=(15, 6), sharex=True, sharey=True)

        for startHour in range(12, 18):
            x1 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat <= 75)].oat
            # y1 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat <= 75)].shed_pct
            y12 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat <= 75)][self.model_id+'_'+'shed_pct']
            x2 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat > 75)].oat
            # y2 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat > 75)].shed_pct
            y22 = df_wk.loc[(df_wk.hour == (startHour - 1)) & (df_wk.oat > 75)][self.model_id+'_'+'shed_pct']

            # break temp points of regression model
            breaks = [75, 95]
            # Two linear regression functions at the breakpoint 70F
            z1 = np.polyfit(x1, y12, 1)
            p1 = np.poly1d(z1)
            xp1 = np.linspace(min(x1), breaks[0], 100)

            z2 = np.polyfit(x2, y22, 1)
            p2 = np.poly1d(z2)
            xp2 = np.linspace(breaks[0], max(x2), 100)

            axes.ravel()[startHour - 12].plot(x1, y12, 'o', label='OAT <= 75F')
            axes.ravel()[startHour - 12].plot(x2, y22, 'o', label='OAT > 75F')
            axes.ravel()[startHour - 12].plot(xp1, p1(xp1), '-')
            axes.ravel()[startHour - 12].plot(xp2, p2(xp2), '-')
            axes.ravel()[startHour - 12].set_title(str(startHour) + ':00' + '~' + str(startHour + 1) + ':00',
                                                   color='red')
            if startHour > 15:
                axes.ravel()[startHour - 12].set_xlabel('Outside Air Temperature, $^\circ$F')
            axes.ravel()[startHour - 12].set_ylabel('Demand Shed Density (w/ft2)')
            axes.ravel()[startHour - 12].legend(loc='upper left')
        output_path = self.root_path.joinpath('eplus_output', 'plot')
        fig.savefig(output_path.joinpath('{}-test.png'.format(self.model_id)), dpi=300, bbox_inches='tight')


# test
test = PlotDFOutput(floor_area=53628,
                    base_csv='MediumOffice_Post1980_3B_74_12_18_0_0.csv',
                    df_csv='MediumOffice_Post1980_3B_74_12_18_2_4.csv',
                    model_id='Post1980')
test.generate_plot()