from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrescriptionPdfData:
    prescription_id: str
    verification_url: str
    patient_name: str
    prescriber_name: str
    prescriber_crm: str
    medication_name: str
    dosage_and_route: str
    instructions: str
    issued_at_str: str
    valid_until_str: str
    icp_signature_hash: str


def _escape_pdf_text(text: str) -> str:
    # Mantém caracteres ASCII imprimíveis básicos para compatibilidade universal PDF 1.4.
    limpo = (
        text.replace('\\', '\\\\')
        .replace('(', '\\(')
        .replace(')', '\\)')
        .replace('\r', ' ')
        .replace('\n', ' ')
    )
    return limpo.encode('latin-1', errors='replace').decode('latin-1')


def render_prescription_pdf(data: PrescriptionPdfData) -> bytes:
    """Gera documento PDF 1.4 imutável de receita digital sem CPF do paciente (Spec 0011)."""
    linhas = [
        'MEDIX.AI - RECEITA DIGITAL ASSINADA (ICP-BRASIL)',
        f'Identificador (UUID): {data.prescription_id}',
        f'Verificacao (QR): {data.verification_url}',
        f'Paciente: {data.patient_name}',
        f'Prescritor: {data.prescriber_name} - CRM {data.prescriber_crm}',
        f'Medicamento: {data.medication_name}',
        f'Posologia e via: {data.dosage_and_route}',
        f'Orientacoes: {data.instructions or "Seguir orientacao medica."}',
        f'Emissao: {data.issued_at_str}',
        f'Validade regulamentar: {data.valid_until_str}',
        f'Hash criptografico ICP-Brasil: {data.icp_signature_hash}',
    ]

    comandos = ['BT', '/F1 11 Tf', '50 770 Td', '18 TL']
    for idx, linha in enumerate(linhas):
        prefixo = '' if idx == 0 else 'T* '
        comandos.append(f'{prefixo}({_escape_pdf_text(linha)}) Tj')
    comandos.append('ET')
    stream_bytes = '\n'.join(comandos).encode('latin-1')

    objetos = [
        b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
        b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
        (
            b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n'
        ),
        b'4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n',
        (
            f'5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n'.encode('ascii')
            + stream_bytes
            + b'\nendstream\nendobj\n'
        ),
    ]

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for obj in objetos:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f'xref\n0 {len(objetos) + 1}\n'.encode('ascii'))
    pdf.extend(b'0000000000 65535 f \n')
    for off in offsets[1:]:
        pdf.extend(f'{off:010d} 00000 n \n'.encode('ascii'))

    pdf.extend(
        (
            f'trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n'
            f'startxref\n{xref_pos}\n%%EOF\n'
        ).encode('ascii')
    )
    return bytes(pdf)
