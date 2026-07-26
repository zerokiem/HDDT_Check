#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
input_utils.py — Chuẩn hóa file Excel đầu vào.

Ký hiệu hóa đơn và số hóa đơn thường được nhập chung 1 ô theo mẫu
"<mẫu_số>-<ký_hiệu>-<số_hóa_đơn>", ví dụ "1-C26TAP-00001765". Module này tự
tách cột gộp đó ra 2 cột riêng (Ky_hieu, So_HD) mà checker cần, đồng thời vẫn
hỗ trợ ngược các file cũ đã có sẵn 2 cột Ky_hieu/So_HD riêng.
"""

import re

import pandas as pd

# Tên cột gộp "Số & Ký hiệu hóa đơn" — thử theo thứ tự ưu tiên (không phân biệt
# hoa/thường, khoảng trắng/gạch dưới).
COMBINED_COLUMN_CANDIDATES = [
    'so_ky_hieu_hd', 'sokyhieuhd', 'sovakyhieuhd',
    'number', 'so_ky_hieu', 'sohoadon_kyhieu',
]

# Mẫu "1-C26TAP-00001765" hoặc "C26TAP-00001765" (không có mẫu số đứng đầu).
_RE_3PART = re.compile(r'^\s*\d+\s*-\s*([A-Za-z0-9]+)\s*-\s*(\d+)\s*$')
_RE_2PART = re.compile(r'^\s*([A-Za-z0-9]+)\s*-\s*(\d+)\s*$')


def split_so_ky_hieu(value):
    """Tách 1 giá trị dạng "1-C26TAP-00001765" -> ("C26TAP", "00001765").

    Trả về (None, None) nếu không khớp định dạng.
    """
    if value is None:
        return None, None
    s = str(value).strip()
    if not s or s.lower() == 'nan':
        return None, None

    m = _RE_3PART.match(s)
    if m:
        return m.group(1).upper(), m.group(2)

    m = _RE_2PART.match(s)
    if m:
        return m.group(1).upper(), m.group(2)

    return None, None


def _normalize_colname(name):
    return re.sub(r'[\s_]+', '', str(name)).lower()


def normalize_input_df(df):
    """Đảm bảo DataFrame có đủ cột 'Ky_hieu' và 'So_HD'.

    - Nếu file đã có sẵn 2 cột này với dữ liệu -> giữ nguyên, chỉ điền các ô
      trống (nếu có) từ cột gộp khi tìm thấy.
    - Nếu chưa có -> tìm cột gộp (NUMBER, So_KyHieu_HD, ...) và tự tách.
    """
    df = df.copy()

    has_ky_hieu = 'Ky_hieu' in df.columns
    has_so_hd = 'So_HD' in df.columns

    if not has_ky_hieu:
        df['Ky_hieu'] = ''
    if not has_so_hd:
        df['So_HD'] = ''

    # Tìm cột gộp theo tên chuẩn hóa (bỏ khoảng trắng/gạch dưới, không phân
    # biệt hoa thường) để khớp cả "So_KyHieu_HD", "Số & Ký hiệu HĐ", "NUMBER"...
    combined_col = None
    normalized_map = {_normalize_colname(c): c for c in df.columns}
    for candidate in COMBINED_COLUMN_CANDIDATES:
        if candidate in normalized_map:
            combined_col = normalized_map[candidate]
            break

    if combined_col is not None:
        for idx, row in df.iterrows():
            cur_kh = str(row.get('Ky_hieu', '') or '').strip()
            cur_shd = str(row.get('So_HD', '') or '').strip()
            if cur_kh and cur_shd:
                continue  # đã có sẵn đủ 2 giá trị, không ghi đè
            kh, shd = split_so_ky_hieu(row.get(combined_col))
            if kh and shd:
                if not cur_kh:
                    df.at[idx, 'Ky_hieu'] = kh
                if not cur_shd:
                    df.at[idx, 'So_HD'] = shd

    return df


def read_input_excel(path):
    """Đọc file Excel đầu vào và chuẩn hóa (tự tách Ky_hieu/So_HD)."""
    df = pd.read_excel(path, dtype=str).fillna('')
    return normalize_input_df(df)
