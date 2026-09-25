from datetime import datetime, timezone

from dgx_spark import GpuUnavailable
from panel_frame import BLACK, RED, YELLOW

WARNING_USAGE_PCT = 60
DANGER_USAGE_PCT = 80
BAR_HEIGHT = 12
BAR_BORDER = 2
ACCOUNT_LABEL_WIDTH = 75
WINDOW_COLUMN_WIDTH = 160
WINDOW_COLUMN_GAP = 10
ROW_SPACING = 48


def time_until(iso_str):
    if not iso_str: return "N/A"
    try:
        target = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        diff = target - datetime.now(timezone.utc)
        if diff.total_seconds() < 0: return "Resetting..."
        hours, rem = divmod(diff.total_seconds(), 3600)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{int(days)}d {int(hours)}h"
        return f"{int(hours)}h {int(rem // 60)}m"
    except Exception:
        return "N/A"


def gauge_fill_color(pct):
    if pct > DANGER_USAGE_PCT:
        return RED
    if pct > WARNING_USAGE_PCT:
        return YELLOW
    return BLACK


def draw_usage_bar(draw, x, y, width, pct, height=BAR_HEIGHT):
    draw.rectangle((x, y, x + width, y + height), outline=BLACK, width=BAR_BORDER)
    fill_w = int((width - 2 * BAR_BORDER) * max(0.0, min(pct / 100.0, 1.0)))
    if fill_w > 0:
        fill_box = (x + BAR_BORDER, y + BAR_BORDER, x + BAR_BORDER + fill_w, y + height - BAR_BORDER)
        draw.rectangle(fill_box, fill=gauge_fill_color(pct))


def draw_dgx_spark_widget(draw, fonts, x, y, statuses):
    draw.text((x, y), "DGX SPARK", font=fonts['28'], fill=BLACK)
    for row, (label, status) in enumerate(statuses.items()):
        _draw_gpu_row(draw, fonts, x, y + 36 + row * ROW_SPACING, label, status)


def _draw_gpu_row(draw, fonts, x, y, label, status):
    if isinstance(status, GpuUnavailable):
        draw.text((x, y), f"{label}  {status.value}", font=fonts['24'], fill=BLACK)
        return
    draw.text((x, y), f"{label}  {status.temperature_c}°C  GPU {status.utilization_pct}%", font=fonts['24'], fill=BLACK)
    draw_usage_bar(draw, x, y + 28, 400, status.utilization_pct)


def draw_vllm_widget(draw, fonts, x, y, node):
    draw.text((x, y), f"VLLM  {_short_model_name(node.model)}", font=fonts['24'], fill=BLACK)
    if node.vllm is None:
        draw.text((x, y + 40), "engine offline", font=fonts['20'], fill=BLACK)
        return
    _draw_engine_load(draw, fonts, x, y + 36, node.vllm)
    _draw_prefill_load(draw, fonts, x, y + 62, node.vllm)
    draw.text((x, y + 88), f"KV cache {round(node.vllm.kv_cache_pct)}%", font=fonts['20'], fill=BLACK)
    draw_usage_bar(draw, x, y + 112, 400, node.vllm.kv_cache_pct)


def _draw_engine_load(draw, fonts, x, y, activity):
    decoding = f"gen {activity.mean_generation_throughput:.1f} tok/s   run {activity.running}"
    draw.text((x, y), decoding, font=fonts['20'], fill=BLACK)
    queued_color = RED if activity.waiting > 0 else BLACK
    draw.text((x + 300, y), f"wait {activity.waiting}", font=fonts['20'], fill=queued_color)


def _draw_prefill_load(draw, fonts, x, y, activity):
    draw.text((x, y), f"prefill {activity.mean_prompt_throughput:.0f} tok/s", font=fonts['20'], fill=BLACK)


def _short_model_name(model):
    if not model:
        return "no model"
    return model.rsplit("/", 1)[-1]


def draw_claude_accounts_widget(draw, fonts, x, y, usages):
    draw.text((x, y), "CLAUDE USAGE  5h / 7d", font=fonts['28'], fill=BLACK)
    for row, (account, usage) in enumerate(usages.items()):
        row_y = y + 40 + row * ROW_SPACING
        draw.text((x, row_y + 6), account, font=fonts['20'], fill=BLACK)
        if usage.get('error'):
            draw.text((x + ACCOUNT_LABEL_WIDTH, row_y + 6), "Usage Error", font=fonts['20'], fill=BLACK)
            continue
        for column, window in enumerate(('five_hour', 'seven_day')):
            column_x = x + ACCOUNT_LABEL_WIDTH + column * (WINDOW_COLUMN_WIDTH + WINDOW_COLUMN_GAP)
            _draw_limit_window(draw, fonts, column_x, row_y, usage.get(window, {}))


def draw_codex_accounts_widget(draw, fonts, x, y, usages):
    draw.text((x, y), "CODEX USAGE  7-day", font=fonts['28'], fill=BLACK)
    for row, (account, usage) in enumerate(usages.items()):
        row_y = y + 40 + row * ROW_SPACING
        if usage.get('error'):
            draw.text((x, row_y), f"{account}  Usage Error", font=fonts['20'], fill=BLACK)
            continue
        window = usage.get('seven_day', {})
        pct = window.get('utilization', 0)
        draw.text((x, row_y), f"{account}  {round(pct)}%  (in {time_until(window.get('resets_at'))})",
                  font=fonts['20'], fill=BLACK)
        draw_usage_bar(draw, x, row_y + 26, 400, pct)


def _draw_limit_window(draw, fonts, x, y, window):
    pct = window.get('utilization', 0)
    draw.text((x, y), f"{round(pct)}% {time_until(window.get('resets_at'))}", font=fonts['20'], fill=BLACK)
    draw_usage_bar(draw, x, y + 26, WINDOW_COLUMN_WIDTH, pct)
