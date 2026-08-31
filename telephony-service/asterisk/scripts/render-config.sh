#!/bin/sh
# =============================================================================
# Рендер конфигурации Asterisk из шаблонов проекта.
#
# Шаблоны смонтированы read-only в /render/config (см. docker-compose.yml),
# результат пишется в /etc/asterisk ПОВЕРХ стандартных файлов образа — только
# явно перечисленные файлы (*.conf из шаблонов), остальная стандартная
# конфигурация образа (sorcery.conf, modules.conf и т.д.) сохраняется.
#
# Переменные окружения:
#   ARI_USERNAME, ARI_PASSWORD   — учётка ARI (совпадают с ASTERISK_ARI_*)
#   GOIP_SIP_PASSWORD            — SIP-пароль GoIP4
#   GOIP_AUTH_MODE               — digest | ip
#   GOIP_HOST                    — IP GoIP4 (для IP-identification)
#   MEDIA_FORMAT                 — ulaw | alaw
#
# ВНИМАНИЕ: в значениях секретов НЕ используйте символы  | & \  (ограничение sed).
# =============================================================================
set -eu

CONFIG_DIR=/render/config
DEST=/etc/asterisk

: "${ARI_USERNAME:?ARI_USERNAME is required}"
: "${ARI_PASSWORD:?ARI_PASSWORD is required}"
: "${GOIP_SIP_PASSWORD:?GOIP_SIP_PASSWORD is required}"

GOIP_AUTH_MODE="${GOIP_AUTH_MODE:-digest}"
GOIP_HOST="${GOIP_HOST:-192.168.1.50}"
MEDIA_FORMAT="${MEDIA_FORMAT:-ulaw}"
ASTERISK_PUBLIC_IP="${ASTERISK_PUBLIC_IP:-}"

for secret in "$ARI_USERNAME" "$ARI_PASSWORD" "$GOIP_SIP_PASSWORD"; do
    case "$secret" in
        *'|'*|*'&'*|*'\'*) echo "[render-config] ERROR: secret contains forbidden chars (| & \\)"; exit 1 ;;
    esac
done

for f in "$CONFIG_DIR"/*.conf; do
    name="$(basename "$f")"
    sed \
        -e "s|@@ARI_USERNAME@@|$ARI_USERNAME|g" \
        -e "s|@@ARI_PASSWORD@@|$ARI_PASSWORD|g" \
        -e "s|@@GOIP_SIP_PASSWORD@@|$GOIP_SIP_PASSWORD|g" \
        -e "s|@@GOIP_HOST@@|$GOIP_HOST|g" \
        -e "s|@@MEDIA_FORMAT@@|$MEDIA_FORMAT|g" \
        -e "s|@@ASTERISK_PUBLIC_IP@@|$ASTERISK_PUBLIC_IP|g" \
        "$f" > "$DEST/$name"
    echo "[render-config] $name -> $DEST/$name"
done

# Условные блоки pjsip.conf: digest-аутентификация против IP-identification.
if [ "$GOIP_AUTH_MODE" = "ip" ]; then
    sed -i -e '/@@IF_DIGEST@@/,/@@ENDIF_DIGEST@@/d' \
           -e '/@@IF_IP@@/d' -e '/@@ENDIF_IP@@/d' "$DEST/pjsip.conf"
    echo "[render-config] pjsip: IP-based identification (match=$GOIP_HOST)"
else
    sed -i -e '/@@IF_IP@@/,/@@ENDIF_IP@@/d' \
           -e '/@@IF_DIGEST@@/d' -e '/@@ENDIF_DIGEST@@/d' "$DEST/pjsip.conf"
    echo "[render-config] pjsip: digest auth (username=goip4)"
fi

# NAT-коррекция SDP/Via: применяется только если задан ASTERISK_PUBLIC_IP.
# Без неё строки local_net/external_* в pjsip.conf не имеют смысла и удаляются.
if [ -n "$ASTERISK_PUBLIC_IP" ]; then
    sed -i -e '/@@IF_MEDIA@@/d' -e '/@@ENDIF_MEDIA@@/d' "$DEST/pjsip.conf"
    echo "[render-config] pjsip: NAT external address=$ASTERISK_PUBLIC_IP (media+signaling)"
else
    sed -i -e '/^local_net=/d' \
           -e '/^external_media_address=/d' \
           -e '/^external_signaling_address=/d' \
           -e '/@@IF_MEDIA@@/,/@@ENDIF_MEDIA@@/d' "$DEST/pjsip.conf"
    echo "[render-config] pjsip: NAT external address NOT set (direct routing)"
fi

# Sanity-check: рендер не должен оставлять плейсхолдеры и должен содержать
# ключевые секции (защита от ошибок шаблона — fail fast)
if grep -q '@@' "$DEST/pjsip.conf" || grep -q '@@' "$DEST/ari.conf"; then
    echo "[render-config] ERROR: unrendered placeholders remain"
    exit 1
fi
if ! grep -q 'type=endpoint' "$DEST/pjsip.conf"; then
    echo "[render-config] ERROR: pjsip.conf lost its endpoint section"
    exit 1
fi

# Тестовый звук для self-loop проверки (10 c G.711 µ-law, без бинарников в репо)
SOUND_DIR=/var/lib/asterisk/sounds/custom
mkdir -p "$SOUND_DIR"
if [ ! -f "$SOUND_DIR/testtone.ulaw" ]; then
    dd if=/dev/urandom of="$SOUND_DIR/testtone.ulaw" bs=8000 count=10 2>/dev/null
    echo "[render-config] generated $SOUND_DIR/testtone.ulaw"
fi

echo "[render-config] done (MEDIA_FORMAT=$MEDIA_FORMAT, GOIP_AUTH_MODE=$GOIP_AUTH_MODE)"
