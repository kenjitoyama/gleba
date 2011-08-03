from gi.repository import Gtk

class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('gui.ui')
        self.window = self.builder.get_object('window')
        self.builder.connect_signals(self)

    def exit_callback(self, widget, data = None):
        Gtk.main_quit()

    def open_edit_window(self, widget, data = None):
        edit_window = self.builder.get_object('edit_window')
        edit_window.show_all()

    def commit_callback(self, widget, data = None):
        pass

    def modify_history_callback(self, widget, data):
        pass

if __name__ == '__main__':
    gui = MainWindow()
    gui.window.show_all()
    Gtk.main()
