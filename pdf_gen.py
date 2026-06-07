"""
pdf_gen.py
Generates a styled CV PDF from a CV JSON file.
Font sizes, margins, and layout are configured in cv_config.json.

Usage:
    python pdf_gen.py                          # uses default JSON from repo
    python pdf_gen.py path/to/custom.json      # uses supplied JSON
    python pdf_gen.py input.json output.pdf    # custom input + output path
"""

import json
import re
import sys
import os
from fpdf import FPDF, XPos, YPos

# ── Paths ─────────────────────────────────────────────────────────────────────
FONT_DIR  = r"C:\Windows\Fonts"
REPO_JSON = r"D:\Work\RiverO2442.github.io\anh_hao_nguyen_cv_data.json"
MATERIAL  = r"D:\Work\material"
CONFIG    = os.path.join(MATERIAL, "cv_config.json")

# ── Colours ───────────────────────────────────────────────────────────────────
INK       = (26,  26,  26)
MUTED     = (85,  85,  85)
RULE      = (212, 212, 212)
HIGHLIGHT = (255, 245, 100)


def _load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def _clean(text):
    return re.sub(r'hl\{([^}]+)\}', r'\1', str(text))


def _parse_segments(text):
    """Split text into [(content, is_highlighted), ...] on hl{} markers."""
    parts = re.split(r'hl\{([^}]+)\}', str(text))
    return [(parts[i], i % 2 == 1) for i in range(len(parts))]


class CV(FPDF):
    def __init__(self, cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sz  = cfg["sizes"]
        self.lay = cfg["layout"]
        self.fam = cfg["font"]["family"]

    def header(self): pass
    def footer(self): pass

    def _W(self):
        return self.w - self.l_margin - self.r_margin

    def _lh(self):
        return self.lay["line_height"]

    def _set(self, style="", size=10, color=INK):
        self.set_font(self.fam, style, size)
        self.set_text_color(*color)

    def _rule(self, lw=0.3):
        self.set_draw_color(*RULE)
        self.set_line_width(lw)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

    def _heavy_rule(self):
        self.set_draw_color(*INK)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

    def _gap(self, h=4):
        self.ln(h)

    def _write_rich(self, text, size, color=INK):
        """Write text inline; hl{} spans get a yellow highlight rect behind them."""
        segments = _parse_segments(text)
        self._set("", size, color)
        for seg, highlighted in segments:
            if not seg:
                continue
            if highlighted:
                x, y = self.get_x(), self.get_y()
                seg_w = self.get_string_width(seg)
                self.set_fill_color(*HIGHLIGHT)
                self.rect(x, y + 0.3, seg_w, self._lh() - 0.3, style='F')
                self._set("", size, color)
            self.write(self._lh(), seg)

    def _section_title(self, title):
        self._gap(3)
        self._set("B", self.sz["section_title"], MUTED)
        self.cell(self._W(), 5, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._rule()
        self._gap(3)

    def _para(self, text, size=None):
        sz = size or self.sz["profile"]
        self._write_rich(text, sz)
        self.ln()
        self.set_x(self.l_margin)

    def _bullet(self, text):
        self._set("", self.sz["bullet"])
        indent = self.lay["bullet_indent"]
        self.set_x(self.l_margin + indent)
        self.write(self._lh(), "—  ")
        self._write_rich(text, self.sz["bullet"])
        self.ln()
        self.set_x(self.l_margin)

    def _row(self, left, right, lsize=None, rsize=None):
        lsize = lsize or self.sz["job_title"]
        rsize = rsize or self.sz["job_date"]
        self._set("B", lsize)
        lw = self.get_string_width(left) + 2
        rw = self.get_string_width(right) + 2
        avail = self._W()
        if lw + rw <= avail:
            self.cell(lw, self._lh(), left)
            self.set_x(self.w - self.r_margin - rw)
            self._set("", rsize, MUTED)
            self.cell(rw, self._lh(), right, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.cell(avail - rw, self._lh(), left)
            self._set("", rsize, MUTED)
            self.cell(rw, self._lh(), right, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _tech_line(self, items):
        self._set("B", self.sz["tech_line"], MUTED)
        self.cell(self.get_string_width("Tech: ") + 1, self._lh(), "Tech: ")
        self._set("", self.sz["tech_line"], MUTED)
        self.multi_cell(self._W(), self._lh(), ", ".join(items),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _skill_row(self, label, values):
        LW = self.lay["skill_label_width"]
        self._set("B", self.sz["skill_label"], MUTED)
        self.cell(LW, self._lh(), label)
        self._set("", self.sz["skill_value"])
        self.multi_cell(self._W() - LW, self._lh(), ", ".join(values),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._gap(1)


def build(data: dict, output_path: str):
    cfg = _load_config()
    sz  = cfg["sizes"]
    lay = cfg["layout"]
    fnt = cfg["font"]

    ML, MR = lay["margin_left"],  lay["margin_right"]
    MT, MB = lay["margin_top"],   lay["margin_bottom"]

    font_family = fnt["family"]
    font_files  = fnt["files"]

    pdf = CV(cfg, orientation="P", unit="mm", format="A4")
    pdf.add_font(font_family, "",   os.path.join(FONT_DIR, font_files["regular"]))
    pdf.add_font(font_family, "B",  os.path.join(FONT_DIR, font_files["bold"]))
    pdf.add_font(font_family, "I",  os.path.join(FONT_DIR, font_files["italic"]))
    pdf.add_font(font_family, "BI", os.path.join(FONT_DIR, font_files["bold_italic"]))
    pdf.set_margins(ML, MT, MR)
    pdf.set_auto_page_break(auto=True, margin=MB)
    pdf.add_page()

    p       = data.get("personal_information", {})
    sk      = data.get("technical_skills", {})
    xp      = data.get("work_experience", [])
    pj      = data.get("personal_projects", [])
    ed      = data.get("education", [])
    profile = data.get("profile", "")

    W = pdf.w - ML - MR

    # ── Name ──────────────────────────────────────────────────────
    pdf._set("B", sz["name"])
    pdf.cell(W, 9, p.get("full_name", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Contact line ──────────────────────────────────────────────
    parts = [v for k in ("phone","email","github","linkedin","location") if (v := p.get(k))]
    pdf._set("", sz["contact"], MUTED)
    pdf.cell(W, 4, "  |  ".join(parts), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf._gap(3)
    pdf._heavy_rule()
    pdf._gap(4)

    # ── Profile ───────────────────────────────────────────────────
    if profile:
        pdf._section_title("Profile")
        pdf._para(profile, size=sz["profile"])

    # ── Skills ────────────────────────────────────────────────────
    lbl = data.get("skill_labels", {})
    skill_map = [
        (lbl.get("frontend",         "Frontend"),   sk.get("frontend",        [])),
        (lbl.get("languages",        "Languages"),  sk.get("languages",       [])),
        (lbl.get("state_management", "State Mgmt"), sk.get("state_management",[])),
        (lbl.get("build_tooling",    "Build"),      sk.get("build_tooling",   [])),
        (lbl.get("testing",          "Testing"),    sk.get("testing",         [])),
        (lbl.get("other",            "Other"),      sk.get("other",           [])),
    ]
    if any(v for _, v in skill_map):
        pdf._section_title("Skills")
        for label, values in skill_map:
            if values:
                pdf._skill_row(label, values)

    # ── Work Experience ───────────────────────────────────────────
    if xp:
        pdf._section_title("Work Experience")
        for job in xp:
            pdf._row(
                f"{job.get('position','')} — {job.get('company','')}",
                job.get("duration", "")
            )
            for item in job.get("responsibilities", job.get("key_achievements", [])):
                text = item if isinstance(item, str) else (
                    item.get("achievement","") + (" " + item.get("method","") if item.get("method") else "")
                )
                pdf._bullet(text.strip())
            if job.get("technologies_used"):
                pdf._tech_line(job["technologies_used"])
            pdf._gap(3)

    # ── Personal Projects ─────────────────────────────────────────
    if pj:
        pdf._section_title("Personal Project")
        for proj in pj:
            name = proj.get("name", "")
            sub  = proj.get("subtitle", "")
            pdf._row(f"{name} — {sub}" if sub else name, proj.get("duration", ""))
            if proj.get("description"):
                pdf._set("I", sz["profile"], MUTED)
                pdf.multi_cell(W, pdf._lh(), _clean(proj["description"]),
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf._gap(1)
            for item in proj.get("responsibilities", []):
                pdf._bullet(item)
            if proj.get("technologies_used"):
                pdf._tech_line(proj["technologies_used"])
            pdf._gap(3)

    # ── Education ─────────────────────────────────────────────────
    if ed:
        pdf._section_title("Education")
        for e in ed:
            inst  = e.get("institution", "")
            loc   = e.get("location", "")
            pdf._row(e.get("degree", ""), e.get("duration", ""))
            pdf._set("", sz["edu_location"], MUTED)
            pdf.cell(W, pdf._lh(), f"{inst} — {loc}" if loc else inst,
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if e.get("grade"):
                pdf._set("B", sz["edu_grade"])
                pdf.cell(W, pdf._lh(), e["grade"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf._gap(3)

    # ── Footer ────────────────────────────────────────────────────
    pdf._gap(2)
    pdf._rule(lw=0.2)
    pdf._gap(2)
    pdf._set("", sz["footer"], RULE)
    name = p.get("full_name", "").upper()
    pdf.cell(W/2, 4, f"{name} · CV 2026", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(W/2, 4, "FRONTEND DEVELOPER", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(output_path)
    print(f"[OK] PDF saved: {output_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        json_path = REPO_JSON
        pdf_path  = os.path.join(MATERIAL, "Anh_Hao_Nguyen_CV.pdf")
    elif len(args) == 1:
        json_path = args[0]
        base      = os.path.splitext(os.path.basename(args[0]))[0]
        pdf_path  = os.path.join(MATERIAL, base + ".pdf")
    else:
        json_path = args[0]
        pdf_path  = args[1]

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    build(data, pdf_path)
