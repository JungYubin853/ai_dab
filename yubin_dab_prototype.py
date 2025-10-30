import tkinter as tk
from functools import lru_cache
import threading

GRID_SIZE = 3  # 4x4 dots = 9 boxes
EDGE_EMPTY = "gray"
HUMAN_COLOR = "green"
AI_COLOR = "red"

HUMAN = 1
AI = 2

# Build box-edge mapping (computed from GRID_SIZE)
NUM_H_EDGES = GRID_SIZE * (GRID_SIZE - 1)
NUM_V_EDGES = (GRID_SIZE - 1) * GRID_SIZE
TOTAL_EDGES = NUM_H_EDGES + NUM_V_EDGES

BOXES = []
for br in range(GRID_SIZE - 1):
    for bc in range(GRID_SIZE - 1):
        top = br * (GRID_SIZE - 1) + bc
        bottom = (br + 1) * (GRID_SIZE - 1) + bc
        # vertical edges start after all horizontal edges
        left = NUM_H_EDGES + br * GRID_SIZE + bc
        right = NUM_H_EDGES + br * GRID_SIZE + (bc + 1)
        BOXES.append((top, bottom, left, right))
# (GRID_SIZE-1)^2 boxes total

class DotsAndBoxes:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Dots and Boxes {GRID_SIZE}x{GRID_SIZE} (Human vs AI)")

        self.canvas = tk.Canvas(root, width=500, height=500, bg="white")
        self.canvas.pack()

        self.spacing = 120
        self.margin = 60

        # game state (sizes depend on GRID_SIZE)
        self.edge_state = [0] * TOTAL_EDGES    # 0 empty, 1 human, 2 ai
        self.box_owner = [0] * ((GRID_SIZE - 1) * (GRID_SIZE - 1))  # 0 none, 1 human, 2 ai
        self.current_player = HUMAN   # human starts

        self.draw_board()
        self.canvas.bind("<Button-1>", self.handle_click)

        self.info = tk.Label(root, text="Your turn (Green)")
        self.info.pack()

    # ---------------- UI DRAWING ----------------
    def get_edge_coords(self):
        h_edges = []
        v_edges = []
        # horizontal
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 1):
                x1 = self.margin + c * self.spacing
                y1 = self.margin + r * self.spacing
                x2 = self.margin + (c + 1) * self.spacing
                y2 = y1
                h_edges.append((x1, y1, x2, y2))
        # vertical
        for r in range(GRID_SIZE - 1):
            for c in range(GRID_SIZE):
                x1 = self.margin + c * self.spacing
                y1 = self.margin + r * self.spacing
                x2 = x1
                y2 = self.margin + (r + 1) * self.spacing
                v_edges.append((x1, y1, x2, y2))
        return h_edges, v_edges

    def draw_board(self):
        self.canvas.delete("all")
        h_edges, v_edges = self.get_edge_coords()

        # boxes
        for i, box in enumerate(BOXES):
            owner = self.box_owner[i]
            if owner == HUMAN:
                color = HUMAN_COLOR
            elif owner == AI:
                color = AI_COLOR
            else:
                color = "#dddddd"
            br = i // (GRID_SIZE - 1)
            bc = i % (GRID_SIZE - 1)
            x = self.margin + bc * self.spacing
            y = self.margin + br * self.spacing
            self.canvas.create_rectangle(
                x + 10, y + 10,
                x + self.spacing - 10, y + self.spacing - 10,
                fill=color, outline=color
            )

        # edges
        for i, (x1, y1, x2, y2) in enumerate(h_edges):
            owner = self.edge_state[i]
            color = EDGE_EMPTY if owner == 0 else (HUMAN_COLOR if owner == HUMAN else AI_COLOR)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)
        for j, (x1, y1, x2, y2) in enumerate(v_edges):
            idx = NUM_H_EDGES + j
            owner = self.edge_state[idx]
            color = EDGE_EMPTY if owner == 0 else (HUMAN_COLOR if owner == HUMAN else AI_COLOR)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)

        # dots
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = self.margin + c * self.spacing
                y = self.margin + r * self.spacing
                self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="black")

    def edge_at(self, x, y):
        h_edges, v_edges = self.get_edge_coords()
        # horizontal
        for i, (x1, y1, x2, y2) in enumerate(h_edges):
            if abs(y - y1) <= 10 and min(x1, x2) - 10 <= x <= max(x1, x2) + 10:
                return i
        # vertical
        for j, (x1, y1, x2, y2) in enumerate(v_edges):
            idx = NUM_H_EDGES + j
            if abs(x - x1) <= 10 and min(y1, y2) - 10 <= y <= max(y1, y2) + 10:
                return idx
        return None

    # ---------------- GAME LOGIC ----------------
    def handle_click(self, event):
        if self.current_player != HUMAN:
            return
        idx = self.edge_at(event.x, event.y)
        if idx is None or self.edge_state[idx] != 0:
            return

        # Human plays
        gained = self.apply_move(idx, HUMAN)
        self.draw_board()
        self.update_info()

        # If human did NOT complete a box, AI's turn
        if not gained and not self.is_game_over():
            self.current_player = AI
            self.root.after(80, self.ai_move)
        else:
            # human gets another move
            self.current_player = HUMAN

    def apply_move(self, move_idx, player):
        """Apply move to real board. Return True if this move completed at least 1 new box."""
        self.edge_state[move_idx] = player
        gained = False
        for bi, (t, b, l, r) in enumerate(BOXES):
            if (self.edge_state[t] != 0 and self.edge_state[b] != 0 and
                self.edge_state[l] != 0 and self.edge_state[r] != 0 and
                self.box_owner[bi] == 0):
                self.box_owner[bi] = player
                gained = True
        return gained

    def is_game_over(self):
        return all(e != 0 for e in self.edge_state)

    def ai_move(self):
        """AI makes exactly 1 move, but if it gained a box, it moves again.

        The minimax search can be expensive for larger GRID_SIZE. Run the
        computation in a background thread and apply the move back on the
        main/UI thread to avoid freezing the Tk event loop.
        """
        if self.is_game_over():
            self.update_info()
            return

        # show thinking state
        self.info.config(text="AI thinking...")

        # Capture current state copies for the worker to use
        edges_snapshot = tuple(self.edge_state)
        boxes_snapshot = tuple(self.box_owner)

        def worker(edges, boxes):
            # run minimax (may take time)
            try:
                _, move = self.minimax(edges, boxes, AI)
            except Exception as e:
                # schedule error display on main thread
                self.root.after(0, lambda: self.info.config(text=f"AI error: {e}"))
                return
            # apply result on main thread
            self.root.after(0, lambda: self._apply_ai_move(move))

        t = threading.Thread(target=worker, args=(edges_snapshot, boxes_snapshot), daemon=True)
        t.start()

    def _apply_ai_move(self, move):
        """Apply AI move on the main thread (called via root.after)."""
        if move is not None:
            gained = self.apply_move(move, AI)
            self.draw_board()
            self.update_info()

            if gained and not self.is_game_over():
                # AI gets another turn
                self.current_player = AI
                # small delay before next AI computation
                self.root.after(80, self.ai_move)
            else:
                # pass to human
                self.current_player = HUMAN
        else:
            # no moves
            self.current_player = HUMAN
            self.update_info()

    def update_info(self):
        if self.is_game_over():
            h = sum(1 for b in self.box_owner if b == HUMAN)
            a = sum(1 for b in self.box_owner if b == AI)
            if h > a:
                self.info.config(text=f"Game Over! You win! ({h}:{a})")
            elif a > h:
                self.info.config(text=f"Game Over! AI wins! ({h}:{a})")
            else:
                self.info.config(text=f"Game Over! Draw! ({h}:{a})")
        else:
            h = sum(1 for b in self.box_owner if b == HUMAN)
            a = sum(1 for b in self.box_owner if b == AI)
            turn = "Your turn (Green)" if self.current_player == HUMAN else "AI thinking..."
            self.info.config(text=f"{turn} | H:{h} A:{a}")

    # ---------------- MINIMAX (with extra-turn rule) ----------------
    @lru_cache(maxsize=None)
    def minimax(self, edges, boxes, player):
        """Pure minimax, no depth, no alpha-beta, but supports extra turns."""
        # terminal
        if all(e != 0 for e in edges):
            ai_score = sum(1 for b in boxes if b == AI)
            human_score = sum(1 for b in boxes if b == HUMAN)
            return ai_score - human_score, None

        moves = [i for i, e in enumerate(edges) if e == 0]

        if player == AI:
            best_val = -999
            best_move = None
            for m in moves:
                e2 = list(edges)
                b2 = list(boxes)
                e2[m] = AI
                # check if this move closed any boxes
                gained = False
                for bi, (t, b, l, r) in enumerate(BOXES):
                    if e2[t] and e2[b] and e2[l] and e2[r] and b2[bi] == 0:
                        b2[bi] = AI
                        gained = True
                # if gained -> AI plays again, else -> human
                next_player = AI if gained else HUMAN
                val, _ = self.minimax(tuple(e2), tuple(b2), next_player)
                if val > best_val:
                    best_val = val
                    best_move = m
            return best_val, best_move
        else:
            # HUMAN turn: minimizing AI score
            best_val = 999
            best_move = None
            for m in moves:
                e2 = list(edges)
                b2 = list(boxes)
                e2[m] = HUMAN
                gained = False
                for bi, (t, b, l, r) in enumerate(BOXES):
                    if e2[t] and e2[b] and e2[l] and e2[r] and b2[bi] == 0:
                        b2[bi] = HUMAN
                        gained = True
                next_player = HUMAN if gained else AI
                val, _ = self.minimax(tuple(e2), tuple(b2), next_player)
                if val < best_val:
                    best_val = val
                    best_move = m
            return best_val, best_move

def main():
    root = tk.Tk()
    game = DotsAndBoxes(root)
    root.mainloop()

if __name__ == "__main__":
    main()