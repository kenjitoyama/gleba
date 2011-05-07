#!/usr/bin/python
from threading import Thread
import time
import gtk
import gobject
import utils
import pygst
pygst.require("0.10")
import gst
import os
import config

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

class MainWindow(gtk.Window):
    save_weight = False
    weight_color = 'white'
    current_batch = None
    current_picker = None
    current_variety = None
    current_picker_weight = 0
    current_weight = 0
    current_state = 0
    stable_weight = 0
    status_text = STATUS_MESSAGES[current_state]
    show_weight = False
    min_weight = 0.0
    weight_window = []
    history_entries = []

    def __init__(self):
        super(MainWindow, self).__init__()

        #Thread to read from scale
        self.serial_thread = utils.ThreadSerial()
        self.serial_thread.daemon = True
        self.serial_thread.start()

        # set minimum size and register the exit button
        self.set_size_request(int(WINDOWW), int(WINDOWH))
        self.connect('destroy', self.exit_callback)

        #Main HBox, pack into main window
        main_hbox = gtk.HBox()
        self.add(main_hbox)

        #status_frame for leftmost VBox, pack into main_hbox
        status_frame = gtk.Frame()
        status_frame.set_size_request(int(WINDOWW/2.5), int(WINDOWH/6))
        main_hbox.pack_start(status_frame)

        #Leftmost VBox, add to status_frame
        status_vbox = gtk.VBox()
        status_frame.add(status_vbox)

        #Extra Frame for Batch ComboBox, add to leftmost VBox
        batch_frame = gtk.Frame(label = 'Batch')
        batch_frame.set_size_request(0, 0) # minimum as possible
        status_vbox.pack_start(batch_frame)

        #Add batch HBox for combo box and button to batch_frame

        #Batch ComboBox, pack into batch HBox
        self.batch_combo_box = gtk.combo_box_new_text()
        batch_frame.add(self.batch_combo_box)
        
        #Status feedback label
        self.status_label = gtk.Label()
        self.status_label.set_size_request(250, 200)
        status_vbox.pack_start(self.status_label)

        #Button to start thread, remove this later
        self.b = gtk.Button(stock=gtk.STOCK_OK)
        self.b.connect('clicked', self.history_callback)
        self.b.set_sensitive(False)

        #Weight and offset display labels 
        weight_display_frame = gtk.Frame(label = 'Weight')
        self.weight_label = gtk.Label()
        self.event_box = gtk.EventBox()
        self.event_box.add(self.weight_label)
        weight_display_frame.add(self.event_box)
        status_vbox.add(weight_display_frame)
        
        offset_display_frame = gtk.Frame(label = 'Offset')
        self.offset_label = gtk.Label()
        self.event_box1 = gtk.EventBox()
        self.event_box1.add(self.offset_label)
        offset_display_frame.add(self.event_box1)
        status_vbox.add(offset_display_frame)

        self.set_status_feedback()

        #Frame for middle VBox() containing pickers
        picker_frame = gtk.Frame(label = 'Pickers')
        picker_frame.set_size_request(int(WINDOWW/2), int(WINDOWH/6))
        self.picker_vbox = gtk.VBox()
        picker_frame.add(self.picker_vbox)
        main_hbox.pack_start(picker_frame)

        self.history_vbox = gtk.VBox()
        varieties_frame = gtk.Frame(label = 'Varieties')
        varieties_frame.set_size_request(int(WINDOWW/2), int(WINDOWH/2))
        self.history_vbox.pack_start(varieties_frame)
	
        self.varieties_vbox = gtk.VBox()
        varieties_frame.add(self.varieties_vbox)

        #Frame for rightmost VBox() containing entry history
        history_frame = gtk.Frame()
        main_hbox.pack_start(history_frame)
        history_frame.set_size_request(int(WINDOWW/4), 0)
        
        adj1 = gtk.Adjustment(0.0, 0.0, 101.0, 0.1, 1.0, 1.0)

        scrolled_window = gtk.ScrolledWindow(adj1)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        history_frame1 = gtk.Frame()
        history_frame1.add(scrolled_window)
        history_frame1.set_size_request(int(WINDOWW/2), int(WINDOWH/3))
        history_frame.add(self.history_vbox)
        self.history_vbox.pack_start(history_frame1)
        
        self.history_list = gtk.TreeView()
        self.history_store = gtk.ListStore(str)
        column = gtk.TreeViewColumn('History', gtk.CellRendererText(), text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        self.history_list.append_column(column)
        self.history_list.set_model(self.history_store)
        scrolled_window.add(self.history_list)
        
        edit_button_box = gtk.HBox()
        
        history_frame2 = gtk.Frame()
        history_frame2.set_size_request(int(WINDOWW/2), int(WINDOWH/24))
        self.history_vbox.pack_start(history_frame2)
        history_frame2.add(edit_button_box)
        
        edit_button = gtk.Button(label='Edit')
        edit_button.set_size_request(20, 20)
        edit_button_box.pack_start(edit_button)
        edit_button.connect('clicked', self.edit_window)

        commit_button = gtk.Button(label='Commit')
        commit_button.connect('clicked', self.commit_callback)
        edit_button_box.pack_start(commit_button)
        
        self.add_initial_data()

        self.keep_running = True #Kenji: flag to stop the thread
        self.count_in_thread(4.3)
        self.show_all()

        self.player = gst.element_factory_make('playbin2', 'player')
        fakesink = gst.element_factory_make('fakesink', 'fakesink')
        self.player.set_property('video-sink', fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def add_initial_data(self):
        """
        Alleviates the burden of adding data from __init__().
        """
        self.batches   = DB.getActiveBatches()
        self.pickers   = DB.getActivePickers()
        self.varieties = DB.getActiveVarieties()
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
            hbox = gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= picker_total:
                    break
                text = '{0}. {1}'.format(self.pickers[idx][0],
                                         self.pickers[idx][1])
                button = gtk.Button(label = text)
                button.set_size_request(14, 10)
                button.connect('clicked', self.select_picker_callback, idx)
                hbox.pack_start(button)
            self.picker_vbox.pack_start(hbox)
        # add varieties
        variety_total = len(self.varieties)
        cols = config.VARIETY_COLS
        rows = variety_total/cols + int(variety_total%cols != 0)
        for row in range(0, rows):
            hbox = gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= variety_total:
                    break
                text = '{0}'.format(self.varieties[idx][1])
                button = gtk.Button(label = text)
                button.set_size_request(14, 15)
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.pack_start(button)
            self.varieties_vbox.pack_start(hbox)
        # initialize weight_window
        for i in range(0, config.WEIGHT_WINDOW_SIZE):
            self.weight_window.append(0)
        
    def edit_window(self, button):
        # add widgets
        self.start_stop('button')
        selection, iterator = self.history_list.get_selection().get_selected()
        if iterator is not None:
            self.edit_dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
            vertical_box = gtk.VBox()
            edit_frame = gtk.Frame(label = 'Modify Entry')
            frame1 = gtk.Frame(label = 'Batch')
            frame2 = gtk.Frame(label = 'Picker')
            frame3 = gtk.Frame(label = 'Variety')
            frame4 = gtk.Frame(label = '')
            vertical_box.pack_start(frame1)
            vertical_box.pack_start(frame2)
            vertical_box.pack_start(frame3)
            vertical_box.pack_start(frame4)
            row = selection.get_path(iterator)[0]
            delete_button = gtk.Button(label = 'Delete Record')
            delete_button.connect('clicked', self.modify_history_callback,
                                                iterator, row, True)
            delete_button.set_size_request(10, 15)
            apply_button = gtk.Button(label = 'Apply Changes')
            apply_button.set_size_request(10, 35)
            apply_button.connect('clicked', self.modify_history_callback,
                                                iterator, row, False)
            edit_frame.set_size_request(0, 60)
            index_list = self.history_entries[row][6]
            # get batches
            self.edit_batch_combo = gtk.combo_box_new_text()
            for b in self.batches:
                self.edit_batch_combo.append_text(
                    'Batch No. {} ({}) Room {}'.format(
                        b[0], b[1], b[2]
                ))
            self.edit_batch_combo.set_active(index_list[0])
            # get pickers
            self.edit_picker_combo = gtk.combo_box_new_text()
            for p in self.pickers:
                self.edit_picker_combo.append_text('{}. {} {}'.format(
                    p[0], p[1], p[2]
                ))
            self.edit_picker_combo.set_active(index_list[2])
            # get varieties
            self.edit_varieties_combo = gtk.combo_box_new_text()
            for v in self.varieties:
                self.edit_varieties_combo.append_text('{}. {}'.format(
                    v[0], v[1]
                ))
            self.edit_varieties_combo.set_active(index_list[1])
            # pack everything and show window
            frame1.add(self.edit_batch_combo)
            frame2.add(self.edit_picker_combo)
            frame3.add(self.edit_varieties_combo)
            vertical_box2 = gtk.VBox()
            frame5 = gtk.Frame()
            frame5.set_size_request(100, 50)
            vertical_box2.pack_start(apply_button)
            vertical_box2.pack_start(frame5)
            vertical_box2.pack_start(delete_button)
            edit_frame.add(vertical_box)
            frame4.add(vertical_box2)
            self.edit_dialog.add(edit_frame)
            self.edit_dialog.set_size_request(int(WINDOWW/2.7),
                                              int(WINDOWH/1.6))
            self.edit_dialog.show_all()
    
    def modify_history_callback(self, button, iterator, row, delete):
        self.start_stop('button')
        self.history_store.remove(iterator)
        if delete is not True:
            entry = self.history_entries[row]
            #modify      
            self.current_batch_ = self.edit_batch_combo.get_active()
            self.current_variety = self.edit_varieties_combo.get_active()
            self.current_picker = self.edit_picker_combo.get_active()
            index_list = (self.current_batch,
                          self.current_variety,
                          self.current_picker)
            #retain
            self.current_picker_weight = entry[3]
            self.current_weight = entry[4]
            self.history_entries[row] = (self.pickers[self.current_picker][0],
                                        self.batches[self.current_batch_][0],
                                        self.varieties[self.current_variety][0],
                                        self.current_picker_weight,
                                        self.current_weight,
                                        time.strftime('%Y-%m-%d %H:%M:%S',
                                                      time.localtime()),
                                        index_list)
            #modify treeView model
            temp = []

            entry = 'Picker No. ' + str(self.pickers[self.current_picker][0])
            entry += ', ' +str(self.pickers[self.current_picker][1])
            entry += ' ' + str(self.pickers[self.current_picker][2])
            entry += ', Variety: ' + self.varieties[self.current_variety][0]
            entry += '. ' + self.varieties[self.current_variety][1]
            entry += ', Batch No. ' + str(self.batches[self.current_batch_][0])
            entry += ' (' + str(self.batches[self.current_batch_][1])
            entry += ') Room ' + str(self.batches[self.current_batch_][0])
            entry += ', Picker Weight: ' + str(self.current_picker_weight)
            entry += ', Final Weight: ' + str(self.current_weight)
            entry += ', Time: ' + time.strftime('%Y-%m-%d %H:%M:%S',
                                                       time.localtime())
            temp.append(entry)
            self.history_store.insert(row, temp)
        else:
            self.history_entries.pop(row)
        self.edit_dialog.destroy()


    def exit_callback(self, widget):
        self.keep_running = False
        self.serial_thread.kill()
        gtk.main_quit()

    def select_picker_callback(self, button, index):
        self.start_stop('button')
        self.current_picker = index
        if self.current_state == AWAITING_PICKER:
            self.current_picker_weight = self.current_weight
            self.change_state()
            self.status_text = STATUS_MESSAGES[self.current_state]
            self.set_status_feedback()

    def select_variety_callback(self, button, index):
        self.start_stop('button')
        self.current_variety = index
        if self.current_state == AWAITING_VARIETY:
            self.change_state()
            self.status_text = STATUS_MESSAGES[self.current_state]
            self.set_status_feedback()

    def commit_callback(self, button):
        self.start_stop('button')
        for (picker, batch, variety, init_weight,
             final_weight, timestamp, index_list) in self.history_entries:
            DB.addBox(picker, batch, variety, init_weight,
                      final_weight, timestamp)
        # clear the history
        self.history_store.clear()
        self.history_entries = []
        self.show_all()

    def get_active_text(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]

    def history_callback(self, button):
        self.start_stop('success')
        self.current_weight = self.stable_weight
        temp = []
        index_list = []
        index_list.append(self.current_batch)
        index_list.append(self.current_variety)
        index_list.append(self.current_picker)
        text = 'Picker {picker_number} ' +\
               '({picker_firstname} {picker_lastname}), ' +\
               'Variety {variety_number} ({variety_name}), ' +\
               'Batch {batch_number} ({batch_date}), Room {room_number}, ' +\
               'Picker Weight: {picker_weight}, ' +\
               'Final Weight: {final_weight}, Time: {timestamp}'
        temp.append(text.format(
            picker_number    = self.pickers[self.current_picker][0],
            picker_firstname = self.pickers[self.current_picker][1],
            picker_lastname  = self.pickers[self.current_picker][2],
            variety_number   = self.varieties[self.current_variety][0],
            variety_name     = self.varieties[self.current_variety][1],
            batch_number     = self.batches[self.current_batch][0],
            batch_date       = self.batches[self.current_batch][1],
            room_number      = self.batches[self.current_batch][2],
            picker_weight    = self.current_picker_weight,
            final_weight     = self.current_weight,
            timestamp        = time.strftime('%Y-%m-%d %H:%M:%S',
                                             time.localtime())
        ))

        self.history_entries.append((self.pickers[self.current_picker][0],
                                    self.batches[self.current_batch][0],
                                    self.varieties[self.current_variety][0],
                                    self.current_picker_weight,
                                    self.current_weight,
                                    time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.localtime()),
                                    index_list))
        self.history_store.append(temp)
        self.history_list.set_model(self.history_store)
        self.show_all()

    def count_in_thread(self, maximum):
        Thread(target=self.count_up, args=(maximum,)).start()

    def set_status_feedback(self):
        self.event_box.modify_bg(gtk.STATE_NORMAL,
                                 gtk.gdk.color_parse(self.weight_color))
        self.event_box1.modify_bg(gtk.STATE_NORMAL,
                                  gtk.gdk.color_parse(self.weight_color))
        self.status_text = STATUS_MESSAGES[self.current_state]
        markup = config.STATUS_STYLE.format(text = self.status_text)
        self.status_label.set_markup(markup)
        if self.show_weight is True:
            markup = config.WEIGHT_STYLE.format(self.current_weight)
            self.weight_label.set_markup(markup)
            offset = self.current_weight - self.min_weight
            markup = config.OFFSET_STYLE.format(offset)
            self.offset_label.set_markup(markup)
        else:
            self.weight_label.set_markup(config.NA_MARKUP)
            self.offset_label.set_markup(config.NA_MARKUP)

    def count_up(self, maximum):
        while self.keep_running:
            self.current_batch = self.batch_combo_box.get_active()
            self.current_weight = self.serial_thread.getWeight()
            if self.current_state == AWAITING_BATCH:
                if self.current_batch is not None and\
                   self.current_batch >= 0: # -1 if no active item
                    self.current_batch = self.batch_combo_box.get_active()
                    gobject.idle_add(self.change_state)
                    gobject.idle_add(self.set_status_feedback)
            elif self.save_weight and self.current_weight < 0.4:
                self.save_weight = False
                self.current_weight = self.stable_weight
                self.current_state = AWAITING_BOX
                self.show_weight = False
                self.weight_color = 'white'
                gobject.idle_add(self.set_status_feedback)
                gobject.idle_add(self.history_callback, self.b)
            elif self.current_state == AWAITING_BOX:
                if self.current_weight > 0.1:
                    gobject.idle_add(self.change_state)
                    gobject.idle_add(self.set_status_feedback)
            elif self.current_batch is not None and self.current_weight < 0.1:
                self.current_state = AWAITING_BOX
                self.show_weight = False
                self.weight_color = 'white'
                gobject.idle_add(self.set_status_feedback)
            if self.show_weight:
                self.weight_window.pop(0)
                self.weight_window.append(self.current_weight)
                self.min_weight = float(self.varieties[self.current_variety][2])
                weight_tolerance = float(
                    self.varieties[self.current_variety][3])
                if self.current_weight >= self.min_weight + weight_tolerance:
                    # overweight
                    self.weight_color = 'red'
                    self.current_state = OVERWEIGHT_ADJUST
                    gobject.idle_add(self.b.set_sensitive, False)
                elif self.current_weight < self.min_weight:
                    # underweight
                    gobject.idle_add(self.b.set_sensitive, False)
                    self.weight_color = 'blue'
                    self.current_state = UNDERWEIGHT_ADJUST
                else: # within acceptable range
                    if self.weight_color != 'green':
                        self.start_stop('green')
                    self.weight_color = 'green'
                    self.current_state = REMOVE_BOX
                    if self.weight_window[0] == self.current_weight:
                        self.stable_weight = self.weight_window[0]
                        self.save_weight = True
                    if not self.save_weight:
                        self.stable_weight = self.current_weight
                        self.save_weight = True
                        gobject.idle_add(self.b.set_sensitive, True)
                gobject.idle_add(self.set_status_feedback)
            time.sleep(0.01)

    def change_state(self):
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
            self.set_status_feedback()

    def start_stop(self, sound):
        path = 'file://{0}/'.format(os.getcwd())
        if sound == 'success':
            self.player.set_property('uri', path + 'success.ogg')
        elif sound == 'green':
            self.player.set_property('uri', path + 'green.ogg')
        elif sound == 'button':
            self.player.set_property('uri', path + 'button.ogg')
        self.player.set_state(gst.STATE_PLAYING)

    def on_message(self, bus, message):
        message_type = message.type
        if message_type == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif message_type == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print('Error: {}'.format(err), debug)
            print('Bus: {}'.format(str(bus)))

if __name__ == '__main__':
    gtk.gdk.threads_init() #serialize access to the interpreter
    main_window = MainWindow()
    gtk.main()
