# making DPI aware
import ctypes
import platform

if int(platform.release()) >= 8:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)



import dearpygui.dearpygui as dpg
from dearpygui_ext.themes import create_theme_imgui_light


def key_press_callback(sender, app_data, user_data, app):
    # key is sent in app_data
    # app.print(f'Key pressed: {sender=} {app_data=}')
    if app_data == 32: # space
        app.toggle_pause()


def resize_after_window(item, window, xoffset=0, yoffset=0):
    rect_size = dpg.get_item_state(window)['rect_size']
    dpg.configure_item(item, width=rect_size[0]-xoffset, height=rect_size[1]-yoffset)



def prepare_gui(app):

    dpg.create_context()

    with dpg.font_registry():
        with dpg.font("FiraMono-Regular.ttf", 16) as smaller_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

        with dpg.font("FiraMono-Regular.ttf", 20) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x2190, 0x21ff)

        dpg.bind_font(default_font)

    with dpg.handler_registry():
        dpg.add_key_press_handler(callback=lambda s,a,u:key_press_callback(s,a,u,app))

    with dpg.theme(tag="line_plot_lw2"):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 5, category=dpg.mvThemeCat_Plots)


    ### BIG WINDOW WITH GRAPH
    with dpg.window(label='Sensor values', tag='w:sensor', height=1000, width=1500, pos=(410,0), no_close=True):
        with dpg.plot(label=f"", height=750, width=780, tag="plot:sensor", crosshairs=True):
            dpg.add_plot_legend(horizontal=True)
            dpg.add_plot_axis(dpg.mvXAxis, label="t, с", tag='ax:x:sensor')
            dpg.add_plot_axis(dpg.mvYAxis, label="s, см", tag='ax:y:coordinate')
            dpg.add_line_series(x=[], y=[], label="Пройденный путь s", parent='ax:y:coordinate', tag='series:coordinate')
            # dpg.add_line_series(x=[], y=[], label="ИНтерп. коорд.", parent='ax:y:coordinate', tag='series:int_coord')

            dpg.add_plot_axis(dpg.mvYAxis, label="v, см/с", tag='ax:y:velocity')
            dpg.add_line_series(x=[], y=[], label="Скорость v", parent='ax:y:velocity', tag='series:velocity')
            dpg.set_axis_limits('ax:y:velocity', 0, 20)

            dpg.add_plot_axis(dpg.mvYAxis, label="a, см/с^2", tag='ax:y:acceleration')
            dpg.add_line_series(x=[], y=[], label="Ускорение a", parent='ax:y:acceleration', tag='series:acceleration')
            dpg.set_axis_limits('ax:y:acceleration', -5, 5)

            dpg.bind_item_theme("plot:sensor", "line_plot_lw2")


            dpg.add_drag_line(label="Начало интервала", tag='drag_left', default_value=1,
                color=[0, 255, 0, 255], thickness=3, show_label=True,
                callback=lambda s,a,u: app.set_interval_start(dpg.get_value(s)))
            dpg.add_drag_line(label="Конец интервала", tag='drag_right', default_value=2,
                color=[255, 0, 0, 255], thickness=3, show_label=True,
                callback=lambda s,a,u: app.set_interval_end(dpg.get_value(s)))


        with dpg.item_handler_registry(tag="sensor handlers") as handler:
            dpg.add_item_resize_handler(callback=lambda s,a,u: resize_after_window('plot:sensor', 'w:sensor', 20, 50))
        dpg.bind_item_handler_registry("w:sensor", "sensor handlers")


    ### CONTROLS
    with dpg.window(label='Управление', tag='w:main', pos=(0, 0), height=1000, width=400, no_close=True):
        with dpg.menu_bar():
            with dpg.menu(label="Menu"):
                # dpg.add_menu_item(label="Save GUI view", callback=save_init)
                dpg.add_menu_item(label="Fonts", callback=dpg.show_font_manager)
                dpg.add_menu_item(label="Debug", callback=dpg.show_debug)
                dpg.add_menu_item(label="Docs", callback=dpg.show_documentation)
                dpg.add_menu_item(label="Items", callback=dpg.show_item_registry)
                dpg.add_menu_item(label="Metrics", callback=dpg.show_metrics)
                dpg.add_menu_item(label="Style", callback=dpg.show_style_editor)

        with dpg.group(horizontal=True):
            dpg.add_button(label='Старт', tag='btn:start', width=100, height=50, callback=app.toggle_pause)
            dpg.add_button(label='Сброс ←', tag='btn:reset', width=100, height=50, callback=app.reset_data)


        dpg.add_separator()
        dpg.add_text("Интервал")

        dpg.add_input_float(label='Начало', default_value=1, tag='int_start',
            callback=lambda s,a,u:app.set_interval_start(a))

        dpg.add_input_float(label='Конец', default_value=2, tag='int_end',
            callback=lambda s,a,u:app.set_interval_end(a))


        dpg.add_separator()
        dpg.add_text('', tag='last_value')




    ### LOG
    with dpg.window(label='Log', tag='w:log', width=600, height=600, pos=(1220, 0), no_close=True, show=False):
        dpg.add_text('', tag='log', wrap=600, )
        dpg.bind_item_font(dpg.last_item(), smaller_font)


    viewport = dpg.create_viewport(title='OFP 105', width=900, height=900)
    light_theme = create_theme_imgui_light()
    dpg.configure_viewport(viewport, clear_color =(220,220,220))
    dpg.bind_theme(light_theme)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.maximize_viewport()

