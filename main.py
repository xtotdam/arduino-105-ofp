import serial
import dearpygui.dearpygui as dpg
import easygui

import faulthandler
faulthandler.enable()

import numpy as np
from scipy.interpolate import Akima1DInterpolator
from scipy.stats import linregress

import itertools
import time

from window import prepare_gui
from settings import S
print(S)

class Application:
    reset_queued = False

    # data storage
    raw_ts = list()


    def __init__(self, S):
        self.on_pause = S.prg.start_on_pause

        # if simulate:
        #     pass

        import serial

        try:
            self.arduino = serial.Serial(S.sensor.port, S.sensor.baudrate, timeout=30)
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


    def queue_reset(self):
        self.reset_queued = True


    def reset_data(self):
        self.raw_ts.clear()

        dpg.configure_item('series:coordinate',     x=[], y=[])
        dpg.configure_item('series:velocity',       x=[], y=[])
        dpg.configure_item('series:velocity2',      x=[], y=[])
        dpg.configure_item('series:acceleration',   x=[], y=[])
        dpg.configure_item('series:acceleration2',  x=[], y=[])

        self.reset_queued = False


    def set_interval_start(self, v):
        self.interval_start = v
        dpg.set_value('int_start', v)
        dpg.set_value('drag_left', v)


    def set_interval_end(self, v):
        self.interval_end = v
        dpg.set_value('int_end', v)
        dpg.set_value('drag_right', v)


    def calculate(self):
        t1 = min(self.interval_start, self.interval_end)
        t2 = max(self.interval_start, self.interval_end)

        print(f'Velocity = [{min(self.vels)}, {max(self.vels)}]')
        print(f'Acceleration = [{min(self.accs)}, {max(self.accs)}]')

        # print(t1, t2)
        indices = np.ravel(np.argwhere((t1 <= app.new_ts) & (app.new_ts <= t2)))
        # print(indices)
        ts = app.new_ts[indices]
        line_x = [ts[0], ts[-1]]

        # Regressing velocities
        vs = app.vels[indices]
        rr = linregress(ts, vs)
        dpg.set_value('txt:velocity_regression',
            f'b = {rr.slope: .3f} ± {rr.stderr:.3f} cм/с²\n'
            f'c = {rr.intercept: .3f} ± {rr.intercept_stderr:.3f} cм/с\n'
            f'R² = {rr.rvalue**2:.3f}')
        line_y = [rr.slope * line_x[0] + rr.intercept, rr.slope * line_x[1] + rr.intercept]
        dpg.configure_item('series:velocity2', x=line_x, y=line_y)

        # Regressing acceleration
        vs = app.accs[indices]
        rr = linregress(ts, vs)
        dpg.set_value('txt:acceleration_regression',
            f'd = {rr.slope: .3f} ± {rr.stderr:.3f} cм/с³\n'
            f'e = {rr.intercept: .3f} ± {rr.intercept_stderr:.3f} cм/с²\n'
            f'R² = {rr.rvalue**2:.3f}')
        line_y = [rr.slope * line_x[0] + rr.intercept, rr.slope * line_x[1] + rr.intercept]
        dpg.configure_item('series:acceleration2', x=line_x, y=line_y)






app = Application(S)

prepare_gui(app, S)

app.set_interval_start(S.prg.interval_1)
app.set_interval_end(S.prg.interval_2)





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
                app.raw_ts.append(t / 1000)    # millis -> s

        prev_t = t

        # dpg.set_value('txt:tech_info', f'{t=}\n{app.arduino.inWaiting()=}\n{len(app.raw_ts)=}')
        dpg.set_value('txt:tech_info',
            f'Последнее значение {t}\n'
            f'Длина очереди {app.arduino.inWaiting()}\n'
            f'Размер буфера {len(app.raw_ts)}')



    if not app.on_pause:
        try:
            app.ts = np.array(app.raw_ts, dtype=float) - app.raw_ts[0]
            app.xs = np.arange(0, app.ts.shape[0], dtype=float) * 6.28 / S.geometry.sectors * S.geometry.radius
        except IndexError:
            print(f'IndexError: {len(app.raw_ts)=}')
            continue

        dpg.configure_item('series:coordinate', x=app.ts, y=app.xs)
        dpg.fit_axis_data('ax:x:sensor')
        dpg.fit_axis_data('ax:y:coordinate')



        # if app.on_pause and not app.vel_acc_calculated and len(app.raw_ts) > 3:
        if len(app.raw_ts) > 50:

            f = Akima1DInterpolator(app.ts, app.xs, method='makima')

            app.new_ts = np.arange(0, app.ts[-1], S.prg.interp_dt)
            app.new_xs = f(app.new_ts)

            app.vels = np.gradient(app.new_xs) / S.prg.interp_dt
            app.accs = np.gradient(app.vels) / S.prg.interp_dt


            # dpg.configure_item('series:coordinate2', x=app.new_ts, y=app.new_xs)
            dpg.configure_item('series:velocity', x=app.new_ts, y=app.vels)
            dpg.configure_item('series:acceleration', x=app.new_ts, y=app.accs)
            # dpg.fit_axis_data('ax:y:velocity')
            # dpg.fit_axis_data('ax:y:acceleration')


    if app.reset_queued:
        app.reset_data()


    dpg.render_dearpygui_frame()

dpg.destroy_context()



