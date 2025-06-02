import SwiftUI
import UIKit

struct ImagePicker: UIViewControllerRepresentable {
    var imageHandler: (UIImage) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(imageHandler: imageHandler)
    }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let imageHandler: (UIImage) -> Void

        init(imageHandler: @escaping (UIImage) -> Void) {
            self.imageHandler = imageHandler
        }

        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let image = info[.originalImage] as? UIImage {
                imageHandler(image)
            }
            picker.dismiss(animated: true)
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            picker.dismiss(animated: true)
        }
    }
}

extension UIImage {
    func cropToSquare() -> UIImage? {
        let originalWidth  = self.size.width
        let originalHeight = self.size.height
        let sideLength = min(originalWidth, originalHeight)
        let xOffset = (originalWidth - sideLength) / 2.0
        let yOffset = (originalHeight - sideLength) / 2.0
        let cropRect = CGRect(x: xOffset, y: yOffset, width: sideLength, height: sideLength)
        guard let cgImage = self.cgImage?.cropping(to: cropRect) else { return nil }
        return UIImage(cgImage: cgImage, scale: self.scale, orientation: self.imageOrientation)
    }
}
