#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Usbplus
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

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation



from gnuradio import qtgui

class usbplus(gr.top_block, Qt.QWidget):

    def __init__(self, GAIN=0.4, HPF=3500, LPF=50, RXSINK='', Sideband=1, TXSOURCE='plughw:CARD=Loopback,DEV=1'):
        gr.top_block.__init__(self, "Usbplus", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Usbplus")
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

        self.settings = Qt.QSettings("GNU Radio", "usbplus")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Parameters
        ##################################################
        self.GAIN = GAIN
        self.HPF = HPF
        self.LPF = LPF
        self.RXSINK = RXSINK
        self.Sideband = Sideband
        self.TXSOURCE = TXSOURCE

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 48000

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_sink_x_0 = qtgui.sink_c(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            False, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0.set_update_time(1.0/8)
        self._qtgui_sink_x_0_win = sip.wrapinstance(self.qtgui_sink_x_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0.enable_rf_freq(False)

        self.top_layout.addWidget(self._qtgui_sink_x_0_win)
        self.low_pass_filter_0_0 = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                HPF,
                100,
                window.WIN_KAISER,
                6.76))
        self.low_pass_filter_0 = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                HPF,
                100,
                window.WIN_KAISER,
                6.76))
        self.hilbert_fc_1_0 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.hilbert_fc_1 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.hilbert_fc_0 = filter.hilbert_fc(201, window.WIN_BLACKMAN, 6.76)
        self.blocks_multiply_const_vxx_0_0_1 = blocks.multiply_const_ff(Sideband)
        self.blocks_multiply_const_vxx_0_0_0_0 = blocks.multiply_const_ff(1)
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_ff(1)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(Sideband)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
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
                HPF,
                100,
                window.WIN_BLACKMAN,
                6.76))
        self.band_pass_filter_0 = filter.fir_filter_fff(
            1,
            firdes.band_pass(
                GAIN,
                samp_rate,
                LPF,
                HPF,
                100,
                window.WIN_BLACKMAN,
                6.76))
        self.audio_source_1 = audio.source(samp_rate, TXSOURCE, True)
        self.audio_source_0 = audio.source(samp_rate, 'hw:RadioHatCodec,1', False)
        self.audio_sink_1 = audio.sink(48000, RXSINK, False)
        self.audio_sink_0 = audio.sink(samp_rate, 'hw:RadioHatCodec,0', False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.audio_source_0, 1), (self.blocks_float_to_complex_0, 0))
        self.connect((self.audio_source_0, 0), (self.blocks_float_to_complex_0, 1))
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
        self.connect((self.blocks_float_to_complex_0, 0), (self.qtgui_sink_x_0, 0))
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
        self.settings = Qt.QSettings("GNU Radio", "usbplus")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_GAIN(self):
        return self.GAIN

    def set_GAIN(self, GAIN):
        self.GAIN = GAIN
        self.band_pass_filter_0.set_taps(firdes.band_pass(self.GAIN, self.samp_rate, self.LPF, self.HPF, 100, window.WIN_BLACKMAN, 6.76))

    def get_HPF(self):
        return self.HPF

    def set_HPF(self, HPF):
        self.HPF = HPF
        self.band_pass_filter_0.set_taps(firdes.band_pass(self.GAIN, self.samp_rate, self.LPF, self.HPF, 100, window.WIN_BLACKMAN, 6.76))
        self.band_pass_filter_1.set_taps(firdes.band_pass(1, self.samp_rate, 100, self.HPF, 100, window.WIN_BLACKMAN, 6.76))
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.HPF, 100, window.WIN_KAISER, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, self.HPF, 100, window.WIN_KAISER, 6.76))

    def get_LPF(self):
        return self.LPF

    def set_LPF(self, LPF):
        self.LPF = LPF
        self.band_pass_filter_0.set_taps(firdes.band_pass(self.GAIN, self.samp_rate, self.LPF, self.HPF, 100, window.WIN_BLACKMAN, 6.76))

    def get_RXSINK(self):
        return self.RXSINK

    def set_RXSINK(self, RXSINK):
        self.RXSINK = RXSINK

    def get_Sideband(self):
        return self.Sideband

    def set_Sideband(self, Sideband):
        self.Sideband = Sideband
        self.blocks_multiply_const_vxx_0_0.set_k(self.Sideband)
        self.blocks_multiply_const_vxx_0_0_1.set_k(self.Sideband)

    def get_TXSOURCE(self):
        return self.TXSOURCE

    def set_TXSOURCE(self, TXSOURCE):
        self.TXSOURCE = TXSOURCE

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_pass_filter_0.set_taps(firdes.band_pass(self.GAIN, self.samp_rate, self.LPF, self.HPF, 100, window.WIN_BLACKMAN, 6.76))
        self.band_pass_filter_1.set_taps(firdes.band_pass(1, self.samp_rate, 100, self.HPF, 100, window.WIN_BLACKMAN, 6.76))
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.HPF, 100, window.WIN_KAISER, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, self.HPF, 100, window.WIN_KAISER, 6.76))
        self.qtgui_sink_x_0.set_frequency_range(0, self.samp_rate)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-G", "--GAIN", dest="GAIN", type=eng_float, default=eng_notation.num_to_str(float(0.4)),
        help="Set GAIN [default=%(default)r]")
    parser.add_argument(
        "--HPF", dest="HPF", type=intx, default=3500,
        help="Set HPF [default=%(default)r]")
    parser.add_argument(
        "--LPF", dest="LPF", type=intx, default=50,
        help="Set LPF [default=%(default)r]")
    parser.add_argument(
        "--RXSINK", dest="RXSINK", type=str, default='',
        help="Set RXSINK [default=%(default)r]")
    parser.add_argument(
        "-S", "--Sideband", dest="Sideband", type=intx, default=1,
        help="Set Sideband [default=%(default)r]")
    parser.add_argument(
        "--TXSOURCE", dest="TXSOURCE", type=str, default='plughw:CARD=Loopback,DEV=1',
        help="Set TXSOURCE [default=%(default)r]")
    return parser


def main(top_block_cls=usbplus, options=None):
    if options is None:
        options = argument_parser().parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print("Error: failed to enable real-time scheduling.")

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(GAIN=options.GAIN, HPF=options.HPF, LPF=options.LPF, RXSINK=options.RXSINK, Sideband=options.Sideband, TXSOURCE=options.TXSOURCE)

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
