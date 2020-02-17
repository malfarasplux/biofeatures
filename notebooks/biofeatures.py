import biosppy.signals.resp as resp
import biosignalsnotebooks as bsnb
from sklearn.linear_model import LinearRegression
import numpy as np
import pyhrv

def r_peak_intervals(data, sampling_rate):
    """ Calculates R-to-R peak intervals from raw ECG signal
    ----------
    data: raw ECG signal

    sampling_rate: sampling rate of ECG recording

    Returns
    ----------
    peaks : timestamps of R-peaks
    r_intervals : R-to-R peak intervals in milliseconds
    """
    peaks = bsnb.detect_r_peaks(data, sampling_rate, time_units=True, plot_result=False)

    intervals = [peaks[0][i] - peaks[0][i-1] for i in range(1,len(peaks[0]))]
    r_intervals = (np.array(intervals) * 1000).astype(int)

    return peaks[0], r_intervals

def hrv_features(intervals):
    """Calculates heart rate variability features from R-to-R peak intervals
    ----------
    intervals : R-to-R peak intervals calculated from ECG signal

    Returns
    ----------
    features : dictionary containing the calculated time and frequency domain features
    """
    features = {}

    rr_features = pyhrv.time_domain.nni_parameters(nni=intervals)
    hr_features = pyhrv.time_domain.hr_parameters(nni=intervals)
    rmssd = pyhrv.time_domain.rmssd(nni=intervals)
    freq_features = pyhrv.frequency_domain.welch_psd(nni=intervals, show=False, mode='dev')

    features.update({'nni_mean': rr_features['nni_mean'], 'hr_mean': hr_features['hr_mean'],
                    'hr_std': hr_features['hr_std'], 'rmssd': rmssd['rmssd'],
                    'lf': freq_features[0]['fft_abs'][1], 'hf': freq_features[0]['fft_abs'][2],
                    'LF/HF ratio': freq_features[0]['fft_ratio']})

    return features

def detect_trend(features):
    """Calculates whether the overall trend in the features is increasing or decreasing
        by fitting a linear function to the feature array
    ----------
    features : 1-D array of HRV features

    Returns
    ----------
    trend :  < 0 if the overall trend is decreasing
             > 0 if the overall trend is increasing
    """
    size = np.arange(0,len(features))
    feature_array = np.array(features)
    trend = np.polyfit(size, feature_array, 1)
    return trend[0]

def resp_intervals(data, sampling_rate = 200, last_breath = False):
    """Calculates respiration intervals and indicates inhale/exhale
    Parameters
    ----------
    data : breathing signal to be processed

    sampling_rate: sampling rate of breathing signal

    last_breath : flag that indicates whether single/mult breath analysis is requested

    Returns
    ----------
    interval_lengths: list of breathing interval lenghts

    interval_breathe_in: list of breathe in True/False flags
    """
    processed_data = resp.resp(signal=data, sampling_rate=sampling_rate, show=False)
    filtered_signal = processed_data[1]
    inst_resp_rate = processed_data[4]

    signal_diff = np.diff(filtered_signal)
    signal_signum = signal_diff > 0

    resp_changes = np.append(np.where(signal_signum[:-1] != signal_signum[1:])[0], [len(signal_signum) - 1])

    if not last_breath:

        resp_intervals = np.append([0], resp_changes)
        interval_lengths = np.diff(resp_intervals)
        interval_breathe_in = [signal_signum[i] for i in resp_changes]
        return interval_lengths, interval_breathe_in

    else:
        if len(resp_changes) > 1:
            last_interval = resp_changes[-1] - resp_changes[-2]
        else:
            last_interval = resp_changes[-1]

        return last_interval, signal_signum[resp_changes[-1]]


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


def resp_features(resp_intervals, is_inhalation, sampling_rate):
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
            - exhale_duration: total duration of exhaling intervals in data in seconds
            - inhale_exhale_ratio: ratio of inhalation to exhalation
    """
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

    features = {'breath_avg_len': avg_breath, 'inhale_duration': breathe_in_len / sampling_rate,
                'exhale_duration': breathe_out_len / sampling_rate, 'inhale_exhale_ratio': in_out_ratio}

    return features
