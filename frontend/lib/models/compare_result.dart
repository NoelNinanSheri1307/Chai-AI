import 'analysis_components.dart';

class CompareResult {
  final String labelA;
  final String labelB;
  final double similarity; // 0..1
  final double aiProbability; // 0..1
  final List<String> similarities;
  final List<String> differences;
  final List<HeatmapRegion> manipulatedRegions;

  const CompareResult({
    required this.labelA,
    required this.labelB,
    required this.similarity,
    required this.aiProbability,
    required this.similarities,
    required this.differences,
    required this.manipulatedRegions,
  });
}
