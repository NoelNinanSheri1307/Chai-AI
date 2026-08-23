import 'dart:typed_data';

import '../models/analysis_result.dart';

/// Contract for the analysis engine.
abstract class AnalysisRepository {
  Future<AnalysisResult> analyzeImage({
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
  });
}

