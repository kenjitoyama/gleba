#!/usr/bin/python
"""
This is the main client the end-user will interact with.
"""
from gi.repository import Gtk
from gi.repository import Gdk
from threading import Thread
import time
import gobject
import utils
import pygst
pygst.require("0.10")
import gst
import os
import config

gobject.threads_init()

DB = utils.DBAPI()

STATUS_MESSAGES = ['Awaiting\nbatch',
                  'Awaiting\nbox',
                  'Awaiting\npicker',
                  'Awaiting\nvariety',
                  'Overweight,\nAdjust',
                  'Underweight,\nAdjust',
                  'Awaiting\nconfirmation',
                  'Remove box']
AWAITING_BATCH = 0
AWAITING_BOX = 1
AWAITING_PICKER = 2
AWAITING_VARIETY = 3
OVERWEIGHT_ADJUST = 4
UNDERWEIGHT_ADJUST = 5
AWAITING_CONFIRMATION = 6
REMOVE_BOX = 7

WINDOWW = config.WINDOW_WIDTH
WINDOWH = config.WINDOW_HEIGHT

class MainWindow(Gtk.Window):
    save_weight = False
    weight_color = config.WHITE_COLOR
    current_batch = None
    current_picker = None
    current_variety = None
    current_picker_weight = 0
    current_weight = 0
    current_state = AWAITING_BATCH
    show_weight = False
    min_weight = 0.0
    weight_window = []

    def __init__(self):
        super(MainWindow, self).__init__()
        self.set_default_size(int(WINDOWW), int(WINDOWH))
        self.connect('destroy', self.exit_callback)

        self.add_widgets()
        self.add_initial_data()
        self.set_status_feedback()

        self.player = gst.element_factory_make('playbin2', 'player')
        fakesink = gst.element_factory_make('fakesink', 'fakesink')
        self.player.set_property('video-sink', fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        # Thread to read from scale (producer)
        self.serial_thread = utils.ThreadSerial()
        self.serial_thread.daemon = True
        self.serial_thread.start()

        # Thread to process stuff (consumer)
        self.keep_running = True # Kenji: flag to stop the consumer thread
        self.reading_thread = Thread(target = self.consumer_thread)
        self.reading_thread.start()
        self.show_all()

    def add_widgets(self):
        """
        Adds GUI widgets to this object.
        """
        #Main HBox, pack into main window
        main_hbox = Gtk.HBox()
        self.add(main_hbox)

        #Leftmost VBox (batches, status, messages, weight and offset)
        left_vbox = Gtk.VBox()
        #Extra Frame for Batch ComboBox, add to leftmost VBox
        batch_frame = Gtk.Frame(label = 'Batch')
        left_vbox.add(batch_frame)
        #Batch ComboBox, pack into batch HBox
        self.batch_combo_box = Gtk.ComboBoxText()
        batch_frame.add(self.batch_combo_box)
        # Current data
        currents_hbox = Gtk.HBox()
        current_picker_frame = Gtk.Frame(label = 'Current Picker')
        self.current_picker_label = Gtk.Label()
        current_picker_frame.add(self.current_picker_label)
        current_variety_frame = Gtk.Frame(label = 'Current Variety')
        self.current_variety_label = Gtk.Label()
        current_variety_frame.add(self.current_variety_label)
        currents_hbox.add(current_picker_frame)
        currents_hbox.add(current_variety_frame)
        left_vbox.add(currents_hbox)
        #Status feedback label
        self.status_label = Gtk.Label()
        left_vbox.add(self.status_label)
        #Weight and offset display labels 
        weight_display_frame = Gtk.Frame(label = 'Weight')
        self.weight_label = Gtk.Label()
        self.event_box = Gtk.EventBox()
        self.event_box.add(self.weight_label)
        weight_display_frame.add(self.event_box)
        left_vbox.add(weight_display_frame)
        offset_display_frame = Gtk.Frame(label = 'Offset')
        self.offset_label = Gtk.Label()
        self.event_box1 = Gtk.EventBox()
        self.event_box1.add(self.offset_label)
        offset_display_frame.add(self.event_box1)
        left_vbox.add(offset_display_frame)

        # Center VBox (Pickers)
        center_vbox = Gtk.VBox()
        picker_frame = Gtk.Frame(label = 'Pickers')
        self.picker_vbox = Gtk.VBox()
        picker_frame.add(self.picker_vbox)
        center_vbox.add(picker_frame)

        # Rightmost VBox (varieties, history and buttons)
        right_vbox = Gtk.VBox()
        varieties_frame = Gtk.Frame(label = 'Varieties')
        right_vbox.add(varieties_frame)
        self.varieties_vbox = Gtk.VBox()
        varieties_frame.add(self.varieties_vbox)
        adj1 = Gtk.Adjustment(0.0, 0.0, 101.0, 0.1, 1.0, 1.0)
        scrolled_window = Gtk.ScrolledWindow(adj1)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.AUTOMATIC)
        right_vbox.add(scrolled_window)
        self.history_list = Gtk.TreeView()
        self.history_store = Gtk.ListStore(
            int,   # picker_number
            str,   # picker_first_name
            str,   # picker_last_name
            int,   # batch_number
            str,   # batch_date
            int,   # room_number
            int,   # variety_number
            str,   # variety_name
            float, # initial_weight
            float, # final_weight
            str,   # timestamp
        )
        col0 = Gtk.TreeViewColumn('Picker Number', Gtk.CellRendererText(), text=0)
        col1 = Gtk.TreeViewColumn('First Name', Gtk.CellRendererText(), text=1)
        col2 = Gtk.TreeViewColumn('Last Name', Gtk.CellRendererText(), text=2)
        col3 = Gtk.TreeViewColumn('Batch Number', Gtk.CellRendererText(), text=3)
        col4 = Gtk.TreeViewColumn('Batch Date', Gtk.CellRendererText(), text=4)
        col5 = Gtk.TreeViewColumn('Room Number', Gtk.CellRendererText(), text=5)
        col6 = Gtk.TreeViewColumn('Variety Number', Gtk.CellRendererText(), text=6)
        col7 = Gtk.TreeViewColumn('Variety Name', Gtk.CellRendererText(), text=7)
        col8 = Gtk.TreeViewColumn('Initial Weight', Gtk.CellRendererText(), text=8)
        col9 = Gtk.TreeViewColumn('Final Weight', Gtk.CellRendererText(), text=9)
        col10 = Gtk.TreeViewColumn('Timestamp', Gtk.CellRendererText(), text=10)
        col0.set_resizable(True)
        col1.set_resizable(True)
        col2.set_resizable(True)
        col3.set_resizable(True)
        col4.set_resizable(True)
        col5.set_resizable(True)
        col6.set_resizable(True)
        col7.set_resizable(True)
        col8.set_resizable(True)
        col9.set_resizable(True)
        col10.set_resizable(True)
        self.history_list.append_column(col0)
        self.history_list.append_column(col1)
        self.history_list.append_column(col2)
        self.history_list.append_column(col3)
        self.history_list.append_column(col4)
        self.history_list.append_column(col5)
        self.history_list.append_column(col6)
        self.history_list.append_column(col7)
        self.history_list.append_column(col8)
        self.history_list.append_column(col9)
        self.history_list.append_column(col10)
        self.history_list.set_model(self.history_store)
        scrolled_window.add(self.history_list)
        edit_button_box = Gtk.HBox()
        right_vbox.add(edit_button_box)
        edit_button = Gtk.Button(label='Edit')
        edit_button_box.add(edit_button)
        edit_button.connect('clicked', self.open_edit_window)
        commit_button = Gtk.Button(label='Commit')
        commit_button.connect('clicked', self.commit_callback)
        edit_button_box.add(commit_button)

        main_hbox.add(left_vbox)
        main_hbox.add(center_vbox)
        main_hbox.add(right_vbox)

    def add_initial_data(self):
        """
        Alleviates the burden of adding data from __init__().
        """
        self.batches   = DB.get_active_batches_xml()
        self.pickers   = DB.get_active_pickers_xml()
        self.varieties = DB.get_active_varieties_xml()
        self.inverted_index_picker = {}
        self.inverted_index_batch = {}
        self.inverted_index_variety = {}
        for i in range(len(self.pickers)):
            self.inverted_index_picker[int(self.pickers[i][0])] = i
        for i in range(len(self.batches)):
            self.inverted_index_batch[int(self.batches[i][0])] = i
        for i in range(len(self.varieties)):
            self.inverted_index_variety[int(self.varieties[i][0])] = i
        # add batches
        batch_text_format = 'Batch No. {} ({}) Room {}'
        for batch in self.batches:
            self.batch_combo_box.append_text(batch_text_format.format(
                batch[0], batch[1], batch[2]
            ))
        # add pickers
        picker_total = len(self.pickers)
        cols = config.PICKER_COLS
        rows = picker_total/cols + int(picker_total%cols != 0)
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= picker_total:
                    break
                text = '{0}. {1}'.format(self.pickers[idx][0],
                                         self.pickers[idx][1])
                button = Gtk.Button(label = text)
                button.connect('clicked', self.select_picker_callback, idx)
                hbox.add(button)
            self.picker_vbox.add(hbox)
        # add varieties
        variety_total = len(self.varieties)
        cols = config.VARIETY_COLS
        rows = variety_total/cols + int(variety_total%cols != 0)
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= variety_total:
                    break
                text = '{0}'.format(self.varieties[idx][1])
                button = Gtk.Button(label = text)
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.add(button)
            self.varieties_vbox.add(hbox)
        # initialize weight_window
        for i in range(0, config.WEIGHT_WINDOW_SIZE):
            self.weight_window.append(0)
        
    def open_edit_window(self, button):
        """
        This callback is fired when editing an entry in the
        history list.
        """
        # add widgets
        self.start_stop('button')
        model, iterator = self.history_list.get_selection().get_selected()
        if iterator is not None:
            edit_dialog = Gtk.Window()
            edit_vbox = Gtk.VBox()
            edit_batch_frame = Gtk.Frame(label = 'Batch')
            edit_picker_frame = Gtk.Frame(label = 'Picker')
            edit_variety_frame = Gtk.Frame(label = 'Variety')
            edit_vbox.add(edit_batch_frame)
            edit_vbox.add(edit_picker_frame)
            edit_vbox.add(edit_variety_frame)
            # get batches
            edit_batch_combo = Gtk.ComboBoxText()
            for batch in self.batches:
                edit_batch_combo.append_text(
                    'Batch No. {} ({}) Room {}'.format(
                        batch[0], batch[1], batch[2]
                ))
            batch_number = model.get(iterator, 3)[0]
            batch_idx = self.inverted_index_batch[batch_number]
            edit_batch_combo.set_active(batch_idx)
            # get pickers
            edit_picker_combo = Gtk.ComboBoxText()
            for picker in self.pickers:
                edit_picker_combo.append_text('{}. {} {}'.format(
                    picker[0], picker[1], picker[2]
                ))
            picker_number = model.get(iterator, 0)[0]
            picker_idx = self.inverted_index_picker[picker_number]
            edit_picker_combo.set_active(picker_idx)
            # get varieties
            edit_varieties_combo = Gtk.ComboBoxText()
            for variety in self.varieties:
                edit_varieties_combo.append_text('{}. {}'.format(
                    variety[0], variety[1]
                ))
            variety_number = model.get(iterator, 6)[0]
            variety_idx = self.inverted_index_variety[variety_number]
            edit_varieties_combo.set_active(variety_idx)
            # pack everything and show window
            edit_batch_frame.add(edit_batch_combo)
            edit_picker_frame.add(edit_picker_combo)
            edit_variety_frame.add(edit_varieties_combo)
            edit_delete_button = Gtk.Button(label = 'Delete Record')
            edit_delete_button.connect(
                'clicked', self.delete_history_row,
                model, iterator, edit_dialog
            )
            edit_apply_button = Gtk.Button(label = 'Apply Changes')
            edit_apply_button.connect(
                'clicked', self.modify_history_callback,
                model, iterator, edit_batch_combo, edit_varieties_combo,
                edit_picker_combo, edit_dialog
            )
            edit_vbox.add(edit_apply_button)
            edit_vbox.add(edit_delete_button)
            edit_dialog.add(edit_vbox)
            edit_dialog.show_all()
    
    def delete_history_row(self, button, model, iterator, edit_dialog):
        """
        Callback that gets called when user deletes a history entry.
        """
        model.remove(iterator)
        edit_dialog.destroy()

    def modify_history_callback(self, button, model, iterator, batch_combobox,
                                varieties_combobox, picker_combobox, edit_dialog):
        """
        This callback is fired when an entry in the history list has been
        edited in the edit window.
        """
        self.start_stop('button')
        selected_picker = self.pickers[picker_combobox.get_active()]
        selected_batch = self.batches[batch_combobox.get_active()]
        selected_variety = self.varieties[varieties_combobox.get_active()]
        model.set_value(iterator, 0,  int(selected_picker[0]))
        model.set_value(iterator, 1,  selected_picker[1])
        model.set_value(iterator, 2,  selected_picker[2])
        model.set_value(iterator, 3,  int(selected_batch[0]))
        model.set_value(iterator, 4,  selected_batch[1])
        model.set_value(iterator, 5,  int(selected_batch[2]))
        model.set_value(iterator, 6,  int(selected_variety[0]))
        model.set_value(iterator, 7,  selected_variety[1])
        model.set_value(iterator, 10, time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime() ))
        edit_dialog.destroy()

    def exit_callback(self, widget):
        """
        This callback is fired when the user exits the program.
        """
        self.keep_running = False
        self.serial_thread.kill()
        Gtk.main_quit()

    def select_picker_callback(self, button, index):
        """
        This callback is fired when the user press a picker button.

        The result of this callback is that the current_picker is changed
        to be the actual picker the user has chosen.
        """
        self.start_stop('button')
        if self.current_state == AWAITING_PICKER:
            self.current_picker = index
            self.current_picker_weight = self.current_weight
            self.change_state()

    def select_variety_callback(self, button, index):
        """
        This callback is fired when the user press a variety button.

        The result of this callback is that the current_variety is changed
        to be the actual variety the user has chosen.
        """
        self.start_stop('button')
        if self.current_state == AWAITING_VARIETY:
            self.current_variety = index
            self.change_state()

    def commit_callback(self, button):
        """
        This callback is fired when the user presses the commit button.

        After this callback, the data in the history is sent to the server and
        committed to the database.
        """
        self.start_stop('button')
        boxes = []
        for row in self.history_store:
            boxes.append({
                'picker':         row[0],
                'batch':          row[3],
                'variety':        row[6],
                'initial_weight': row[8],
                'final_weight':   row[9],
                'timestamp':      row[10]
            })
        DB.add_boxes(boxes)
        # clear the history
        self.history_store.clear()

    def save_box(self):
        """
        Saves a box with the current picker, batch, variety, weight and timestamp.

        The information will map from -> to:
        - self.current_picker        -> box.picker
        - self.current_batch         -> box.batch
        - self.current_variety       -> box.contentVariety
        - self.current_weight        -> box.finalWeight
        - self.current_picker_weight -> box.initialWeight
        - self.timestamp             -> box.timestamp
        """
        self.start_stop('success')
        self.history_store.append((
            int(self.pickers[self.current_picker][0]),    # picker_number
            self.pickers[self.current_picker][1],         # picker_first_name
            self.pickers[self.current_picker][2],         # picker_last_name
            int(self.batches[self.current_batch][0]),     # batch_number
            self.batches[self.current_batch][1],          # batch_date
            int(self.batches[self.current_batch][2]),     # room_number
            int(self.varieties[self.current_variety][0]), # variety_number
            self.varieties[self.current_variety][1],      # variety_name
            self.current_picker_weight,                   # initial_weight
            self.current_weight,                          # final_weight
            time.strftime('%Y-%m-%d %H:%M:%S',            # timestamp
                          time.localtime())
        ))
        self.current_picker = self.current_variety = None

    def set_status_feedback(self):
        """
        This callback is fired when the status_label needs to be updated.
        """
        color = Gdk.Color(*self.weight_color) # unpack the tuple
        self.event_box.modify_bg(Gtk.StateType.NORMAL, color)
        self.event_box1.modify_bg(Gtk.StateType.NORMAL, color)
        markup = config.STATUS_STYLE.format(
            text = STATUS_MESSAGES[self.current_state])
        self.status_label.set_markup(markup)
        # update currents data
        if self.current_picker is not None:
            self.current_picker_label.set_markup(
                self.pickers[self.current_picker][1]
            )
        else:
            self.current_picker_label.set_markup('')
        if self.current_variety is not None:
            self.current_variety_label.set_markup(
                self.varieties[self.current_variety][1]
            )
        else:
            self.current_variety_label.set_markup('')
        if self.show_weight is True:
            markup = config.WEIGHT_STYLE.format(self.current_weight)
            self.weight_label.set_markup(markup)
            offset = self.current_weight - self.min_weight
            markup = config.OFFSET_STYLE.format(offset)
            self.offset_label.set_markup(markup)
        else:
            self.weight_label.set_markup(config.NA_MARKUP)
            self.offset_label.set_markup(config.NA_MARKUP)

    def consumer_thread(self):
        """
        This is the main thread that consumes the stream given from a scale.
        """
        stable_weight = 0
        while self.keep_running:
            self.current_weight = self.serial_thread.get_weight()
            if (self.current_state == AWAITING_BATCH and
                self.batch_combo_box.get_active() >= 0):
                self.current_batch = self.batch_combo_box.get_active()
                self.change_state()
            elif (self.save_weight and
                  self.current_weight < config.BOX_WEIGHT): # save the box
                self.save_weight = False
                self.current_weight = stable_weight
                self.save_box()
                self.change_state(AWAITING_BOX)
            elif (self.current_state == AWAITING_BOX and
                  self.current_weight > config.BOX_WEIGHT):
                self.change_state()
            elif (self.current_batch is not None and
                  self.current_weight < config.BOX_WEIGHT):
                self.change_state(AWAITING_BOX)
            elif self.show_weight:
                self.weight_window.pop(0)
                self.weight_window.append(self.current_weight)
                self.min_weight = self.varieties[self.current_variety][2]
                weight_tolerance = self.varieties[self.current_variety][3]
                if self.current_weight >= self.min_weight + weight_tolerance:
                    self.change_state(OVERWEIGHT_ADJUST)
                elif self.current_weight < self.min_weight:
                    self.change_state(UNDERWEIGHT_ADJUST)
                else: # within acceptable range
                    if self.weight_color != config.GREEN_COLOR:
                        self.start_stop('green')
                    self.change_state(REMOVE_BOX)
                    if self.weight_window[0] == self.current_weight:
                        stable_weight = self.weight_window[0]
                        self.save_weight = True
                    if not self.save_weight:
                        stable_weight = self.current_weight
                        self.save_weight = True
            time.sleep(0.01)

    def change_state(self, state = None):
        """
        This method is fired when the overall state of the program is updated.

        The natural order is: AWAITING_BATCH -> AWAITING_BOX ->
        AWAITING_VARIETY -> AWAITING_PICKER -> UNDERWEIGHT|OVERWEIGHT|REMOVE_BOX
        If state is not given, the "next" one in the list follows.
        """
        if state:
            self.current_state = state
            if state == AWAITING_BOX:
                self.show_weight = False
                self.weight_color = config.WHITE_COLOR
            elif state == OVERWEIGHT_ADJUST:
                self.weight_color = config.RED_COLOR
            elif state == UNDERWEIGHT_ADJUST:
                self.weight_color = config.BLUE_COLOR
            elif state == REMOVE_BOX:
                self.weight_color = config.GREEN_COLOR
        else:
            if self.current_state == AWAITING_BATCH:
                self.current_state = AWAITING_BOX
            elif self.current_state == AWAITING_BOX:
                self.current_state = AWAITING_VARIETY
            elif self.current_state == AWAITING_VARIETY:
                self.current_state = AWAITING_PICKER
            elif self.current_state == AWAITING_PICKER:
                self.show_weight = True
            elif self.current_state == REMOVE_BOX:
                self.show_weight = False
                self.current_state = AWAITING_BOX
        gobject.idle_add(self.set_status_feedback)

    def start_stop(self, sound):
        """
        This method is used to play or stop a sound file.
        """
        path = 'file://{0}/'.format(os.getcwd())
        if sound == 'success':
            self.player.set_property('uri', path + 'success.ogg')
        elif sound == 'green':
            self.player.set_property('uri', path + 'green.ogg')
        elif sound == 'button':
            self.player.set_property('uri', path + 'button.ogg')
        self.player.set_state(gst.STATE_PLAYING)

    def on_message(self, bus, message):
        """
        This callback is fired when messages for GStreamer happen.
        """
        message_type = message.type
        if message_type == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif message_type == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print('Error: {}'.format(err), debug)
            print('Bus: {}'.format(str(bus)))

if __name__ == '__main__':
    main_window = MainWindow()
    Gtk.main()
