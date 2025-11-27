import os
import re
import tempfile
import argparse
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF
import torch
from transformers import AutoModel, AutoTokenizer


# Patch .cuda() to be a no-op on CPU-only machines
if not torch.cuda.is_available():
    print("[INFO] CUDA not available; patching Tensor.cuda / Module.cuda to no-ops")

    def _tensor_cuda(self, *args, **kwargs):
        return self

    def _module_cuda(self, *args, **kwargs):
        return self

    torch.Tensor.cuda = _tensor_cuda
    torch.nn.Module.cuda = _module_cuda


NENA_PDF_URL = (
    "https://cdn.ymaws.com/www.nena.org/resource/resmgr/standards/"
    "nena-sta-020.1-2020_911_call.pdf"
)


def download_pdf(url: str, dst_path: Path) -> Path:
    dst_path = dst_path.expanduser().resolve()
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[+] Downloading PDF from {url}")
    urllib.request.urlretrieve(url, dst_path)
    print(f"[+] Saved PDF to {dst_path}")
    return dst_path


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 200) -> list[Path]:
    """
    Render each PDF page to a PNG image using PyMuPDF.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_path.expanduser().resolve()
    print(f"[+] Rendering pages from {pdf_path}")

    doc = fitz.open(pdf_path)
    image_paths: list[Path] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap(dpi=dpi)
        img_path = output_dir / f"page_{page_index + 1:03d}.png"
        pix.save(img_path.as_posix())
        image_paths.append(img_path)
        print(f"    - Rendered page {page_index + 1} -> {img_path.name}")

    doc.close()
    print(f"[+] Rendered {len(image_paths)} pages")
    return image_paths


def load_deepseek_ocr(device: str | None = None):
    """
    Load DeepSeek-OCR via Hugging Face transformers.
    """
    model_name = "deepseek-ai/DeepSeek-OCR"

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[+] Loading model {model_name} on {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_safetensors=True,
    )

    # DeepSeek-OCR uses bfloat16 internally for images/features; keep model in bfloat16
    dtype = torch.bfloat16
    model = model.to(device=device, dtype=dtype).eval()

    return tokenizer, model, device


def run_ocr_on_images(
    tokenizer,
    model,
    image_paths: list[Path],
    ocr_root_dir: Path,
    base_size: int = 1024,
    image_size: int = 640,
    start_page: int = 1,
    end_page: int | None = None,
):
    """
    Run DeepSeek-OCR on a subset of image files.
    """
    ocr_root_dir.mkdir(parents=True, exist_ok=True)
    prompt = "<image>\n<|grounding|>Convert the document to markdown. "

    total_pages = len(image_paths)
    if end_page is None or end_page > total_pages:
        end_page = total_pages

    if start_page < 1:
        start_page = 1

    if start_page > end_page:
        print(f"[!] start_page ({start_page}) > end_page ({end_page}); nothing to do.")
        return

    num_to_process = end_page - start_page + 1
    print(
        f"[+] Running DeepSeek-OCR on pages {start_page}–{end_page} "
        f"({num_to_process} pages out of {total_pages})"
    )

    for idx, img_path in enumerate(image_paths, start=1):
        if idx < start_page or idx > end_page:
            continue

        print(f"    - Page {idx}: {img_path.name}")
        page_out_dir = ocr_root_dir / f"page_{idx:03d}"
        page_out_dir.mkdir(parents=True, exist_ok=True)

        _ = model.infer(
            tokenizer,
            prompt=prompt,
            image_file=img_path.as_posix(),
            output_path=page_out_dir.as_posix(),
            base_size=base_size,
            image_size=image_size,
            crop_mode=True,
            save_results=True,
            test_compress=True,
        )


def _read_first_text_like_file(page_dir: Path) -> str:
    """
    Read the first markdown or text file in page_dir.
    """
    md_files = sorted(page_dir.glob("*.md"))
    if md_files:
        return md_files[0].read_text(encoding="utf-8", errors="ignore")

    txt_files = sorted(page_dir.glob("*.txt"))
    if txt_files:
        return txt_files[0].read_text(encoding="utf-8", errors="ignore")

    # If DeepSeek saved into nested dirs, try recursively:
    md_files = sorted(page_dir.rglob("*.md"))
    if md_files:
        return md_files[0].read_text(encoding="utf-8", errors="ignore")

    txt_files = sorted(page_dir.rglob("*.txt"))
    if txt_files:
        return txt_files[0].read_text(encoding="utf-8", errors="ignore")

    print(f"[!] No .md or .txt files found in {page_dir}")
    return ""


def combine_pages_to_single_markdown(
    ocr_root_dir: Path,
    output_file: Path,
    add_page_separators: bool = True,
):
    """
    Combine per-page OCR outputs into a single markdown file.
    """
    page_dirs = sorted(
        [d for d in ocr_root_dir.iterdir() if d.is_dir() and d.name.startswith("page_")],
        key=lambda p: int(re.search(r"page_(\d+)", p.name).group(1)),
    )

    print(f"[+] Combining {len(page_dirs)} page folders into {output_file.name}")
    combined_chunks = []

    for idx, page_dir in enumerate(page_dirs, start=1):
        page_text = _read_first_text_like_file(page_dir)
        if not page_text.strip():
            continue

        if add_page_separators:
            combined_chunks.append(f"\n\n---\n\n<!-- Page {idx} -->\n\n")

        combined_chunks.append(page_text.strip())

    combined_text = "\n".join(combined_chunks).strip()
    output_file.write_text(combined_text, encoding="utf-8")
    print(f"[+] Wrote combined markdown to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run DeepSeek-OCR on a PDF and produce a single combined markdown file."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Path or URL to a PDF. If omitted, uses the NENA call-processing standard.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="deepseek_ocr_output",
        help="Directory to write OCR outputs.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cpu", "cuda"],
        help="Force device (cpu or cuda). If omitted, auto-detect.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="nena_document_full.md",
        help="Name of the combined markdown output file.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Decide which PDF to use and render all pages to images
    if args.pdf is None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = download_pdf(NENA_PDF_URL, Path(tmpdir) / "nena_sta_020.1_2020.pdf")
            image_dir = out_dir / "page_images"
            image_paths = pdf_to_images(pdf_path, image_dir)
    else:
        pdf_arg = args.pdf
        if pdf_arg.lower().startswith("http://") or pdf_arg.lower().startswith("https://"):
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = download_pdf(pdf_arg, Path(tmpdir) / "input.pdf")
                image_dir = out_dir / "page_images"
                image_paths = pdf_to_images(pdf_path, image_dir)
        else:
            pdf_path = Path(pdf_arg)
            image_dir = out_dir / "page_images"
            image_paths = pdf_to_images(pdf_path, image_dir)

    # 2) Load DeepSeek-OCR
    tokenizer, model, device = load_deepseek_ocr(device=args.device)

    # 3) Run OCR ONLY on pages 17–22 (inclusive)
    ocr_root_dir = out_dir / "ocr_results"
    run_ocr_on_images(
        tokenizer,
        model,
        image_paths,
        ocr_root_dir,
        start_page=17,
        end_page=22,
    )

    # 4) Combine per-page markdown/text into a single file
    combined_md_path = out_dir / args.output_md
    combine_pages_to_single_markdown(ocr_root_dir, combined_md_path)

    print(f"[+] All done. Combined result at:\n    {combined_md_path}")


if __name__ == "__main__":
    main()
