import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else { exit(1) }
let url = URL(fileURLWithPath: args[1])

guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    exit(1)
}

var lines: [(y: CGFloat, text: String)] = []

let request = VNRecognizeTextRequest { request, error in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for observation in observations {
        if let topCandidate = observation.topCandidates(1).first {
            let boundingBox = observation.boundingBox
            // Hook titles are large text (height >= 0.025) at the very top (y >= 0.80)
            if boundingBox.origin.y >= 0.80 && boundingBox.size.height >= 0.025 {
                let text = topCandidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
                if !text.isEmpty {
                    lines.append((boundingBox.origin.y, text))
                }
            }
        }
    }
}
request.recognitionLanguages = ["ru-RU", "en-US"]
request.recognitionLevel = .accurate

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])

lines.sort { $0.y > $1.y }
let result = lines.map { $0.text }.joined(separator: " ")
print(result)
