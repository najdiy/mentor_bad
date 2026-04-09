from bot.database.models import Supplement, Stock


def progress_bar(taken: int, total: int, width: int = 10) -> str:
    if total == 0:
        return "░" * width + " 0%"
    filled = round((taken / total) * width)
    pct = round((taken / total) * 100)
    return "█" * filled + "░" * (width - filled) + f" {pct}%"


def format_stats_message(period_label: str, stats_rows: list[dict], supplements: dict[int, Supplement], stocks: dict[int, Stock]) -> str:
    if not stats_rows:
        return f"📊 Статистика за {period_label}\n\nЗаписей пока нет."

    lines = [f"📊 Статистика за {period_label}\n"]
    for row in stats_rows:
        sid = row["supplement_id"]
        sup = supplements.get(sid)
        if not sup:
            continue
        taken = row.get("taken", 0)
        skipped = row.get("skipped", 0)
        total = taken + skipped
        bar = progress_bar(taken, total) if total > 0 else "Нет данных"
        stock = stocks.get(sid)
        stock_str = f"Остаток: {stock.current_count} шт." if stock else ""
        lines.append(f"💊 <b>{sup.name}</b>")
        lines.append(f"{bar}")
        lines.append(f"Принято: {taken} | Пропущено: {skipped} {stock_str}")
        lines.append("")
    return "\n".join(lines)


def format_schedule_message(logs_today: list, supplements: dict) -> str:
    if not logs_today:
        return "📋 На сегодня приёмов не запланировано.\n\nДобавьте БАД через /add_supplement"

    STATUS_EMOJI = {"taken": "✅", "skipped": "❌", "pending": "⏳", "snoozed": "⏰"}
    lines = ["📋 <b>Расписание на сегодня:</b>\n"]
    for log in logs_today:
        sup = supplements.get(log.supplement_id)
        name = sup.name if sup else f"БАД #{log.supplement_id}"
        time_str = log.scheduled_at.strftime("%H:%M")
        emoji = STATUS_EMOJI.get(log.status, "❓")
        lines.append(f"{emoji} {time_str} — {name} ({log.dose_taken} шт.)")
    return "\n".join(lines)


def format_stock_message(stocks: list[Stock], supplements: dict) -> str:
    if not stocks:
        return "📦 Запасы пусты. Добавьте БАД через /add_supplement"

    lines = ["📦 <b>Ваши запасы:</b>\n"]
    for stock in stocks:
        sup = supplements.get(stock.supplement_id)
        name = sup.name if sup else f"БАД #{stock.supplement_id}"
        warn = " ⚠️ Мало!" if stock.current_count <= stock.reorder_threshold else ""
        lines.append(f"💊 <b>{name}</b>: {stock.current_count} шт.{warn}")
        lines.append(f"   Порог заказа: {stock.reorder_threshold} шт.")
    return "\n".join(lines)
