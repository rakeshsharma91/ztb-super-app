from flask import Blueprint, request, jsonify, send_file
from models import db, UserResponse, PricingSKU, TCOEntry
from routes.admin_sections_routes import evaluate_sections
import re, io
from datetime import datetime

export_ppt_bp = Blueprint('export_ppt', __name__)

def _make_slug(name):
    slug = (name or 'unknown').strip().lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or 'unknown'

def _find_by_slug(customer_slug):
    rows = (UserResponse.query
            .filter_by(status='completed')
            .order_by(UserResponse.completed_at.desc())
            .all())
    for r in rows:
        if _make_slug(r.customer_name) == customer_slug:
            return r
    return None


@export_ppt_bp.route('/user/<customer_slug>/export-pptx', methods=['POST'])
def export_pptx(customer_slug):
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np

    user_resp = _find_by_slug(customer_slug)
    if not user_resp:
        return jsonify({'error': 'Not found'}), 404

    data         = request.get_json() or {}
    pricing_rows = data.get('pricing_rows', [])
    phase        = data.get('phase', 'standard')
    support_pct  = float(data.get('support_pct', 20) or 20)
    margin_pct   = float(data.get('margin_pct',  20) or 20)
    services_amt = float(data.get('services_amt', 0) or 0)
    tco_rows     = data.get('tco_rows', [])
    fte_count    = float(data.get('fte_count',   0) or 0)
    fte_cost     = float(data.get('fte_cost',    0) or 0)
    breach_cost  = float(data.get('breach_cost', 0) or 0)
    acv          = float(data.get('acv', 0) or 0)

    section_outcomes = evaluate_sections(user_resp.answers or {})

    NAVY   = RGBColor(0x00, 0x22, 0x44)
    NAVY2  = RGBColor(0x00, 0x33, 0x66)
    NAVY3  = RGBColor(0x0D, 0x2D, 0x52)
    ACCENT = RGBColor(0x00, 0xAA, 0xFF)
    WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
    MUTED  = RGBColor(0xA0, 0xBC, 0xD8)
    GREEN  = RGBColor(0x00, 0xDC, 0x82)
    AMBER  = RGBColor(0xF5, 0x9E, 0x0B)
    RED    = RGBColor(0xF8, 0x71, 0x71)
    BLUE   = RGBColor(0x00, 0x70, 0xC0)

    W = Inches(13.33)
    H = Inches(7.5)

    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    BL = prs.slide_layouts[6]

    def _bg(slide, color=None):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color or NAVY

    def _box(slide, text, l, t, w, h,
             sz=16, bold=False, color=None, italic=False, align=PP_ALIGN.LEFT):
        txb = slide.shapes.add_textbox(l, t, w, h)
        tf  = txb.text_frame
        tf.word_wrap = True
        p   = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text           = text
        run.font.size      = Pt(sz)
        run.font.bold      = bold
        run.font.italic    = italic
        run.font.color.rgb = color or WHITE
        return txb

    def _rect(slide, l, t, w, h, color):
        s = slide.shapes.add_shape(1, l, t, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = color
        s.line.fill.background()
        return s

    def _fmt(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return '—'
        if v == 0:
            return '—'
        if v >= 1_000_000:
            return f'${v/1_000_000:.1f}M'
        if v >= 1_000:
            return f'${int(round(v/1000))}K'
        return f'${int(round(v)):,}'

    def _fmt_exact(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return '—'
        if v == 0:
            return '—'
        return f'${int(round(v)):,}'


    # ── pricing calculations ───────────────────────────────────────────────
    skus      = PricingSKU.query.filter_by(active=True).all()
    app_map   = {s.id: s for s in skus if s.category == 'appliance'}
    sdwan_map = {s.id: s for s in skus if s.category == 'sdwan'}
    seg_map   = {s.id: s for s in skus if s.category == 'segmentation'}

    def _sku_price(mapping, sid):
        if not sid:
            return 0
        try:
            s = mapping.get(int(sid))
        except (ValueError, TypeError):
            return 0
        return float(getattr(s, phase, 0) or 0) if s else 0

    al_total  = 0
    bom_lines = []
    for row in pricing_rows:
        qty    = int(row.get('qty', 0) or 0)
        app_p  = _sku_price(app_map,   row.get('appliance_id'))
        sdw_p  = _sku_price(sdwan_map, row.get('sdwan_id'))
        seg_p  = _sku_price(seg_map,   row.get('seg_id'))
        site_t = app_p + sdw_p + seg_p
        line_t = qty * site_t
        al_total += line_t
        if qty > 0:
            bom_lines.append((row.get('label', '—'), qty,
                              app_p, sdw_p, seg_p, site_t, line_t))

    support_amt = round(al_total * support_pct / 100)
    margin_amt  = round(al_total * margin_pct  / 100)
    annual_rec  = al_total + support_amt + margin_amt
    yr1_total   = annual_rec + services_amt

    # multiplier for exec summary: bake support + margin into per-site cost
    _sm_mult = 1 + (support_pct / 100) + (margin_pct / 100)

    # ── TCO calculations ───────────────────────────────────────────────────
    tco_catalog = {e.id: float(e.annual_cost or 0)
                   for e in TCOEntry.query.filter_by(active=True).all()}
    TCO_CATS = ['fw_ns','sdwan','mpls','fw_ew','iot_ot','nac','l3sw','pam']
    legacy_hw = 0.0
    for row in tco_rows:
        qty = int(row.get('qty', 0) or 0)
        for cat in TCO_CATS:
            eid = row.get(f'{cat}_id')
            if eid:
                try:
                    legacy_hw += tco_catalog.get(int(eid), 0) * qty
                except (ValueError, TypeError):
                    pass

    legacy_total = legacy_hw + fte_count * fte_cost + breach_cost
    annual_sav   = legacy_total - acv
    yr3_sav      = annual_sav * 3
    roi_pct      = round(annual_sav / legacy_total * 100) if legacy_total > 0 else 0
    payback_mo   = round((acv / annual_sav) * 12) if annual_sav > 0 else None

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 1 — Title
    # ══════════════════════════════════════════════════════════════════════
    s1 = prs.slides.add_slide(BL)
    _bg(s1, NAVY)
    _rect(s1, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _rect(s1, Inches(0.35), Inches(2.25), Inches(12.6), Emu(55000), ACCENT)
    _box(s1, 'ZTB OPPORTUNITY PACKAGE',
         Inches(0.5), Inches(0.55), Inches(11), Inches(0.6),
         sz=12, bold=True, color=ACCENT)
    _box(s1, user_resp.customer_name,
         Inches(0.5), Inches(1.05), Inches(12), Inches(1.1),
         sz=46, bold=True, color=WHITE)
    meta = []
    if user_resp.se_name:
        meta.append(f'Solutions Consultant: {user_resp.se_name}')
    if user_resp.completed_at:
        meta.append(user_resp.completed_at.strftime('%B %d, %Y'))
    if meta:
        _box(s1, '     '.join(meta),
             Inches(0.5), Inches(2.5), Inches(11), Inches(0.5),
             sz=14, color=MUTED)
    _box(s1, 'Zero Trust Branch  ·  Zscaler',
         Inches(0.5), Inches(6.75), Inches(7), Inches(0.45),
         sz=11, color=MUTED, italic=True)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 2 — Value Drivers  (fully auto-scaling)
    # ══════════════════════════════════════════════════════════════════════
    s2 = prs.slides.add_slide(BL)
    _bg(s2, NAVY)
    _rect(s2, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _box(s2, 'VALUE DRIVERS',
         Inches(0.4), Inches(0.2), Inches(11), Inches(0.42),
         sz=11, bold=True, color=ACCENT)
    _box(s2, 'Current State → Future State with Zscaler ZTB',
         Inches(0.4), Inches(0.6), Inches(11), Inches(0.48),
         sz=22, bold=True, color=WHITE)
    _rect(s2, Inches(0.4), Inches(1.12), Inches(12.7), Emu(40000), ACCENT)

    drivers = [s for s in section_outcomes if s.get('format') == 'value_driver']
    if not drivers:
        _box(s2, 'No value drivers configured for this assessment.',
             Inches(0.5), Inches(2.0), Inches(11), Inches(0.5),
             sz=14, color=MUTED, italic=True)
    else:
        col_x = [Inches(0.4),  Inches(2.75), Inches(7.8)]
        col_w = [Inches(2.2),  Inches(4.9),  Inches(4.9)]

        # Column header row
        hdrs = ['DRIVER', 'CURRENT STATE', 'FUTURE STATE (ZTB)']
        HDR_Y  = Inches(1.2)
        HDR_H  = Inches(0.38)
        for i, h in enumerate(hdrs):
            _rect(s2, col_x[i], HDR_Y, col_w[i]-Inches(0.05), HDR_H, NAVY2)
            _box(s2, h, col_x[i]+Inches(0.07), HDR_Y,
                 col_w[i], HDR_H, sz=9, bold=True, color=ACCENT)

        TABLE_TOP    = Inches(1.62)
        TABLE_BOTTOM = Inches(7.2)          # leave small bottom margin
        AVAILABLE    = TABLE_BOTTOM - TABLE_TOP
        n            = min(len(drivers), 7)

        # --- estimate relative weights (line count) per row ---
        LINES_PER_INCH = 8.5   # approximate for sz=8 with word wrap in 4.8" column
        PAD_INCH       = 0.18  # top+bottom padding per row

        def _est_lines(drv):
            # count bullet lines; each line ~15 words in a 4.8" col at sz=8
            def count(lines):
                total = 0
                for ln in lines:
                    words = len((ln or '').split())
                    total += max(1, -(-words // 10))   # ceiling div at sz=11
                return total
            return max(
                count(drv.get('current_state_lines', [])),
                count(drv.get('future_state_lines',  [])),
                1
            )

        weights   = [_est_lines(d) for d in drivers[:n]]
        total_w   = sum(weights)
        # minimum row height = 0.55", scale up proportionally to fill slide
        MIN_H     = Inches(0.7)
        raw_heights = [max(MIN_H, (w / total_w) * float(AVAILABLE)) for w in weights]

        # if total raw < available, distribute leftover evenly
        leftover = float(AVAILABLE) - sum(raw_heights)
        if leftover > 0:
            bonus = leftover / n
            raw_heights = [rh + bonus for rh in raw_heights]

        y_cursor = TABLE_TOP
        for ri, drv in enumerate(drivers[:n]):
            rh   = int(raw_heights[ri])
            bg_  = NAVY3 if ri % 2 == 0 else NAVY2
            PAD  = Emu(int(Inches(0.06)))

            # background rects
            for i in range(3):
                _rect(s2, col_x[i], y_cursor,
                      col_w[i]-Inches(0.05), rh - int(Inches(0.03)), bg_)

            # DRIVER label — vertically centred in row
            _box(s2, drv.get('label', ''),
                 col_x[0]+Inches(0.1), y_cursor + PAD,
                 col_w[0]-Inches(0.15), rh,
                 sz=11, bold=True, color=ACCENT)

            # Current State — textbox height = full row so word-wrap has room
            _box(s2, '\n'.join(drv.get('current_state_lines', [])),
                 col_x[1]+Inches(0.08), y_cursor + PAD,
                 col_w[1]-Inches(0.15), rh,
                 sz=11, color=WHITE)

            # Future State
            _box(s2, '\n'.join(drv.get('future_state_lines', [])),
                 col_x[2]+Inches(0.08), y_cursor + PAD,
                 col_w[2]-Inches(0.15), rh,
                 sz=11, color=WHITE)

            y_cursor += rh

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 3 — Pricing Executive Summary
    # ══════════════════════════════════════════════════════════════════════
    s3 = prs.slides.add_slide(BL)
    _bg(s3, NAVY)
    _rect(s3, Inches(0), Inches(0), Inches(0.2), H, BLUE)
    _box(s3, 'PRICING SUMMARY',
         Inches(0.4), Inches(0.2), Inches(12), Inches(0.42),
         sz=11, bold=True, color=BLUE)
    _box(s3, 'Executive Overview',
         Inches(0.4), Inches(0.6), Inches(12), Inches(0.48),
         sz=22, bold=True, color=WHITE)
    _rect(s3, Inches(0.4), Inches(1.12), Inches(12.7), Emu(40000), BLUE)

    # full-width columns
    COL_X = [Inches(0.4),  Inches(5.8),  Inches(9.4)]
    COL_W = [Inches(5.2),  Inches(3.4),  Inches(3.53)]

    HDR_Y = Inches(1.22)
    HDR_H = Inches(0.42)
    for i, h in enumerate(['SITE LABEL', 'COST PER SITE', 'LINE TOTAL']):
        _rect(s3, COL_X[i], HDR_Y, COL_W[i] - Inches(0.05), HDR_H, NAVY2)
        align = PP_ALIGN.RIGHT if i > 0 else PP_ALIGN.LEFT
        _box(s3, h, COL_X[i]+Inches(0.14), HDR_Y+Inches(0.05),
             COL_W[i]-Inches(0.18), HDR_H,
             sz=10, bold=True, color=ACCENT, align=align)

    active = [
        (lbl, round(site_t * _sm_mult), round(qty * site_t * _sm_mult))
        for lbl, qty, app_p, sdw_p, seg_p, site_t, line_t in bom_lines
    ]

    # rows fill available space; cap so GT+pills+footer always fit below
    TABLE_TOP    = Inches(1.67)
    BELOW_BUDGET = Inches(3.1)   # GT bar + gap + label + pills + footer
    MAX_BOTTOM   = H - BELOW_BUDGET
    MIN_ROW_H    = int(Inches(0.45))
    n_rows       = max(len(active), 1)
    TABLE_BOTTOM = min(Inches(4.2), MAX_BOTTOM)
    ROW_H        = max(MIN_ROW_H, int((TABLE_BOTTOM - TABLE_TOP) / n_rows))

    y_cur = int(TABLE_TOP)
    for ri, (lbl, cost_per_site, line_total) in enumerate(active):
        bg_  = NAVY3 if ri % 2 == 0 else NAVY2
        PAD  = int(Inches(0.12))
        for i in range(3):
            _rect(s3, COL_X[i], y_cur,
                  COL_W[i]-Inches(0.05), ROW_H-int(Inches(0.03)), bg_)
        _box(s3, lbl,
             COL_X[0]+Inches(0.14), y_cur+PAD,
             COL_W[0]-Inches(0.2), ROW_H,
             sz=18, bold=True, color=ACCENT)
        _box(s3, _fmt_exact(cost_per_site),
             COL_X[1]+Inches(0.05), y_cur+PAD,
             COL_W[1]-Inches(0.1), ROW_H,
             sz=18, color=WHITE, align=PP_ALIGN.RIGHT)
        _box(s3, _fmt_exact(line_total),
             COL_X[2]+Inches(0.05), y_cur+PAD,
             COL_W[2]-Inches(0.1), ROW_H,
             sz=18, bold=True, color=WHITE, align=PP_ALIGN.RIGHT)
        y_cur += ROW_H

    # grand total — full width, flush below last row
    GT_Y = y_cur + int(Inches(0.12))
    _rect(s3, Inches(0.4), GT_Y, Inches(12.53), Inches(0.7), NAVY2)
    _rect(s3, Inches(0.4), GT_Y, Inches(0.08), Inches(0.7), BLUE)
    _box(s3, 'GRAND TOTAL',
         Inches(0.6), GT_Y+Inches(0.12), Inches(5.0), Inches(0.48),
         sz=16, bold=True, color=WHITE)
    _box(s3, _fmt_exact(annual_rec),
         Inches(5.8), GT_Y+Inches(0.08), Inches(6.9), Inches(0.54),
         sz=22, bold=True, color=ACCENT, align=PP_ALIGN.RIGHT)

    # licenses — full width, flush below grand total
    LIC_Y = GT_Y + Inches(1.3)
    _box(s3, 'LICENSES INCLUDED',
         Inches(0.4), LIC_Y-Inches(0.28), Inches(12), Inches(0.26),
         sz=9, bold=True, color=MUTED)

    has_sdwan = any(row.get('sdwan_id') for row in pricing_rows)
    has_seg   = any(row.get('seg_id')   for row in pricing_rows)
    lic_labels = []
    if has_sdwan: lic_labels.append('SD-WAN Licenses')
    if has_seg:   lic_labels.append('Segmentation Licenses')
    if not lic_labels: lic_labels = ['Appliance only — no software licenses']

    n_pills = len(lic_labels)
    pill_w  = int((Inches(12.53) - int(Inches(0.15)) * (n_pills - 1)) / n_pills)
    pill_x  = int(Inches(0.4))
    for lic in lic_labels:
        _rect(s3, pill_x, LIC_Y, pill_w, int(Inches(0.55)), NAVY2)
        _rect(s3, pill_x, LIC_Y, int(Inches(0.07)), int(Inches(0.55)), BLUE)
        _box(s3, lic, pill_x+int(Inches(0.16)), LIC_Y+int(Inches(0.1)),
             pill_w-int(Inches(0.24)), int(Inches(0.42)),
             sz=13, bold=True, color=WHITE)
        pill_x += pill_w + int(Inches(0.15))

    _box(s3, f'Phase: {phase.upper()}  ·  Annual Recurring: {_fmt(annual_rec)}',
         Inches(0.4), LIC_Y+Inches(0.65), Inches(12.5), Inches(0.3),
         sz=9, color=MUTED, italic=True, align=PP_ALIGN.RIGHT)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 4 — TCO KPIs + Bar Chart
    # ══════════════════════════════════════════════════════════════════════
    s4 = prs.slides.add_slide(BL)
    _bg(s4, NAVY)
    _rect(s4, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _box(s4, 'TCO ANALYSIS',
         Inches(0.4), Inches(0.2), Inches(8), Inches(0.42),
         sz=11, bold=True, color=ACCENT)
    _box(s4, 'Legacy Infrastructure vs. Zscaler ZTB',
         Inches(0.4), Inches(0.6), Inches(8), Inches(0.48),
         sz=22, bold=True, color=WHITE)
    _rect(s4, Inches(0.4), Inches(1.12), Inches(12.7), Emu(40000), ACCENT)

    kpis = [
        ('Legacy Annual Spend', _fmt(legacy_total), RED,   'HW + FTE + Breach Risk'),
        ('Annual Savings',      _fmt(annual_sav),   GREEN, 'Legacy − Zscaler ACV'),
        ('3-Year Savings',      _fmt(yr3_sav),      GREEN, '3× Annual Savings'),
        ('ROI',                 f'{roi_pct}%',       AMBER,
         f'Payback: ~{payback_mo} months' if payback_mo else 'Set ACV above'),
    ]
    kw = Inches(3.0); kh = Inches(1.55); kg = Inches(0.18)
    for i, (title, val, col, sub) in enumerate(kpis):
        kx = Inches(0.4) + i * (kw + kg)
        _rect(s4, kx, Inches(1.25), kw, kh, NAVY3)
        _rect(s4, kx, Inches(1.25), Inches(0.07), kh, col)
        _box(s4, title, kx+Inches(0.15), Inches(1.37), kw, Inches(0.35),
             sz=8, bold=True, color=MUTED)
        _box(s4, val, kx+Inches(0.1), Inches(1.7), kw-Inches(0.1), Inches(0.6),
             sz=26, bold=True, color=col)
        if sub:
            _box(s4, sub, kx+Inches(0.15), Inches(2.3), kw, Inches(0.3),
                 sz=8, color=MUTED, italic=True)

    fig, ax = plt.subplots(figsize=(12.5, 3.5), facecolor='#002244')
    ax.set_facecolor('#002244')
    x_pos = [0, 1, 2]
    ax.bar([x-0.22 for x in x_pos], [legacy_total]*3, 0.38,
           color='#f87171', label='Legacy Annual Cost', zorder=3)
    ax.bar([x+0.22 for x in x_pos], [acv]*3, 0.38,
           color='#00d9ff', label='Zscaler ACV', zorder=3)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Year 1','Year 2','Year 3'], color='#a0bcd8', fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'${v/1e6:.1f}M' if v >= 1e6 else f'${v/1e3:.0f}K'))
    ax.tick_params(axis='y', colors='#a0bcd8', labelsize=10)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.yaxis.grid(True, color='#0a2a50', linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(facecolor='#0a2244', edgecolor='#003366',
              labelcolor='#a0bcd8', fontsize=10, loc='upper right')
    plt.tight_layout(pad=0.3)
    chart_buf = io.BytesIO()
    fig.savefig(chart_buf, format='png', dpi=130,
                facecolor='#002244', bbox_inches='tight')
    plt.close(fig)
    chart_buf.seek(0)
    s4.shapes.add_picture(chart_buf, Inches(0.35), Inches(2.95),
                          Inches(12.6), Inches(4.25))

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 5 — Thank You
    # ══════════════════════════════════════════════════════════════════════
    s5 = prs.slides.add_slide(BL)
    _bg(s5, NAVY)
    _rect(s5, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _rect(s5, Inches(0.35), Inches(3.85), Inches(12.6), Emu(55000), ACCENT)
    _box(s5, 'Thank You',
         Inches(0.5), Inches(1.3), Inches(12), Inches(1.2),
         sz=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _box(s5, user_resp.customer_name,
         Inches(0.5), Inches(2.65), Inches(12), Inches(0.6),
         sz=20, color=ACCENT, align=PP_ALIGN.CENTER)
    _box(s5, 'Zscaler Zero Trust Branch',
         Inches(0.5), Inches(4.15), Inches(12), Inches(0.55),
         sz=16, color=MUTED, align=PP_ALIGN.CENTER, italic=True)
    if user_resp.se_name:
        _box(s5, user_resp.se_name,
             Inches(0.5), Inches(4.85), Inches(12), Inches(0.45),
             sz=13, color=MUTED, align=PP_ALIGN.CENTER)
    _box(s5, '© 2025 Zscaler, Inc. — Internal Sales Engineering Tool',
         Inches(0.5), Inches(6.8), Inches(12), Inches(0.35),
         sz=9, color=RGBColor(0x40, 0x60, 0x80),
         align=PP_ALIGN.CENTER, italic=True)

    # ── stream ─────────────────────────────────────────────────────────────
    out = io.BytesIO()
    prs.save(out)
    out.seek(0)
    safe  = (user_resp.customer_name or 'Customer').replace(' ', '_').replace('/', '_')
    fname = f"ZTB_{safe}_{datetime.utcnow().strftime('%Y%m%d')}.pptx"
    return send_file(
        out,
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True,
        download_name=fname
    )

# ══════════════════════════════════════════════════════════════════════════════
# POV DECK EXPORT  —  /user/<slug>/export-pov-deck
# Slides: Title · Success Criteria · Pre-POV Checklist · POV Timeline · Thank You
# ══════════════════════════════════════════════════════════════════════════════

@export_ppt_bp.route('/user/<customer_slug>/export-pov-deck', methods=['POST'])
def export_pov_deck(customer_slug):
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    user_resp = _find_by_slug(customer_slug)
    if not user_resp:
        return jsonify({'error': 'Not found'}), 404

    NAVY   = RGBColor(0x00, 0x22, 0x44)
    NAVY2  = RGBColor(0x00, 0x33, 0x66)
    NAVY3  = RGBColor(0x0D, 0x2D, 0x52)
    ACCENT = RGBColor(0x00, 0xAA, 0xFF)
    WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
    MUTED  = RGBColor(0xA0, 0xBC, 0xD8)
    GREEN  = RGBColor(0x00, 0xDC, 0x82)
    AMBER  = RGBColor(0xF5, 0x9E, 0x0B)
    BLUE   = RGBColor(0x00, 0x70, 0xC0)

    W = Inches(13.33)
    H = Inches(7.5)

    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    BL = prs.slide_layouts[6]

    def _bg(slide, color=None):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color or NAVY

    def _box(slide, text, l, t, w, h,
             sz=16, bold=False, color=None, italic=False, align=PP_ALIGN.LEFT):
        txb = slide.shapes.add_textbox(l, t, w, h)
        tf  = txb.text_frame
        tf.word_wrap = True
        p   = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text           = text
        run.font.size      = Pt(sz)
        run.font.bold      = bold
        run.font.italic    = italic
        run.font.color.rgb = color or WHITE
        return txb

    def _rect(slide, l, t, w, h, color):
        s = slide.shapes.add_shape(1, l, t, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = color
        s.line.fill.background()
        return s

    def _slide_header(slide, eyebrow, title, accent_color=None):
        ac = accent_color or ACCENT
        _rect(slide, Inches(0), Inches(0), Inches(0.2), H, ac)
        _box(slide, eyebrow,
             Inches(0.4), Inches(0.2), Inches(12), Inches(0.42),
             sz=11, bold=True, color=ac)
        _box(slide, title,
             Inches(0.4), Inches(0.6), Inches(12), Inches(0.52),
             sz=22, bold=True, color=WHITE)
        _rect(slide, Inches(0.4), Inches(1.15), Inches(12.7), Emu(40000), ac)

    raw       = user_resp.raw_responses or {}
    prepov    = raw.get('prepov_data', {})
    checks    = prepov.get('checks', {})
    notes_map = prepov.get('notes', {})
    tl_rows   = prepov.get('pov_timeline_v2', [])

    results   = user_resp.results or {}
    asset_ids = results.get('asset_ids', [])
    all_assets = []
    if asset_ids:
        from models import Asset
        all_assets = Asset.query.filter(Asset.id.in_(asset_ids)).all()
    success_criteria = [
        a for a in all_assets
        if (a.asset_type or '').lower() in ('success criteria', 'success_criteria')
    ]

    CHECKLIST_ITEMS = [
        ('arch_workshops',   'Architecture & Design Workshops'),
        ('stakeholders',     'Stakeholders Defined'),
        ('budget_owners',    'Budget Owners Defined'),
        ('costs_defined',    'Estimated Costs & Commercials Defined'),
        ('test_cases',       'POV Test Cases, Requirements & Scope Defined'),
        ('tech_feasibility', 'Technical Feasibility Review'),
        ('logistics',        'Logistics, Timeline & Roles Defined'),
        ('signoffs',         'POV Sign-Offs Completed by all Parties'),
    ]

    # SLIDE 1 — Title
    s1 = prs.slides.add_slide(BL)
    _bg(s1, NAVY)
    _rect(s1, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _rect(s1, Inches(0.35), Inches(2.25), Inches(12.6), Emu(55000), ACCENT)
    _box(s1, 'PROOF OF VALUE — POV DECK',
         Inches(0.5), Inches(0.55), Inches(11), Inches(0.6),
         sz=12, bold=True, color=ACCENT)
    _box(s1, user_resp.customer_name or 'Customer',
         Inches(0.5), Inches(1.05), Inches(12), Inches(1.1),
         sz=46, bold=True, color=WHITE)
    meta = []
    if user_resp.se_name:
        meta.append(f'Solutions Consultant: {user_resp.se_name}')
    if user_resp.completed_at:
        meta.append(user_resp.completed_at.strftime('%B %d, %Y'))
    if meta:
        _box(s1, '     '.join(meta),
             Inches(0.5), Inches(2.5), Inches(11), Inches(0.5),
             sz=14, color=MUTED)
    _box(s1, 'Zero Trust Branch  ·  Zscaler',
         Inches(0.5), Inches(6.75), Inches(7), Inches(0.45),
         sz=11, color=MUTED, italic=True)

    # SLIDE 2 — Success Criteria
    s2 = prs.slides.add_slide(BL)
    _bg(s2, NAVY)
    _slide_header(s2, 'POV SUCCESS CRITERIA',
                  'Agreed criteria for a successful Proof of Value', BLUE)
    if not success_criteria:
        _box(s2, 'No success criteria have been tagged for this assessment.',
             Inches(0.5), Inches(2.0), Inches(12), Inches(0.5),
             sz=14, color=MUTED, italic=True)
    else:
        TABLE_TOP = Inches(1.32)
        n         = min(len(success_criteria), 8)
        ROW_H     = max(int((Inches(7.1) - TABLE_TOP) / n), int(Inches(0.55)))
        COL_NUM_X = Inches(0.4);  COL_NUM_W = Inches(0.5)
        COL_TIT_X = Inches(0.95); COL_TIT_W = Inches(5.8)
        COL_DSC_X = Inches(6.85); COL_DSC_W = Inches(6.25)
        HDR_Y = int(TABLE_TOP); HDR_H = int(Inches(0.38))
        for cx, cw, lbl in [(COL_NUM_X,COL_NUM_W,'#'),(COL_TIT_X,COL_TIT_W,'SUCCESS CRITERIA'),(COL_DSC_X,COL_DSC_W,'DESCRIPTION')]:
            _rect(s2, cx, HDR_Y, cw, HDR_H, NAVY2)
            _box(s2, lbl, cx+Inches(0.08), HDR_Y, cw, HDR_H, sz=9, bold=True, color=BLUE)
        y = HDR_Y + HDR_H
        for i, sc in enumerate(success_criteria[:n]):
            bg_ = NAVY3 if i%2==0 else NAVY2
            PAD = int(Inches(0.1))
            for cx, cw in [(COL_NUM_X,COL_NUM_W),(COL_TIT_X,COL_TIT_W),(COL_DSC_X,COL_DSC_W)]:
                _rect(s2, cx, y, cw, ROW_H-int(Inches(0.03)), bg_)
            _box(s2, str(i+1), COL_NUM_X+Inches(0.08), y+PAD, COL_NUM_W, ROW_H,
                 sz=11, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
            title = (getattr(sc,'asset_name',None) or getattr(sc,'title',None) or f'Criteria {i+1}')
            _box(s2, title, COL_TIT_X+Inches(0.08), y+PAD, COL_TIT_W-Inches(0.12), ROW_H,
                 sz=11, bold=True, color=WHITE)
            desc = getattr(sc,'description',None) or getattr(sc,'Description',None) or ''
            if desc:
                _box(s2, desc, COL_DSC_X+Inches(0.08), y+PAD, COL_DSC_W-Inches(0.12), ROW_H,
                     sz=10, color=MUTED)
            y += ROW_H

    # SLIDE 3 — Pre-POV Checklist
    s3 = prs.slides.add_slide(BL)
    _bg(s3, NAVY)
    done_count = sum(1 for iid,_ in CHECKLIST_ITEMS if checks.get(iid))
    _slide_header(s3, 'PRE-POV CHECKLIST',
                  f'Completion: {done_count} of {len(CHECKLIST_ITEMS)} items', GREEN)
    TABLE_TOP = Inches(1.32)
    ROW_H = max(int((Inches(7.15)-TABLE_TOP)/len(CHECKLIST_ITEMS)), int(Inches(0.62)))
    COL_ST_X=Inches(0.4); COL_ST_W=Inches(0.55)
    COL_TT_X=Inches(1.0); COL_TT_W=Inches(5.6)
    COL_NT_X=Inches(6.7); COL_NT_W=Inches(6.4)
    HDR_Y=int(TABLE_TOP); HDR_H=int(Inches(0.38))
    for cx,cw,lbl in [(COL_ST_X,COL_ST_W,''),(COL_TT_X,COL_TT_W,'CHECKLIST ITEM'),(COL_NT_X,COL_NT_W,'NOTES')]:
        _rect(s3, cx, HDR_Y, cw, HDR_H, NAVY2)
        if lbl:
            _box(s3, lbl, cx+Inches(0.08), HDR_Y, cw, HDR_H, sz=9, bold=True, color=GREEN)
    y = HDR_Y + HDR_H
    for i, (item_id, item_title) in enumerate(CHECKLIST_ITEMS):
        checked = bool(checks.get(item_id))
        bg_ = NAVY3 if i%2==0 else NAVY2
        PAD = int(Inches(0.1))
        for cx,cw in [(COL_ST_X,COL_ST_W),(COL_TT_X,COL_TT_W),(COL_NT_X,COL_NT_W)]:
            _rect(s3, cx, y, cw, ROW_H-int(Inches(0.03)), bg_)
        _box(s3, '✅' if checked else '⬜',
             COL_ST_X+Inches(0.04), y+PAD, COL_ST_W, ROW_H,
             sz=16, color=GREEN if checked else MUTED, align=PP_ALIGN.CENTER)
        _box(s3, item_title,
             COL_TT_X+Inches(0.08), y+PAD, COL_TT_W-Inches(0.12), ROW_H,
             sz=11, bold=(not checked), color=MUTED if checked else WHITE)
        note_text = notes_map.get(item_id, '')
        if note_text:
            _box(s3, note_text,
                 COL_NT_X+Inches(0.08), y+PAD, COL_NT_W-Inches(0.12), ROW_H,
                 sz=10, color=MUTED, italic=True)
        y += ROW_H

    # SLIDE 4 — POV Timeline
    s4 = prs.slides.add_slide(BL)
    _bg(s4, NAVY)
    _slide_header(s4, 'POV TIMELINE', 'Milestone schedule for the Proof of Value', AMBER)
    if not tl_rows:
        _box(s4, 'No timeline milestones have been defined yet.',
             Inches(0.5), Inches(2.0), Inches(12), Inches(0.5),
             sz=14, color=MUTED, italic=True)
    else:
        TABLE_TOP = Inches(1.32)
        n = min(len(tl_rows), 14)
        ROW_H = max(int((Inches(7.15)-TABLE_TOP)/n), int(Inches(0.38)))
        COL_NUM_X=Inches(0.4); COL_NUM_W=Inches(0.5)
        COL_MIL_X=Inches(0.95); COL_MIL_W=Inches(8.7)
        COL_DAT_X=Inches(9.75); COL_DAT_W=Inches(3.25)
        HDR_Y=int(TABLE_TOP); HDR_H=int(Inches(0.38))
        for cx,cw,lbl,al in [(COL_NUM_X,COL_NUM_W,'#',PP_ALIGN.CENTER),(COL_MIL_X,COL_MIL_W,'MILESTONE',PP_ALIGN.LEFT),(COL_DAT_X,COL_DAT_W,'TARGET DATE',PP_ALIGN.RIGHT)]:
            _rect(s4, cx, HDR_Y, cw, HDR_H, NAVY2)
            _box(s4, lbl, cx+Inches(0.06), HDR_Y, cw, HDR_H, sz=9, bold=True, color=AMBER, align=al)
        y = HDR_Y + HDR_H
        for i, row in enumerate(tl_rows[:n]):
            bg_ = NAVY3 if i%2==0 else NAVY2
            PAD = int(Inches(0.08))
            for cx,cw in [(COL_NUM_X,COL_NUM_W),(COL_MIL_X,COL_MIL_W),(COL_DAT_X,COL_DAT_W)]:
                _rect(s4, cx, y, cw, ROW_H-int(Inches(0.02)), bg_)
            _box(s4, str(i+1), COL_NUM_X+Inches(0.06), y+PAD, COL_NUM_W, ROW_H,
                 sz=10, bold=True, color=MUTED, align=PP_ALIGN.CENTER)
            _box(s4, row.get('label',''), COL_MIL_X+Inches(0.08), y+PAD, COL_MIL_W-Inches(0.12), ROW_H,
                 sz=11, color=WHITE)
            if row.get('date',''):
                _box(s4, row['date'], COL_DAT_X+Inches(0.06), y+PAD, COL_DAT_W-Inches(0.1), ROW_H,
                     sz=11, bold=True, color=ACCENT, align=PP_ALIGN.RIGHT)
            y += ROW_H

    # SLIDE 5 — Thank You
    s5 = prs.slides.add_slide(BL)
    _bg(s5, NAVY)
    _rect(s5, Inches(0), Inches(0), Inches(0.2), H, ACCENT)
    _rect(s5, Inches(0.35), Inches(3.85), Inches(12.6), Emu(55000), ACCENT)
    _box(s5, 'Thank You',
         Inches(0.5), Inches(1.3), Inches(12), Inches(1.2),
         sz=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _box(s5, user_resp.customer_name or 'Customer',
         Inches(0.5), Inches(2.65), Inches(12), Inches(0.6),
         sz=20, color=ACCENT, align=PP_ALIGN.CENTER)
    _box(s5, 'Zscaler Zero Trust Branch',
         Inches(0.5), Inches(4.15), Inches(12), Inches(0.55),
         sz=16, color=MUTED, align=PP_ALIGN.CENTER, italic=True)
    if user_resp.se_name:
        _box(s5, user_resp.se_name,
             Inches(0.5), Inches(4.85), Inches(12), Inches(0.45),
             sz=13, color=MUTED, align=PP_ALIGN.CENTER)
    _box(s5, '© 2025 Zscaler, Inc. — Internal Sales Engineering Tool',
         Inches(0.5), Inches(6.8), Inches(12), Inches(0.35),
         sz=9, color=RGBColor(0x40, 0x60, 0x80),
         align=PP_ALIGN.CENTER, italic=True)

    out = io.BytesIO()
    prs.save(out)
    out.seek(0)
    safe  = (user_resp.customer_name or 'Customer').replace(' ','_').replace('/','_')
    fname = f"ZTB_POV_Deck_{safe}_{datetime.utcnow().strftime('%Y%m%d')}.pptx"
    return send_file(
        out,
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True,
        download_name=fname
    )
