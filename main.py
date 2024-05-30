import serial
import dearpygui.dearpygui as dpg
import easygui

import faulthandler
faulthandler.enable()

import yaml
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator, Akima1DInterpolator, make_interp_spline

# from more_itertools import windowed
import itertools
import time

from window import prepare_gui



class Application:
    on_pause = True
    reset_queued = False
    log = ''

    # data storage
    raw_ts = list()

    # defaults
    port = 'COM8'
    baudrate = 115200

    sectors = 120    # 1 sector = 3 deg
    interp_dt = 0.05 # s


    def __init__(self):
        import serial

        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=30)
            time.sleep(2)

        except serial.serialutil.SerialException as e:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()

            all_ports = list()
            for port, desc, hwid in sorted(ports):
                    all_ports.append("{}: {} [{}]".format(port, desc, hwid))
            all_ports = "\n".join(all_ports)

            easygui.exceptionbox(title='Ошибка!', msg=f'Доступные порты ({len(all_ports)} штук):\n{all_ports}')
            exit(1)


    def toggle_pause(self):
        self.on_pause = not self.on_pause
        if self.on_pause:
            dpg.configure_item('btn:start', label='Старт')
        else:
            dpg.configure_item('btn:start', label='Стоп')
        self.print(f'{self.on_pause=}')


    def queue_reset(self):
        self.reset_queued = True


    def reset_data(self):
        self.raw_ts.clear()

        dpg.configure_item('series:coordinate',     x=[], y=[])
        dpg.configure_item('series:velocity',       x=[], y=[])
        dpg.configure_item('series:acceleration',   x=[], y=[])

        self.reset_queued = False
        self.print('*** RESET ***')


    def print(self, *s):
        ss = ', '.join(str(s2) for s2 in s)
        self.log += '\n' + str(ss)
        dpg.set_value('log', self.log)
        dpg.set_y_scroll('w:log', dpg.get_y_scroll_max('w:log'))


    def set_interval_start(self, v):
        self.interval_start = v
        dpg.set_value('int_start', v)
        dpg.set_value('drag_left', v)


    def set_interval_end(self, v):
        self.interval_end = v
        dpg.set_value('int_end', v)
        dpg.set_value('drag_right', v)





app = Application()

prepare_gui(app)

app.set_interval_start(0.1)
app.set_interval_end(0.2)





prev_t, t = -1, 0


while dpg.is_dearpygui_running():

    while app.arduino.inWaiting() > 100:

        raw_t = app.arduino.readline()    # millis

        try:
            t = int(raw_t.decode('utf8').strip())
        except UnicodeDecodeError:
            print('*** UDE', raw_t)
        except ValueError:
            print('*** VE', raw_t)

        if not app.on_pause:
            if t != prev_t:
                app.raw_ts.append(t / 1000)

        prev_t = t

        dpg.set_value('last_value', f'{t=} {app.arduino.inWaiting()=}')



    if not app.on_pause:
        try:
            app.ts = np.array(app.raw_ts, dtype=float) - app.raw_ts[0]
            app.xs = np.arange(0, app.ts.shape[0], dtype=float) * 6.28 / app.sectors
        except IndexError:
            continue

        dpg.configure_item('series:coordinate', x=app.ts, y=app.xs)
        dpg.fit_axis_data('ax:x:sensor')
        dpg.fit_axis_data('ax:y:coordinate')



        # if app.on_pause and not app.vel_acc_calculated and len(app.raw_ts) > 3:
        if len(app.raw_ts) > 50:

            # f = CubicSpline(ts, xs)
            f = Akima1DInterpolator(app.ts, app.xs)
            # f = PchipInterpolator(ts, xs)

            app.new_ts = np.arange(0, app.ts[-1], app.interp_dt)
            app.new_xs = f(app.new_ts)

            app.vels = np.gradient(app.new_xs) / app.interp_dt
            app.accs = np.gradient(app.vels) / app.interp_dt


            # dpg.configure_item('series:int_coord', x=new_ts, y=new_xs)
            dpg.configure_item('series:velocity', x=app.new_ts, y=app.vels)
            dpg.configure_item('series:acceleration', x=app.new_ts, y=app.accs)
            # dpg.fit_axis_data('ax:y:velocity')
            # dpg.fit_axis_data('ax:y:acceleration')


    if app.reset_queued:
        app.reset_data()


    dpg.render_dearpygui_frame()

dpg.destroy_context()



