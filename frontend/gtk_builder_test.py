from gi.repository import Gtk
import utils
import config

DB = utils.DBAPI()

class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('gui.ui')
        self.window = self.builder.get_object('window')
        self.builder.connect_signals(self)
        self.batches   = DB.get_active_batches_list()
        self.pickers   = DB.get_active_pickers_list()
        self.varieties = DB.get_active_varieties_list()
        # add batches
        batch_combo_box = self.builder.get_object('batch_combo_box')
        batch_text_format = 'Batch No. {} ({}/{}/{}) Room {}'
        for batch in self.batches:
            batch_combo_box.append_text(batch_text_format.format(
                batch['id'],
                batch['date']['day'],
                batch['date']['month'],
                batch['date']['year'],
                batch['room_number']
            ))
        # add pickers
        picker_total = len(self.pickers)
        cols = config.PICKER_COLS
        rows = picker_total/cols + int(picker_total%cols != 0)
        picker_vbox = self.builder.get_object('picker_vbox')
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= picker_total:
                    break
                text = '{0}. {1}'.format(self.pickers[idx]['id'],
                                         self.pickers[idx]['first_name'])
                button = Gtk.Button(label = text)
                button.set_size_request(14, 10)
                button.connect('clicked', self.select_picker_callback, idx)
                hbox.add(button)
            picker_vbox.add(hbox)
        # add varieties
        variety_total = len(self.varieties)
        cols = config.VARIETY_COLS
        rows = variety_total/cols + int(variety_total%cols != 0)
        variety_vbox = self.builder.get_object('variety_vbox')
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= variety_total:
                    break
                text = '{0}'.format(self.varieties[idx]['name'])
                button = Gtk.Button(label = text)
                button.set_size_request(14, 15)
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.add(button)
            variety_vbox.add(hbox)

    def exit_callback(self, widget, data = None):
        Gtk.main_quit()

    def open_edit_window(self, widget, data = None):
        edit_window = self.builder.get_object('edit_window')
        edit_window.show_all()

    def commit_callback(self, widget, data = None):
        pass

    def modify_history_callback(self, widget, data):
        pass

    def select_picker_callback(self, widget, data):
        pass

    def select_variety_callback(self, widget, data):
        pass

if __name__ == '__main__':
    gui = MainWindow()
    gui.window.show_all()
    Gtk.main()
