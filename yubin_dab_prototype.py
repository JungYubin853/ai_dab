import tkinter as tk
from functools import lru_cache
import threading

# Variabel global yang digunakan
HUMAN, AI = 1, 2
EDGE_EMPTY = "gray"
HUMAN_COLOR = "green"
AI_COLOR = "red"

# Variabel global yang digunakan untuk menyimpan nilai awal dari struktur petak/papan
GRID_SIZE = 4
NUM_H_EDGES = NUM_V_EDGES = TOTAL_EDGES = 0

def configure_grid(size: int):
    """
    Rebuilds all grid-dependent globals for a given size.
    Called at startup and whenever the user picks a new mode.
    """
    global GRID_SIZE, NUM_H_EDGES, NUM_V_EDGES, TOTAL_EDGES, BOXES
    GRID_SIZE = size
    NUM_H_EDGES = GRID_SIZE * (GRID_SIZE - 1)              
    NUM_V_EDGES = (GRID_SIZE - 1) * GRID_SIZE              
    TOTAL_EDGES = NUM_H_EDGES + NUM_V_EDGES

    # Membuat default atau semacam container untuk menggabungkan edges dengan dots sehingga membentuk kotak
    BOXES = []
    for r in range(GRID_SIZE - 1):
        for c in range(GRID_SIZE - 1):
            top = r * (GRID_SIZE - 1) + c
            bottom = (r + 1) * (GRID_SIZE - 1) + c
            left = NUM_H_EDGES + r * GRID_SIZE + c
            right = NUM_H_EDGES + r * GRID_SIZE + (c + 1)
            BOXES.append((top, bottom, left, right))


# Inisialisasi bentuk grid awal
configure_grid(GRID_SIZE)


class DotsAndBoxes:
    def __init__(self, root, on_back=None, timer_seconds=None):
        self.root = root
        self.on_back = on_back
        self.root.title(f"Dots and Boxes {GRID_SIZE}x{GRID_SIZE} (Human vs AI)")

        # Tampilan GUI atau dots and boxes nya
        self.canvas = tk.Canvas(root, width=500, height=500, bg="white")
        self.canvas.pack()

        # header: centered info with timer below
        self.header = tk.Frame(root)
        self.header.pack(fill=tk.X, pady=(6, 0))
        # status_frame holds the centered message and the timer under it
        self.status_frame = tk.Frame(self.header)
        self.status_frame.pack(fill=tk.X)
        self.info = tk.Label(self.status_frame, text="Your turn (Green)")
        # center the info label horizontally
        self.info.pack(side=tk.TOP, anchor=tk.CENTER)

        # timer support
        self.timer_total = timer_seconds if timer_seconds and timer_seconds > 0 else None
        self.remaining = self.timer_total
        self.time_up = False
        self._timer_id = None
        # alive flag: set False when UI is torn down to stop callbacks
        self._alive = True
        self.timer_started = False
        timer_text = "Timer: off" if self.timer_total is None else self._format_time(self.remaining)
        # put the timer below the centered info
        self.timer_label = tk.Label(self.status_frame, text=timer_text, font=(None, 14, "bold"))
        self.timer_label.pack(side=tk.TOP, anchor=tk.CENTER, pady=(2, 0))

        self.controls = tk.Frame(root)
        self.controls.pack(pady=6)
        tk.Button(self.controls, text="New Game", command=self.reset_game).pack(side=tk.LEFT, padx=6)
        tk.Button(self.controls, text="Back to Menu", command=self._on_back).pack(side=tk.LEFT, padx=6)

        # Ukuran atau tampilan spasi pada GUI
        self.spacing = 130
        self.margin = 60

        # Status awal game atau initial state
        self.edge_state = [0] * TOTAL_EDGES
        self.box_owner = [0] * ((GRID_SIZE - 1) * (GRID_SIZE - 1))
        self.current_player = HUMAN

        # draw and bind
        self.draw_board()
        # bind clicks after board created
        self.canvas.bind("<Button-1>", self.handle_click)

    # ===== Menggambar =====
    def get_edge_coords(self):
        """Returns (horizontal_edges, vertical_edges) lists of line coords."""
        h_edges, v_edges = [], []

        # Koordinat Garis horizontal
        for r in range(GRID_SIZE):
            y = self.margin + r * self.spacing
            for c in range(GRID_SIZE - 1):
                x1 = self.margin + c * self.spacing
                x2 = x1 + self.spacing
                h_edges.append((x1, y, x2, y))

        # Koordinat Garis vertikal
        for r in range(GRID_SIZE - 1):
            for c in range(GRID_SIZE):
                x = self.margin + c * self.spacing
                y1 = self.margin + r * self.spacing
                y2 = y1 + self.spacing
                v_edges.append((x, y1, x, y2))

        return h_edges, v_edges

    def draw_board(self):
        if not getattr(self, '_alive', True):
            return
        self.canvas.delete("all")
        h_edges, v_edges = self.get_edge_coords()

        # Menggambar kotak atau boxes
        for i, owner in enumerate(self.box_owner):
            br, bc = divmod(i, GRID_SIZE - 1)
            x = self.margin + bc * self.spacing
            y = self.margin + br * self.spacing
            color = "#dddddd"
            if owner == HUMAN:
                color = HUMAN_COLOR
            elif owner == AI:
                color = AI_COLOR
            self.canvas.create_rectangle(
                x + 10, y + 10,
                x + self.spacing - 10, y + self.spacing - 10,
                fill=color, outline=color
            )

        # Menggambar garis atau edges
        for i, (x1, y1, x2, y2) in enumerate(h_edges):
            owner = self.edge_state[i]
            color = EDGE_EMPTY if owner == 0 else (HUMAN_COLOR if owner == HUMAN else AI_COLOR)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)

        for j, (x1, y1, x2, y2) in enumerate(v_edges):
            idx = NUM_H_EDGES + j
            owner = self.edge_state[idx]
            color = EDGE_EMPTY if owner == 0 else (HUMAN_COLOR if owner == HUMAN else AI_COLOR)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)

        # Menggambar titik atau dots
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = self.margin + c * self.spacing
                y = self.margin + r * self.spacing
                self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="black")

    def edge_at(self, x, y):
        """Returns edge index near given point or None."""
        h_edges, v_edges = self.get_edge_coords()

        # Mengecek input user pada garis secara horizontal
        for i, (x1, y1, x2, y2) in enumerate(h_edges):
            if abs(y - y1) <= 10 and x1 - 10 <= x <= x2 + 10:
                return i

        # Mengecek input user pada garis secara vertikal
        for j, (x1, y1, x2, y2) in enumerate(v_edges):
            idx = NUM_H_EDGES + j
            if abs(x - x1) <= 10 and y1 - 10 <= y <= y2 + 10:
                return idx

        return None

    # ===== game logic =====
    def handle_click(self, event):
        # start timer on the first human action if timer configured
        if getattr(self, 'timer_total', None) is not None and not getattr(self, 'timer_started', False):
            self.timer_started = True
            self.start_timer()

        if self.current_player != HUMAN or self.time_up:
            return
        idx = self.edge_at(event.x, event.y)
        if idx is None or self.edge_state[idx] != 0:
            return

        gained = self.apply_move(idx, HUMAN)
        self.draw_board()
        self.update_info()

        if not gained and not self.is_game_over():
            self.current_player = AI
            # AI melakukan delay sebelum bergerak
            self.root.after(80, self.ai_move)
        else:
            self.current_player = HUMAN

    def apply_move(self, edge_idx, player):
        """
        Marks the edge, assigns any newly completed boxes,
        returns True if at least one box was completed.
        """
        self.edge_state[edge_idx] = player
        gained = False
        for bi, (t, b, l, r) in enumerate(BOXES):
            if (self.edge_state[t] and self.edge_state[b] and
                self.edge_state[l] and self.edge_state[r] and
                self.box_owner[bi] == 0):
                self.box_owner[bi] = player
                gained = True
        return gained

    def is_game_over(self):
        return all(e != 0 for e in self.edge_state)

    # ===== AI =====
    def ai_move(self):
        """Run minimax in a background thread, then apply the chosen move."""
        if not getattr(self, '_alive', True) or self.is_game_over() or self.time_up:
            self.update_info()
            return

        self.info.config(text="AI thinking...")

        edges = tuple(self.edge_state)
        boxes = tuple(self.box_owner)
        depth_limit = None if GRID_SIZE <= 3 else 3       # small boards -> full search

        def worker(e, b):
            try:
                _, move = self.minimax(e, b, AI, depth_limit)
            except Exception as err:
                self.root.after(0, lambda: self.info.config(text=f"AI error: {err}"))
                return
            # schedule apply only if still alive
            self.root.after(0, lambda: self._apply_ai_move(move) if getattr(self, '_alive', True) else None)

        threading.Thread(target=worker, args=(edges, boxes), daemon=True).start()

    def _apply_ai_move(self, move):
        if not getattr(self, '_alive', True):
            return
        if self.time_up:
            self.current_player = HUMAN
            self.update_info()
            return

        if move is None:
            self.current_player = HUMAN
            self.update_info()
            return

        gained = self.apply_move(move, AI)
        self.draw_board()
        self.update_info()

        if gained and not self.is_game_over():
            self.current_player = AI
            self.root.after(80, self.ai_move)
        else:
            self.current_player = HUMAN

    def reset_game(self):
        """Reset current board with same grid size."""
        try:
            DotsAndBoxes.minimax.cache_clear()
        except Exception:
            pass

        self.edge_state = [0] * TOTAL_EDGES
        self.box_owner = [0] * ((GRID_SIZE - 1) * (GRID_SIZE - 1))
        self.current_player = HUMAN
        # reset timer: cancel any pending tick and restart if timer configured
        self.time_up = False
        if getattr(self, '_timer_id', None) is not None:
            try:
                self.root.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None
        if getattr(self, 'timer_total', None) is not None:
            self.remaining = self.timer_total
            # reset but do not auto-start; wait for first player click
            self.timer_started = False
            try:
                self.timer_label.config(text=self._format_time(self.remaining))
            except Exception:
                pass

        self.draw_board()
        self.update_info()

    def _on_back(self):
        """Destroy widgets and go back to launcher."""
        # mark not alive first to stop callbacks
        try:
            self._alive = False
        except Exception:
            pass
        # destroy primary UI widgets (if present)
        for w in (getattr(self, 'canvas', None), getattr(self, 'info', None),
                  getattr(self, 'controls', None), getattr(self, 'timer_label', None),
                  getattr(self, 'status_frame', None), getattr(self, 'header', None)):
            try:
                if w is not None:
                    w.destroy()
            except Exception:
                pass
        # cancel timer if running
        if getattr(self, '_timer_id', None) is not None:
            try:
                self.root.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

        # reset timer-related flags to a clean state so new games behave correctly
        try:
            self.timer_started = False
            self.time_up = False
            if getattr(self, 'timer_total', None) is not None:
                self.remaining = self.timer_total
        except Exception:
            pass

        if callable(self.on_back):
            self.on_back()
        # clear reference on root so start_game won't try to reset a torn-down instance
        try:
            if getattr(self.root, 'current_game', None) is self:
                self.root.current_game = None
        except Exception:
            pass

    def update_info(self):
        human_score = sum(1 for b in self.box_owner if b == HUMAN)
        ai_score = sum(1 for b in self.box_owner if b == AI)

        if getattr(self, 'time_up', False):
            msg = f"Time's up! Final score ({human_score}:{ai_score})"
        elif self.is_game_over():
            if human_score > ai_score:
                msg = f"Game Over! You win! ({human_score}:{ai_score})"
            elif ai_score > human_score:
                msg = f"Game Over! AI wins! ({human_score}:{ai_score})"
            else:
                msg = f"Game Over! Draw! ({human_score}:{ai_score})"
        else:
            turn = "Your turn (Green)" if self.current_player == HUMAN else "AI thinking..."
            msg = f"{turn} | H:{human_score} A:{ai_score}"

        self.info.config(text=msg)

        # update timer label if timer running
        if getattr(self, 'timer_total', None) is not None and not getattr(self, 'time_up', False):
            if getattr(self, 'remaining', None) is not None:
                try:
                    self.timer_label.config(text=self._format_time(self.remaining))
                except Exception:
                    pass

    # ---- timer helpers ----
    def _format_time(self, secs):
        if secs is None:
            return "Timer: off"
        m, s = divmod(secs, 60)
        return f"Time: {m:02d}:{s:02d}"

    def start_timer(self):
        if not getattr(self, '_alive', True) or getattr(self, 'timer_total', None) is None:
            return
        if getattr(self, 'remaining', None) is None:
            self.remaining = self.timer_total
        if getattr(self, '_timer_id', None) is None:
            # schedule first tick
            self._tick()

    def _tick(self):
        if not getattr(self, '_alive', True):
            return
        # stop ticking if game over or time up
        if getattr(self, 'time_up', False) or self.is_game_over():
            return
        if getattr(self, 'remaining', None) is None:
            return
        # update display
        try:
            self.timer_label.config(text=self._format_time(self.remaining))
        except Exception:
            pass
        if self.remaining <= 0:
            self.time_up = True
            self.end_game_due_to_time()
            return
        self.remaining -= 1
        try:
            self._timer_id = self.root.after(1000, self._tick)
        except Exception:
            self._timer_id = None

    def end_game_due_to_time(self):
        # cancel pending timer
        if getattr(self, '_timer_id', None) is not None:
            try:
                self.root.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None
        self.time_up = True
        # redraw and update info to reflect final state
        self.draw_board()
        self.update_info()

    # ===== minimax =====
    @lru_cache(maxsize=None)
    def minimax(self, edges, boxes, player, depth=None):
        """
        Minimax with optional depth limit.
        Returns (score_from_AI_pov, best_move).
        """
        # terminal
        if all(e != 0 for e in edges):
            ai_score = sum(1 for b in boxes if b == AI)
            human_score = sum(1 for b in boxes if b == HUMAN)
            return ai_score - human_score, None

        # depth cutoff -> heuristic: difference in boxes
        if depth is not None and depth <= 0:
            ai_score = sum(1 for b in boxes if b == AI)
            human_score = sum(1 for b in boxes if b == HUMAN)
            return ai_score - human_score, None

        moves = [i for i, e in enumerate(edges) if e == 0]

        if player == AI:
            best_val, best_move = -999, None
            for m in moves:
                val = self._simulate_move(edges, boxes, m, AI, depth)
                if val[0] > best_val:
                    best_val, best_move = val[0], m
            return best_val, best_move
        else:
            best_val, best_move = 999, None
            for m in moves:
                val = self._simulate_move(edges, boxes, m, HUMAN, depth)
                if val[0] < best_val:
                    best_val, best_move = val[0], m
            return best_val, best_move

    def _simulate_move(self, edges, boxes, move, player, depth):
        """Helper for minimax: apply move on copies and recurse."""
        e2 = list(edges)
        b2 = list(boxes)
        e2[move] = player

        gained = False
        for bi, (t, b, l, r) in enumerate(BOXES):
            if e2[t] and e2[b] and e2[l] and e2[r] and b2[bi] == 0:
                b2[bi] = player
                gained = True

        next_player = player if gained else (AI if player == HUMAN else HUMAN)
        next_depth = None if depth is None else depth - 1
        return self.minimax(tuple(e2), tuple(b2), next_player, next_depth)


def main():
    root = tk.Tk()
    root.title("Dots and Boxes")

    launcher = tk.Frame(root)
    launcher.pack(padx=60, pady=60)
    tk.Label(launcher, text="Choose mode:", font=(None, 14)).pack(pady=(0, 10))
    # timer input: two separate fields for minutes and seconds (both 0 = off)
    minutes_var = tk.StringVar(value="0")
    seconds_var = tk.StringVar(value="0")
    # tk.Label(launcher, text="Timer :").pack()
    frame_timer = tk.Frame(launcher)
    tk.Entry(frame_timer, width=5, textvariable=minutes_var).pack(side=tk.LEFT)
    tk.Label(frame_timer, text="min").pack(side=tk.LEFT, padx=(4, 8))
    tk.Entry(frame_timer, width=5, textvariable=seconds_var).pack(side=tk.LEFT)
    tk.Label(frame_timer, text="sec").pack(side=tk.LEFT, padx=(4, 0))
    frame_timer.pack(pady=(0, 10))

    def show_launcher():
        launcher.pack(padx=60, pady=60)
        root.title("Dots and Boxes")

    def start_game(size):
        configure_grid(size)
        try:
            DotsAndBoxes.minimax.cache_clear()
        except Exception:
            pass

        # Jika sudah ada game yang aktif yang masih hidup, cukup reset tanpa kembali ke menu
        prev = getattr(root, 'current_game', None)
        if prev is not None:
            # if the previous game is still alive, reset it and reuse
            if getattr(prev, '_alive', False):
                prev.reset_game()
                return
            else:
                # previous instance is torn down; clear reference and continue
                try:
                    root.current_game = None
                except Exception:
                    pass

        # hide launcher before creating a new game
        try:
            launcher.pack_forget()
        except Exception:
            pass
        root.title(f"Dots and Boxes {GRID_SIZE}x{GRID_SIZE}")
        
        # Timer parsing
        tval = None
        raw_min = minutes_var.get().strip()
        raw_sec = seconds_var.get().strip()
        try:
            mm = int(raw_min) if raw_min != "" else 0
            ss = int(raw_sec) if raw_sec != "" else 0
            if mm < 0 or ss < 0 or ss >= 60:
                raise ValueError()
            total = mm * 60 + ss
            if total > 0:
                tval = total
        except Exception:
            tval = None

        root.current_game = DotsAndBoxes(root, on_back=show_launcher, timer_seconds=tval)
        try:
            root.update_idletasks()
            root.current_game.canvas.lift()
            root.current_game.canvas.focus_set()
        except Exception:
            pass


    # expose start_game so a running DotsAndBoxes instance can start a fresh game
    root.start_game = start_game

    tk.Button(launcher, text="Easy (3x3)", width=20, command=lambda: start_game(3)).pack(pady=5)
    tk.Button(launcher, text="Hard (4x4)", width=20, command=lambda: start_game(4)).pack(pady=5)
    tk.Button(launcher, text="Quit", width=20, command=root.destroy).pack(pady=(12, 0))

    root.mainloop()


if __name__ == "__main__":
    main()