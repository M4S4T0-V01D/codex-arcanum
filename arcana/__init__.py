from .layers import FRAMES, HALOS, draw_degree, draw_motto, draw_ring
from . import hierophants  # noqa: F401  (registers the Seven Hierophants)
from .sigils import SIGILS


def draw_plate(p, t, tok):
    """Draw one frame of a token: halo -> figure -> ring -> frame -> motto."""
    tr = tok["traits"]
    if tok.get("one"):
        SIGILS[tok["sigil"]]["fn"](p, t, tok)
        draw_degree(p, 5, t)
        return
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
    if "degree_level" in tok:
        draw_degree(p, tok["degree_level"], t)
