import 'verdict.dart';

/// A single forensic measurement contributing to the final verdict.
class ForensicScore {
  final ScoreCategory category;
  final double value; // 0..1

  const ForensicScore({required this.category, required this.value});
}

/// A detected indicator and its evidence.
class DetectedIndicator {
  final IndicatorType type;
  final double confidence; // 0..1
  final String severity; // Low | Moderate | Strong
  final String description;

  const DetectedIndicator({
    required this.type,
    required this.confidence,
    required this.severity,
    required this.description,
  });
}

/// A localized manipulation region returned by the heatmap model.
class HeatmapRegion {
  // Normalized (0..1) rectangle within the image.
  final double x;
  final double y;
  final double width;
  final double height;
  final double intensity; // 0..1
  final String label;

  const HeatmapRegion({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.intensity,
    required this.label,
  });
}

class HeatmapData {
  final List<HeatmapRegion> regions;
  final double overallManipulation; // 0..1

  const HeatmapData({required this.regions, required this.overallManipulation});
}
