#!/usr/bin/env python

import glob
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

filename = "step_response.tsv"
L = 1.13 # System intrinsic delay
coefs = (0.00025367167216867206, 0.013758701616520147, 0.29619387624368226)


def func(x, a=1, b=1, c=1):
    return (1*x / (a*x**2 + b*x + c))


def main(mode='optimize'):

    t, vel = np.loadtxt(filename, delimiter='\t', unpack=True)

    print(type(t), type(vel))
    plt.scatter(t, vel, marker='o', c='r')

    if mode is 'manual':
        y = func(t, *coefs)
        plt.plot(t, y, 'b-', label='data')
    elif mode is 'optmize':
        popt, pcov = curve_fit(func, t, vel, maxfev = 10000)
        for coef in popt:
                print(coef)
        plt.plot(t, func(t, *popt), 'b-', label = 'fit: a=%5.3f, b=%5.3f, , c=%5.3f' % tuple(popt))
        plt.legend(loc='best')
    plt.show()


if not os.path.exists(filename):
    print(filename + " doesn't exist")

else:
    main()

