"""Tool for mapping the B0 of a magnet using a 3D printer as a motion stage/positioning system"""
import print3d
import lakeshore
import csv
import argparse
import numpy as np
import time
from alive_progress import alive_bar

def cube_gen(side, spacing):
    """Generate a numpy array of points occupying a cube of a given side length around a center with a given spacing
    Points are generated at the given spacing moving outwards from the center, which is always included.
    If the edges aren't an even multiple of the spacing, the

    args:
        side:    side length in mm
        spacing: spacing of points, in mm
    
    returns:
        points:  2D numpy array of points
                 x0, y0, z0
                 x0, y0, z1
                 ...
                 xN, yN, zN
    """
    
    upper_axis = np.arange(0, side/2+spacing, spacing)
    lower_axis = np.arange(-1*spacing, -1*(side/2+spacing), -1*spacing)[::-1]
    axis = np.concatenate((upper_axis,lower_axis))

    X, Y, Z = np.meshgrid(axis, axis, axis, indexing='ij')
    X = X.flatten()
    Y = Y.flatten()
    Z = Z.flatten()

    points = np.stack((X, Y, Z)).T
    points = points[np.lexsort((points[:,0],points[:,1],points[:,2]))]
    return points

def sphere_gen(diameter, spacing):
    """Generate a list of points occupying a sphere of a given diameter

    args:
        diameter: sphere diameter in mm
        spacing:  spacing of points, in mm
    
    returns:
        points:  2D numpy array of points
                 x0, y0, z0
                 x0, y0, z1
                 ...
                 xN, yN, zN
    """

    cube = cube_gen(diameter, spacing)
    distance = np.sqrt((cube[:,0])**2 + (cube[:,1])**2 + (cube[:,2])**2)
    index = distance <= diameter/2
    sphere = cube[index,:]
    return sphere

def cylinder_gen(diameter, spacing):
    """Generate a list of points occupying a right cylinder (d=h) of a given diameter/height

    args:
        diameter: cylinder diameter in mm
        spacing:  spacing of points, in mm
    
    returns:
        points:  2D numpy array of points
                 x0, y0, z0
                 x0, y0, z1
                 ...
                 xN, yN, zN
    """

    cube = cube_gen(diameter, spacing)
    distance = np.sqrt((cube[:,0])**2 + (cube[:,1])**2)
    index = distance <= diameter/2
    cylinder = cube[index,:]
    return cylinder

def circle_gen(diameter, spacing):
    """Generate a list of points occupying a circle in the YZ plane of the printer of a given diameter

    args:
        diameter: circle diameter in mm
        spacing:  spacing of points, in mm
    
    returns:
        points:  2D numpy array of points
                 x0, y0, z0
                 x0, y0, z1
                 ...
                 xN, yN, zN
    """

    upper_axis = np.arange(0, diameter/2+spacing, spacing)
    lower_axis = np.arange(-1*spacing, -1*(diameter/2+spacing), -1*spacing)[::-1]
    axis = np.concatenate((upper_axis,lower_axis))

    Y, Z = np.meshgrid(axis, axis, indexing='ij')
    Y = Y.flatten()
    Z = Z.flatten()
    X = (np.zeros_like(Y)).flatten()

    rect = np.stack((X, Y, Z)).T
    rect = rect[np.lexsort((rect[:,0],rect[:,1],rect[:,2]))]

    distance = np.sqrt((rect[:,0])**2 + (rect[:,1])**2 + (rect[:,2])**2)
    index = distance <= diameter/2
    circle = rect[index,:]

    return circle

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Map the B0 of a magnet with a 3D printer and Hall probe.')
    parser.add_argument('probe_port', action='store', help='Port for Hall probe communication (e.g., COM1)')
    parser.add_argument('printer_port', action='store', help='Port for 3D printer communication (e.g., COM5)')
    parser.add_argument('shape', type=str, action='store', choices=['cube', 'cylinder', 'sphere', 'circle'], help='Shape of sampling pattern', default='sphere')
    parser.add_argument('-d', '--diameter', action='store', default=100, help='Diameter of measurement volume (and length of cylinder if applicable) in mm')
    parser.add_argument('-x', '--set_center_pos', action='store_true', help='Use current position as center of measurement volume')
    parser.add_argument('-c', '--center', action='store', nargs=3, default=[110,110,250], type=float)
    parser.add_argument('-s', '--save_name', action='store', required=True)
    parser.add_argument('-p', '--spacing', action='store', default=5, type=float, help='Measurement point spacing in mm')
    parser.add_argument('-r', '--restart', action='store', default=0, type=int, help='Point to start at if restarting')
    parser.add_argument('-m', '--remeasure_interval', action='store', default=10, type=int, help='Maximum number of points to measure before re-measuring center')

    args = parser.parse_args()
    port_lakeshore = args.probe_port
    port_printer = args.printer_port
    shape = args.shape
    diameter = args.diameter
    set_center_pos = args.set_center_pos
    center = args.center
    save_name = args.save_name
    spacing = args.spacing
    start = args.restart
    remeasure_interval = args.remeasure_interval

    probe = lakeshore.LakeshoreF71(port_lakeshore)

    printer = print3d.Printer(port_printer)


    if start != 0:
        print(f'Starting at point {start}')

    home = input("Home printer?[y/n]")
    if home.lower() == 'y':
        print('Homing Printer, please wait.')
        printer.home()
        printer.wait()
    
    if set_center_pos:
        input("Move field probe to magnet center and press Enter.")
        center = printer.get_pos()

    print(f'Generating a {shape} of diameter {diameter} mm centered about ({center[0]},{center[1]},{center[2]})')
    print(f'Points are spaced every {spacing} mm')

    # Define affine transformation to move from magnet to printer coordinate system
    printer.affine =  np.array([[0,  0, -1, center[0]],
                                [0, -1,  0, center[1]],
                                [1,  0,  0, center[2]],
                                [0,  0,  0,  0]])
                
    if shape == 'cube':
        points = cube_gen(diameter, spacing)
    elif shape == 'cylinder':
        points = cylinder_gen(diameter, spacing)
    elif shape == 'sphere':
        points = sphere_gen(diameter, spacing)
    elif shape == 'circle':
        points = circle_gen(diameter, spacing)


    n_points = points.shape[0]
    with open(save_name, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, dialect='excel')
        if probe.axes == 1:
            csvwriter.writerow(['X', 'Y', 'Z', 'Bz', 'T'])
        else:
            csvwriter.writerow(['X', 'Y', 'Z', 'Mag', 'Bx', 'By', 'Bz', 'T'])
        
        with alive_bar(n_points, dual_line=True) as bar:
            def measure(point):
                printer.move_mag(point)
                time.sleep(0.5)
                field = probe.get_field()
                temp = probe.get_temp()
                if probe.axes == 1:    
                    bar.text(f'{point}: {field}')
                    csvwriter.writerow([*point, field, temp])
                else:
                    bar.text(f'{point}: Mag:{field[0]}, X:{field[1]}, Y:{field[2]}, Z:{field[3]}')
                    csvwriter.writerow([*point, *field, temp])


            bar.title('B0 Mapping in Progress')
            if start !=0:
                bar(start, skipped=True)

            # measure center to start
            measure([0,0,0])

            for i in range(start, n_points):
                # Re-measure center to track B0 drift
                if i % remeasure_interval == 0:
                    measure([0,0,0])
                
                point = points[i,:]
                measure(point)
                bar()
            # Re-measure center to end
            measure([0,0,0])
    printer.beep() # Let everyone know you're done!
