import pyvisa

class LakeshoreF71():
    """Defines an interface to the Lakeshore Teslameter"""
    def __init__(self,port):
        self.port = port
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource(self.port, timeout=10000, baud_rate=115200)
        print('Tesla Meter Name:',self.inst.query('*IDN?'))
        self.axes = int(self.inst.query('Probe:Axes?'))
        print(f'Operating in {self.axes}-axis mode')

    def get_field(self):
        """Get field from probe"""
        if self.axes == 1:
            field = float(self.inst.query(f'Fetch:DC? X'))
        else:
            resp = self.inst.query(f'FETCh:DC? ALL')
            field = [float(a) for a in resp.split(',')] # Magnitude, X, Y, Z
        return field
    
    def get_field_3axis(self):
        """Get field from three-axis probe"""
        resp = self.inst.query(f'FETCh:DC? ALL')
        fields = [float(a) for a in resp.split(',')] # Magnitude, X, Y, Z
        return fields
    
    def get_temp(self):
        """Get temperature from field probe"""
        resp = self.inst.query(f'FETCh:TEMPerature?')
        return(float(resp))