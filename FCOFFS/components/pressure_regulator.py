
from FCOFFS.pressureSystem.PressureSystem import PressureSystem
from FCOFFS.state.State import State
from FCOFFS.utilities.units import UnitValue
from FCOFFS.utilities.component_curve import ComponentCurve
from FCOFFS.components.componentClass import ComponentClass
from FCOFFS.fluids.Fluid import Fluid

class PressureRegulator(ComponentClass):
    def __init__(self, parent_system: PressureSystem, diameter: UnitValue, fluid: str, flow_curve_filename: str, set_pressure: UnitValue, method: str = 'linear', name: str = "Pressure_Regulator"):
        super().__init__(parent_system, diameter, fluid, name)

        self.set_pressure = set_pressure.convert_base_metric()
        self.flow_curve = ComponentCurve(flow_curve_filename, False, method)

    def eval(self, new_states: tuple[State, State] | None = None) -> list:
        if new_states is None:
            state_in = self.interface_in.state
            state_out = self.interface_out.state
        else:
            state_in = new_states[0]
            state_out = new_states[1]

        curve_res = self.flow_curve([self.set_pressure, state_in.p, state_in.u * state_in.area])
        res1 = (curve_res - state_out.p) / state_out.p 
        # (curve(p, p, Q) - state_out.p) / state_out.p
        
        res2 = (state_out.mdot - state_in.mdot) / state_in.mdot

        # get cp at inlet and outlet state
        cp_in = Fluid.Cp(self.fluid, state_in.T, state_in.p)
        cp_out = Fluid.Cp(self.fluid, state_out.T, state_out.p)
        
        # initialize specific energies, and use average of them to normalize the second residual # double check energy for temperature 
        e1 = cp_in * state_in.T + 1/2 * state_in.u**2
        e2 = cp_out * state_out.T + 1/2 * state_out.u**2

        res3 =  (e2 - e1) / ( 0.5 * (e1 + e2))
        # ((Cp_out*T_out - Cp_in*T_in) + 1/2(v_out^2 - v_in^2)) / Average energy
        
        return [res1, res2, res3]
