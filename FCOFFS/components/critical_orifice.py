'''
Description
'''

from numpy import sqrt, pi
import warnings

from ..pressureSystem.PressureSystem import PressureSystem
from ..state.State import *
from ..components.componentClass import ComponentClass
from ..fluids.Fluid import Fluid
from ..utilities.units import *


class CriticalOrifice(ComponentClass):

    FLUID_CDS = {"N2O":1, "CO2": 1, "C2H6O": 1}

    def __init__(self, parent_system: PressureSystem, diameter_in: UnitValue,  diameter_out: UnitValue, orifice_diameter: UnitValue, fluid: str, name: str='critical_orifice', Cd: float|None = None):
        if fluid not in ['N2O','CO2']:
            raise Exception("Fluid type not supported")
        super().__init__(parent_system, diameter_in, fluid, name)
        self.orifice_diameter = orifice_diameter.convert_base_metric()
        self.diameter_out = diameter_out.convert_base_metric()
        self.diameter_in = diameter_in.convert_base_metric()
        if Cd is None:
            self.Cd = self.FLUID_CDS[fluid]
        else:
            self.Cd = Cd
        self.decoupler = True 

    def initialize(self):
            if self.parent_system.outlet_BC != 'PRESSURE':
                warnings.warn("Outlet BC not well posed. ")
            self.interface_in.initialize(parent_system=self.parent_system, area=pi*self.diameter_in**2/4, fluid=self.fluid)
            self.interface_out.initialize(parent_system=self.parent_system, area=pi*self.orifice_diameter**2/4, fluid=self.fluid, rho=self.interface_in.state.rho, u=self.interface_in.state.u, p=self.interface_in.state.p)
            # we will assume that component adjacent to orifice has inlet diameter matching orifice diameter (up to user variability)

    def update(self):
        self.interface_in.update()
        self.interface_out.update()

    def eval(self, new_states: tuple[State, State]|None=None) -> list:
        if new_states is None:
            state_in = self.interface_in.state
            state_out = self.interface_out.state
        else:
            state_in = new_states[0]
            state_out = new_states[1]
            
        c_s = Fluid.local_speed_sound(self.fluid, state_out.T, state_out.rho)
        Mach_initial = state_in.u / c_s
        Mach_final = state_out.u / c_s   
              
        Cp = Fluid.Cp(self.fluid, state_out.T , state_out.p)
        Cv = Fluid.Cv(self.fluid, state_out.T , state_out.p)
        gamma = Cp / Cv
        
        R_gas = Fluid.get_gas_constant(self.fluid)
                
        #from mass continuity 
        res1 = (state_out.mdot - state_in.rho*self.diameter_in*state_in.u) / state_out.mdot
        
        #from isentropic nozzle flow equations
        res2 = ((state_in.p/state_out.p) - (1 + ((gamma-1)/2) * (Mach_final**2 - Mach_initial**2))**(gamma/(gamma-1))) /( 0.5 * ((state_in.p/state_out.p) - (1 + ((gamma-1)/2) * (Mach_final**2 - Mach_initial**2))**(gamma/(gamma-1))))
        
        #output mass flux calculations that follow from isentropic nozzle flow 
        res3 = (state_out.mdot - state_in.p * Mach_final * pi * self.diameter_out**2/4 * sqrt(gamma/(state_in.T*R_gas)) * (1 + ((gamma-1)/2) * (Mach_final**2 - Mach_initial**2) )**( (gamma+1) / (2*(1-gamma)) ) ) / state_out.mdot
        
        # verify what the optimal two state variable are to input for CoolProps equation of state calculations-->temperature and density
        return [res1, res2, res3]

        

