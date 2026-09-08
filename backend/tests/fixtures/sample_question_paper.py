def create_sample_neet_question_paper_pdf() -> bytes:
    """Generates an in-memory valid, standard PDF 1.4 byte stream matching a real ALLEN NEET Question Paper."""
    sample_lines = [
        "ALLEN CAREER INSTITUTE (KOTA, RAJASTHAN)               ROLL: 0999DMD363104260005",
        "DATE: 30-08-2026                                              TEST CODE: MD",
        "--------------------------------------------------------------------------------",
        "                                   PHYSICS",
        "--------------------------------------------------------------------------------",
        "",
        "1) Given below are two statements:",
        "   Statement-I: The magnetic force acting on a moving charge can never change speed.",
        "   Statement-II: An electric field can only speed up or slow down a moving charge.",
        "   In the light of the above statements, choose the most appropriate answer:",
        "   (1) Both statement I and statement II are incorrect",
        "   (2) Statement I is correct but statement II is incorrect",
        "   (3) Statement I is incorrect but statement II is correct",
        "   (4) Both statement I and statement II are correct",
        "",
        "2) The figure gives experimentally measured B vs. H variation in a ferromagnetic material.",
        "   The retentivity, co-ercivity and saturation, respectively, of the material are:",
        "   (1) 150 A/m, 1.0 T and 1.5 T",
        "   (2) 1.0 T, 50 A/m and 1.5 T",
        "   (3) 1.0 T, 50 A/m and 1.0 T",
        "   (4) 1.5 T, 50 A/m and 1.0 T",
        "",
        "3) A proton carrying 1 MeV kinetic energy is moving in a circular path of radius R in",
        "   uniform magnetic field. What should be the energy of an alpha-particle to describe a circle",
        "   of same radius in the same magnetic field?",
        "   (1) 0.5 MeV",
        "   (2) 4 MeV",
        "   (3) 2 MeV",
        "   (4) 1 MeV",
        "",
        "4) The magnetic field at the centre of the circular loop as shown in figure, when a single",
        "   wire is bent to form a circular loop and also extends to form straight sections is:",
        "   (1) mu_0 * I / (2 * R) * (1 + 1/pi)",
        "   (2) mu_0 * I / (2 * R) * (1 - 1/pi)",
        "   (3) mu_0 * I / (4 * pi * R)",
        "   (4) Zero",
    ]

    # Build PDF text stream using standard Tj and T* operators
    stream_content = "BT\n/F1 10 Tf\n13 TL\n40 740 Td\n"
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
