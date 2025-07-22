# -*- coding: utf-8 -*-
from threading import Thread
import time
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from dobot_api import *
import json
from files.alarm_controller import alarm_controller_list
from files.alarm_servo import alarm_servo_list

LABEL_JOINT = [["J1-", "J2-", "J3-", "J4-", "J5-", "J6-"],
               ["J1:", "J2:", "J3:", "J4:", "J5:", "J6:"],
               ["J1+", "J2+", "J3+", "J4+", "J5+", "J6+"]]

LABEL_COORD = [["X-", "Y-", "Z-", "Rx-", "Ry-", "Rz-"],
               ["X:", "Y:", "Z:", "Rx:", "Ry:", "Rz:"],
               ["X+", "Y+", "Z+", "Rx+", "Ry+", "Rz+"]]

LABEL_ROBOT_MODE = {
    1: "ROBOT_MODE_INIT",
    2: "ROBOT_MODE_BRAKE_OPEN",
    3: "",
    4: "ROBOT_MODE_DISABLED",
    5: "ROBOT_MODE_ENABLE",
    6: "ROBOT_MODE_BACKDRIVE",
    7: "ROBOT_MODE_RUNNING",
    8: "ROBOT_MODE_RECORDING",
    9: "ROBOT_MODE_ERROR",
    10: "ROBOT_MODE_PAUSE",
    11: "ROBOT_MODE_JOG"
}


class RobotUI(object):

    def __init__(self):
        self.root = Tk()
        self.root.title("Sample Picker V1")
        # fixed window size
        self.root.geometry("900x1100")
        # set window icon
        self.root.iconbitmap("images/robot.ico")

        # Create main container frame
        self.main_container = Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=1)

        # Create canvas with scrollbar
        self.canvas = Canvas(self.main_container)
        self.scrollbar = Scrollbar(self.main_container, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas which will be scrolled with it
        self.scrollable_frame = Frame(self.canvas)

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure scrolling with mouse wheel
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.root.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.root.bind("<Button-4>", self.on_mousewheel)  # Linux scroll up
        self.root.bind("<Button-5>", self.on_mousewheel)  # Linux scroll down

        # global state dict
        self.global_state = {}

        # all button
        self.button_list = []

        # all entry
        self.entry_dict = {}

        # Robot Connect
        self.frame_robot = LabelFrame(self.scrollable_frame, text="Robot Connect",
                                      labelanchor="nw", bg="#FFFFFF", width=870, height=120, border=2)

        self.label_ip = Label(self.frame_robot, text="IP Address:")
        self.label_ip.place(rely=0.2, x=10)
        ip_port = StringVar(self.root, value="192.168.5.1")
        self.entry_ip = Entry(self.frame_robot, width=12, textvariable=ip_port)
        self.entry_ip.place(rely=0.2, x=90)

        self.label_dash = Label(self.frame_robot, text="Dashboard Port:")
        self.label_dash.place(rely=0.2, x=210)
        dash_port = IntVar(self.root, value=29999)
        self.entry_dash = Entry(
            self.frame_robot, width=7, textvariable=dash_port)
        self.entry_dash.place(rely=0.2, x=320)

        self.label_move = Label(self.frame_robot, text="Move Port:")
        self.label_move.place(rely=0.2, x=400)
        move_port = IntVar(self.root, value=30003)
        self.entry_move = Entry(
            self.frame_robot, width=7, textvariable=move_port)
        self.entry_move.place(rely=0.2, x=480)

        self.label_feed = Label(self.frame_robot, text="Feedback Port:")
        self.label_feed.place(rely=0.2, x=580)
        feed_port = IntVar(self.root, value=30004)
        self.entry_feed = Entry(
            self.frame_robot, width=7, textvariable=feed_port)
        self.entry_feed.place(rely=0.2, x=680)

        # Connect/DisConnect
        self.button_connect = self.set_button(master=self.frame_robot,
                                              text="Connect", rely=0.6, x=630, command=self.connect_port)
        self.button_connect["width"] = 10
        self.global_state["connect"] = False

        # Dashboard Function
        self.frame_dashboard = LabelFrame(self.scrollable_frame, text="Dashboard Function",
                                          labelanchor="nw", bg="#FFFFFF", pady=10, width=870, height=120, border=2)

        # Enable/Disable
        self.button_enable = self.set_button(master=self.frame_dashboard,
                                             text="Enable", rely=0.1, x=10, command=self.enable)
        self.button_enable["width"] = 7
        self.global_state["enable"] = False

        # Reset Robot / Clear Error / Continue
        self.set_button(master=self.frame_dashboard,
                        text="ResetRobot", rely=0.1, x=90, command=self.reset_robot)
        self.set_button(master=self.frame_dashboard,
                        text="ClearError", rely=0.1, x=200, command=self.clear_error)
        self.set_button(master=self.frame_dashboard,
                        text=" Continue ", rely=0.1, x=300, command=self.Continue)
        self.set_button(master=self.frame_dashboard,
                        text="PowerOn", rely=0.1, x=390, command=self.PowerOn)

        # Speed Ratio
        self.label_speed = Label(self.frame_dashboard, text="Speed Ratio:")
        self.label_speed.place(rely=0.1, x=480)

        s_value = StringVar(self.root, value="50")
        self.entry_speed = Entry(self.frame_dashboard,
                                 width=6, textvariable=s_value)
        self.entry_speed.place(rely=0.1, x=570)
        self.label_cent = Label(self.frame_dashboard, text="%")
        self.label_cent.place(rely=0.1, x=620)

        self.set_button(master=self.frame_dashboard,
                        text="Confirm", rely=0.1, x=586, command=self.confirm_speed)

        # DO:Digital Outputs
        self.label_digitial = Label(
            self.frame_dashboard, text="Digital Outputs: Index:")
        self.label_digitial.place(rely=0.55, x=10)

        i_value = IntVar(self.root, value="1")
        self.entry_index = Entry(
            self.frame_dashboard, width=5, textvariable=i_value)
        self.entry_index.place(rely=0.55, x=160)

        self.label_status = Label(self.frame_dashboard, text="Status:")
        self.label_status.place(rely=0.55, x=220)

        self.combo_status = ttk.Combobox(self.frame_dashboard, width=5)
        self.combo_status["value"] = ("On", "Off")
        self.combo_status.current(0)
        self.combo_status["state"] = "readonly"
        self.combo_status.place(rely=0.55, x=275)

        self.set_button(self.frame_dashboard, "Confirm",
                        rely=0.55, x=350, command=self.confirm_do)

        # Move Function
        self.frame_move = LabelFrame(self.scrollable_frame, text="Move Function", labelanchor="nw",
                                     bg="#FFFFFF", width=870, pady=10, height=130, border=2)

        self.set_move(text="X:", label_value=10,
                      default_value="600", entry_value=40, rely=0.1, master=self.frame_move)
        self.set_move(text="Y:", label_value=110,
                      default_value="-260", entry_value=140, rely=0.1, master=self.frame_move)
        self.set_move(text="Z:", label_value=210,
                      default_value="380", entry_value=240, rely=0.1, master=self.frame_move)
        self.set_move(text="Rx:", label_value=310,
                      default_value="170", entry_value=340, rely=0.1, master=self.frame_move)
        self.set_move(text="Ry:", label_value=410,
                      default_value="12", entry_value=440, rely=0.1, master=self.frame_move)
        self.set_move(text="Rz:", label_value=510,
                      default_value="140", entry_value=540, rely=0.1, master=self.frame_move)

        self.set_button(master=self.frame_move, text="MovJ",
                        rely=0.05, x=610, command=self.movj)
        self.set_button(master=self.frame_move, text="MovL",
                        rely=0.05, x=700, command=self.movl)

        self.set_move(text="J1:", label_value=10,
                      default_value="0", entry_value=40, rely=0.5, master=self.frame_move)
        self.set_move(text="J2:", label_value=110,
                      default_value="-20", entry_value=140, rely=0.5, master=self.frame_move)
        self.set_move(text="J3:", label_value=210,
                      default_value="-80", entry_value=240, rely=0.5, master=self.frame_move)
        self.set_move(text="J4:", label_value=310,
                      default_value="30", entry_value=340, rely=0.5, master=self.frame_move)
        self.set_move(text="J5:", label_value=410,
                      default_value="90", entry_value=440, rely=0.5, master=self.frame_move)
        self.set_move(text="J6:", label_value=510,
                      default_value="120", entry_value=540, rely=0.5, master=self.frame_move)

        self.set_button(master=self.frame_move,
                        text="JointMovJ", rely=0.45, x=610, command=self.joint_movj)

        self.frame_feed_log = Frame(
            self.scrollable_frame, bg="#FFFFFF", width=870, pady=10, height=400, border=2)
        # Feedback
        self.frame_feed = LabelFrame(self.frame_feed_log, text="Feedback", labelanchor="nw",
                                     bg="#FFFFFF", width=550, height=150)

        self.frame_feed.place(relx=0, rely=0, relheight=1)

        # Current Speed Ratio
        self.set_label(self.frame_feed,
                       text="Current Speed Ratio:", rely=0.05, x=10)
        self.label_feed_speed = self.set_label(
            self.frame_feed, "", rely=0.05, x=145)
        self.set_label(self.frame_feed, text="%", rely=0.05, x=175)

        # Robot Mode
        self.set_label(self.frame_feed, text="Robot Mode:", rely=0.1, x=10)
        self.label_robot_mode = self.set_label(
            self.frame_feed, "", rely=0.1, x=95)

        # 点动及获取坐标
        self.label_feed_dict = {}
        self.set_feed(LABEL_JOINT, 9, 52, 74, 117)
        self.set_feed(LABEL_COORD, 165, 209, 231, 272)

        # Digitial I/O
        self.set_label(self.frame_feed, "Digital Inputs:", rely=0.8, x=11)
        self.label_di_input = self.set_label(
            self.frame_feed, "", rely=0.8, x=100)
        self.set_label(self.frame_feed, "Digital Outputs:", rely=0.85, x=10)
        self.label_di_output = self.set_label(
            self.frame_feed, "", rely=0.85, x=100)

        # Error Info
        self.frame_err = LabelFrame(self.frame_feed, text="Error Info", labelanchor="nw",
                                    bg="#FFFFFF", width=180, height=50)
        self.frame_err.place(relx=0.65, rely=0, relheight=0.7)

        self.text_err = ScrolledText(
            self.frame_err, width=170, height=50, relief="flat")
        self.text_err.place(rely=0, relx=0, relheight=0.7, relwidth=1)

        self.set_button(self.frame_feed, "Clear", rely=0.71,
                        x=487, command=self.clear_error_info)

        # Log
        self.frame_log = LabelFrame(self.frame_feed_log, text="Log", labelanchor="nw",
                                    bg="#FFFFFF", width=300, height=150)
        self.frame_log.place(relx=0.65, rely=0, relheight=1)

        self.text_log = ScrolledText(
            self.frame_log, width=270, height=140, relief="flat")
        self.text_log.place(rely=0, relx=0, relheight=1, relwidth=1)

        # initial client
        self.client_dash = None
        self.client_move = None
        self.client_feed = None

        self.alarm_controller_dict = self.convert_dict(alarm_controller_list)
        self.alarm_servo_dict = self.convert_dict(alarm_servo_list)

        ################################ movement test AB with button
        # --- Vial Position Definitions ---
        # Each position is [X, Y, Z, Rx, Ry, Rz] Rx,Ry,Rz should Ideally be at 0,0,145

        self.pos_1a = [300, 30, 360, 0, 0, 145]  # Go above vial 1
        self.pos_1b = [300, 30, 420, 0, 0, 145]  # Go into vial 1

        self.pos_2a = [300, 70, 360, 0, 0, 145]
        self.pos_2b = [300, 70, 420, 0, 0, 145]

        self.pos_3a = [300, 100, 360, 0, 0, 145]
        self.pos_3b = [300, 100, 420, 0, 0, 145]

        self.pos_4a = [215, 375, 350, 0, 0, 145]
        self.pos_4b = [215, 375, 450, 0, 0, 145]

        self.pos_5a = [425, -161, 365, 0, 0, 145]
        self.pos_5b = [425, -161, 400, 0, 0, 145]

        self.pos_6a = [425, -166, 365, 0, 0, 145]
        self.pos_6b = [425, -166, 400, 0, 0, 145]

        self.pos_7a = [425, -171, 365, 0, 0, 145]
        self.pos_7b = [425, -171, 400, 0, 0, 145]

        self.pos_8a = [425, -176, 365, 0, 0, 145]
        self.pos_8b = [425, -176, 400, 0, 0, 145]

        self.pos_9a = [425, -181, 365, 0, 0, 145]
        self.pos_9b = [425, -181, 400, 0, 0, 145]

        self.pos_10a = [425, -186, 365, 0, 0, 145]
        self.pos_10b = [425, -186, 400, 0, 0, 145]

        # --- Vial Button Grid ---
        self.frame_vial_buttons = Frame(self.scrollable_frame, bg="#FFFFFF", width=870, height=100)
        self.frame_vial_buttons.pack(pady=10)  # Use pack instead of place

        columns = 5  # Number of buttons per row
        button_width = 15
        button_padding_x = 10
        button_padding_y = 10

        for i in range(10):  # Vials 1 to 10
            vial_num = i + 1
            row = i // columns
            col = i % columns

            button = Button(
                self.frame_vial_buttons,
                text=f"Move to Vial {vial_num}",
                width=button_width,
                command=lambda n=vial_num: self.move_to_vial(n)
            )
            button.grid(row=row, column=col, padx=button_padding_x, pady=button_padding_y)

        # Disable until connected, then auto-enable like others
        button["state"] = "disable"
        self.button_list.append(button)

        # set to not currently in a vial
        self.current_vial = None
        # (JD) picking sequence##########################################

        self.sequence_queue = []
        self.sequence_running = False
        self.sequence_paused = False

        # UI elements for vial/wait input
        # === Sequence Input Section ===
        sequence_frame = Frame(self.scrollable_frame, bg="#FFFFFF", width=870)
        sequence_frame.pack(pady=10, fill=X)

        input_frame = Frame(sequence_frame, bg="#FFFFFF")
        input_frame.pack(pady=5)

        Label(input_frame, text="Vial #").pack(side=LEFT, padx=5)
        self.entry_vial_number = Entry(input_frame, width=5)
        self.entry_vial_number.pack(side=LEFT, padx=5)

        Label(input_frame, text="Wait (s)").pack(side=LEFT, padx=5)
        self.entry_wait_time = Entry(input_frame, width=5)
        self.entry_wait_time.pack(side=LEFT, padx=5)

        Label(input_frame, text="Label").pack(side=LEFT, padx=5)
        self.entry_vial_label = Entry(input_frame, width=15)
        self.entry_vial_label.pack(side=LEFT, padx=5)

        self.btn_add_to_queue = Button(input_frame, text="Add to Queue", command=self.add_to_sequence)
        self.btn_add_to_queue.pack(side=LEFT, padx=10)

        # Button frames
        button_frame = Frame(sequence_frame, bg="#FFFFFF")
        button_frame.pack(pady=5)

        # First row of buttons
        self.btn_run_sequence = Button(button_frame, text="Run", width=8, command=self.run_sequence)
        self.btn_run_sequence.pack(side=LEFT, padx=5)

        self.btn_pause_sequence = Button(button_frame, text="Pause", width=8, command=self.pause_sequence)
        self.btn_pause_sequence.pack(side=LEFT, padx=5)

        self.btn_resume_sequence = Button(button_frame, text="Resume", width=8, command=self.resume_sequence)
        self.btn_resume_sequence.pack(side=LEFT, padx=5)

        self.btn_cancel_sequence = Button(button_frame, text="Cancel", width=8, command=self.cancel_sequence)
        self.btn_cancel_sequence.pack(side=LEFT, padx=5)

        self.btn_clear_queue = Button(button_frame, text="Clear", width=8, command=self.clear_sequence)
        self.btn_clear_queue.pack(side=LEFT, padx=5)

        self.btn_remove_last = Button(button_frame, text="Remove", width=10, command=self.remove_last_from_sequence)
        self.btn_remove_last.pack(side=LEFT, padx=5)

        self.btn_save_sequence = Button(button_frame, text="Save", width=8, command=self.save_sequence)
        self.btn_save_sequence.pack(side=LEFT, padx=5)

        self.btn_load_sequence = Button(button_frame, text="Load", width=8, command=self.load_sequence)
        self.btn_load_sequence.pack(side=LEFT, padx=5)

        # Sequence Display
        display_frame = Frame(sequence_frame, bg="#FFFFFF")
        display_frame.pack(pady=5, fill=X)

        Label(display_frame, text="Sequence Preview:").pack(anchor=W)
        self.sequence_display = ScrolledText(display_frame, width=75, height=6)
        self.sequence_display.pack(fill=X, pady=5)

        # Reset button
        self.btn_reset_robot = Button(
            sequence_frame,
            text="🔄 Reset Dobot",
            command=self.reset_robot
        )
        self.btn_reset_robot.pack(anchor=E, padx=20, pady=5)
        ##############################################################
        self.root.protocol("WM_DELETE_WINDOW", self.safe_shutdown)

    ################################################################
    def convert_dict(self, alarm_list):
        alarm_dict = {}
        for i in alarm_list:
            alarm_dict[i["id"]] = i
        return alarm_dict

    def read_file(self, path):
        # 读json文件耗时大，选择维护两个变量alarm_controller_list alarm_servo_list
        # self.read_file("files/alarm_controller.json")
        with open(path, "r", encoding="utf8") as fp:
            json_data = json.load(fp)
        return json_data

    def mainloop(self):
        self.root.mainloop()

    def pack(self):
        self.frame_robot.pack(in_=self.scrollable_frame, fill=X)
        self.frame_dashboard.pack(in_=self.scrollable_frame, fill=X)
        self.frame_move.pack(in_=self.scrollable_frame, fill=X)
        self.frame_feed_log.pack(in_=self.scrollable_frame, fill=X)

    def set_move(self, text, label_value, default_value, entry_value, rely, master):
        self.label = Label(master, text=text)
        self.label.place(rely=rely, x=label_value)
        value = StringVar(self.root, value=default_value)
        self.entry_temp = Entry(master, width=6, textvariable=value)
        self.entry_temp.place(rely=rely, x=entry_value)
        self.entry_dict[text] = self.entry_temp

    def move_jog(self, text):
        if self.global_state["connect"]:
            self.client_move.MoveJog(text)

    def move_stop(self, event):
        if self.global_state["connect"]:
            self.client_move.MoveJog("")

    def set_button(self, master, text, rely, x, **kargs):
        self.button = Button(master, text=text, padx=5,
                             command=kargs["command"])
        self.button.place(rely=rely, x=x)

        if text != "Connect":
            self.button["state"] = "disable"
            self.button_list.append(self.button)
        return self.button

    def set_button_bind(self, master, text, rely, x, **kargs):
        self.button = Button(master, text=text, padx=5)
        self.button.bind("<ButtonPress-1>",
                         lambda event: self.move_jog(text=text))
        self.button.bind("<ButtonRelease-1>", self.move_stop)
        self.button.place(rely=rely, x=x)

        if text != "Connect":
            self.button["state"] = "disable"
            self.button_list.append(self.button)
        return self.button

    def set_label(self, master, text, rely, x):
        self.label = Label(master, text=text)
        self.label.place(rely=rely, x=x)
        return self.label

    def connect_port(self):
        if self.global_state["connect"]:
            print("断开成功")
            self.client_dash.close()
            self.client_feed.close()
            self.client_move.close()
            self.client_dash = None
            self.client_feed = None
            self.client_move = None

            for i in self.button_list:
                i["state"] = "disable"
            self.button_connect["text"] = "Connect"
        else:
            try:
                print("连接成功")
                self.client_dash = DobotApiDashboard(
                    self.entry_ip.get(), int(self.entry_dash.get()), self.text_log)
                self.client_move = DobotApiMove(
                    self.entry_ip.get(), int(self.entry_move.get()), self.text_log)
                self.client_feed = DobotApi(
                    self.entry_ip.get(), int(self.entry_feed.get()), self.text_log)
            except Exception as e:
                messagebox.showerror("Attention!", f"Connection Error:{e}")
                return

            for i in self.button_list:
                i["state"] = "normal"
            self.button_connect["text"] = "Disconnect"
        self.global_state["connect"] = not self.global_state["connect"]
        self.set_feed_back()

    def set_feed_back(self):
        if self.global_state["connect"]:
            thread = Thread(target=self.feed_back)
            thread.setDaemon(True)
            thread.start()

    def enable(self):
        try:
            print("=== Enable button clicked ===")
            print("Current state:", self.global_state["enable"])

            if self.global_state["enable"]:
                print("Disabling robot...")
                # Save position
                data = self.client_feed.socket_dobot.recv(1440)
                a = np.frombuffer(data, dtype=MyType)
                self.last_known_origin = a["tool_vector_actual"][0].copy()
                print("Saved origin:", self.last_known_origin)

                self.client_dash.DisableRobot()
                self.button_enable["text"] = "Enable"
                self.global_state["enable"] = False
                print("Robot disabled")

            else:
                print("Enabling robot...")
                self.client_dash.EnableRobot()
                time.sleep(1)
                error_id = self.client_dash.GetErrorID()
                print("Error ID:", error_id)

                if error_id and error_id != '{"controller": [], "servo": []}':
                    messagebox.showerror("Robot Error", f"Robot is in error state:\n{error_id}")
                    self.button_enable["text"] = "Enable"
                    print("Robot has error, aborting enable.")
                    return

            # Get new origin
                data = self.client_feed.socket_dobot.recv(1440)
                a = np.frombuffer(data, dtype=MyType)
                new_origin = a["tool_vector_actual"][0]
                print("New origin:", new_origin)

                if hasattr(self, "last_known_origin"):
                    offset = new_origin - self.last_known_origin
                    print("Offset:", offset)
                    self.recalibrate_positions(offset)

                self.button_enable["text"] = "Disable"
                self.global_state["enable"] = True
                print("Robot enabled")

            print("Updated state:", self.global_state["enable"])
            print("Button label:", self.button_enable["text"])

        except Exception as e:
            print("Exception:", e)
            messagebox.showerror("Enable/Disable Error", str(e))

    def reset_robot(self):
        self.client_dash.ResetRobot()

    def clear_error(self):
        self.client_dash.ClearError()

    def Continue(self):
        self.client_dash.Continue()

    def PowerOn(self):
        self.client_dash.PowerOn()

    def confirm_speed(self):
        self.client_dash.SpeedFactor(int(self.entry_speed.get()))

    def movj(self):
        self.client_move.MovJ(float(self.entry_dict["X:"].get()), float(self.entry_dict["Y:"].get()),
                              float(self.entry_dict["Z:"].get()),
                              float(self.entry_dict["Rx:"].get()), float(self.entry_dict["Ry:"].get()),
                              float(self.entry_dict["Rz:"].get()))

    def movl(self):
        self.client_move.MovL(float(self.entry_dict["X:"].get()), float(self.entry_dict["Y:"].get()),
                              float(self.entry_dict["Z:"].get()),
                              float(self.entry_dict["Rx:"].get()), float(self.entry_dict["Ry:"].get()),
                              float(self.entry_dict["Rz:"].get()))

    def joint_movj(self):
        self.client_move.JointMovJ(float(self.entry_dict["J1:"].get()), float(self.entry_dict["J2:"].get()),
                                   float(self.entry_dict["J3:"].get()),
                                   float(self.entry_dict["J4:"].get()), float(self.entry_dict["J5:"].get()),
                                   float(self.entry_dict["J6:"].get()))

    def confirm_do(self):
        if self.combo_status.get() == "On":
            print("高电平")
            self.client_dash.DO(int(self.entry_index.get()), 1)
        else:
            print("低电平")
            self.client_dash.DO(int(self.entry_index.get()), 0)

    def set_feed(self, text_list, x1, x2, x3, x4):
        self.set_button_bind(
            self.frame_feed, text_list[0][0], rely=0.2, x=x1, command=lambda: self.move_jog(text_list[0][0]))
        self.set_button_bind(
            self.frame_feed, text_list[0][1], rely=0.3, x=x1, command=lambda: self.move_jog(text_list[0][1]))
        self.set_button_bind(
            self.frame_feed, text_list[0][2], rely=0.4, x=x1, command=lambda: self.move_jog(text_list[0][2]))
        self.set_button_bind(
            self.frame_feed, text_list[0][3], rely=0.5, x=x1, command=lambda: self.move_jog(text_list[0][3]))
        self.set_button_bind(
            self.frame_feed, text_list[0][4], rely=0.6, x=x1, command=lambda: self.move_jog(text_list[0][4]))
        self.set_button_bind(
            self.frame_feed, text_list[0][5], rely=0.7, x=x1, command=lambda: self.move_jog(text_list[0][5]))

        self.set_label(self.frame_feed, text_list[1][0], rely=0.21, x=x2)
        self.set_label(self.frame_feed, text_list[1][1], rely=0.31, x=x2)
        self.set_label(self.frame_feed, text_list[1][2], rely=0.41, x=x2)
        self.set_label(self.frame_feed, text_list[1][3], rely=0.51, x=x2)
        self.set_label(self.frame_feed, text_list[1][4], rely=0.61, x=x2)
        self.set_label(self.frame_feed, text_list[1][5], rely=0.71, x=x2)

        self.label_feed_dict[text_list[1][0]] = self.set_label(
            self.frame_feed, " ", rely=0.21, x=x3)
        self.label_feed_dict[text_list[1][1]] = self.set_label(
            self.frame_feed, " ", rely=0.31, x=x3)
        self.label_feed_dict[text_list[1][2]] = self.set_label(
            self.frame_feed, " ", rely=0.41, x=x3)
        self.label_feed_dict[text_list[1][3]] = self.set_label(
            self.frame_feed, " ", rely=0.51, x=x3)
        self.label_feed_dict[text_list[1][4]] = self.set_label(
            self.frame_feed, " ", rely=0.61, x=x3)
        self.label_feed_dict[text_list[1][5]] = self.set_label(
            self.frame_feed, " ", rely=0.71, x=x3)

        self.set_button_bind(
            self.frame_feed, text_list[2][0], rely=0.2, x=x4, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][1], rely=0.3, x=x4, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][2], rely=0.4, x=x4, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][3], rely=0.5, x=x4, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][4], rely=0.6, x=x4, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][5], rely=0.7, x=x4, command=lambda: self.move_jog(text_list[2][0]))

    def feed_back(self):
        hasRead = 0
        while True:
            print("self.global_state(connect)", self.global_state["connect"])
            if not self.global_state["connect"]:
                break
            data = bytes()
            while hasRead < 1440:
                temp = self.client_feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            a = np.frombuffer(data, dtype=MyType)
            print("robot_mode:", a["robot_mode"][0])
            print("test_value:", hex((a['test_value'][0])))
            if hex((a['test_value'][0])) == '0x123456789abcdef':
                # print('tool_vector_actual',
                #       np.around(a['tool_vector_actual'], decimals=4))
                # print('q_actual', np.around(a['q_actual'], decimals=4))

                # Refresh Properties
                self.label_feed_speed["text"] = a["speed_scaling"][0]
                self.label_robot_mode["text"] = LABEL_ROBOT_MODE[a["robot_mode"][0]]
                self.label_di_input["text"] = bin(a["digital_input_bits"][0])[
                                              2:].rjust(64, '0')
                self.label_di_output["text"] = bin(a["digital_output_bits"][0])[
                                               2:].rjust(64, '0')

                # Refresh coordinate points
                self.set_feed_joint(LABEL_JOINT, a["q_actual"])
                self.set_feed_joint(LABEL_COORD, a["tool_vector_actual"])

                # check alarms
                if a["robot_mode"] == 9:
                    self.display_error_info()

            time.sleep(0.005)

    def display_error_info(self):
        error_list = self.client_dash.GetErrorID().split("{")[1].split("}")[0]

        error_list = json.loads(error_list)
        print("error_list:", error_list)
        if error_list[0]:
            for i in error_list[0]:
                self.form_error(i, self.alarm_controller_dict,
                                "Controller Error")

        for m in range(1, len(error_list)):
            if error_list[m]:
                for n in range(len(error_list[m])):
                    self.form_error(n, self.alarm_servo_dict, "Servo Error")

    def form_error(self, index, alarm_dict: dict, type_text):
        if index in alarm_dict.keys():
            date = datetime.datetime.now().strftime("%Y.%m.%d:%H:%M:%S ")
            error_info = f"Time Stamp:{date}\n"
            error_info = error_info + f"ID:{index}\n"
            error_info = error_info + \
                         f"Type:{type_text}\nLevel:{alarm_dict[index]['level']}\n" + \
                         f"Solution:{alarm_dict[index]['en']['solution']}\n"

            self.text_err.insert(END, error_info)

    def clear_error_info(self):
        self.text_err.delete("1.0", "end")

    def set_feed_joint(self, label, value):
        array_value = np.around(value, decimals=4)
        self.label_feed_dict[label[1][0]]["text"] = array_value[0][0]
        self.label_feed_dict[label[1][1]]["text"] = array_value[0][1]
        self.label_feed_dict[label[1][2]]["text"] = array_value[0][2]
        self.label_feed_dict[label[1][3]]["text"] = array_value[0][3]
        self.label_feed_dict[label[1][4]]["text"] = array_value[0][4]
        self.label_feed_dict[label[1][5]]["text"] = array_value[0][5]

    ################(JD) Set movement into vial

    def move_to_vial(self, vial_number):
        if not self.global_state.get("connect"):
            messagebox.showwarning("Connection", "Robot not connected!")
            return

        # Target vial positions
        top_pos = getattr(self, f"pos_{vial_number}a", None)
        bottom_pos = getattr(self, f"pos_{vial_number}b", None)

        if top_pos is None or bottom_pos is None:
            messagebox.showerror("Error", f"Positions for vial {vial_number} not defined.")
            return

        # Optional: Gentle motion settings
        self.client_dash.SpeedFactor(30)
        self.client_dash.AccL(10)
        self.client_dash.SpeedL(10)

        # If already in a vial, retract vertically (go to current vial's 'a' position)
        if self.current_vial is not None:
            current_top = getattr(self, f"pos_{self.current_vial}a", None)
            if current_top:
                self.client_move.MovL(*current_top)
                time.sleep(1)

        # Now proceed to new vial
        self.client_move.MovL(*top_pos)  # move above target
        time.sleep(2)
        self.client_move.MovL(*bottom_pos)  # move into target

        # Update current vial
        self.current_vial = vial_number

    #######(JD) Sequence##################################
    def add_to_sequence(self):
        try:
            vial = int(self.entry_vial_number.get())
            wait = float(self.entry_wait_time.get())
            label = self.entry_vial_label.get().strip()
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        self.sequence_queue.append((vial, wait, label))
        self.update_sequence_display()

    def update_sequence_display(self, highlight_index=None):
        self.sequence_display.delete("1.0", END)
        for i, (vial, wait, label) in enumerate(self.sequence_queue):
            text = f"{i + 1}. Vial {vial} ({label}) → wait {wait}s\n"
            self.sequence_display.insert(END, text)

        if highlight_index is not None:
            start = f"{highlight_index + 1}.0"
            end = f"{highlight_index + 1}.end"
            self.sequence_display.tag_add("highlight", start, end)
            self.sequence_display.tag_config("highlight", background="yellow", foreground="black")

    def run_sequence(self):
        if not self.global_state.get("connect"):
            messagebox.showwarning("Connection", "Robot not connected!")
            return

        if self.sequence_running:
            messagebox.showinfo("Info", "Sequence already running.")
            return

        self.sequence_running = True
        self.sequence_paused = False

        def sequence_thread():
            for index, (vial, wait_time, label) in enumerate(self.sequence_queue):
                if not self.sequence_running:
                    break

                while self.sequence_paused:
                    time.sleep(0.1)

                self.update_sequence_display(highlight_index=index)

                self.move_to_vial(vial)

                for _ in range(int(wait_time * 10)):
                    if not self.sequence_running:
                        break
                    while self.sequence_paused:
                        time.sleep(0.1)
                    time.sleep(0.1)

            self.sequence_running = False
            self.sequence_queue.clear()
            self.update_sequence_display()

        Thread(target=sequence_thread).start()

    def clear_sequence(self):
        self.sequence_queue.clear()
        self.update_sequence_display()

    def remove_last_from_sequence(self):
        if self.sequence_queue:
            self.sequence_queue.pop()
            self.update_sequence_display()

    def save_sequence(self):
        try:
            with open("sequence.json", "w") as f:
                json.dump(self.sequence_queue, f)
            messagebox.showinfo("Saved", "Sequence saved to sequence.json")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_sequence(self):
        try:
            with open("sequence.json", "r") as f:
                self.sequence_queue = json.load(f)
                self.update_sequence_display()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def pause_sequence(self):
        if self.sequence_running:
            self.sequence_paused = True

    def resume_sequence(self):
        if self.sequence_running and self.sequence_paused:
            self.sequence_paused = False

    def cancel_sequence(self):
        self.sequence_running = False
        self.sequence_paused = False
        self.update_sequence_display()

    ######################################################

    def safe_shutdown(self):
        if not messagebox.askokcancel("Quit", "Do you really want to exit?"):
            return  # User canceled exit

        try:
            if self.text_log:
                self.text_log.insert(END, "Shutting down...\n")
                self.text_log.see(END)

            if self.client_dash:
                self.client_dash.DisableRobot()
                self.client_dash.Close()
            if self.client_move:
                self.client_move.Close()
            if self.client_feed:
                self.client_feed.Close()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            self.root.destroy()

    def reset_robot(self):
        try:
            self.client_dash.ClearError()
            self.client_dash.DisableRobot()
            time.sleep(1)
            self.client_dash.EnableRobot()
            messagebox.showinfo("Reset", "Robot has been reset.")
        except Exception as e:
            messagebox.showerror("Reset Failed", str(e))

    def on_canvas_configure(self, event):
        # 设置滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # 调整 scrollable_frame 宽度适应 canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

        # 计算居中偏移
        frame_width = self.scrollable_frame.winfo_reqwidth()
        x_offset = max((canvas_width - frame_width) // 2, 0)

        # 设置 frame 的新坐标，居中放置
        self.canvas.coords(self.canvas_frame, x_offset, 0)

    def on_frame_configure(self, event):
        """Reset the canvas window to encompass inner frame when required"""
        # Update the width of the canvas window to fit the inner frame
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        """Scroll canvas view when mouse wheel is rotated"""
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, "units")
            
    def recalibrate_positions(self, offset):
        for attr in dir(self):
            if attr.startswith("pos_") and isinstance(getattr(self, attr), list):
                pos = getattr(self, attr)
                adjusted = [pos[i] + offset[i] for i in range(6)]
                setattr(self, attr, adjusted)