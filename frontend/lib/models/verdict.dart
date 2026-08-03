enum Verdict {
  original,
  aiEdited,
  aiGenerated;

  String get label {
    switch (this) {
      case Verdict.original:
        return 'Original';
      case Verdict.aiEdited:
        return 'AI Edited';
      case Verdict.aiGenerated:
        return 'AI Generated';
    }
  }

  static Verdict fromLabel(String label) {
    for (final v in Verdict.values) {
      if (v.label.toLowerCase() == label.toLowerCase()) return v;
    }
    return Verdict.original;
  }
}

enum RiskLevel {
  low,
  medium,
  high;

  String get label {
    switch (this) {
      case RiskLevel.low:
        return 'Low';
      case RiskLevel.medium:
        return 'Medium';
      case RiskLevel.high:
        return 'High';
    }
  }
}

enum IndicatorType {
  frequency('Frequency inconsistencies'),
  texture('Texture anomalies'),
  metadata('Metadata mismatch'),
  diffusion('Diffusion artifacts'),
  compression('Compression artifacts');

  final String label;
  const IndicatorType(this.label);
}

enum ScoreCategory {
  texture('Texture'),
  metadata('Metadata'),
  lighting('Lighting'),
  frequency('Frequency'),
  noisePattern('Noise pattern'),
  compression('Compression'),
  edgeConsistency('Edge consistency'),
  colorDistribution('Color distribution');

  final String label;
  const ScoreCategory(this.label);
}

enum HeatmapMode {
  original('Original'),
  heatmap('Heatmap'),
  split('Split view');

  final String label;
  const HeatmapMode(this.label);
}
