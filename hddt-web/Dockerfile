# HDDT Checker Web - image chay tren Linux/Pi4, NAS Synology (ARM64) va may
# chu x86_64 - qua Docker.
#
# Dua tren image chinh thuc cua Playwright (da co san Chromium + moi thu vien
# he thong, ho tro ca linux/arm64 lan linux/amd64) nen KHONG can tu cai
# Chromium bang apt-get (tranh loi build tren mot so NAS bi timeout mang khi
# apt-get qua BuildKit) - da kiem chung hoat dong tren NAS DS423 ARM64
# (xem docs/INSTALL_NAS_SYNOLOGY.md).
#
# Code KHONG duoc COPY vao image ma se BIND-MOUNT tu ngoai luc chay (xem
# docker-compose.yml, giong DO_Auto) -> sua code xong chi can restart
# container, khong can build lai image.
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

ENV TZ=Asia/Ho_Chi_Minh \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

WORKDIR /app

# Ghim dung playwright==1.55.0 khop voi tag image de dung thang Chromium co
# san trong image (KHONG tai lai browser rieng qua "playwright install").
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "playwright==1.55.0" && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 14687

CMD ["gunicorn", \
     "--bind", "0.0.0.0:14687", \
     "--workers", "2", \
     "--threads", "4", \
     "--preload", \
     "--timeout", "300", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
