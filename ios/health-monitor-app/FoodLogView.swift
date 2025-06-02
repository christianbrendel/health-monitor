import SwiftUI
import UIKit

struct FoodLogView: View {
    @Environment(\.presentationMode) private var presentationMode
    @State private var note: String = ""
    @State private var images: [UIImage] = []
    @State private var showImagePicker = false

    private let supabase = SupabaseClient()

    var body: some View {
        NavigationView {
            VStack(alignment: .leading) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(images, id: \.self) { image in
                            Image(uiImage: image)
                                .resizable()
                                .scaledToFill()
                                .frame(width: 80, height: 80)
                                .clipped()
                                .cornerRadius(8)
                        }
                    }
                    .padding(.horizontal)
                }

                Button("Add Photo") {
                    showImagePicker = true
                }
                .padding()

                Text("Notes")
                    .font(.headline)
                    .padding(.horizontal)

                TextEditor(text: $note)
                    .frame(height: 100)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.gray.opacity(0.5)))
                    .padding()

                Spacer()
            }
            .navigationTitle("New Entry")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Upload") {
                        uploadEntry()
                    }
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
            .sheet(isPresented: $showImagePicker) {
                ImagePicker(imageHandler: { image in
                    if let squared = image.cropToSquare() {
                        images.append(squared)
                    }
                })
            }
        }
    }

    private func uploadEntry() {
        let sessionId = UUID()
        let timestamp = Date()
        supabase.logFood(sessionId: sessionId, timestamp: timestamp, note: note)
        for image in images {
            supabase.uploadImage(sessionId: sessionId, image: image)
        }
        presentationMode.wrappedValue.dismiss()
    }
}

struct FoodLogView_Previews: PreviewProvider {
    static var previews: some View {
        FoodLogView()
    }
}
