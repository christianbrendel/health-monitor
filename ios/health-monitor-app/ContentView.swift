import SwiftUI

struct ContentView: View {
    @State private var showLogger = false

    var body: some View {
        NavigationView {
            VStack {
                Button("Log Food") {
                    showLogger = true
                }
                .padding()
            }
            .navigationTitle("Health Monitor")
            .sheet(isPresented: $showLogger) {
                FoodLogView()
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
