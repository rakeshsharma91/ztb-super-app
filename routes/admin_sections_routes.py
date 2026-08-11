# routes/admin_sections_routes.py — Result Sections CRUD + Rule Evaluation Engine
import ast
import re
import operator as op_module
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models import db, ResultSection
from functools import wraps

sections_bp = Blueprint('sections', __name__, url_prefix='/admin/sections')

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@sections_bp.route('/', methods=['GET'])
def sections_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login_page'))
    return render_template('admin_sections.html')

@sections_bp.route('/api', methods=['GET'])
@require_admin
def get_sections():
    sections = ResultSection.query.order_by(ResultSection.order, ResultSection.id).all()
    return jsonify({'success': True, 'sections': [s.to_dict() for s in sections]})

@sections_bp.route('/api', methods=['POST'])
@require_admin
def create_section():
    data = request.get_json()
    max_order = db.session.query(db.func.max(ResultSection.order)).scalar() or 0
    section = ResultSection(
        name=data.get('name', 'New Section'),
        order=max_order + 1,
        rules_json=data.get('rules_json', []),
        format=data.get('format')
    )
    db.session.add(section)
    db.session.commit()
    return jsonify({'success': True, 'section': section.to_dict()})

@sections_bp.route('/api/<int:section_id>', methods=['PUT'])
@require_admin
def update_section(section_id):
    section = ResultSection.query.get_or_404(section_id)
    data = request.get_json()
    if 'name' in data:
        section.name = data['name']
    if 'order' in data:
        section.order = data['order']
    if 'rules_json' in data:
        section.rules_json = data['rules_json']
    if 'format' in data:
        section.format = data['format']
    db.session.commit()
    return jsonify({'success': True, 'section': section.to_dict()})

@sections_bp.route('/api/<int:section_id>', methods=['DELETE'])
@require_admin
def delete_section(section_id):
    section = ResultSection.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()
    return jsonify({'success': True})

@sections_bp.route('/api/reorder', methods=['POST'])
@require_admin
def reorder_sections():
    data = request.get_json()
    for item in data.get('order', []):
        section = ResultSection.query.get(item['id'])
        if section:
            section.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

_ALLOWED_OPS = {
    ast.Add:  op_module.add,
    ast.Sub:  op_module.sub,
    ast.Mult: op_module.mul,
    ast.Div:  op_module.truediv,
    ast.Pow:  op_module.pow,
    ast.USub: op_module.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type}")
        return _ALLOWED_OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type}")
        return _ALLOWED_OPS[op_type](_safe_eval(node.operand))
    else:
        raise ValueError(f"Unsupported node type: {type(node)}")

def _interpolate(text, answers):
    if not text:
        return text
    def replacer(match):
        var = match.group(1).strip()
        val = answers.get(var)
        if val is None:
            return ''
        if isinstance(val, list):
            return ', '.join(str(v) for v in val)
        return str(val)
    return re.sub(r'\[([a-zA-Z_][a-zA-Z0-9_]*)\]', replacer, text)

def _resolve_outcome(outcome_str, answers):
    if not outcome_str:
        return outcome_str
    outcome_str = _interpolate(outcome_str, answers)
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', outcome_str)
    if not tokens:
        return outcome_str
    substituted = outcome_str
    is_formula = False
    for token in set(tokens):
        if token in answers:
            raw = answers[token]
            try:
                num = float(raw) if not isinstance(raw, list) else None
                if num is None:
                    continue
                substituted = substituted.replace(token, str(num))
                is_formula = True
            except (ValueError, TypeError):
                pass
    if not is_formula:
        return outcome_str
    try:
        tree = ast.parse(substituted, mode='eval')
        result = _safe_eval(tree.body)
        return result
    except Exception:
        return outcome_str

def _format_outcome(value, fmt):
    if fmt == 'currency_usd':
        try:
            return f"${float(value):,.0f}"
        except (ValueError, TypeError):
            return str(value)
    return str(value) if value is not None else '—'

def _eval_condition(condition, answers):
    variable = condition.get('variable', '')
    operator = condition.get('operator', '=')
    value    = condition.get('value')
    raw = answers.get(variable)
    if raw is None:
        answer = ''
    elif isinstance(raw, list):
        answer = [str(v).strip().lower() for v in raw]
    else:
        answer = str(raw).strip()
    if isinstance(value, list):
        comp_list = [str(v).strip().lower() for v in value]
        comp_str  = ''
    else:
        comp_str  = str(value).strip().lower() if value is not None else ''
        comp_list = [comp_str]
    answer_lower = answer.lower() if isinstance(answer, str) else answer
    if operator in ('=', '=='):
        if isinstance(answer_lower, list):
            return comp_str in answer_lower
        return answer_lower == comp_str
    elif operator in ('!=', '<>'):
        if isinstance(answer_lower, list):
            return comp_str not in answer_lower
        return answer_lower != comp_str
    elif operator == 'in':
        if isinstance(answer_lower, list):
            return any(a in comp_list for a in answer_lower)
        return answer_lower in comp_list
    elif operator == 'not_in':
        if isinstance(answer_lower, list):
            return not any(a in comp_list for a in answer_lower)
        return answer_lower not in comp_list
    elif operator == 'contains':
        if isinstance(answer_lower, list):
            return comp_str in answer_lower
        return comp_str in answer_lower
    elif operator == 'not_contains':
        if isinstance(answer_lower, list):
            return comp_str not in answer_lower
        return comp_str not in answer_lower
    elif operator in ('>', '<', '>=', '<='):
        try:
            ans_num  = float(answer) if isinstance(answer, str) else float(answer[0]) if answer else 0
            comp_num = float(comp_str)
            if operator == '>':  return ans_num > comp_num
            if operator == '<':  return ans_num < comp_num
            if operator == '>=': return ans_num >= comp_num
            if operator == '<=': return ans_num <= comp_num
        except (ValueError, TypeError, IndexError):
            return False
    elif operator in ('count_gt', 'count_gte', 'count_lt', 'count_lte', 'count_eq'):
        lst = answer if isinstance(answer, list) else ([answer] if answer else [])
        try:
            count    = len(lst)
            comp_num = int(float(comp_str))
            if operator == 'count_gt':  return count > comp_num
            if operator == 'count_gte': return count >= comp_num
            if operator == 'count_lt':  return count < comp_num
            if operator == 'count_lte': return count <= comp_num
            if operator == 'count_eq':  return count == comp_num
        except (ValueError, TypeError):
            return False
    return False

def _eval_rule(rule, answers):
    if rule.get('is_default'):
        return True
    groups = rule.get('condition_groups', [])
    if not groups:
        return True
    for group in groups:
        if all(_eval_condition(cond, answers) for cond in group):
            return True
    return False

def _evaluate_score_section(section, answers):
    config = section.rules_json
    if not isinstance(config, dict):
        return {'formatted': '—', 'banner': '', 'color': ''}
    max_score     = config.get('max_score', 1)
    scoring_rules = config.get('scoring_rules', [])
    total = 0
    for rule in scoring_rules:
        if _eval_condition(rule, answers):
            total += rule.get('points', 0)
    total = min(total, max_score)
    pct = (total / max_score * 100) if max_score else 0
    formatted = f"{total}/{max_score} ({pct:.2f}%)"
    banner = ''
    color  = ''
    for tier in config.get('score_banners', []):
        if pct >= tier.get('min', 0) and pct <= tier.get('max', 100):
            banner = _interpolate(tier.get('banner', ''), answers)
            color  = tier.get('color', '')
            break
    return {'formatted': formatted, 'banner': banner, 'color': color}

def _evaluate_value_driver_section(section, answers):
    """
    Value Driver section.
    rules_json structure:
    {
      "type": "value_driver",
      "condition_groups": [[{"variable": "vp_problem_to_be_solved", "operator": "contains", "value": "Reduce Risks"}]],
      "label": "Reduce Risks",
      "answer_variable": "vp_reduce_risks",
      "rows": [
        {
          "option_value": "Reduce Lateral Movement",
          "current_state": "Lateral movement is a possibility at the branch.",
          "future_state": "Zero Trust Branch completely eliminates lateral movement."
        },
        ...
      ]
    }
    Returns dict: {label, current_state_lines, future_state_lines} or None if gate fails.
    """
    config = section.rules_json
    if not isinstance(config, dict):
        return None

    # Check gate condition
    gate_groups = config.get('condition_groups', [])
    if gate_groups:
        gate_passed = False
        for group in gate_groups:
            if all(_eval_condition(cond, answers) for cond in group):
                gate_passed = True
                break
        if not gate_passed:
            return None

    label           = config.get('label', section.name)
    answer_variable = config.get('answer_variable', '')
    rows            = config.get('rows', [])

    raw_answers = answers.get(answer_variable)
    if raw_answers is None:
        selected = []
    elif isinstance(raw_answers, list):
        selected = [str(v).strip().lower() for v in raw_answers]
    else:
        selected = [str(raw_answers).strip().lower()]

    current_state_lines = []
    future_state_lines  = []

    for row in rows:
        option_value = str(row.get('option_value', '')).strip().lower()
        if not option_value:
            continue
        matched = any(option_value in sel or sel in option_value for sel in selected)
        if matched:
            cs = row.get('current_state', '').strip()
            fs = row.get('future_state', '').strip()
            if cs:
                current_state_lines.append(cs)
            if fs:
                future_state_lines.append(fs)

    return {
        'label':               label,
        'current_state_lines': current_state_lines,
        'future_state_lines':  future_state_lines,
    }

def evaluate_sections(answers):
    """
    Run all ResultSections against the answers dict.
    Returns a list of dicts: [{name, outcome, format, order, banner, color}, ...]
    Value driver sections return format='value_driver' with extra keys:
      label, current_state_lines, future_state_lines
    """
    sections = ResultSection.query.order_by(ResultSection.order, ResultSection.id).all()
    outcomes = []
    for section in sections:
        rj = section.rules_json

        # ── value_driver ────────────────────────────────────────────────────
        if isinstance(rj, dict) and rj.get('type') == 'value_driver':
            result = _evaluate_value_driver_section(section, answers)
            if result is not None:
                outcomes.append({
                    'name':                section.name,
                    'outcome':             result['label'],
                    'format':              'value_driver',
                    'order':               section.order,
                    'banner':              '',
                    'color':               '#00aaff',
                    'label':               result['label'],
                    'current_state_lines': result['current_state_lines'],
                    'future_state_lines':  result['future_state_lines'],
                })

        # ── score ────────────────────────────────────────────────────────────
        elif isinstance(rj, dict) and rj.get('type') == 'score':
            result = _evaluate_score_section(section, answers)
            outcomes.append({
                'name':    section.name,
                'outcome': result['formatted'],
                'format':  'score',
                'order':   section.order,
                'banner':  result['banner'],
                'color':   result['color'],
            })

        # ── banner ───────────────────────────────────────────────────────────
        elif isinstance(rj, dict) and rj.get('type') == 'banner':
            banners = sorted(rj.get('banners', []), key=lambda b: b.get('order', 0))
            for b in banners:
                groups  = b.get('condition_groups', [])
                matched = False
                if b.get('is_default') or not groups:
                    matched = True
                else:
                    for group in groups:
                        if all(_eval_condition(cond, answers) for cond in group):
                            matched = True
                            break
                if matched:
                    outcomes.append({
                        'name':    section.name,
                        'outcome': _interpolate(b.get('outcome', ''), answers),
                        'format':  'banner',
                        'order':   section.order,
                        'banner':  _interpolate(b.get('banner', ''), answers),
                        'color':   b.get('color', '#00aaff'),
                    })
                    break
            # No match → silently skip

        # ── standard (first-match) ───────────────────────────────────────────
        else:
            rules       = sorted(rj or [], key=lambda r: r.get('order', 0))
            raw_outcome = None
            banner      = ''
            color       = ''
            for rule in rules:
                if _eval_rule(rule, answers):
                    raw_outcome = rule.get('outcome', '')
                    banner      = _interpolate(rule.get('banner', ''), answers)
                    color       = rule.get('color', '')
                    break
            resolved  = _resolve_outcome(raw_outcome or '—', answers)
            formatted = _format_outcome(resolved, section.format)
            outcomes.append({
                'name':    section.name,
                'outcome': formatted,
                'format':  section.format,
                'order':   section.order,
                'banner':  banner,
                'color':   color,
            })

    return outcomes
