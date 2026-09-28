import pandas as pd

from app.services.structured.tabular_service import TabularService


def test_tabular_service_csv(tmp_path):

    file_path = tmp_path / "sales.csv"

    dataframe = pd.DataFrame(
        {
            "product": ["A", "B", "C"],
            "revenue": [100, 200, 300],
        }
    )

    dataframe.to_csv(file_path, index=False)

    service = TabularService()

    result = service.preview(str(file_path))

    assert result["row_count"] == 3
    assert "revenue" in result["columns"]