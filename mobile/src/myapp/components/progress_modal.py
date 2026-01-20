import toga
from toga.style import Pack

class ProgressModal:
    def __init__(self, parent_window, title="Processing..."):
        self.parent_window = parent_window
        self.title = title
        
        self.dialog = toga.Window(title=title, size=(300, 150))
        
        content = toga.Box(style=Pack(direction='column', padding=20))
        
        self.message_label = toga.Label(
            "Starting...",
            style=Pack(padding_bottom=10, text_align='center')
        )
        
        self.progress_bar = toga.ProgressBar(
            max=100,
            value=0,
            style=Pack(padding_bottom=10)
        )
        
        self.cancel_btn = toga.Button(
            "Cancel",
            on_press=self.cancel,
            style=Pack()
        )
        
        content.add(self.message_label)
        content.add(self.progress_bar)
        content.add(self.cancel_btn)
        
        self.dialog.content = content
        self.parent_window.app.add_window(self.dialog)
    
    def show(self):
        """Show the progress modal"""
        self.dialog.show()
    
    def update(self, progress, message):
        """Update progress and message"""
        self.progress_bar.value = progress
        self.message_label.text = message
    
    def close(self):
        """Close the modal"""
        self.dialog.close()
    
    def cancel(self, widget):
        """Handle cancel button press"""
        self.close()
        # Notify parent about cancellation
        if hasattr(self.parent_window, 'on_progress_cancel'):
            self.parent_window.on_progress_cancel()# -*- coding: utf-8 -*-

