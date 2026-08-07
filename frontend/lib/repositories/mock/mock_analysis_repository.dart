import 'dart:math';
import 'dart:typed_data';

import '../../models/analysis_components.dart';
import '../../models/analysis_result.dart';
import '../../models/compare_result.dart';
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

  @override
  Future<CompareResult> compareImages({
    String? pathA,
    String? pathB,
    String? nameA,
    String? nameB,
    Uint8List? bytesA,
    Uint8List? bytesB,
  }) async {
    final seedA = _seedFrom(pathA, nameA);
    final seedB = _seedFrom(pathB, nameB);
    await Future<void>.delayed(const Duration(milliseconds: 2600));
    return _buildCompare(seedA, seedB, nameA, nameB);
  }

  int _seedFrom(String? path, String? name) {
    final raw = '${path ?? ''}::${name ?? ''}';
    return (raw.isEmpty ? DateTime.now().microsecondsSinceEpoch : raw.hashCode)
        .abs()
        .clamp(1, 1 << 30);
  }

  CompareResult _buildCompare(int seedA, int seedB, String? nameA, String? nameB) {
    final rng = Random(seedA + seedB);
    final similarity = (0.3 + rng.nextDouble() * 0.55).clamp(0.0, 1.0);
    final aiProbability = (0.18 + rng.nextDouble() * 0.68).clamp(0.0, 1.0);

    final regions = <HeatmapRegion>[];
    if (rng.nextBool()) {
      regions.add(HeatmapRegion(
        x: 0.35 + rng.nextDouble() * 0.2,
        y: 0.3 + rng.nextDouble() * 0.2,
        width: 0.2 + rng.nextDouble() * 0.2,
        height: 0.2 + rng.nextDouble() * 0.2,
        intensity: 0.6 + rng.nextDouble() * 0.35,
        label: 'Divergent region',
      ));
    }

    return CompareResult(
      labelA: nameA ?? 'Image A',
      labelB: nameB ?? 'Image B',
      similarity: similarity,
      aiProbability: aiProbability,
      similarities: const [
        'Shared color palette across both images',
        'Consistent focal plane and lens profile',
        'Overlapping sensor noise characteristics',
      ],
      differences: const [
        'Background texture differs in the lower third',
        'Lighting direction is inconsistent between the two',
        'Metadata reports different capture devices',
      ],
      manipulatedRegions: regions,
    );
  }
}
