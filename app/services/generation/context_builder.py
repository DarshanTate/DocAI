class ContextBuilder:

    def build(self, results):

        context_parts = []

        for index, result in enumerate(
            results,
            start=1,
        ):

            payload = result.payload or {}

            document_id = payload.get(
                "document_id",
                "unknown",
            )

            metadata = payload.get(
                "metadata",
                {},
            )

            content = payload.get(
                "content",
                "",
            )

            source_location = self._format_location(
                metadata
            )

            context_parts.append(
                f"""
[Source {index}]

Document ID:
{document_id}

Location:
{source_location}

Content:
{content}
""".strip()
            )

        return "\n\n".join(context_parts)

    def _format_location(self, metadata):

        if "page" in metadata:
            return f"Page {metadata['page']}"

        if "slide" in metadata:
            return f"Slide {metadata['slide']}"

        if "sheet" in metadata:
            return f"Sheet {metadata['sheet']}"

        if "row" in metadata:
            return f"Row {metadata['row']}"

        return "Document"