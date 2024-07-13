def generate_message(
        number: int,
        highest_number: int,
        lowest_number: int,
        default_message: str,
        cond_messages: list[list[int, str, bool, bool]]
    ) -> str:
    additional_message = default_message

    for cm in cond_messages:
        if number == cm[0] or \
            (cm[0] == "highest" and number == highest_number) or \
                (cm[0] == "lowest" and number == lowest_number):
            additional_message = cm[1] if cm[2] else f"{additional_message} {cm[1]}"
            if cm[3]:
                break

    return additional_message
