import logging

logger = logging.getLogger("simple_bank.transfers")


def mask_account_number(account_number: str) -> str:
    last_four = account_number[-4:].rjust(4, "0")
    return f"XXXX{last_four}"


def log_transfer_event(
    event: str,
    *,
    from_account: str,
    to_account: str,
    result_code: str,
) -> None:
    logger.info(
        "transfer_event",
        extra={
            "event": event,
            "from_account": mask_account_number(from_account),
            "to_account": mask_account_number(to_account),
            "result_code": result_code,
        },
    )
