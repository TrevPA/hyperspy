# Copyright 2007-2011 The Hyperspy developers
#
# This file is part of  Hyperspy.
#
#  Hyperspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  Hyperspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  Hyperspy.  If not, see <http://www.gnu.org/licenses/>.


import numpy as np
from nose.tools import assert_true, assert_equal, assert_not_equal

from hyperspy.signals import EDSSEMSpectrum
from hyperspy.defaults_parser import preferences
from hyperspy.components import Gaussian
from hyperspy import utils


class Test_mapped_parameters:

    def setUp(self):
        # Create an empty spectrum
        s = EDSSEMSpectrum(np.ones((4, 2, 1024)))
        s.axes_manager.signal_axes[0].scale = 1e-3
        s.axes_manager.signal_axes[0].units = "keV"
        s.axes_manager.signal_axes[0].name = "Energy"
        s.mapped_parameters.SEM.EDS.live_time = 3.1
        s.mapped_parameters.SEM.beam_energy = 15.0
        s.mapped_parameters.SEM.tilt_stage = -38
        s.mapped_parameters.SEM.EDS.azimuth_angle = 63
        s.mapped_parameters.SEM.EDS.elevation_angle = 35
        self.signal = s

    def test_sum_live_time(self):
        s = self.signal
        sSum = s.sum(0)
        assert_equal(sSum.mapped_parameters.SEM.EDS.live_time, 3.1 * 2)

    def test_rebin_live_time(self):
        s = self.signal
        dim = s.axes_manager.shape
        s = s.rebin([dim[0] / 2, dim[1] / 2, dim[2]])
        assert_equal(s.mapped_parameters.SEM.EDS.live_time, 3.1 * 2 * 2)

    def test_add_elements(self):
        s = self.signal
        s.add_elements(['Al', 'Ni'])
        assert_equal(s.mapped_parameters.Sample.elements, ['Al', 'Ni'])
        s.add_elements(['Al', 'Ni'])
        assert_equal(s.mapped_parameters.Sample.elements, ['Al', 'Ni'])
        s.add_elements(["Fe", ])
        assert_equal(s.mapped_parameters.Sample.elements, ['Al', "Fe", 'Ni'])
        s.set_elements(['Al', 'Ni'])
        assert_equal(s.mapped_parameters.Sample.elements, ['Al', 'Ni'])

    def test_add_lines(self):
        s = self.signal
        s.add_lines(lines=())
        assert_equal(s.mapped_parameters.Sample.Xray_lines, [])
        s.add_lines(("Fe_Ln",))
        assert_equal(s.mapped_parameters.Sample.Xray_lines, ["Fe_Ln"])
        s.add_lines(("Fe_Ln",))
        assert_equal(s.mapped_parameters.Sample.Xray_lines, ["Fe_Ln"])
        s.add_elements(["Ti", ])
        s.add_lines(())
        assert_equal(s.mapped_parameters.Sample.Xray_lines, ['Fe_Ln', 'Ti_La'])
        s.set_lines((), only_one=False, only_lines=False)
        assert_equal(s.mapped_parameters.Sample.Xray_lines,
                     ['Fe_La', 'Fe_Lb3', 'Fe_Ll', 'Fe_Ln', 'Ti_La',
                      'Ti_Lb3', 'Ti_Ll', 'Ti_Ln'])
        s.mapped_parameters.SEM.beam_energy = 0.4
        s.set_lines((), only_one=False, only_lines=False)
        assert_equal(s.mapped_parameters.Sample.Xray_lines, ['Ti_Ll'])
#        s.add_lines()
#        results.append(mp.Sample.Xray_lines[1])
#        mp.SEM.beam_energy = 10.0
#        s.set_elements(['Al','Ni'])
#        results.append(mp.Sample.Xray_lines[1])
#        s.add_elements(['Fe'])
#        results.append(mp.Sample.Xray_lines[1])
#        assert_equal(results, ['Al_Ka','Ni','Ni_Ka','Ni_La','Fe_La'])

    def test_default_param(self):
        s = self.signal
        mp = s.mapped_parameters
        assert_equal(mp.SEM.EDS.energy_resolution_MnKa,
                     preferences.EDS.eds_mn_ka)

    def test_SEM_to_TEM(self):
        s = self.signal[0, 0]
        signal_type = 'EDS_TEM'
        mp = s.mapped_parameters
        mp.SEM.EDS.energy_resolution_MnKa = 125.3
        sTEM = s.deepcopy()
        sTEM.set_signal_type(signal_type)
        mpTEM = sTEM.mapped_parameters
        results = [mp.SEM.EDS.energy_resolution_MnKa]
        results.append(signal_type)
        resultsTEM = [mpTEM.TEM.EDS.energy_resolution_MnKa]
        resultsTEM.append(mpTEM.signal_type)
        assert_equal(results, resultsTEM)

    def test_get_calibration_from(self):
        s = self.signal
        scalib = EDSSEMSpectrum(np.ones((1024)))
        energy_axis = scalib.axes_manager.signal_axes[0]
        energy_axis.scale = 0.01
        energy_axis.offset = -0.10
        s.get_calibration_from(scalib)
        assert_equal(s.axes_manager.signal_axes[0].scale,
                     energy_axis.scale)

    def test_take_off_angle(self):
        s = self.signal
        assert_equal(s.get_take_off_angle(), 12.886929785732487)


class Test_get_lines_intentisity:

    def setUp(self):
        # Create an empty spectrum
        s = EDSSEMSpectrum(np.zeros((2, 2, 3, 100)))
        energy_axis = s.axes_manager.signal_axes[0]
        energy_axis.scale = 0.04
        energy_axis.units = 'keV'
        energy_axis.name = "Energy"
        g = Gaussian()
        g.sigma.value = 0.05
        g.centre.value = 1.487
        s.data[:] = g.function(energy_axis.axis)
        s.mapped_parameters.SEM.EDS.live_time = 3.1
        s.mapped_parameters.SEM.beam_energy = 15.0
        self.signal = s

    def test(self):
        s = self.signal
        sAl = s.get_lines_intensity(["Al_Ka"],
                                    plot_result=False,
                                    integration_window_factor=5)[0]
        assert_true(np.allclose(1, sAl.data[0, 0, 0], atol=1e-3))
        sAl = s[0].get_lines_intensity(["Al_Ka"],
                                       plot_result=False,
                                       integration_window_factor=5)[0]
        assert_true(np.allclose(1, sAl.data[0, 0], atol=1e-3))
        sAl = s[0, 0].get_lines_intensity(["Al_Ka"],
                                          plot_result=False,
                                          integration_window_factor=5)[0]
        assert_true(np.allclose(1, sAl.data[0], atol=1e-3))
        sAl = s[0, 0, 0].get_lines_intensity(["Al_Ka"],
                                             plot_result=False,
                                             integration_window_factor=5)[0]
        assert_true(np.allclose(1, sAl.data, atol=1e-3))


class Test_tools_bulk:

    def setUp(self):
        s = EDSSEMSpectrum(np.ones(1024))
        s.mapped_parameters.SEM.beam_energy = 5.0
        s.set_elements(['Al', 'Zn'])
        s.add_lines()
        self.signal = s

    def test_electron_range(self):
        s = self.signal
        mp = s.mapped_parameters
        elec_range = utils.eds.electron_range(
            mp.Sample.elements[0],
            mp.SEM.beam_energy,
            density='auto',
            tilt=mp.SEM.tilt_stage)
        assert_equal(elec_range, 0.41350651162374225)

    def test_xray_range(self):
        s = self.signal
        mp = s.mapped_parameters
        xr_range = utils.eds.xray_range(
            mp.Sample.Xray_lines[0],
            mp.SEM.beam_energy,
            density=4.37499648818)
        assert_equal(xr_range, 0.19002078834050035)
