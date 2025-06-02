import UIKit
import Foundation

class SupabaseClient {
    func logFood(sessionId: UUID, timestamp: Date, note: String) {
        // Mock network request
        print("[Supabase] Log food: \(sessionId) \(timestamp) \(note)")
    }

    func uploadImage(sessionId: UUID, image: UIImage) {
        let imageId = UUID()
        print("[Supabase] Upload image: session \(sessionId)/\(imageId)")
    }
}
