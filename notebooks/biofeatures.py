import biosppy.signals.resp as resp
import biosignalsnotebooks as bsnb
from sklearn.linear_model import LinearRegression
import numpy as np
import threading
import pyhrv

# Breathing
class breathing(object):
    """
    Object containing breathing features, buffered data, signal properties and flags
    """

    def __init__(self, data, buffer_length = 1000, srate = 200, bits = 12):
        self.buffer_length = buffer_length
        self.srate = srate
        self.bits = bits

        # Feature data
        self.data = data
        self.interval_lengths = -1
        self.interval_breathe_in = -1
        self.resp_rate = -1
        self.resp_changes = -1
        self.resp_amplitude = 0
        self.filtered = -1
        self.feature_names = -1

        self.last_breath = -1
        self.last_is_inhale = True

        # Flags
        self.is_warmed_up = False
        self.update_data_flag = True

        # Debug
        self.count_updates = 0

    def update_loop(self):
        """
        Launches a recursive loop to update the feature computation:
        1) Breathing intervals
        2) Breathing features (average breath, inhale, exhale)
        3) Amplitudes
        4) Generic (area, linear regression, etc.)
        """
        if self.update_data_flag:
            self.timerT = threading.Timer(0.5, self.update_loop)

        self.count_updates = self.count_updates + 1
        self.timerT.start()
        data = (self.data).copy()

        try:
            self.resp_intervals(data)
            self.resp_features()
            print(self.features)
            self.calc_amplitudes(data)
        except:
            print("RESP ERROR")
            raise


    def set_data(self, data):
        """
        Stores data into the class attribute
        """
        self.data = data

    def resp_intervals(self, data):
        """Calculates respiration intervals and indicates inhale/exhale
        Parameters
        ----------
        data : breathing signal to be processed

        sampling_rate: sampling rate of breathing signal

        Returns
        ----------
        interval_lengths: list of breathing interval lenghts

        interval_breathe_in: list of breathe in True/False flags
        """
        processed_data = resp.resp(signal=data, sampling_rate=self.srate, show=False)
        filtered_signal = processed_data[1]
        inst_resp_rate = processed_data[4]
        self.filtered = filtered_signal
        self.resp_rate = inst_resp_rate

        signal_diff = np.diff(filtered_signal)
        signal_signum = signal_diff > 0

        resp_changes = np.append(np.where(signal_signum[:-1] != signal_signum[1:])[0], [len(signal_signum) - 1])
        self.resp_changes = resp_changes

        resp_intervals = np.append([0], resp_changes)
        interval_lengths = np.diff(resp_intervals)
        interval_breathe_in = [signal_signum[i] for i in resp_changes]
        self.interval_lengths, self.interval_breathe_in = interval_lengths, interval_breathe_in

        last_interval = -1
        if len(resp_changes) > 1:
            last_interval = resp_changes[-1] - resp_changes[-2]
        else:
            last_interval = resp_changes[-1]

        self.last_breath = last_interval
        self.last_is_inhale = signal_signum[resp_changes[-1]]



    def resp_features(self):
        """Calculates respiration features from inhale/exhale intervals
        ----------
        resp_intervals : inhalation and exhalation intervals

        is_inhalation : array of boolean values indicating the kind of breathing in resp_intervals
                        True -> inhalation
                        False -> exhalation

        sampling_rate : sampling rate of respiration sensor

        Returns
        ----------
        features: dictionary containing the calculated features
                - breath_avg_len: average breath length in seconds
                - inhale_duration: total duration of inhaling intervals in data in seconds
                - avg_inhale: average duration of inhale in seconds
                - exhale_duration: total duration of exhaling intervals in data in seconds
                - avg_exhale: average duration of exhale in seconds
                - inhale_exhale_ratio: ratio of inhalation to exhalation
        """
        resp_intervals = self.interval_lengths
        is_inhalation = self.interval_breathe_in
        sampling_rate = self.srate
        # calculate the average breath length in s
        breath_lengths = []
        i = 0

        while i < len(resp_intervals):
            if not is_inhalation[i] or i == len(resp_intervals) - 1 :
                breath_lengths.append(resp_intervals[i])
                i = i + 1
            else:
                breath_lengths.append(resp_intervals[i] + resp_intervals[i + 1])
                i = i + 2

        avg_breath = np.average(breath_lengths) / sampling_rate

        # calculate the inhalation/exhalation ratio
        breathe_in_len = 0
        breathe_out_len = 0

        for i in range(len(resp_intervals)):
            if is_inhalation[i]:
                breathe_in_len += resp_intervals[i]
            else:
                breathe_out_len += resp_intervals[i]

        in_out_ratio = breathe_in_len/breathe_out_len

        inhale_dur = round(breathe_in_len / sampling_rate,2)
        exhale_dur = round(breathe_out_len / sampling_rate,2)

        features = {'breath_avg_len': round(avg_breath,2),
                    'inhale_duration': inhale_dur,
                    'avg_inhale': round(inhale_dur / len([x for x in is_inhalation if x]),2),
                    'exhale_duration': exhale_dur,
                    'avg_exhale': round(exhale_dur / len([x for x in is_inhalation if not x]),2),
                    'inhale_exhale_ratio': round(in_out_ratio,2)}

        self.feature_names = features.keys()
        self.features = features

    # Amplitudes
    def calc_amplitudes(self, data):
        # TODO guarantee stop update data between interval and amplitude
        """Calculates respiration intervals and indicates inhale/exhale
        Parameters
        ----------
        data : breathing signal to be processed

        last_breath : flag that indicates whether single/mult breath analysis is requested

        Returns
        ----------

        amplitude: list of amplitude
        """
        data = np.array(data)
        if len(self.resp_changes)>1:
            self.resp_amplitude = np.diff(np.append([0],data[self.resp_changes]))[1:-1]
        else:
            self.resp_amplitude = 0

# Generic
#########

def area_fraction(data, bits):
    """Calculates the area fraction covered by the data
    Parameters
    ----------
    data : input signal to be processed

    bits : number of resolution bits (digital) R-IoT=12, BITalino = 10, IMU/bsp = 16

    Returns
    ----------
    fraction of area covered by the signal


    """
    frac = np.mean(np.absolute(data))/(2**bits)
    return frac


def lastpoint_linreg(data, samples = 100, sampling_rate = 200):
    """Calculates a linear regression a determines a hold flag based on slope
    Parameters
    ----------
    data : signal to be processed, ideally filtered

    samples : samples needed

    sampling_rate : acquisition sampling rate

    Returns
    ----------
    hold_flag: flag informing whether there is an inhale or exhale
    OR
    regression coefficient and intercept:

    """
    reg = LinearRegression().fit(np.linspace(0,1/sampling_rate*samples, samples).reshape(-1,1), data[-samples:].reshape(-1,1))
    return reg.coef_[0], reg.intercept_

# HRV
class hrv(object):
    """
    Object containing hrv features, buffered data, other properties
    """

    def __init__(self, data, buffer_length = 1000, srate = 1000):
        self.buffer_length = buffer_length
        self.srate = srate

        # Feature data
        self.data = data
        self.peaks = []
        self.r_intervals = []
        self.features = []
        self.feature_names = []
        self.current_trends = []

        # Flags
        self.update_data_flag = True
        self.is_warmed_up = False

    def update_loop(self):
        """
        Launches a recursive loop to update the feature computation
        """
        if self.update_data_flag:
            self.update_timer = threading.Timer(0.5, self.update_loop)
        self.update_timer.start()

        data = self.data.copy()

        try:
            self.r_peak_intervals(data)
            self.hrv_features()
            print(self.features[-5:])
            self.detect_trends()
        except:
            print("HRV update loop error")
            raise

    def set_data(self, data):
        """
        Stores data in the class attribute
        """
        self.data = data

    def r_peak_intervals(self, data):
        """
        Calculates R-to-R peak intervals from raw ECG data
        """
        peaks = bsnb.detect_r_peaks(data, self.srate, time_units=True, plot_result=False)

        intervals = [peaks[0][i] - peaks[0][i-1] for i in range(1,len(peaks[0]))]
        r_intervals = (np.array(intervals) * 1000).astype(int)

        self.peaks = peaks
        self.r_intervals = r_intervals

    def hrv_features(self):
        """
        Calculates heart rate variability features from R-to-R peak intervals
        """
        new_features = {}

        rr_features = pyhrv.time_domain.nni_parameters(nni=self.r_intervals)
        hr_features = pyhrv.time_domain.hr_parameters(nni=self.r_intervals)
        rmssd = pyhrv.time_domain.rmssd(nni=self.r_intervals)
        freq_features = pyhrv.frequency_domain.welch_psd(nni=self.r_intervals, show=False, mode='dev')

        new_features.update({'nni_mean': round(rr_features['nni_mean'], 2),
                            'hr_mean': round(hr_features['hr_mean'], 2),
                            'hr_std': round(hr_features['hr_std'], 2),
                            'rmssd': round(rmssd['rmssd'], 2),
                            'lf': round(freq_features[0]['fft_abs'][1], 2),
                            'hf': round(freq_features[0]['fft_abs'][2], 2),
                            'LF/HF ratio': round(freq_features[0]['fft_ratio'], 2)})

        self.features = self.features + [new_features]
        self.feature_names = new_features.keys()


    def detect_trends(self, max_samples = 60):
        """Calculates whether the overall trend in the features is increasing or decreasing
           by fitting a linear function to the feature array

        trend :  < 0 if the overall trend is decreasing
                 > 0 if the overall trend is increasing
        """
        trends = {}

        if len(self.features) > 1:

            for key in self.feature_names:
                feats = [f[key] for f in self.features][-max_samples:]
                size = np.arange(0,len(feats))
                feature_array = np.array(feats)
                trend = np.polyfit(size, feature_array, 1)
                trends.update({key: trend[0]})

                self.current_trends = trends
