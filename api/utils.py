def generate_stats_message(stats: list) -> str:
    """
    Generate a distribution stats message for previous day.

    Args:
        stats (list): A list of dictionaries with the following keys:
            - 'distribution_id': The ID of the distribution.
            - 'total_messages': The total number of messages in the distribution.
            - 'sent_messages': The number of sent messages in the distribution.
            - 'not_sent_messages': The number of not sent messages in the distribution.

    Returns:
        str: A message containing the statistics for the previous day's mailings.
    """

    if not stats:
        return (
            f"Статистика по рассылкам, запущенным за предыдущий день.\n\n"
            f"Всего рассылок: 0\n"
        )

    message = (
        f"Статистика по рассылкам, запущенным за предыдущий день.\n\n"
        f"Всего рассылок: {len(stats)}\n"
        f"Всего отправлено сообщений: {sum([stat.get('sent_messages') for stat in stats])}\n\n"
        "Детальный список:\n"
    )

    for stat in stats:
        message += (
            f"- Рассылка #{stat.get('distribution_id')}: "
            f"Всего сообщений: {stat.get('total_messages')}, "
            f"Отправлено: {stat.get('sent_messages')}, "
            f"Не отправлено: {stat.get('not_sent_messages')}\n"
        )

    return message
