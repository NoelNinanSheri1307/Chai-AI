import 'dart:typed_data';

import '../../models/analysis_result.dart';
import '../analysis_repository.dart';
import 'mock_data.dart';

class MockAnalysisRepository implements AnalysisRepository {
  @override
  Future<AnalysisResult> analyzeImage({
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
  }) async {
    final seed = _seedFrom(imagePath, fileName);
    await Future<void>.delayed(
      Duration(milliseconds: 2200 + (seed % 12) * 220),
    );
    return MockData.buildAnalysisResult(
      seed: seed,
      imagePath: imagePath,
      imageBytes: imageBytes,
      fileName: fileName,
    );
  }

  int _seedFrom(String? path, String? name) {
    final raw = '${path ?? ''}::${name ?? ''}';
    return (raw.isEmpty ? DateTime.now().microsecondsSinceEpoch : raw.hashCode)
        .abs()
        .clamp(1, 1 << 30);
  }
}

