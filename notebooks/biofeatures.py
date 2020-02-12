import biosppy.signals.resp as resp
from sklearn.linear_model import LinearRegression
import numpy as np

def calc_resp_intervals(data, last_breath = False):
    """Calculates respiration intervals and indicates inhale/exhale
    Parameters
    ----------
    data : breathing signal to be processed
    
    last_breath : flag that indicates whether single/mult breath analysis is requested
    
    Returns
    ----------
    interval_lengths: list of breathing interval lenghts
    
    interval_breathe_in: list of breathe in True/False flags
    """
    processed_data = resp.resp(signal=data, sampling_rate=200, show=False)
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
    hold_flag: flag informing whther there is an inhale or exhale
    OR 
    regression coefficient and intercept: 

    
    """
    reg = LinearRegression().fit(np.linspace(0,1/sampling_rate*samples, samples).reshape(-1,1), data[-samples:].reshape(-1,1))
    return reg.coef_[0], reg.intercept_