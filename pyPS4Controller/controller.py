import logging
import os
import struct
import time

logging.basicConfig()
logger = logging.getLogger("pyPS4Controller")
logger.setLevel(logging.DEBUG)


class Actions:
    """
    Actions are inherited in the Controller class.
    In order to bind to the controller events, subclass the Controller class and
    override desired action events in this class.
    """

    def __init__(self):
        return

    def on_x_press(self):
        pass

    def on_x_release(self):
        pass

    def on_triangle_press(self):
        pass

    def on_triangle_release(self):
        pass

    def on_circle_press(self):
        pass

    def on_circle_release(self):
        pass

    def on_square_press(self):
        pass

    def on_square_release(self):
        pass

    def on_L1_press(self):
        pass

    def on_L1_release(self):
        pass

    def on_L2_press(self, value):
        pass

    def on_L2_release(self):
        pass

    def on_R1_press(self):
        pass

    def on_R1_release(self):
        pass

    def on_R2_press(self, value):
        pass

    def on_R2_release(self):
        pass

    def on_up_arrow_press(self):
        pass

    def on_up_down_arrow_release(self):
        pass

    def on_down_arrow_press(self):
        pass

    def on_left_arrow_press(self):
        pass

    def on_left_right_arrow_release(self):
        pass

    def on_right_arrow_press(self):
        pass

    def on_L3_up(self, value):
        pass

    def on_L3_down(self, value):
        pass

    def on_L3_left(self, value):
        pass

    def on_L3_right(self, value):
        pass

    def on_L3_y_at_rest(self):
        """L3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_L3_x_at_rest(self):
        """L3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_L3_press(self):
        """L3 joystick is clicked. This event is only detected when connecting without ds4drv"""
        pass

    def on_L3_release(self):
        """L3 joystick is released after the click. This event is only detected when connecting without ds4drv"""
        pass

    def on_R3_up(self, value):
        pass

    def on_R3_down(self, value):
        pass

    def on_R3_left(self, value):
        pass

    def on_R3_right(self, value):
        pass

    def on_R3_y_at_rest(self):
        """R3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_R3_x_at_rest(self):
        """R3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_R3_press(self):
        """R3 joystick is clicked. This event is only detected when connecting without ds4drv"""
        pass

    def on_R3_release(self):
        """R3 joystick is released after the click. This event is only detected when connecting without ds4drv"""
        pass

    def on_options_press(self):
        pass

    def on_options_release(self):
        pass

    def on_share_press(self):
        """this event is only detected when connecting without ds4drv"""
        pass

    def on_share_release(self):
        """this event is only detected when connecting without ds4drv"""
        pass

    def on_playstation_button_press(self):
        """this event is only detected when connecting without ds4drv"""
        pass

    def on_playstation_button_release(self):
        """this event is only detected when connecting without ds4drv"""
        pass


class Controller(Actions):
    def __init__(
        self,
        interface,
        connecting_using_ds4drv=True,
        event_definition=None,
        event_format=None,
    ):
        """
        Initiate controller instance that is capable of listening to all events on specified input interface
        :param interface: STRING aka /dev/input/js0 or any other PS4 Duelshock controller interface.
                          You can see all available interfaces with a command "ls -la /dev/input/"
        :param connecting_using_ds4drv: BOOLEAN. If you are connecting your controller using ds4drv, then leave it set
                                                 to True. Otherwise if you are connecting directly via directly via
                                                 bluetooth/bluetoothctl, set it to False otherwise the controller
                                                 button mapping will be off.
        """
        Actions.__init__(self)
        self.stop = False
        self.is_connected = False
        self.interface = interface
        self.connecting_using_ds4drv = connecting_using_ds4drv
        self.debug = False  # If you want to see raw event stream, set this to True.
        self.black_listed_buttons = []  # set a list of blocked buttons if you dont want to process their events
        if self.connecting_using_ds4drv and event_definition is None:
            # when device is connected via ds4drv its sending hundreds of events for those button IDs
            # thus they are blacklisted by default. Feel free to adjust this list to your linking when sub-classing
            self.black_listed_buttons += [6, 7, 8, 11, 12, 13]
        self.event_format = event_format if event_format else "3Bh2b"

        if event_definition is None:  # means it wasn't specified by user
            if self.event_format == "LhBB":
                from pyPS4Controller.event_mapping.DefaultMapping import DefaultMapping

                self.event_definition = DefaultMapping
            else:
                from pyPS4Controller.event_mapping.Mapping3Bh2b import Mapping3Bh2b

                self.event_definition = Mapping3Bh2b
        else:
            self.event_definition = event_definition

        self.event_size = struct.calcsize(self.event_format)
        self.event_history = []

        self.accelerating = False
        self.stopping = False

    def listen(self, timeout=30, on_connect=None, on_disconnect=None, on_sequence=None):
        """
        Start listening for events on a given self.interface
        :param timeout: INT, seconds. How long you want to wait for the self.interface.
                        This allows you to start listening and connect your controller after the fact.
                        If self.interface does not become available in N seconds, the script will exit with exit code 1.
        :param on_connect: function object, allows to register a call back when connection is established
        :param on_disconnect: function object, allows to register a call back when connection is lost
        :param on_sequence: list, allows to register a call back on specific input sequence.
                            e.g [{"inputs": ['up', 'up', 'down', 'down', 'left', 'right,
                                             'left', 'right, 'start', 'options'],
                                  "callback": () -> None)}]
        :return: None
        """

        def on_disconnect_callback():
            self.is_connected = False
            if on_disconnect is not None:
                on_disconnect()

        def on_connect_callback():
            self.is_connected = True
            if on_connect is not None:
                on_connect()

        def wait_for_interface():
            print(f"Waiting for interface: {self.interface} to become available . . .")
            for i in range(timeout):
                if os.path.exists(self.interface):
                    print(f"Successfully bound to: {self.interface}.")
                    on_connect_callback()
                    return
                time.sleep(1)
            print(f"Timeout({timeout} sec). Interface not available.")
            exit(1)

        def read_events():
            try:
                return _file.read(self.event_size)
            except OSError:
                print("Interface lost. Device disconnected?")
                on_disconnect_callback()
                exit(1)

        def check_for(sub, full, start_index):
            return [
                start
                for start in range(start_index, len(full) - len(sub) + 1)
                if sub == full[start : start + len(sub)]
            ]

        def unpack():
            __event = struct.unpack(self.event_format, event)
            return (__event[3:], __event[2], __event[1], __event[0])

        wait_for_interface()
        try:
            _file = open(self.interface, "rb")
            event = read_events()
            if on_sequence is None:
                on_sequence = []
            special_inputs_indexes = [0] * len(on_sequence)
            while not self.stop and event:
                (overflow, value, button_type, button_id) = unpack()
                event_mapped = self.map_event(
                    button_id, button_type, value, overflow, self.debug
                )
                logger.debug(f"Current speed: {self.cur_speed}, time: {time.time()}.")
                if self.accelerating:
                    logger.debug("Accelerating in controller.")
                    r2_value = None
                    if event_mapped.R2_pressed():
                        r2_value = event_mapped.value
                    logger.debug(f"Accelerating from controller with {r2_value}.")
                    self.on_R2_press(r2_value)
                if self.stopping:
                    logger.debug("Stopping in controller.")
                    self.on_R2_release()

                if button_id not in self.black_listed_buttons:
                    self.__handle_event(event_mapped)
                for i, special_input in enumerate(on_sequence):
                    check = check_for(
                        special_input["inputs"],
                        self.event_history,
                        special_inputs_indexes[i],
                    )
                    if len(check) != 0:
                        special_inputs_indexes[i] = check[0] + 1
                        special_input["callback"]()
                event = read_events()
        except KeyboardInterrupt:
            print("\nExiting (Ctrl + C)")
            on_disconnect_callback()
            exit(1)

    def map_event(self, button_id, button_type, value, overflow, debug):
        return self.event_definition(
            button_id=button_id,
            button_type=button_type,
            value=value,
            connecting_using_ds4drv=self.connecting_using_ds4drv,
            overflow=overflow,
            debug=debug,
        )

    def __handle_event(self, event):
        if event.R3_event():
            self.event_history.append("right_joystick")
            if event.R3_y_at_rest():
                self.on_R3_y_at_rest()
            elif event.R3_x_at_rest():
                self.on_R3_x_at_rest()
            elif event.R3_right():
                self.on_R3_right(event.value)
            elif event.R3_left():
                self.on_R3_left(event.value)
            elif event.R3_up():
                self.on_R3_up(event.value)
            elif event.R3_down():
                self.on_R3_down(event.value)
        elif event.L3_event():
            self.event_history.append("left_joystick")
            if event.L3_y_at_rest():
                self.on_L3_y_at_rest()
            elif event.L3_x_at_rest():
                self.on_L3_x_at_rest()
            elif event.L3_up():
                self.on_L3_up(event.value)
            elif event.L3_down():
                self.on_L3_down(event.value)
            elif event.L3_left():
                self.on_L3_left(event.value)
            elif event.L3_right():
                self.on_L3_right(event.value)
        elif event.circle_pressed():
            self.event_history.append("circle")
            self.on_circle_press()
        elif event.circle_released():
            self.on_circle_release()
        elif event.x_pressed():
            self.event_history.append("x")
            self.on_x_press()
        elif event.x_released():
            self.on_x_release()
        elif event.triangle_pressed():
            self.event_history.append("triangle")
            self.on_triangle_press()
        elif event.triangle_released():
            self.on_triangle_release()
        elif event.square_pressed():
            self.event_history.append("square")
            self.on_square_press()
        elif event.square_released():
            self.on_square_release()
        elif event.L1_pressed():
            self.event_history.append("L1")
            self.on_L1_press()
        elif event.L1_released():
            self.on_L1_release()
        elif event.L2_pressed():
            self.event_history.append("L2")
            self.on_L2_press(event.value)
        elif event.L2_released():
            self.on_L2_release()
        elif event.R1_pressed():
            self.event_history.append("R1")
            self.on_R1_press()
        elif event.R1_released():
            self.on_R1_release()
        # the acceleration should occur only once per cycle, hence the flags are necessary
        elif event.R2_pressed() and not self.accelerating:
            self.event_history.append("R2")
            self.on_R2_press(event.value)
        elif event.R2_released() and not self.stopping:
            self.on_R2_release()
        elif event.options_pressed():
            self.event_history.append("options")
            self.on_options_press()
        elif event.options_released():
            self.on_options_release()
        elif event.left_right_arrow_released():
            self.on_left_right_arrow_release()
        elif event.up_down_arrow_released():
            self.on_up_down_arrow_release()
        elif event.left_arrow_pressed():
            self.event_history.append("left")
            self.on_left_arrow_press()
        elif event.right_arrow_pressed():
            self.event_history.append("right")
            self.on_right_arrow_press()
        elif event.up_arrow_pressed():
            self.event_history.append("up")
            self.on_up_arrow_press()
        elif event.down_arrow_pressed():
            self.event_history.append("down")
            self.on_down_arrow_press()
        elif event.playstation_button_pressed():
            self.event_history.append("ps")
            self.on_playstation_button_press()
        elif event.playstation_button_released():
            self.on_playstation_button_release()
        elif event.share_pressed():
            self.event_history.append("share")
            self.on_share_press()
        elif event.share_released():
            self.on_share_release()
        elif event.R3_pressed():
            self.event_history.append("R3")
            self.on_R3_press()
        elif event.R3_released():
            self.on_R3_release()
        elif event.L3_pressed():
            self.event_history.append("L3")
            self.on_L3_press()
        elif event.L3_released():
            self.on_L3_release()
