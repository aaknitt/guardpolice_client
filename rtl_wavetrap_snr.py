#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: WAVETRAP SNR-BASED RF RECORDER
# Author: Andy Knitt
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from datetime import datetime
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy
import os
import sip
import time
import threading
import subprocess

'''
Built on GNUradio 3.10
TO DO
- *Stop and start capture based on SNR trigger and release time
  - *New file for each capture
- *Automatically call script to created demodulated audio wav file after capture
- Run on Pi
- SNR Threshold and release times configurable
- Add center frequency, sample rate, trigger frequency to file name
- Ungate 1 PPS pulse prior to release time
- Filename renamed to time of 1 PPS pulse
- Improve squelch
  - debounce before opening?
  - something that adjusts more to recent noise floor rather than using all-time low value
- Cleanup to remove unused blocks from old SNR method (Probe1)


- Multichannel RX capability


'''


class rtl_wavetrap(gr.top_block, Qt.QWidget):

	def __init__(self):
		gr.top_block.__init__(self, "WAVETRAP SNR RF RECORDER", catch_exceptions=True)
		Qt.QWidget.__init__(self)
		self.setWindowTitle("WAVETRAP SNR RF RECORDER")
		qtgui.util.check_set_qss()
		try:
			self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
		except BaseException as exc:
			print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
		self.top_scroll_layout = Qt.QVBoxLayout()
		self.setLayout(self.top_scroll_layout)
		self.top_scroll = Qt.QScrollArea()
		self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
		self.top_scroll_layout.addWidget(self.top_scroll)
		self.top_scroll.setWidgetResizable(True)
		self.top_widget = Qt.QWidget()
		self.top_scroll.setWidget(self.top_widget)
		self.top_layout = Qt.QVBoxLayout(self.top_widget)
		self.top_grid_layout = Qt.QGridLayout()
		self.top_layout.addLayout(self.top_grid_layout)

		self.settings = Qt.QSettings("GNU Radio", "rtl_wavetrap")

		try:
			geometry = self.settings.value("geometry")
			if geometry:
				self.restoreGeometry(geometry)
		except BaseException as exc:
			print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

		##################################################
		# Variables
		##################################################
		self.gui_samp_rate = gui_samp_rate = 2400000.0
		self.gui_gain = gui_gain = 10.0
		#self.center_freq = freq = 162e6
		self.center_freq = center_freq = 126.475e6
		self.variable_low_pass_filter_taps_0 = variable_low_pass_filter_taps_0 = firdes.low_pass(1.0, gui_samp_rate, 10000,30000, window.WIN_HAMMING, 6.76)
		self.timestamp = timestamp = datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H:%M:%S')
		self.str_center_freq = str_center_freq = str(center_freq)
		self.rootdir = rootdir = str(os.path.expanduser("~")+"\\")
		self.record_file_path = record_file_path = "data\\"
		self.filename = filename = 'recordings/' + str(int(time.time()))+'.wav'
		self.Probe1 = Probe1 = -100
		self.Probe2 = Probe2 = -100
		self.wav_file_name = wav_file_name = 'test1.wav'
		self.last_record_time = last_record_time = 0
		self.recording = recording = False
		self.min_sig_dB = 100

		##################################################
		# Blocks
		##################################################

		self.tabs = Qt.QTabWidget()
		self.tabs_widget_0 = Qt.QWidget()
		self.tabs_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tabs_widget_0)
		self.tabs_grid_layout_0 = Qt.QGridLayout()
		self.tabs_layout_0.addLayout(self.tabs_grid_layout_0)
		self.tabs.addTab(self.tabs_widget_0, 'Tab 0')
		self.top_grid_layout.addWidget(self.tabs, 0, 0, 7, 4)
		for r in range(0, 7):
			self.top_grid_layout.setRowStretch(r, 1)
		for c in range(0, 4):
			self.top_grid_layout.setColumnStretch(c, 1)
		# Create the options list
		self._gui_samp_rate_options = [1024000.0, 1536000.0, 1792000.0, 1920000.0, 2048000.0, 2160000.0, 2400000.0, 2560000.0, 2880000.0, 3200000.0, 5000000.0, 10000000.0, 15000000.0, 20000000.0, 25000000.0, 30000000.0, 35000000.0, 40000000.0, 45000000.0, 50000000.0, 55000000.0]
		# Create the labels list
		self._gui_samp_rate_labels = ['1.02MHz', '1.54MHz', '1.79MHz', '1.92MHz', '2.05MHz', '2.16MHz', '2.4MHz','2.56MHz', '2.88MHz', '3.2MHz', '5.0MHz', '10.0MHz', '15.0MHz', '20MHz', '25.0MHz', '30.0MHz', '35.0MHz', '40.0MHz', '45.0MHz', '50.0MHz', '55.0MHz']
		# Create the combo box
		self._gui_samp_rate_tool_bar = Qt.QToolBar(self)
		self._gui_samp_rate_tool_bar.addWidget(Qt.QLabel("SAMPLE RATE" + ": "))
		self._gui_samp_rate_combo_box = Qt.QComboBox()
		self._gui_samp_rate_tool_bar.addWidget(self._gui_samp_rate_combo_box)
		for _label in self._gui_samp_rate_labels: self._gui_samp_rate_combo_box.addItem(_label)
		self._gui_samp_rate_callback = lambda i: Qt.QMetaObject.invokeMethod(self._gui_samp_rate_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._gui_samp_rate_options.index(i)))
		self._gui_samp_rate_callback(self.gui_samp_rate)
		self._gui_samp_rate_combo_box.currentIndexChanged.connect(
			lambda i: self.set_gui_samp_rate(self._gui_samp_rate_options[i]))
		# Create the radio buttons
		self.tabs_grid_layout_0.addWidget(self._gui_samp_rate_tool_bar, 0, 1, 1, 1)
		for r in range(0, 1):
			self.tabs_grid_layout_0.setRowStretch(r, 1)
		for c in range(1, 2):
			self.tabs_grid_layout_0.setColumnStretch(c, 1)
		self._gui_gain_range = qtgui.Range(0, 49.6, 1, 10.0, 200)
		self._gui_gain_win = qtgui.RangeWidget(self._gui_gain_range, self.set_gui_gain, "RX Gain", "counter_slider", float, QtCore.Qt.Horizontal)
		self.tabs_grid_layout_0.addWidget(self._gui_gain_win, 0, 0, 1, 1)
		for r in range(0, 1):
			self.tabs_grid_layout_0.setRowStretch(r, 1)
		for c in range(0, 1):
			self.tabs_grid_layout_0.setColumnStretch(c, 1)
		self.SNR_dB = blocks.probe_signal_f()
		self.sig_dB = blocks.probe_signal_f()
		self.soapy_rtlsdr_source_0 = None
		dev = 'driver=rtlsdr'
		stream_args = 'bufflen=16384'
		tune_args = ['']
		settings = ['']

		def _set_soapy_rtlsdr_source_0_gain_mode(channel, agc):
			self.soapy_rtlsdr_source_0.set_gain_mode(channel, agc)
			if not agc:
				  self.soapy_rtlsdr_source_0.set_gain(channel, self._soapy_rtlsdr_source_0_gain_value)
		self.set_soapy_rtlsdr_source_0_gain_mode = _set_soapy_rtlsdr_source_0_gain_mode

		def _set_soapy_rtlsdr_source_0_gain(channel, name, gain):
			self._soapy_rtlsdr_source_0_gain_value = gain
			if not self.soapy_rtlsdr_source_0.get_gain_mode(channel):
				self.soapy_rtlsdr_source_0.set_gain(channel, gain)
		self.set_soapy_rtlsdr_source_0_gain = _set_soapy_rtlsdr_source_0_gain

		def _set_soapy_rtlsdr_source_0_bias(bias):
			if 'biastee' in self._soapy_rtlsdr_source_0_setting_keys:
				self.soapy_rtlsdr_source_0.write_setting('biastee', bias)
		self.set_soapy_rtlsdr_source_0_bias = _set_soapy_rtlsdr_source_0_bias

		self.soapy_rtlsdr_source_0 = soapy.source(dev, "fc32", 1, 'biastee=True',
								  stream_args, tune_args, settings)

		self._soapy_rtlsdr_source_0_setting_keys = [a.key for a in self.soapy_rtlsdr_source_0.get_setting_info()]

		self.soapy_rtlsdr_source_0.set_sample_rate(0, gui_samp_rate)
		self.soapy_rtlsdr_source_0.set_frequency(0, center_freq)
		self.soapy_rtlsdr_source_0.set_frequency_correction(0, 0)
		self.set_soapy_rtlsdr_source_0_bias(bool(False))
		self._soapy_rtlsdr_source_0_gain_value = gui_gain
		self.set_soapy_rtlsdr_source_0_gain_mode(0, bool(False))
		self.set_soapy_rtlsdr_source_0_gain(0, 'TUNER', gui_gain)
		self.qtgui_number_sink_0_0_0_0 = qtgui.number_sink(
			gr.sizeof_float,
			0,
			qtgui.NUM_GRAPH_HORIZ,
			1,
			None # parent
		)
		self.qtgui_number_sink_0_0_0_0.set_update_time(0.10)
		self.qtgui_number_sink_0_0_0_0.set_title("SNR")

		labels = ['', '', '', '', '',
			'', '', '', '', '']
		units = ['', '', '', '', '',
			'', '', '', '', '']
		colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
			("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
		factor = [1, 1, 1, 1, 1,
			1, 1, 1, 1, 1]

		for i in range(1):
			self.qtgui_number_sink_0_0_0_0.set_min(i, 0)
			self.qtgui_number_sink_0_0_0_0.set_max(i, 100)
			self.qtgui_number_sink_0_0_0_0.set_color(i, colors[i][0], colors[i][1])
			if len(labels[i]) == 0:
				self.qtgui_number_sink_0_0_0_0.set_label(i, "Data {0}".format(i))
			else:
				self.qtgui_number_sink_0_0_0_0.set_label(i, labels[i])
			self.qtgui_number_sink_0_0_0_0.set_unit(i, units[i])
			self.qtgui_number_sink_0_0_0_0.set_factor(i, factor[i])

		self.qtgui_number_sink_0_0_0_0.enable_autoscale(False)
		self._qtgui_number_sink_0_0_0_0_win = sip.wrapinstance(self.qtgui_number_sink_0_0_0_0.qwidget(), Qt.QWidget)
		self.top_layout.addWidget(self._qtgui_number_sink_0_0_0_0_win)
		self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
			8192, #size
			window.WIN_BLACKMAN_hARRIS, #wintype
			center_freq, #fc
			gui_samp_rate, #bw
			"", #name
			1,
			None # parent
		)
		self.qtgui_freq_sink_x_0.set_update_time(0.05)
		self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
		self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
		self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
		self.qtgui_freq_sink_x_0.enable_autoscale(False)
		self.qtgui_freq_sink_x_0.enable_grid(False)
		self.qtgui_freq_sink_x_0.set_fft_average(1.0)
		self.qtgui_freq_sink_x_0.enable_axis_labels(True)
		self.qtgui_freq_sink_x_0.enable_control_panel(False)
		self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



		labels = ['', '', '', '', '',
			'', '', '', '', '']
		widths = [1, 1, 1, 1, 1,
			1, 1, 1, 1, 1]
		colors = ["blue", "red", "green", "black", "cyan",
			"magenta", "yellow", "dark red", "dark green", "dark blue"]
		alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
			1.0, 1.0, 1.0, 1.0, 1.0]

		for i in range(1):
			if len(labels[i]) == 0:
				self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
			else:
				self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
			self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
			self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
			self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

		self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
		self.tabs_grid_layout_0.addWidget(self._qtgui_freq_sink_x_0_win, 2, 0, 5, 4)
		for r in range(2, 7):
			self.tabs_grid_layout_0.setRowStretch(r, 1)
		for c in range(0, 4):
			self.tabs_grid_layout_0.setColumnStretch(c, 1)
		self.qtgui_edit_box_msg_0_0 = qtgui.edit_box_msg(qtgui.FLOAT, str(center_freq), 'Freq', True, True, 'freq', None)
		self._qtgui_edit_box_msg_0_0_win = sip.wrapinstance(self.qtgui_edit_box_msg_0_0.qwidget(), Qt.QWidget)
		self.tabs_grid_layout_0.addWidget(self._qtgui_edit_box_msg_0_0_win, 1, 0, 1, 1)
		for r in range(1, 2):
			self.tabs_grid_layout_0.setRowStretch(r, 1)
		for c in range(0, 1):
			self.tabs_grid_layout_0.setColumnStretch(c, 1)
		self.center_freq_xlating_fir_filter_xxx_0_0 = filter.freq_xlating_fir_filter_ccc(1, variable_low_pass_filter_taps_0, 400000, gui_samp_rate)
		self.blocks_wavfile_sink_0 = blocks.wavfile_sink(
			filename,
			2,
			int(gui_samp_rate),
			blocks.FORMAT_WAV,
			blocks.FORMAT_FLOAT,
			False
			)
		self.blocks_sub_xx_0 = blocks.sub_ff(1)
		self.blocks_selector_0 = blocks.selector(gr.sizeof_gr_complex*1,0,0)
		self.blocks_selector_0.set_enabled(False)
		self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)
		self.blocks_nlog10_ff_0_0 = blocks.nlog10_ff(1, 1, 0)
		self.blocks_nlog10_ff_0 = blocks.nlog10_ff(1, 1, 0)
		self.blocks_nlog10_ff_1 = blocks.nlog10_ff(1, 1, 0)
		self.blocks_multiply_const_vxx_0_1_0 = blocks.multiply_const_ff((1/gui_samp_rate))
		self.blocks_multiply_const_vxx_0_1 = blocks.multiply_const_ff((1/10000))
		self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(10)
		self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(10)
		self.blocks_multiply_const_vxx_1 = blocks.multiply_const_ff(10)
		self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_freq)
		self.blocks_moving_average_xx_0_0 = blocks.moving_average_ff(10000, (1/10000), 4000, 1)
		self.blocks_moving_average_xx_1 = blocks.moving_average_ff(10000, (1/10000), 4000, 1)
		self.blocks_complex_to_mag_squared_0_0 = blocks.complex_to_mag_squared(1)
		self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
		self.blocks_complex_to_float_0 = blocks.complex_to_float(1)
		def _Probe1_probe():
			while True:
				val = self.SNR_dB.level()
				try:
					try:
						self.doc.add_next_tick_callback(functools.partial(self.set_Probe1,val))
					except AttributeError:
						self.set_Probe1(val)
				except AttributeError:
					pass
				time.sleep(1.0 / (10))
		_Probe1_thread = threading.Thread(target=_Probe1_probe)
		_Probe1_thread.daemon = True
		_Probe1_thread.start()
		def _Probe2_probe():
			while True:
				val = self.sig_dB.level()
				try:
					try:
						self.doc.add_next_tick_callback(functools.partial(self.set_Probe2,val))
					except AttributeError:
						self.set_Probe2(val)
				except AttributeError:
					pass
				time.sleep(1.0 / (10))
		_Probe2_thread = threading.Thread(target=_Probe2_probe)
		_Probe2_thread.daemon = True
		_Probe2_thread.start()


		##################################################
		# Connections
		##################################################
		self.msg_connect((self.qtgui_edit_box_msg_0_0, 'msg'), (self.blocks_msgpair_to_var_0, 'inpair'))
		self.msg_connect((self.qtgui_edit_box_msg_0_0, 'msg'), (self.qtgui_freq_sink_x_0, 'freq'))
		self.msg_connect((self.qtgui_freq_sink_x_0, 'freq'), (self.qtgui_edit_box_msg_0_0, 'val'))
		self.connect((self.blocks_complex_to_float_0, 0), (self.blocks_wavfile_sink_0, 0))
		self.connect((self.blocks_complex_to_float_0, 1), (self.blocks_wavfile_sink_0, 1))
		self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_multiply_const_vxx_0_1, 0))
		self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_nlog10_ff_1, 0))
		self.connect((self.blocks_nlog10_ff_1, 0), (self.blocks_multiply_const_vxx_1, 0))
		self.connect((self.blocks_multiply_const_vxx_1, 0),(self.blocks_moving_average_xx_1, 0))
		self.connect((self.blocks_moving_average_xx_1, 0), (self.sig_dB, 0))
		self.connect((self.blocks_complex_to_mag_squared_0_0, 0), (self.blocks_multiply_const_vxx_0_1_0, 0))
		self.connect((self.blocks_moving_average_xx_0_0, 0), (self.SNR_dB, 0))
		self.connect((self.blocks_moving_average_xx_0_0, 0), (self.qtgui_number_sink_0_0_0_0, 0))
		self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_sub_xx_0, 0))
		self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_sub_xx_0, 1))
		self.connect((self.blocks_multiply_const_vxx_0_1, 0), (self.blocks_nlog10_ff_0, 0))
		self.connect((self.blocks_multiply_const_vxx_0_1_0, 0), (self.blocks_nlog10_ff_0_0, 0))
		self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_multiply_const_vxx_0, 0))
		self.connect((self.blocks_nlog10_ff_0_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
		self.connect((self.blocks_selector_0, 0), (self.blocks_complex_to_float_0, 0))
		self.connect((self.blocks_selector_0, 1), (self.blocks_null_sink_0, 0))
		#self.blocks_selector_0.set_output_index(1)  #null sink by default
		self.connect((self.blocks_sub_xx_0, 0), (self.blocks_moving_average_xx_0_0, 0))
		self.connect((self.center_freq_xlating_fir_filter_xxx_0_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
		self.connect((self.soapy_rtlsdr_source_0, 0), (self.blocks_complex_to_mag_squared_0_0, 0))
		self.connect((self.soapy_rtlsdr_source_0, 0), (self.blocks_selector_0, 0))
		self.connect((self.soapy_rtlsdr_source_0, 0), (self.center_freq_xlating_fir_filter_xxx_0_0, 0))
		self.connect((self.soapy_rtlsdr_source_0, 0), (self.qtgui_freq_sink_x_0, 0))


	def closeEvent(self, event):
		self.settings = Qt.QSettings("GNU Radio", "rtl_wavetrap")
		self.settings.setValue("geometry", self.saveGeometry())
		self.stop()
		self.wait()

		event.accept()

	def get_gui_samp_rate(self):
		return self.gui_samp_rate

	def set_gui_samp_rate(self, gui_samp_rate):
		self.gui_samp_rate = gui_samp_rate
		self.set_filename(str(int(self.center_freq))+"Hz_"+str(int(self.gui_samp_rate))+"sps_"+str(self.gui_gain)+"dB_")
		self._gui_samp_rate_callback(self.gui_samp_rate)
		self.set_variable_low_pass_filter_taps_0(firdes.low_pass(1.0, self.gui_samp_rate, 10000, 30000, window.WIN_HAMMING, 6.76))
		self.blocks_multiply_const_vxx_0_1_0.set_k((1/self.gui_samp_rate))
		self.qtgui_freq_sink_x_0.set_frequency_range(self.center_freq, self.gui_samp_rate)
		self.soapy_rtlsdr_source_0.set_sample_rate(0, self.gui_samp_rate)

	def get_gui_gain(self):
		return self.gui_gain

	def set_gui_gain(self, gui_gain):
		self.gui_gain = gui_gain
		self.set_filename(str(int(self.center_freq))+"Hz_"+str(int(self.gui_samp_rate))+"sps_"+str(self.gui_gain)+"dB_")
		self.set_soapy_rtlsdr_source_0_gain(0, 'TUNER', self.gui_gain)

	def get_freq(self):
		return self.center_freq

	def set_freq(self, freq):
		self.center_freq = freq
		self.set_filename(str(int(self.center_freq))+"Hz_"+str(int(self.gui_samp_rate))+"sps_"+str(self.gui_gain)+"dB_")
		self.set_str_freq(str(self.center_freq))
		self.qtgui_freq_sink_x_0.set_frequency_range(self.center_freq, self.gui_samp_rate)
		self.soapy_rtlsdr_source_0.set_frequency(0, self.center_freq)

	def get_variable_low_pass_filter_taps_0(self):
		return self.variable_low_pass_filter_taps_0

	def set_variable_low_pass_filter_taps_0(self, variable_low_pass_filter_taps_0):
		self.variable_low_pass_filter_taps_0 = variable_low_pass_filter_taps_0
		self.center_freq_xlating_fir_filter_xxx_0_0.set_taps(self.variable_low_pass_filter_taps_0)

	def get_timestamp(self):
		return self.timestamp

	def set_timestamp(self, timestamp):
		self.timestamp = timestamp

	def get_str_freq(self):
		return self.str_center_freq

	def set_str_freq(self, str_freq):
		self.str_center_freq = str_freq

	def get_rootdir(self):
		return self.rootdir

	def set_rootdir(self, rootdir):
		self.rootdir = rootdir

	def get_record_file_path(self):
		return self.record_file_path

	def set_record_file_path(self, record_file_path):
		self.record_file_path = record_file_path

	def get_filename(self):
		return self.filename

	def set_filename(self, filename):
		self.filename = filename

	def get_Probe1(self):
		return self.Probe1

	def set_Probe1(self, Probe1):
		self.Probe1 = Probe1

	def set_wav_file_name(self, fname):
		self.wav_file_name = fname

	def timer_function(self):
		#print(self.SNR_dB.level())
		if self.sig_dB.level() < self.min_sig_dB:
			self.min_sig_dB = self.sig_dB.level()
		#print("SNR:",round(self.sig_dB.level() - self.min_sig_dB,1)," dB")
		if self.sig_dB.level()>self.min_sig_dB + 10:
			self.last_record_time = time.time()
			if self.recording == False:
				self.recording = True
				self.set_wav_file_name('recordings/'+str(int(time.time()))+'.wav')
				self.blocks_wavfile_sink_0.open(self.wav_file_name)
				self.blocks_selector_0.set_enabled(True)
				#self.blocks_selector_0.set_output_index(0)  #connect to wav file sink
				print("should have started a new file " + self.wav_file_name)
		else:
			if self.recording == True and time.time()-self.last_record_time > 1:  #1 second release time
				self.recording = False
				print("closing file " + self.wav_file_name)
				self.blocks_selector_0.set_enabled(False)
				self.blocks_wavfile_sink_0.close()
				subprocess.Popen(['python', 'demod_am_from_wav.py','--input-file',self.wav_file_name])
				#self.blocks_selector_0.set_output_index(1)  #connect to null sink
				

def main(top_block_cls=rtl_wavetrap, options=None):

	qapp = Qt.QApplication(sys.argv)

	tb = top_block_cls()

	tb.start()

	tb.show()

	def sig_handler(sig=None, frame=None):
		tb.stop()
		tb.wait()

		Qt.QApplication.quit()

	signal.signal(signal.SIGINT, sig_handler)
	signal.signal(signal.SIGTERM, sig_handler)

	timer = Qt.QTimer()
	timer.start(100)
	#timer.timeout.connect(lambda: None)
	timer.timeout.connect(lambda: tb.timer_function())

	qapp.exec_()

if __name__ == '__main__':
	main()
