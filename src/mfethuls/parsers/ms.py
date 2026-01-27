import os
import re

import pandas as pd

from mfethuls.parsers.registry import register_parser


@register_parser('ms', 'bruker')
class BrukerMS:
    def __init__(self, file_extension='.bsc', delimiter=','):
        self.file_extension = file_extension
        self.delimiter = delimiter

    def parse(self, dict_paths):
        # Store data here
        df = pd.DataFrame()

        for name, paths in dict_paths.items():
            for path in paths:

                if path.casefold().endswith(self.file_extension):
                    df = pd.concat([df, self.parse_raw_data(path)], axis=0)

                elif path.casefold().endswith('.parquet'):
                    df = pd.concat([df, pd.read_parquet(path)], axis=0)

                else:
                    print(f'Not reading: {path}')

        return df.reset_index(drop=True)

    def parse_raw_data(self, path):
        # Read main data from raw data file
        df = pd.read_csv(path, sep=self.delimiter, names=['m/z', 'intensity'], header=None) \
               .drop_duplicates(subset=['m/z']) \
               .apply(pd.to_numeric, errors='coerce') \
               .sort_values(by='m/z', ascending=True) \
               .reset_index(drop=True) \
               .dropna(axis=0, how='any')
               
        name = f'{os.path.basename(os.path.normpath(path)).casefold().rstrip(self.file_extension)}'
        df.loc[:, 'name'] = [name] * df.shape[0]

        peak_mz = self._read_peak_mz_from_raw_file(path)
        df['peaks'] = df['m/z'].isin(peak_mz)
    
        return df

    def _read_peak_mz_from_raw_file(self, path):
        # Identify peaks from raw data file
        lines = []
        with open(path) as f:
            take = 0
            for line in f.readlines():

                if take == 1:
                    curate_line = re.split(',', line.strip(), maxsplit=2)
                    lines.append(curate_line)

                if 'Peak' in line:
                    take = 1

                elif 'End' in line:
                    take = 0

        df_peaks = pd.DataFrame(lines, columns=['m/z', 'intensity']) \
                     .apply(pd.to_numeric, errors='coerce' ) \
                     .dropna(axis=0, how='any')

        return df_peaks['m/z']
