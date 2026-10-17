// Local owned PNG recognition through macOS Vision. No capture or device control.
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: owned-ocr owned-image.png\n", stderr); exit(2)
}
do {
    let url = URL(fileURLWithPath: CommandLine.arguments[1])
    let bytes = try Data(contentsOf: url)
    guard let image = NSBitmapImageRep(data: bytes) else {
        fputs("Unreadable owned image\n", stderr); exit(2)
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(url: url, options: [:]).perform([request])
    let rows: [[String: Any]] = (request.results ?? []).compactMap { result in
        guard let text = result.topCandidates(1).first else { return nil }
        let b = result.boundingBox
        return ["text": text.string, "confidence": text.confidence,
                "box": ["x": b.origin.x * Double(image.pixelsWide),
                        "y": (1 - b.origin.y - b.height) * Double(image.pixelsHigh),
                        "width": b.width * Double(image.pixelsWide),
                        "height": b.height * Double(image.pixelsHigh)]]
    }
    let output = try JSONSerialization.data(withJSONObject: rows, options: [.sortedKeys])
    FileHandle.standardOutput.write(output)
    FileHandle.standardOutput.write(Data([10]))
} catch {
    fputs("Owned OCR failed: \(error.localizedDescription)\n", stderr); exit(1)
}
