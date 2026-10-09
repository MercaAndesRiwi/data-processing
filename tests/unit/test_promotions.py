from datetime import datetime
from pathlib import Path
import pytest
from openpyxl import Workbook
from src.ingestion.promotions.main import read_promotions


@pytest.fixture
def create_excel(tmp_path):
    """Create a temporary Excel file for testing."""

    def _create(headers, rows):
        file_path = tmp_path / "test_promotions.xlsx"
        workbook = Workbook()
        sheet = workbook.active

        sheet.append(headers)

        for row in rows:
            sheet.append(row)

        workbook.save(file_path)
        workbook.close()

        return file_path

    return _create


def test_read_valid_promotions(create_excel):
    file_path = create_excel(
        [
            "sku",
            "tienda_o_canal",
            "descuento_pct",
            "fecha_inicio",
            "fecha_fin",
        ],
        [
            [
                "MA-HOG-0001",
                "CO_TIENDA_BARRANQUILLA",
                15,
                datetime(2026, 10, 5),
                datetime(2026, 10, 11),
            ]
        ],
    )

    promotions = read_promotions(file_path)

    assert len(promotions) == 1
    assert promotions[0]["sku"] == "MA-HOG-0001"
    assert promotions[0]["descuento_pct"] == 15


def test_reject_invalid_columns(create_excel):
    file_path = create_excel(
        ["sku", "discount", "start_date"],
        [["MA-HOG-0001", 15, datetime(2026, 10, 5)]],
    )

    with pytest.raises(ValueError, match="Invalid columns"):
        read_promotions(file_path)


def test_reject_empty_fields(create_excel):
    file_path = create_excel(
        [
            "sku",
            "tienda_o_canal",
            "descuento_pct",
            "fecha_inicio",
            "fecha_fin",
        ],
        [
            [
                "MA-HOG-0001",
                None,
                15,
                datetime(2026, 10, 5),
                datetime(2026, 10, 11),
            ]
        ],
    )

    with pytest.raises(ValueError, match="Empty fields"):
        read_promotions(file_path)


@pytest.mark.parametrize("discount", [0, -5, 101, "15"])
def test_reject_invalid_discounts(create_excel, discount):
    file_path = create_excel(
        [
            "sku",
            "tienda_o_canal",
            "descuento_pct",
            "fecha_inicio",
            "fecha_fin",
        ],
        [
            [
                "MA-HOG-0001",
                "CO_TIENDA_BARRANQUILLA",
                discount,
                datetime(2026, 10, 5),
                datetime(2026, 10, 11),
            ]
        ],
    )

    with pytest.raises(ValueError, match="Invalid discount"):
        read_promotions(file_path)


def test_reject_inverted_dates(create_excel):
    file_path = create_excel(
        [
            "sku",
            "tienda_o_canal",
            "descuento_pct",
            "fecha_inicio",
            "fecha_fin",
        ],
        [
            [
                "MA-HOG-0001",
                "CO_TIENDA_BARRANQUILLA",
                15,
                datetime(2026, 10, 12),
                datetime(2026, 10, 5),
            ]
        ],
    )

    with pytest.raises(ValueError, match="Start date is after end date"):
        read_promotions(file_path)
