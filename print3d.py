import serial
from typing import Union
import numpy as np

numeric = Union[int, float]

class Printer:
    """Defines an interface to a 3D printer over serial"""
    def __init__(self, port, baudrate = 115200):
        self.ser = serial.Serial(port=port, baudrate=baudrate)
        self.set_absolute()
        self.write('M18 S0\n') # Disable motor timeout

        self.affine = np.array([[0,  0, -1,  0],
                                [0, -1,  0,  0],
                                [1,  0,  0,  0],
                                [0,  0,  0,  1]])
    
    def write(self, command: str):
        """Write a string encoded properly for the printer"""
        return self.ser.write(command.encode())
    
    def read(self):
        """Read a string response from the printer"""
        return self.ser.readline().decode()

    def home(self):
        """Auto-home all three axes"""
        self.write('G28\n')

    def set_relative(self):
        """Put in relative coordinate mode (default)"""
        self.write('G91\n')
    
    def set_absolute(self):
        """Put in absolute coordinate mode"""
        self.write('G90\n')
    
    def move(self, position: tuple[numeric, numeric, numeric]):
        """Move to/by specified position/ammount in printer coordinate system
        If in relative mode, move by specified ammount
        If in absolute mode, move to specified position
        Args:
            position (tuple[numeric, numeric, numeric]):
        """
        self.write(f'G0 X{position[0]} Y{position[1]} Z{position[2]}\n')
    
    def wait(self):
        """Wait for previous command to complete and return once it has."""
        self.write('M400\nM118 Finished\n')
        finished = False
        while not finished:
            read = self.read()
            # read = self.ser.readline().decode()
            # print(read)
            if read[:8] == 'Finished':
                finished = True

    def move_wait(self, position: tuple[numeric, numeric, numeric]):
        """Move to/by specified position/ammount in printer coordinate system and wait until move is complete before returning
        If in relative mode, move by specified ammount
        If in absolute mode, move to specified position

        Args:
            position (tuple[numeric, numeric, numeric]):
        """
        self.ser.reset_input_buffer()
        self.write(f'G0 X{position[0]} Y{position[1]} Z{position[2]}\n')
        self.wait()
    
    def move_mag(self, position: tuple[numeric, numeric, numeric]):
        """Move to specified position in magnet coordinate system and wait until move is complete before returning

        Args:
            position (tuple[numeric, numeric, numeric]):
        """
        pos_magnet = np.append(position,1)
        pos_printer = (self.affine @ pos_magnet)[0:3]
        self.move_wait(pos_printer)

    def get_pos(self):
        """Get current position of printer"""
        self.ser.reset_input_buffer()
        self.write('M114\n')
        read = self.read()
        i_x = read.index('X:')
        i_y = read.index('Y:')
        i_z = read.index('Z:')
        i_end = read.index('E:')
        X = float(read[i_x+2:i_y])
        Y = float(read[i_y+2:i_z])
        Z = float(read[i_z+2:i_end])
        return (X, Y, Z)

    def beep(self, t_ms:int = 100):
        """Beep!"""
        self.write(f'M300 P{t_ms}\n')