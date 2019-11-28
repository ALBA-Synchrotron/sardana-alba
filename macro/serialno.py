from sardana.macroserver.macro import *
from sardana.macroserver.scan import *

class set_serialno(Macro):
    
    param_def = [
       ['serialno', Type.Integer, 0, 'new scan serial number']
    ]

    def run(self, serialno):
        ScanFactory().serialno = serialno
        self.info("Scan serial number set to %d." % ScanFactory().serialno)
        self.info("Next scan will have serial number %d" % (ScanFactory().serialno+1))

class get_serialno(Macro):
    
    def run(self):
        serialno = ScanFactory().serialno 
        self.info("Scan serial number set to %d." % serialno)
        self.info("Next scan will have serial number %d" % (serialno+1))
