import sys
import os
import pandas as pd
import time
import datetime

class SpeedProfile:

    def input_file(self, default_input='speed_profile.tsv'):
        self.user_input = raw_input('Enter speed profile file path including filename extension:\n')
        if not self.user_input:
            self.user_input = default_input
        user_input_file_type = [self.user_input[-3:], '\t' if self.user_input[-3:] == 'tsv' else ',']
        try:
            self.df = pd.read_csv(
                os.path.abspath(self.user_input), 
                delimiter = user_input_file_type[1], 
                dtype = {"Time": float},
                skiprows = [1])
        except IOError:
            print("file does not exist in the following path: %s" % os.path.abspath(self.user_input))
            sys.exit(1)
        return self.df

    def print_loaded_file(self):
        print('found file in: ' + os.path.abspath(self.user_input))

if __name__ == '__main__':
    instance = SpeedProfile()
    data = instance.input_file()
    instance.print_loaded_file()
    print(instance.df.loc[100:])
    #for row in data.itertuples(index=False):
        # print(str(round(time.time())) + ' ' + row[0] + ' ' + row[1])
        # print(type(row[0]), type(row[1]))