import sys
import os
import pandas as pd
import time
import datetime

class SpeedProfile:

    def input_file(self, default_input='speedProfile'):
        self.user_input = input('Enter speed profile file path including filename extension:\n')
        user_input_file_type = [self.user_input[-3:], '\t' if self.user_input[-3:] == 'tsv' else ',']
        if not self.user_input:
            self.user_input = default_input
        try:
            self.df = pd.read_csv(os.path.abspath(self.user_input), delimiter=user_input_file_type[1], encoding='utf-8')
        except FileNotFoundError:
            print("file does not exist in the following path: %s" % os.path.abspath(self.user_input))
            sys.exit(1)
        return self.df

    def print_loaded_file(self):
        print('found file in: ' + os.path.abspath(self.user_input))

if __name__ == '__main__':
    instance = SpeedProfile()
    data = instance.input_file()
    # instance.print_loaded_file()
    # for row in data.itertuples():
    #     print(str(round(time.time())) + ' ' + row[1] + ' ' + row[2])
    now = time.time()
    now_c = round(time.time() * 1e6)
    time.sleep(1e-3)
    print(time.time() - now)
    print(round(time.time() * 1e6) - now_c)