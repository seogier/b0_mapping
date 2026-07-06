"""Tool for measuring the change in magnetic field over time."""
import print3d
import lakeshore
import csv
import argparse
import numpy as np
import time
from alive_progress import alive_bar
from datetime import datetime

parser = argparse.ArgumentParser('Map the B0 of a magnet with a 3D printer and Hall probe.')
parser.add_argument('probe_port', action='store', help='Port for Hall probe communication (e.g. COM1)')
parser.add_argument('printer_port', action='store', help='Port for 3D printer communication (e.g. COM5)')
parser.add_argument('-s', '--save_name', action='store', required=True)

args = parser.parse_args()
port_lakeshore = args.probe_port
port_printer = args.printer_port
save_name = args.save_name

probe = lakeshore.LakeshoreF71(port_lakeshore)

n_points = 60*60*24
with open(save_name, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, dialect='excel')
    csvwriter.writerow(['Time', 'Mag', 'Bx', 'By', 'Bz', 'T'])
    with alive_bar(n_points, dual_line=True) as bar:
        bar.title('B0 Stability Measurement in Progress')
        for point in range(n_points):
            time.sleep(1)
            timepoint = datetime.now()
            field = probe.get_field()
            temp = probe.get_temp()
            bar.text(f'{timepoint}: Mag:{field[0]}, X:{field[1]}, Y:{field[2]}, Z:{field[3]}')
            csvwriter.writerow([timepoint, *field, temp])
            bar()
