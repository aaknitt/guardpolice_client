#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: andyk
# GNU Radio version: 3.10.9.2

from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation




class demod_am_from_wav(gr.top_block):

    def __init__(self, input_filename="1707684526.wav", offset_freq_khz=400000, samp_rate=2400000):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)

        ##################################################
        # Parameters
        ##################################################
        self.input_filename = input_filename
        self.offset_freq_khz = offset_freq_khz
        self.samp_rate = samp_rate

        ##################################################
        # Variables
        ##################################################
        self.variable_low_pass_filter_taps_0 = variable_low_pass_filter_taps_0 = firdes.low_pass(samp_rate/10000, samp_rate, 10000,5000, window.WIN_HAMMING, 6.76)
        self.transition_bw = transition_bw = 20000
        self.decimation = decimation = 1

        ##################################################
        # Blocks
        ##################################################

        self.rational_resampler_xxx_0_0 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=30,
                taps=[],
                fractional_bw=0)
        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_ccc(10, variable_low_pass_filter_taps_0, offset_freq_khz, samp_rate)
        self.dc_blocker_xx_0_1 = filter.dc_blocker_ff(32, True)
        self.blocks_wavfile_source_0 = blocks.wavfile_source("" +str(input_filename), False)
        self.blocks_wavfile_sink_0_0_0 = blocks.wavfile_sink(
            input_filename.replace(".wav","_audio.wav"),
            1,
            8000,
            blocks.FORMAT_WAV,
            blocks.FORMAT_PCM_16,
            False
            )
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_0, 0), (self.dc_blocker_xx_0_1, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.blocks_wavfile_source_0, 1), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_wavfile_source_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.dc_blocker_xx_0_1, 0), (self.blocks_wavfile_sink_0_0_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.rational_resampler_xxx_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0, 0), (self.blocks_complex_to_mag_0, 0))


    def get_input_filename(self):
        return self.input_filename

    def set_input_filename(self, input_filename):
        self.input_filename = input_filename

    def get_offset_freq_khz(self):
        return self.offset_freq_khz

    def set_offset_freq_khz(self, offset_freq_khz):
        self.offset_freq_khz = offset_freq_khz
        self.freq_xlating_fir_filter_xxx_0.set_center_freq(self.offset_freq_khz)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_variable_low_pass_filter_taps_0(firdes.low_pass(self.samp_rate/10000, self.samp_rate, 10000, 5000, window.WIN_HAMMING, 6.76))

    def get_variable_low_pass_filter_taps_0(self):
        return self.variable_low_pass_filter_taps_0

    def set_variable_low_pass_filter_taps_0(self, variable_low_pass_filter_taps_0):
        self.variable_low_pass_filter_taps_0 = variable_low_pass_filter_taps_0
        self.freq_xlating_fir_filter_xxx_0.set_taps(self.variable_low_pass_filter_taps_0)

    def get_transition_bw(self):
        return self.transition_bw

    def set_transition_bw(self, transition_bw):
        self.transition_bw = transition_bw

    def get_decimation(self):
        return self.decimation

    def set_decimation(self, decimation):
        self.decimation = decimation



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--input-filename", dest="input_filename", type=str, default="1707684526.wav",
        help="Set input_filename [default=%(default)r]")
    parser.add_argument(
        "--offset-freq-khz", dest="offset_freq_khz", type=intx, default=400000,
        help="Set offset_freq_khz [default=%(default)r]")
    parser.add_argument(
        "--samp-rate", dest="samp_rate", type=intx, default=2400000,
        help="Set samp_rate [default=%(default)r]")
    return parser


def main(top_block_cls=demod_am_from_wav, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(input_filename=options.input_filename, offset_freq_khz=options.offset_freq_khz, samp_rate=options.samp_rate)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()
