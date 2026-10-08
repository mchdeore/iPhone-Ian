---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, ocr, paddleocr, tesseract, easyocr, apple-vision]
---

# OCR — Engines for Phone Screens

**TL;DR**
- OCR is on Marc's action list ("how to code and train the OCR"). It also powers **deterministic reward checks** and **state verification**.
- Benchmarks disagree by domain. **PaddleOCR** usually wins on accuracy, **Tesseract** on speed and low effort, **EasyOCR** sits between, and **Apple Vision** is fast and accurate on macOS (anecdotal).
- No benchmark covers **phone UI captures**, so build a 200-image ground-truth set and measure all four.

**Builds on:** [[RL — Rewards and Success Detection from the Screen]] (OCR checks are rung 2 of the reward ladder) and [[Security — Prompt Injection and Pop-up Attacks on GUI Agents]] (OCR text is untrusted input).

## What benchmarks say (none on UI screenshots)

| Study | Domain | Result |
|---|---|---|
| arXiv 2510.03570 | Packaging labels (113 images) | **Tesseract** lowest CER (0.912) and best BLEU; EasyOCR good accuracy/multilingual balance; PaddleOCR CPU-only and slower [1] |
| arXiv 2506.17185 | Web-scraped images | **PaddleOCR** 0.579 bag-of-words accuracy vs EasyOCR 0.426 vs Tesseract 0.168 [2] |
| Codesota (Mar 2026) | One invoice, 24 items, Apple M-series | PaddleOCR 100%, Tesseract 87.5%, RapidOCR 75%, EasyOCR 62.5% (indicative only) [3] |
| imagetotable.ai | SROIE receipts | PaddleOCR 32.5% vs EasyOCR 14.8% field extraction (vendor) [4] |
| MCP OCR table | General | Apple Vision rated fastest and most accurate; zero dependencies on macOS (anecdotal) [5] |

Takeaway: **domain matters more than engine reputation**, so measure on our data.

## Phone-UI specifics

- Small fonts, icons mixed with text, high contrast, dark mode, and (via camera) moiré and glare.
- **Crop first:** run OCR on detected element boxes from YOLO, not the full frame. That's faster and more accurate.
- **Apple Vision** (`VNRecognizeTextRequest`) is attractive if the capture host is a Mac (USB capture path: [[Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)]]).
- **Fine-tuning:** PaddleOCR supports training its recogniser on custom data. Generate synthetic UI text crops in the Flask app with known strings, so labels are free.

## Evaluation plan

1. 200 captures (light/dark, 3 apps, camera and capture paths); label the text of 10 elements each.
2. Metrics: CER, exact-match per element, latency per crop (CPU and GPU).
3. Pick the engine per path (Mac host → Apple Vision vs Linux → PaddleOCR).

## Pitch in

- [ ] ML: build the 200-image set and the 4-engine harness (code in repo); post the table here.

## Sources

1. [OCR on packaging labels (arXiv 2510.03570)](https://arxiv.org/abs/2510.03570v1) `[Benchmark]`
2. [A Common Pool of Privacy Problems — OCR comparison (arXiv 2506.17185)](https://arxiv.org/pdf/2506.17185) `[Benchmark]`
3. [Codesota — best OCR for Python](https://codesota.com/ocr/best-for-python) `[Community]`
4. [PaddleOCR vs EasyOCR receipts](https://imagetotable.ai/fr/references/paddleocr-vs-easyocr-receipt-benchmark) `[Community]` (vendor)
5. [MCP OCR server comparison](https://glama.ai/mcp/servers/timaliev/mcp_ocr) `[Community]`
6. [LlamaIndex — best OCR libraries](https://llamaindex.ai/blog/best-ocr-libraries-for-developers) `[Community]`
