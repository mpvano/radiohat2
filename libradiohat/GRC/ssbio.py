#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Ssbio
# GNU Radio version: 3.10.5.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from gnuradio import audio
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



from gnuradio import qtgui

class ssbio(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Ssbio", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Ssbio")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
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

        self.settings = Qt.QSettings("GNU Radio", "ssbio")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 48000
        self.LSB = LSB = 0

        ##################################################
        # Blocks
        ##################################################

        self.low_pass_filter_0_0 = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                3000,
                100,
                window.WIN_BLACKMAN,
                6.76))
        self.low_pass_filter_0 = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                3000,
                100,
                window.WIN_KAISER,
                6.76))
        self.hilbert_fc_1_0 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.hilbert_fc_1 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.hilbert_fc_0 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.blocks_multiply_const_vxx_0_0_1 = blocks.multiply_const_ff(LSB)
        self.blocks_multiply_const_vxx_0_0_0_0 = blocks.multiply_const_ff(1)
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_ff(1)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(LSB)
        self.blocks_complex_to_real_1 = blocks.complex_to_real(1)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.blocks_complex_to_imag_1 = blocks.complex_to_imag(1)
        self.blocks_complex_to_imag_0 = blocks.complex_to_imag(1)
        self.blocks_add_xx_0 = blocks.add_vff(1)
        self.band_pass_filter_1 = filter.interp_fir_filter_fff(
            1,
            firdes.band_pass(
                1,
                samp_rate,
                100,
                3000,
                100,
                window.WIN_BLACKMAN,
                6.76))
        self.band_pass_filter_0 = filter.fir_filter_fff(
            1,
            firdes.band_pass(
                .4,
                samp_rate,
                100,
                3000,
                100,
                window.WIN_BLACKMAN,
                6.76))
        self.audio_source_1 = audio.source(samp_rate, '', True)
        self.audio_source_0 = audio.source(samp_rate, 'hw:RadioHatCodec,1', False)
        self.audio_sink_1 = audio.sink(48000, '', False)
        self.audio_sink_0 = audio.sink(samp_rate, 'hw:RadioHatCodec,0', False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.audio_source_0, 1), (self.hilbert_fc_0, 0))
        self.connect((self.audio_source_0, 0), (self.hilbert_fc_1, 0))
        self.connect((self.audio_source_1, 0), (self.band_pass_filter_1, 0))
        self.connect((self.band_pass_filter_0, 0), (self.audio_sink_1, 0))
        self.connect((self.band_pass_filter_1, 0), (self.hilbert_fc_1_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.band_pass_filter_0, 0))
        self.connect((self.blocks_complex_to_imag_0, 0), (self.blocks_multiply_const_vxx_0_0_0, 0))
        self.connect((self.blocks_complex_to_imag_1, 0), (self.blocks_multiply_const_vxx_0_0_1, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.blocks_complex_to_real_1, 0), (self.blocks_multiply_const_vxx_0_0_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_const_vxx_0_0_0_0, 0), (self.low_pass_filter_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0_1, 0), (self.low_pass_filter_0, 0))
        self.connect((self.hilbert_fc_0, 0), (self.blocks_complex_to_imag_0, 0))
        self.connect((self.hilbert_fc_1, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.hilbert_fc_1_0, 0), (self.blocks_complex_to_imag_1, 0))
        self.connect((self.hilbert_fc_1_0, 0), (self.blocks_complex_to_real_1, 0))
        self.connect((self.low_pass_filter_0, 0), (self.audio_sink_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.audio_sink_0, 1))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "ssbio")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_pass_filter_0.set_taps(firdes.band_pass(.4, self.samp_rate, 100, 3000, 100, window.WIN_BLACKMAN, 6.76))
        self.band_pass_filter_1.set_taps(firdes.band_pass(1, self.samp_rate, 100, 3000, 100, window.WIN_BLACKMAN, 6.76))
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 3000, 100, window.WIN_KAISER, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 3000, 100, window.WIN_BLACKMAN, 6.76))

    def get_LSB(self):
        return self.LSB

    def set_LSB(self, LSB):
        self.LSB = LSB
        self.blocks_multiply_const_vxx_0_0.set_k(self.LSB)
        self.blocks_multiply_const_vxx_0_0_1.set_k(self.LSB)




def main(top_block_cls=ssbio, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
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
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
