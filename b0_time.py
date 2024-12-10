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

printer = print3d.Printer(port_printer)

home = input("Home printer?[y/n]")
if home.lower() == 'y':
    print('Homing Printer, please wait.')
    printer.home()
    printer.wait()

n_points = 60*60*12
with open(save_name, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, dialect='excel')
    csvwriter.writerow(['Time', 'Bz'])
    with alive_bar(n_points, dual_line=True) as bar:
        bar.title('B0 Stability Measurement in Progress')
        for point in range(n_points):
            time.sleep(1)
            timepoint = datetime.now()
            field = probe.get_field()
            bar.text(f'{timepoint}: {field}')
            csvwriter.writerow([timepoint,field])
            bar()
printer.beep() # Let everyone know you're done!
