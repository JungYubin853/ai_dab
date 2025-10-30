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

def main():
    root = tk.Tk()
    game = DotsAndBoxes(root)
    root.mainloop()

if __name__ == "__main__":
    main()