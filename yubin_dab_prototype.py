import tkinter as tk
from functools import lru_cache
import threading

# Variabel global yang digunakan
HUMAN, AI = 1, 2
EDGE_EMPTY = "gray"
HUMAN_COLOR = "green"
AI_COLOR = "red"

# Variabel global yang digunakan untuk menyimpan nilai awal dari struktur petak/papan
GRID_SIZE = 3
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
    def __init__(self, root, on_back=None):
        self.root = root
        self.on_back = on_back
        self.root.title(f"Dots and Boxes {GRID_SIZE}x{GRID_SIZE} (Human vs AI)")

        # Tampilan GUI atau dots and boxes nya
        self.canvas = tk.Canvas(root, width=500, height=500, bg="white")
        self.canvas.pack()
        self.info = tk.Label(root, text="Your turn (Green)")
        self.info.pack()
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
        if self.current_player != HUMAN:
            return
        idx = self.edge_at(event.x, event.y)
        if idx is None or self.edge_state[idx] != 0:
            return

        gained = self.apply_move(idx, HUMAN)
        self.draw_board()
        self.update_info()

        if not gained and not self.is_game_over():
            self.current_player = AI
            self.root.after(80, self.ai_move)  # AI turn
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
        if self.is_game_over():
            self.update_info()
            return

        self.info.config(text="AI thinking...")

        edges = tuple(self.edge_state)
        boxes = tuple(self.box_owner)
        depth_limit = None if GRID_SIZE <= 3 else 6  # small boards -> full search

        def worker(e, b):
            try:
                _, move = self.minimax(e, b, AI, depth_limit)
            except Exception as err:
                self.root.after(0, lambda: self.info.config(text=f"AI error: {err}"))
                return
            self.root.after(0, lambda: self._apply_ai_move(move))

        threading.Thread(target=worker, args=(edges, boxes), daemon=True).start()

    def _apply_ai_move(self, move):
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
        self.draw_board()
        self.update_info()

    def _on_back(self):
        """Destroy widgets and go back to launcher."""
        for w in (self.canvas, self.info, self.controls):
            try:
                w.destroy()
            except Exception:
                pass
        if callable(self.on_back):
            self.on_back()

    def update_info(self):
        human_score = sum(1 for b in self.box_owner if b == HUMAN)
        ai_score = sum(1 for b in self.box_owner if b == AI)

        if self.is_game_over():
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

    def show_launcher():
        launcher.pack(padx=60, pady=60)
        root.title("Dots and Boxes")

    def start_game(size):
        configure_grid(size)
        try:
            DotsAndBoxes.minimax.cache_clear()
        except Exception:
            pass
        launcher.pack_forget()
        root.title(f"Dots and Boxes {GRID_SIZE}x{GRID_SIZE}")
        DotsAndBoxes(root, on_back=show_launcher)

    tk.Button(launcher, text="Easy (3x3)", width=20, command=lambda: start_game(3)).pack(pady=5)
    tk.Button(launcher, text="Hard (4x4)", width=20, command=lambda: start_game(4)).pack(pady=5)
    tk.Button(launcher, text="Quit", width=20, command=root.destroy).pack(pady=(12, 0))

    root.mainloop()


if __name__ == "__main__":
    main()