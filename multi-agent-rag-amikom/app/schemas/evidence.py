from pydantic import BaseModel, Field
from typing import Optional

class Evidence(BaseModel):
    chunk_id: str = Field(..., description="ID unik chunk")
    source_id: str = Field(..., description="Kode dokumen sumber (misal B01, B03)")
    title: str = Field(..., description="Judul dokumen/sub-bab")
    locator: str = Field(..., description="Lokasi dokumen (halaman/bagian)")
    lifecycle: str = Field(..., description="Status lifecycle (ACTIVE, ACTIVE_DYNAMIC, ARCHIVE)")
    score: float = Field(..., description="Skor kemiripan retrieval")
    chunk_text: str = Field(..., description="Isi teks chunk")
    freshness_status: Optional[str] = Field(default="CURRENT", description="Status kesegaran data")
