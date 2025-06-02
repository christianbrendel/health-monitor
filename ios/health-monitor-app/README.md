# Food Logger iOS App

This is a very small SwiftUI example that demonstrates the food logging
workflow. The app lets you capture multiple square photos with the camera,
optionally add a short note and then upload everything to Supabase. The
Supabase interactions are mocked.

## Features

- **Log Food** button on the main screen opens a logger view.
- Photos are taken with the camera. You can capture multiple photos in one
  session. Each image is cropped to a square before uploading.
- A text field lets you add a few sentences about the meal.
- On upload a random session id and timestamp are created. Images would be
  uploaded under `sessionId/<uuid>` on Supabase Storage. In this mock
  implementation the data is simply printed to the console.

This code can serve as a starting point for integrating the real Supabase SDK
and later expanding the application with additional features.

## Configuration

Create an `Info.plist` file in the project root (next to `FoodLoggerApp.swift`) with the following contents:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>FoodLoggerApp</string>
    <key>NSCameraUsageDescription</key>
    <string>We need camera access so you can take photos of your meals.</string>
</dict>
</plist>
```

The `NSCameraUsageDescription` key is required for camera access on iOS. Without it, the app will crash when attempting to take a photo.
