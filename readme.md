# B0 Mapping Tools

Because the 3D printer and teslameter present themselves to the PC as serial devices, you'll need to look up the port of each device whenever you plug them in and use that in your code.

## Setup

You'll need to install a the following python libraries:
 - numpy
 - pyvisa
 - alive-progress

As well as the the [NI-VISA library](https://pyvisa.readthedocs.io/en/stable/faq/getting_nivisa.html).

## B0 Mapping

b0_map.py is a script to map the B0 of a magnet using a PC-connected 3D printer and teslameter/gaussmeter.

Usage is as follows:

`py b0_map.py [probe_port] [printer_port] [shape] [--diameter] [--center] [--save_name] [--spacing] [--restart]`

e.g. `python .\b0_map.py COM4 COM5 circle -c 110 101 152 -s ../Smallbach_ring_0_background.csv`

`[probe_port]` is the COM port for the tesla/gaussmeter (e.g., COM3)

`[printer_port]` is the COM port for the 3D printer (e.g., COM4)

`[shape]` is the shape of the region to map. Options include:
 - `cube`
 - `cylinder`
 - `sphere`
 - `circle`

`--diameter -d` is the diameter of the circle and cylinder, edge length of the cube, and height of the cylinder, in mm. Default is 100 mm

`--set_center_pos -x` interactively set the center position of the magnet.

`--center -c` is the center of the measurement volume, in mm. Default is (110, 110, 250).

`--save_name -s` is the filename to save the results in (in CSV format)

`--spacing -p` is the measurement point spacing in mm. Default is 5 mm.

`--restart -r` is the index of the point to start measuring at if restarting an interrupted measurement.

## B0 Over Time

b0_time.py is a script to measure the change in magnetic field over time. Presently, the duration is hard-coded to be approximately 12 hours.

Usage is as follows:

`py b0_map.py [probe_port] [printer_port] [--save_name]`

with parameters having the same definitions as in b0_map.py

## Libraries

### print3d

print3d.py is a library to interface with a 3D printer over a serial connection for the purposes of field mapping.

Create a printer object (`p = print3d.Printer(port)`) and use that to control the printer (e.g. `p.move_wait((X, Y, Z))`).

Notes for usage:
 - This was designed to work with a Ender-5 Pro, so it may require tweaking for other printers
 - Upon initialization, motor timeout is disabled, so that the stepper motors are always energized. This prevents the bed of the printer from moving due to the weight of the magnet in printers where the magnet rests on the moving print bed.
 - Using the `move_wait` function is recommended over `move`, as with `move` there is no guarantee that the move will be complete before the next command - often a measurement that requires a stationary probe.

### lakeshore

lakeshore.py is a library to interface with a Lakeshore F71 Teslameter with a single-axis probe. It uses VISA and SCPI commands to obtain readings from the probe.

Create an object (`l = lakeshore.LakeshoreF71(port)`) and use that to interface with the teslameter (`l.get_field()`)