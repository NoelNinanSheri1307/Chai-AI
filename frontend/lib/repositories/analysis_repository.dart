import 'dart:typed_data';

import '../models/analysis_result.dart';
import '../models/compare_result.dart';

/// Contract for the analysis engine.
///
/// The mock implementation returns realistic simulated results. When the real
/// backend is available, swap the provider for an [ApiAnalysisRepository]
/// implementing this same interface — the UI does not need to change.
abstract class AnalysisRepository {
  Future<AnalysisResult> analyzeImage({
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
  });

  Future<CompareResult> compareImages({
    String? pathA,
    String? pathB,
    String? nameA,
    String? nameB,
    Uint8List? bytesA,
    Uint8List? bytesB,
  });
}
