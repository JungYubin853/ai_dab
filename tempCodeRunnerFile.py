    timer_text = "Timer: off" if self.timer_total is None else self._format_time(self.remaining)
        # put the timer below the centered info
        self.timer_label = tk.Label(self.status_frame, text=timer_text, font=(None, 14, "bold"))
        self.timer_label.pack(side=tk.TOP, anchor=tk.CENTER, pady=(2, 0))