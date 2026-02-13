from src.core.entities import Report


class PromptTemplate:
    """
    Handles prompt generation for the AI.
    Follows SRP: Only responsible for formatting prompts.
    """
    
    @staticmethod
    def generate_report_prompt(context: str, daily_activity: str) -> str:
        return f"""
Kamu adalah asisten yang membantu membuat laporan harian magang.

Konteks Magang:
{context}

Aktivitas hari ini:
{daily_activity}

Buatkan 3 bagian laporan harian dengan format JSON.
Setiap bagian minimal {Report.MIN_FIELD_LENGTH} karakter, maksimal {Report.MAX_FIELD_LENGTH} karakter.
Gunakan bahasa Indonesia yang profesional namun mengalir (seperti manusia).
Jangan gunakan bullet points.

Format output (JSON murni):
{{
    "activity": "Uraian detail aktivitas...",
    "learning": "Pembelajaran yang didapat...",
    "obstacles": "Kendala (jika ada) atau tantangan..."
}}
"""

    @staticmethod
    def extend_content_prompt(text: str, field_type: str) -> str:
        return f"""
Kembangkan teks berikut menjadi minimal {Report.MIN_FIELD_LENGTH} karakter
(maks {Report.MAX_FIELD_LENGTH}) dengan bahasa profesional:

Tipe: {field_type}
Teks asli: {text}

Output hanya teks hasil pengembangan.
"""
