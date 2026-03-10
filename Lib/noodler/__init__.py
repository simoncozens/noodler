"""
Noodler is a library for adding round strokes (noodles) to glyphs by offsetting the path and joining the ends with arcs.

It can be used on its own, or as a ufo2ft filter. The main entry point is the `noodle` function, which takes a `kurbopy` `BezPath`
object and returns a new `BezPath` with the stroke applied.
"""

from typing import Iterable, List, Union

from kurbopy import BezPath, Circle, CubicBez, Line, Point, offset_cubic
from ufo2ft.filters import BaseFilter, DecomposeTransformedComponentsFilter

Segment = Union[Line, CubicBez]

MAGIC = 0.55228


class NoodleFilter(BaseFilter):
    """A ufo2ft filter that adds a round stroke to a glyph by offsetting the path and joining the ends with arcs if necessary."""

    _kwargs = {
        "Width": 10,
        "StartCap": "round",
        "EndCap": "round",
    }

    def __init__(self, *args, **kwargs):
        self.subfilter = DecomposeTransformedComponentsFilter()
        super().__init__(*args, **kwargs)

    def set_context(self, font, glyphSet):
        self.subfilter.set_context(font, glyphSet)
        return super().set_context(font, glyphSet)

    def filter(self, glyph):
        self.subfilter.filter(glyph)

        if not len(glyph):
            return False

        # Use list here to copy, not proxy
        components = list(glyph.components)
        glyph.clearComponents()

        paths = BezPath.from_drawable(glyph)
        new_bezpaths = []
        for p in paths:
            new_bezpaths.append(
                noodle(
                    p,
                    self.options.Width,
                    start_cap=self.options.StartCap,
                    end_cap=self.options.EndCap,
                )
            )
        glyph.clearContours()
        for bez in new_bezpaths:
            bez.draw(glyph.getPen())
        glyph.components = components
        return True


def noodle(
    p: BezPath, size: float, start_cap: str = "round", end_cap: str = "round"
) -> BezPath:
    """Offset a BezPath by `size` in both directions, and join the ends with arcs if necessary.

    This is the main entry point of this library.
    """
    if start_cap not in ["round", "butt"]:
        raise ValueError(f"Invalid start cap: {start_cap}")
    if end_cap not in ["round", "butt"]:
        raise ValueError(f"Invalid end cap: {end_cap}")
    offset_paths = [offset_seg(seg, size, 0.001) for seg in p.segments()]
    final_path = join_paths(offset_paths)
    offset_paths2 = [
        offset_seg(seg, size, 0.001) for seg in p.reverse_subpaths().segments()
    ]
    joining_segs = join_path(
        offset_paths[-1], offset_paths2[0], arc=(start_cap == "round")
    )
    for seg in joining_segs:
        push_seg(final_path, seg)
    fp2 = join_paths(offset_paths2, arc=True)
    for el in list(fp2.elements())[1:]:
        final_path.push(el)
    joining_segs = join_path(
        offset_paths2[-1], offset_paths[0], arc=(end_cap == "round")
    )
    for seg in joining_segs:
        push_seg(final_path, seg)
    final_path.close_path()
    return final_path


def join_path(p1, p2, arc=False):
    ls = list(p1.segments())[-1]
    ns = next(p2.segments())
    return join_segs(ls, ns, arc=arc)


def join_segs(
    ls: Union[CubicBez, Line], ns: Union[CubicBez, Line], arc=False
) -> Iterable[Union[CubicBez, Line]]:
    """Join two segments together.

    Join two Line/CubicBez segments with a CubicBez if they don't already meet at the end/start point.
    If `arc` is `True`, use an arc instead of a cubic bezier if the segments are too far apart; if
    not, use a line."""
    l1 = Line(ls.eval(0.99), ls.end())
    l2 = Line(ns.start(), ns.eval(0.01))
    pt = l1.crossing_point(l2)
    if not pt or pt.distance(ls.end()) > 100 * ls.end().distance(ns.start()):
        if arc:
            midpoint = ls.end().lerp(ns.start(), 0.5)
            circle = Circle(midpoint, midpoint.distance(ls.end()))
            start = (ls.end().to_vec2() - midpoint.to_vec2()).atan2()
            sweepangle = (ns.start().to_vec2() - midpoint.to_vec2()).atan2() - (
                ls.end().to_vec2() - midpoint.to_vec2()
            ).atan2()
            sweepangle = -abs(sweepangle)
            circleseg = list(
                circle.segment(
                    0,
                    start,
                    sweepangle,
                )
                .to_path(0.1)
                .segments()
            )
            return circleseg[1:3]
        else:
            return [Line(ls.end(), ns.start())]

    return [
        CubicBez(
            ls.end(), ls.end().lerp(pt, MAGIC), ns.start().lerp(pt, MAGIC), ns.start()
        )
    ]


def end_pt(path: BezPath) -> Point:
    return list(path.segments())[-1].end()


def start_pt(path: BezPath) -> Point:
    return next(path.segments()).start()


def join_paths(paths: List[BezPath], arc=False) -> BezPath:
    new = BezPath()
    last = None
    for p in paths:
        if last and end_pt(last).distance(start_pt(p)) > 0.01:
            for seg in join_path(last, p, arc=arc):
                push_seg(new, seg)
        els = list(p.elements())
        if last is not None:  # There's a move already
            els = els[1:]
        for el in els:
            new.push(el)
        last = p
    return new


def push_seg(path: BezPath, seg: Segment):
    if isinstance(seg, Line):
        path.line_to(seg.end())
    else:
        path.curve_to(seg.p1, seg.p2, seg.p3)


def offset_seg(seg: Segment, d: float, tol: float) -> BezPath:
    if isinstance(seg, Line):
        cubic_seg = CubicBez(
            seg.start(), seg.eval(1 / 3.0), seg.eval(2 / 3.0), seg.end()
        )
        c = offset_cubic(cubic_seg, d, tol)
        n = BezPath()
        n.move_to(start_pt(c))
        n.line_to(end_pt(c))
        return n
    else:
        return offset_cubic(seg, d, tol)


# I found that we didn't need path fitting for any cases so far.
# Keeping it here in case it becomes useful later.

# def segs_ts_and_lengths(segs):
#     segs = list(segs)
#     ts = [0.0]
#     lengths = []
#     len_total = 0.0
#     for seg in segs:
#         l = seg.arclen(0.01)
#         lengths.append(l)
#         len_total += l
#     for i in range(len(lengths)):
#         ts.append(ts[-1] + lengths[i] / len_total)
#     return [
#         {"start_t": t, "length": l, "seg": seg}
#         for t, l, seg in zip(ts[:-1], lengths, segs)
#     ]


# def change_domain(t, seglist) -> Tuple[float, CubicBez]:
#     for i in range(len(seglist) - 1):
#         if seglist[i]["start_t"] <= t < seglist[i + 1]["start_t"]:
#             local_t = (t - seglist[i]["start_t"]) / (
#                 seglist[i + 1]["start_t"] - seglist[i]["start_t"]
#             )
#             return local_t, seglist[i]["seg"]
#     # So it's in the last segment
#     local_t = (t - seglist[-1]["start_t"]) / (1.0 - seglist[-1]["start_t"])
#     return local_t, seglist[-1]["seg"]


# class PathFitter:
#     def __init__(self, paths: List[BezPath], orig: BezPath):
#         self.paths = paths
#         self.orig = orig

#         all_paths_segs = []
#         for p in self.paths:
#             all_paths_segs.extend(p.segments())
#         self.paths_segs = segs_ts_and_lengths(all_paths_segs)
#         self.orig_segs = segs_ts_and_lengths(list(self.orig.segments()))

#     def sample_pt_tangent(self, t, _sign) -> Tuple[Point, Vec2]:
#         # Get the point from the paths list, but the tangent from the original path
#         local_t, seg = change_domain(t, self.paths_segs)
#         pt = seg.eval(local_t)
#         # We assume no cusps/corners at this point. Get more clever later
#         local_t_orig, seg_orig = change_domain(t, self.orig_segs)
#         deriv = seg_orig.deriv().eval(local_t_orig)
#         return pt, deriv.to_vec2()

#     def sample_pt_deriv(self, t) -> Tuple[Point, Vec2]:
#         local_t, seg = change_domain(t, self.paths_segs)
#         pt = seg.eval(local_t)
#         local_t_orig, seg_orig = change_domain(t, self.orig_segs)
#         deriv = seg_orig.deriv().eval(local_t_orig)
#         return pt, deriv.to_vec2()

#     def break_cusp(self, start, end):
#         return None
