from pathlib import Path

import pandas as pd


class TabularService:

    def load(self, file_path: str):
        path = Path(file_path)

        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)

        if path.suffix.lower() == ".xlsx":
            return pd.read_excel(path)

        raise ValueError(
            f"Unsupported tabular file type: {path.suffix}"
        )

    def preview(
        self,
        file_path: str,
        rows: int = 10,
    ) -> dict:

        dataframe = self.load(file_path)

        return {
            "columns": dataframe.columns.tolist(),
            "rows": dataframe.head(rows).to_dict(
                orient="records"
            ),
            "row_count": len(dataframe),
        }

    def column_summary(
        self,
        file_path: str,
    ) -> dict:

        dataframe = self.load(file_path)

        summary = {}

        for column in dataframe.columns:

            series = dataframe[column]

            summary[column] = {
                "dtype": str(series.dtype),
                "non_null": int(series.notna().sum()),
                "null": int(series.isna().sum()),
            }

            if pd.api.types.is_numeric_dtype(series):
                summary[column].update(
                    {
                        "min": float(series.min()),
                        "max": float(series.max()),
                        "mean": float(series.mean()),
                        "sum": float(series.sum()),
                    }
                )

        return summary