from typing import Tuple, Dict, List

Point = Tuple[int, int]

class LineCrossCounter:
    def __init__(self, line_p1: Point, line_p2: Point, direction_vector: Point = (0, 1)):
        self.line_p1 = line_p1
        self.line_p2 = line_p2
        self.direction_vector = direction_vector
        self.history: Dict[int, List[Point]] = {}
        self.crossed_ids: set = set()

    def _cross_product(self, p1: Point, p2: Point, p3: Point) -> float:
        return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])

    def update_position(self, obj_id: int, pos: Point) -> List[Dict]:
        events = []
        if obj_id not in self.history:
            self.history[obj_id] = [pos]
            return events

        prev_pos = self.history[obj_id][-1]
        self.history[obj_id].append(pos)

        cp1 = self._cross_product(self.line_p1, self.line_p2, prev_pos)
        cp2 = self._cross_product(self.line_p1, self.line_p2, pos)

        if cp1 * cp2 < 0 and obj_id not in self.crossed_ids:
            self.crossed_ids.add(obj_id)
            direction = "forward" if cp2 > cp1 else "backward"
            events.append({
                "obj_id": obj_id,
                "direction": direction,
                "prev_pos": prev_pos,
                "curr_pos": pos
            })

        return events

    def reset_track(self, obj_id: int):
        self.history.pop(obj_id, None)
        self.crossed_ids.discard(obj_id)
