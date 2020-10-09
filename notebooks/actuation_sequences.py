import time
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient
import threading
from random import uniform
import numpy as np

class actuation(object):

    def __init__(self, osc_client, actuation_flag):
        self.osc_client = osc_client
        self.actuation_flag = actuation_flag

    def warmup_inflate(self, act_id, duration):
          self.osc_client.send_message("/actuator/" + act_id + "/inflate", 100.0)
          time.sleep(duration)
          self.osc_client.send_message("/actuator/" + act_id + "/inflate", 0.0)

    def deflate(self, act_id, duration):
        self.osc_client.send_message("/actuator/" + act_id + "/inflate", -100.0)
        time.sleep(duration)
        self.osc_client.send_message("/actuator/" + act_id + "/inflate", 0.0)

    # computes inhale and exhale interval duration as average duration of breath * breathing_factor
    def breathing_biofeedback(self, first_id, snd_id, B, inflate, hold, hold_time):
        if not self.actuation_flag or not B.routine.startswith("breathing_biofeedback"):
            return

        breathing_factor = B.breathing_factor

        if hold:
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", 0.0)
            timer_in = threading.Timer(hold_time, self.breathing_biofeedback, [first_id, snd_id, B, True, False, hold_time])
            timer_in.start()

        if not hold and inflate:
            print("inhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", B.inflation_speed)
            timer_exhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.breathing_biofeedback, [first_id, snd_id, B, False, False, hold_time])
            timer_exhale.start()

        if not hold and not inflate:
            print("exhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", -1 * B.inflation_speed)
            timer_inhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.breathing_biofeedback, [first_id, snd_id, B, True, True, hold_time])
            timer_inhale.start()


    # increases speed when intervals are below a certain threshold (2 seconds, or 10 breaths per minute)
    def regulated_biofeedback(self, first_id, snd_id, B, inflate, hold, hold_time):
        if not self.actuation_flag or not B.routine.startswith("regulated_biofeedback"):
            return

        if inflate and (B.features['avg_inhale'] < 2 or B.features['avg_inhale'] < 2):
            B.inflation_speed = 100.0
        else:
            B.inflation_speed = 50.0

        breathing_factor = B.breathing_factor

        if hold:
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", 0.0)
            timer_in = threading.Timer(hold_time, self.regulated_biofeedback, [first_id, snd_id, B, True, False, hold_time])
            timer_in.start()

        if not hold and inflate:
            print("inhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", B.inflation_speed)
            timer_exhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.regulated_biofeedback, [first_id, snd_id, B, False, False, hold_time])
            timer_exhale.start()

        if not hold and not inflate:
            print("exhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", -1 * B.inflation_speed)
            timer_inhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.regulated_biofeedback, [first_id, snd_id, B, True, True, hold_time])
            timer_inhale.start()


    def breathing_biofeedback_without_hold(self, first_id, snd_id, B, inflate):
        if not self.actuation_flag or not B.routine.startswith("breathing_biofeedback"):
            return

        breathing_factor = B.breathing_factor

        if inflate:
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.breathing_biofeedback_without_hold, [first_id, snd_id, B, False])
            timer_in.start()

        if not inflate:
            self.osc_client.send_message("/actuator/" + first_id + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + snd_id + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.breathing_biofeedback_without_hold, [first_id, snd_id, B, True])
            timer_in.start()

    # specify inhale and exhale interval duration in seconds
    def intervals(self, act_id, B, inhale_duration, exhale_duration, inflate):
        if not self.actuation_flag:
            return

        if inflate:
            print("inhale: ", inhale_duration)
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", B.inflation_speed)
            timer_exhale = threading.Timer(inhale_duration, self.intervals, [act_id, B, inhale_duration, exhale_duration, False])
            timer_exhale.start()

        else:
            print("exhale: ", exhale_duration)
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", -1 * B.inflation_speed)
            timer_inhale = threading.Timer(exhale_duration, self.intervals, [act_id, B, inhale_duration, exhale_duration, True])
            timer_inhale.start()


    def pulsating(self, act_id, B, inflate):
        if not self.actuation_flag or B.routine != "pulsating":
            return

        if inflate:
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", B.inflation_speed)
            timer_deflate = threading.Timer(3, self.pulsating, [act_id, B, False])
            timer_deflate.start()

        else:
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", -1 * B.inflation_speed)
            timer_inflate = threading.Timer(3, self.pulsating, [act_id, B, True])
            timer_inflate.start()


    def async_intervals(self, act_first, act_snd, B, inhale_dur, exhale_dur, inflate_first):

        if not self.actuation_flag or not B.routine.startswith("async_intervals"):
            return

        if inflate_first:
            print("inhale: ", inhale_dur)
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_inhale = threading.Timer(inhale_dur, self.async_intervals, [act_first, act_snd, B, inhale_dur, exhale_dur, False])
            timer_inhale.start()

        else:
            print("exhale: ", exhale_dur)
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_exhale = threading.Timer(exhale_dur, self.async_intervals, [act_first, act_snd, B, inhale_dur, exhale_dur, True])
            timer_exhale.start()

    def async_breathing(self, act_first, act_snd, B, inflate, hold, hold_time):

        if not self.actuation_flag or not B.routine.startswith("async_breathing"):
            return

        breathing_factor = B.breathing_factor

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(hold_time, self.async_breathing, [act_first, act_snd, B, True, False, hold_time])
            timer_in.start()

        if inflate and not hold:
            print("inhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_exhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.async_breathing, [act_first, act_snd, B, False, False, hold_time])
            timer_exhale.start()

        if not inflate and not hold:
            print("exhale: ", B.features['avg_exhale'])
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_inhale = threading.Timer(B.features['avg_exhale'] * breathing_factor, self.async_breathing, [act_first, act_snd, B, True, True, hold_time])
            timer_inhale.start()


    def async_breathing_without_hold(self, act_first, act_snd, B, inflate):

        if not self.actuation_flag or not B.routine.startswith("async_breathing"):
            return

        breathing_factor = B.breathing_factor

        if inflate:
            print("inhale: ", B.features['avg_inhale'])
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_exhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.async_breathing_without_hold, [act_first, act_snd, B, False])
            timer_exhale.start()

        if not inflate:
            print("exhale: ", B.features['avg_exhale'])
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_inhale = threading.Timer(B.features['avg_inhale'] * breathing_factor, self.async_breathing_without_hold, [act_first, act_snd, B, True])
            timer_inhale.start()


    def offset_intervals(self, act_first, act_second, int_first, int_snd, offset, B):

        if not self.actuation_flag or not B.routine.startswith("Offset"):
            return

        self.intervals(act_first, B, int_first, int_first, True);

        timer_snd = threading.Timer(offset, self.intervals, [act_second, B, int_snd, int_snd, True])
        timer_snd.start()


    #BREATHING TECHNIQUES
    def five_five_breath(self, act_first, act_snd, B, inflate):

        if not self.actuation_flag or B.routine != "five_five_breath":
            return

        if inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(5.5, self.five_five_breath, [act_first, act_snd, B, False])
            timer_in.start()

        if not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(5.5, self.five_five_breath, [act_first, act_snd, B, True])
            timer_in.start()


    def three_break_breath(self, act_first, act_snd, B, inflate, hold):

        if not self.actuation_flag or B.routine != "three_break_breath":
            return

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(2, self.three_break_breath, [act_first, act_snd, B, True, False])
            timer_in.start()

        elif inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(3, self.three_break_breath, [act_first, act_snd, B, False, False])
            timer_in.start()

        elif not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(3, self.three_break_breath, [act_first, act_snd, B, False, True])
            timer_in.start()


    def four_seven_eight(self, act_first, act_snd, B, inflate, hold):

        if not self.actuation_flag or B.routine != "four_seven_eight":
            return

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(7, self.four_seven_eight, [act_first, act_snd, B, False, False])
            timer_in.start()

        elif inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(4, self.four_seven_eight, [act_first, act_snd, B, False, True])
            timer_in.start()

        elif not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -0.5 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -0.5 * B.inflation_speed)
            timer_in = threading.Timer(8, self.four_seven_eight, [act_first, act_snd, B, True, False])
            timer_in.start()


    def five_five_breath_async(self, act_first, act_snd, B, inflate):

        if not self.actuation_flag or B.routine != "five_five_breath_async":
            return

        if inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(5.5, self.five_five_breath_async, [act_first, act_snd, B, False])
            timer_in.start()

        if not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(5.5, self.five_five_breath_async, [act_first, act_snd, B, True])
            timer_in.start()


    def three_break_breath_async(self, act_first, act_snd, B, inflate, hold):

        if not self.actuation_flag or B.routine != "three_break_breath_async":
            return

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(2, self.three_break_breath_async, [act_first, act_snd, B, True, False])
            timer_in.start()

        elif inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(3, self.three_break_breath_async, [act_first, act_snd, B, False, False])
            timer_in.start()

        elif not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(3, self.three_break_breath_async, [act_first, act_snd, B, False, True])
            timer_in.start()


    def four_seven_eight_async(self, act_first, act_snd, B, inflate, hold):

        if not self.actuation_flag or B.routine != "four_seven_eight_async":
            return

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(7, self.four_seven_eight_async, [act_first, act_snd, B, False, False])
            timer_in.start()

        elif inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(4, self.four_seven_eight_async, [act_first, act_snd, B, False, True])
            timer_in.start()

        elif not inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.5 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -0.5 * B.inflation_speed)
            timer_in = threading.Timer(8, self.four_seven_eight_async, [act_first, act_snd, B, True, False])
            timer_in.start()

    def alternate_breaths(self, act_first, act_snd, B, inflate_first, inflate, remaining, max_breaths):
        if not self.actuation_flag or not B.routine.startswith("alternate_breaths"):
            return

        if inflate_first:
            if inflate:
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
                timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, inflate_first, not inflate, remaining, max_breaths])
                timer_in.start()
            else:
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)

                if remaining > 1:
                    timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, inflate_first, not inflate, remaining - 1, max_breaths])
                    timer_in.start()
                else:
                    timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, not inflate_first, not inflate, max_breaths, max_breaths])
                    timer_in.start()

        else:
            if inflate:
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
                timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, inflate_first, not inflate, remaining, max_breaths])
                timer_in.start()
            else:
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)

                if remaining > 1:
                    timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, inflate_first, not inflate, remaining - 1, max_breaths])
                    timer_in.start()
                else:
                    timer_in = threading.Timer(5, self.alternate_breaths, [act_first, act_snd, B, not inflate_first, not inflate, max_breaths, max_breaths])
                    timer_in.start()


    def alternate_breaths_min(self, act_first, act_snd, B, inflate_first, inflate, start_time, duration):
        if not self.actuation_flag or not B.routine.startswith("alternate_breaths_min"):
            return

        if inflate_first:
            if inflate:
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
                timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, inflate_first, not inflate, start_time, duration])
                timer_in.start()
            else:
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)

                if time.time() - start_time < duration:
                    timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, inflate_first, not inflate, start_time, duration])
                    timer_in.start()
                else:
                    timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, not inflate_first, not inflate, time.time(), duration])
                    timer_in.start()

        else:
            if inflate:
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
                timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, inflate_first, not inflate, start_time, duration])
                timer_in.start()
            else:
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)

                if time.time() - start_time < duration:
                    timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, inflate_first, not inflate, start_time, duration])
                    timer_in.start()
                else:
                    timer_in = threading.Timer(5, self.alternate_breaths_min, [act_first, act_snd, B, not inflate_first, not inflate, time.time(), duration])
                    timer_in.start()


    def belly_to_chest_breathing(self, act_first, act_snd, B, inflate_first, inflate, hold):
        if not self.actuation_flag or not B.routine.startswith("belly_to_chest_breathing"):
            return

        if hold:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
            timer_in = threading.Timer(1, self.belly_to_chest_breathing, [act_first, act_snd, B, inflate_first, inflate, False])
            timer_in.start()

        else:
            if inflate_first:
                if inflate:
                    print("one inf")
                    self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
                    timer_in = threading.Timer(2, self.belly_to_chest_breathing, [act_first, act_snd, B, not inflate_first, inflate, False])
                    timer_in.start()
                else:
                    print("one def, two stop")
                    self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
                    self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
                    timer_in = threading.Timer(2, self.belly_to_chest_breathing, [act_first, act_snd, B, inflate_first, not inflate, True])
                    timer_in.start()
            else:
                if inflate:
                    print("two inf, one stop")
                    self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
                    self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
                    timer_in = threading.Timer(2, self.belly_to_chest_breathing, [act_first, act_snd, B, inflate_first, not inflate, False])
                    timer_in.start()
                else:
                    print("two def")
                    self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
                    timer_in = threading.Timer(2, self.belly_to_chest_breathing, [act_first, act_snd, B, not inflate_first, inflate, False])
                    timer_in.start()



    # computes degree of inflation/deflation based on ECG features
    def heartrate_actuation(self, act_id, HR, timer_interval):
        if not self.actuation_flag:
            return

        current_trend = HR.current_trends["hr_mean"]
        #current_trend = HR.current_trends["rmssd"]
        #current_trend = HR.current_trends["LF/HF ratio"]

        current_feature = HR.features[-1]["hr_mean"]
        #current_feature = HR.features[-1]["rmssd"]
        #current_feature = HR.features[-1]["LF/HF ratio"]

        if current_trend > 0:
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", B.inflation_speed)
            #osc_client.send_message("/actuator/" + act_id + "/inflate", current_trend * 1000/current_feature)
            timer_exhale = threading.Timer(timer_interval, self.heartrate_actuation, [act_id, HR, timer_interval])
            timer_exhale.start()

        else:
            #osc_client.send_message("/actuator/inflate", current_trend * 1000/current_feature)
            self.osc_client.send_message("/actuator/" + act_id + "/inflate", -1 * B.inflation_speed)
            timer_inhale = threading.Timer(timer_interval, self.heartrate_actuation, [act_id, HR, timer_interval])
            timer_inhale.start()

    def hr_biofeedback(self, act_first, act_snd, HR, B, inflate):
        if not self.actuation_flag or not B.routine.startswith("HR_biofeedback"):
            return

        current_hr = HR.features[-1]["hr_mean"]
        actuation_duration = 30 / ((current_hr // 5) - 6)
        print("current HR: ", current_hr)

        if inflate:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
            timer_in = threading.Timer(actuation_duration, self.hr_biofeedback, [act_first, act_snd, HR, B, False])
            timer_in.start()

        else:
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(actuation_duration, self.hr_biofeedback, [act_first, act_snd, HR, B, True])
            timer_in.start()

        """
        print("baseline: ", HR.baseline)

        if HR.baseline > 0 and inflate:
            lfhf = [x['LF/HF ratio'] for x in HR.features[-5:]]
            current_ratio = np.mean(lfhf)
            print("current: ", current_ratio)
            if current_ratio / HR.baseline > 1.5:
                print("inflate")
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", B.inflation_speed)
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", B.inflation_speed)
                timer_in = threading.Timer(5.5, self.hr_biofeedback, [act_first, act_snd, HR, B, False])
                timer_in.start()
            else:
                self.osc_client.send_message("/actuator/" + act_first + "/inflate", 0.0)
                self.osc_client.send_message("/actuator/" + act_snd + "/inflate", 0.0)
                timer_in = threading.Timer(1, self.hr_biofeedback, [act_first, act_snd, HR, B, True])
                timer_in.start()

        if not inflate:
            print("deflate")
            self.osc_client.send_message("/actuator/" + act_first + "/inflate", -1 * B.inflation_speed)
            self.osc_client.send_message("/actuator/" + act_snd + "/inflate", -1 * B.inflation_speed)
            timer_in = threading.Timer(5.5, self.hr_biofeedback, [act_first, act_snd, HR, B, True])
            timer_in.start()
        """
