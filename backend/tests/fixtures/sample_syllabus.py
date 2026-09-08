import io
from pypdf import PdfWriter


def create_sample_neet_syllabus_pdf() -> bytes:
    """Generates an in-memory valid, standard PDF 1.4 byte stream containing NEET syllabus text."""
    sample_lines = [
        "ALLEN CAREER INSTITUTE",
        "TARGET : NEET (UG)",
        "TEST SYLLABUS & SCHEDULE",
        "MINOR TEST (DLP) - 13 Sep 2026",
        "",
        "PHYSICS:",
        "Current Electricity: Electric Current, Ohm's Law, Resistance, Kirchhoff's Laws, Potentiometer.",
        "Moving Charges and Magnetism: Biot-Savart Law, Ampere's Circuital Law, Cyclotron.",
        "",
        "CHEMISTRY:",
        "Solutions: Types of solutions, Raoult's Law, Colligative properties, Osmotic pressure.",
        "Electrochemistry: Galvanic cells, Nernst Equation, Kohlrausch's Law.",
        "",
        "BIOLOGY:",
        "Sexual Reproduction in Flowering Plants: Pre-fertilization events, Pollination, Double Fertilization.",
        "Human Reproduction: Male Reproductive System, Female Reproductive System, Gametogenesis.",
    ]

    # Build PDF text stream using standard Tj and T* operators
    stream_content = "BT\n/F1 12 Tf\n14 TL\n50 720 Td\n"
    for line in sample_lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({escaped}) Tj\nT*\n"
    stream_content += "ET\n"
    stream_bytes = stream_content.encode("latin1")
    stream_len = len(stream_bytes)

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {stream_len} >>\nstream\n".encode("latin1") + stream_bytes + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("latin1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin1"))
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin1"))

    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
    return bytes(pdf)


SAMPLE_RAW_SYLLABUS_TEXT = """
ALLEN CAREER INSTITUTE
TARGET: NEET (UG)
MINOR TEST (DLP)
Date: 13 Sep 2026

PHYSICS
1. Current Electricity: Electric Current, Ohm's Law, Resistance, Combinations of Resistors, Kirchhoff's Laws, Potentiometer, Meter Bridge.
2. Electromagnetic Waves: Displacement Current, EM Waves characteristics.

CHEMISTRY
1. Solutions: Types of Solutions, Raoult's law, Ideal and Non-ideal solutions, Colligative Properties.
2. Coordination Compounds: IUPAC nomenclature, Werner's theory, Valence Bond Theory, Crystal Field Theory.

BIOLOGY
Sexual Reproduction in Flowering Plants: Flower structure, Pollination, Double fertilization, Seeds and Fruits.
Human Reproduction: Male and Female reproductive systems, Menstrual cycle, Fertilization and Implantation.
"""
