import logging

from simple_bank.logging import log_transfer_event, mask_account_number


def test_account_number_is_masked_to_its_last_four_digits() -> None:
    assert mask_account_number("12345678") == "XXXX5678"


def test_transfer_log_contains_only_masked_account_references(
    caplog,
) -> None:
    with caplog.at_level(logging.INFO, logger="simple_bank.transfers"):
        log_transfer_event(
            "declined",
            from_account="12345678",
            to_account="87654321",
            result_code="INSUFFICIENT_BALANCE",
        )

    assert "12345678" not in caplog.text
    assert "87654321" not in caplog.text
    record = caplog.records[0]
    assert record.from_account == "XXXX5678"
    assert record.to_account == "XXXX4321"
    assert record.event == "declined"
    assert record.result_code == "INSUFFICIENT_BALANCE"
