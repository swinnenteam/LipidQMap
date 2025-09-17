from dataclasses import dataclass


@dataclass
class SprayRun:
    x_left: float  # mm
    x_right: float  # mm
    y_bottom: float  # mm
    y_top: float  # mm
    margin: float  # mm
    total_used_volume_mL: float  # mL
    syringe_flow_mL_per_min: float  # mL/min
    drying_time_min: float  # min
    drying_cycles: int  # unitless
    initial_equilibration_min: float  # min
    stock_conc_mg_per_mL: float  # mg/mL
    working_dilution_factor: float  # unitless
    volume_working_stock_uL: float  # uL
    final_mix_volume_mL: float  # mL
    molecular_weight_ug_per_umol: float  # µg/µmol

    @property
    def area_mm2(self) -> float:
        return float(
            ((self.x_right + self.margin) - (self.x_left - self.margin))
            * ((self.y_top + self.margin) - (self.y_bottom - self.margin))
        )

    @property
    def delivered_volume_mL(self) -> float:
        """
        One typical calc: volume sprayed during drying cycles + any initial equilibration.
        """
        return (
            self.total_used_volume_mL
            - (self.syringe_flow_mL_per_min * self.drying_time_min * self.drying_cycles)
            - (self.syringe_flow_mL_per_min * self.initial_equilibration_min)
        )

    @property
    def spray_mix_conc(self) -> float:
        return (
            (self.stock_conc_mg_per_mL / self.working_dilution_factor)
            * (self.volume_working_stock_uL / self.molecular_weight_ug_per_umol)
            / self.final_mix_volume_mL
            * 1e6
        )

    @property
    def pmol_per_mm2(self) -> float:
        """Convert stock concentration to pmol/mL"""
        return self.spray_mix_conc * (self.delivered_volume_mL / self.area_mm2)
