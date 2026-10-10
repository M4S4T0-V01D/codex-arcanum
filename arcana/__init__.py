from .layers import FRAMES, HALOS, draw_motto, draw_ring
from .sigils import SIGILS


def draw_plate(p, t, tok):
    """Draw one frame of a token: halo -> figure -> ring -> frame -> motto."""
    tr = tok["traits"]
    halo = HALOS[tr["Halo"]][1]
    if halo:
        halo(p, t)
    SIGILS[tok["sigil"]]["fn"](p, t, tok)
    draw_ring(p, tr["Glyph Ring"], t)
    frame = FRAMES[tr["Frame"]][1]
    if frame:
        frame(p, t, tok)
    if tr["Motto"] != "None":
        draw_motto(p, tr["Motto"], t)
