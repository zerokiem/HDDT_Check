#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify.py — Gửi thông báo qua Telegram Bot API khi đăng nhập và khi 1 lượt
kiểm tra hóa đơn hoàn tất. Im lặng bỏ qua (không raise lỗi ra ngoài) nếu chưa
cấu hình TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID hoặc gửi thất bại — không được
làm hỏng luồng chính (đăng nhập / chạy kiểm tra) chỉ vì Telegram lỗi.
"""

import json
import urllib.error
import urllib.request
from datetime import datetime

TELEGRAM_API_BASE = 'https://api.telegram.org'


def _escape_html(text):
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def send_telegram(token, chat_id, text):
    """Gửi 1 tin nhắn. Trả về (thành_công, lỗi_nếu_có)."""
    if not token or not chat_id:
        return False, 'Chưa cấu hình TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID.'

    url = f'{TELEGRAM_API_BASE}/bot{token}/sendMessage'
    payload = json.dumps({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload,
                                  headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            if body.get('ok'):
                return True, ''
            return False, body.get('description', 'Không rõ lỗi.')
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode('utf-8')).get('description', str(e))
        except Exception:
            detail = str(e)
        return False, f'HTTP {e.code}: {detail}'
    except Exception as e:
        return False, str(e)


def _configured(config):
    return bool(config.get('TELEGRAM_BOT_TOKEN') and config.get('TELEGRAM_CHAT_ID'))


def notify_login(config, username, ip_address):
    """Gọi sau khi đăng nhập THÀNH CÔNG."""
    if not _configured(config):
        return
    msg = (
        f'🔐 <b>HDDT Checker</b> — Đăng nhập\n'
        f'👤 Tài khoản: {_escape_html(username)}\n'
        f'🌐 IP: {_escape_html(ip_address or "—")}\n'
        f'🕐 {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    )
    try:
        ok, err = send_telegram(config['TELEGRAM_BOT_TOKEN'], config['TELEGRAM_CHAT_ID'], msg)
        if not ok:
            print(f'[telegram] Gửi thông báo đăng nhập thất bại: {err}')
    except Exception as e:
        print(f'[telegram] Lỗi không mong muốn: {e}')


def notify_job_done(config, job):
    """Gọi khi 1 job kết thúc (done/error) — job là instance models.Job."""
    if not _configured(config):
        return
    icon = {'done': '✅', 'error': '❌', 'cancelled': '⏹️'}.get(job.status, 'ℹ️')
    username = job.user.username if job.user else '—'
    msg = (
        f'{icon} <b>HDDT Checker</b> — Job #{job.id} hoàn tất ({job.status.upper()})\n'
        f'📄 File: {_escape_html(job.input_filename)}\n'
        f'📊 Tổng: {job.total} | ✓ YES: {job.yes_count} | ✗ NO: {job.no_count} | '
        f'⚠ Captcha: {job.captcha_err} | ! Lỗi: {job.error_count}\n'
        f'⏱ Thời gian chạy: {job.duration_str()}\n'
        f'👤 Người chạy: {_escape_html(username)}'
    )
    if job.error_msg:
        msg += f'\n❗ {_escape_html(job.error_msg[:300])}'
    try:
        ok, err = send_telegram(config['TELEGRAM_BOT_TOKEN'], config['TELEGRAM_CHAT_ID'], msg)
        if not ok:
            print(f'[telegram] Gửi thông báo kết quả thất bại: {err}')
    except Exception as e:
        print(f'[telegram] Lỗi không mong muốn: {e}')
